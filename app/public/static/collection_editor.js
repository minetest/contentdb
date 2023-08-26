// @author rubenwardy
// @license magnet:?xt=urn:btih:1f739d935676111cfff4b4693e3816e664797050&dn=gpl-3.0.txt GPL-v3-or-Later

"use strict";


function updateOrder() {
	const elements = [...document.querySelector(".sortable").children];
	const ids = elements
		.filter(x => !x.classList.contains("d-none"))
		.map(x => x.dataset.id)
		.filter(x => x);

	document.querySelector("input[name='order']").value = ids.join(",");
}


function removePackage(card) {
	const message = document.getElementById("confirm_delete").innerText.trim();
	const title = card.querySelector("h5 a").innerText.trim();
	if (!confirm(message.replace("{title}", title))) {
		return;
	}

	card.querySelector("input[name^=package_removed]").value = "1";
	card.classList.add("d-none");
	onPackageQueryUpdate();
	updateOrder();
}


function restorePackage(id) {
	const idElement = document.querySelector(`[value='${id}']`);
	if (!idElement) {
		return false;
	}

	const card = idElement.parentNode.parentNode.parentNode.parentNode;
	console.assert(card.classList.contains("card"));

	card.classList.remove("d-none");
	card.querySelector("input[name^=package_removed]").value = "0";
	card.scrollIntoView();
	onPackageQueryUpdate();
	updateOrder();
	return true;
}


function getAddedPackages() {
	const ids = document.querySelectorAll("#package_list > article:not(.d-none) input[name^=package_ids]");
	return [...ids].map(x => x.value);
}


function escapeHtml(unsafe) {
	return unsafe
		.replace(/&/g, "&amp;")
		.replace(/</g, "&lt;")
		.replace(/>/g, "&gt;")
		.replace(/"/g, "&quot;")
		.replace(/'/g, "&#039;");
}


function addPackage(pkg) {
	document.getElementById("add_package").value = "";
	document.getElementById("add_package_results").innerHTML = "";

	const id = `${pkg.author}/${pkg.name}`;
	if (restorePackage(id)) {
		return;
	}

	const nextId = document.querySelectorAll("input[name^=package_ids-]").length;
	const url = `/packages/${id}/`;
	const temp = document.createElement("div");
	temp.innerHTML = `
		<article class="card my-3" data-id="${escapeHtml(id)}">
			<div class="card-body">
				<div class="row">
					<div class="col-auto text-muted pe-2">
						<i class="fas fa-bars"></i>
					</div>
					<div class="col">
						<button class="btn btn-sm btn-danger remove-package float-end" type="button" aria-label="Remove">
							<i class="fas fa-trash"></i>
						</button>
						<h5>
							<a href="${escapeHtml(url)}" target="_blank">
								${escapeHtml(pkg.title)} by ${escapeHtml(pkg.author)}
							</a>
						</h5>
						<p class="text-muted">
							${escapeHtml(pkg.short_description)}
						</p>
						<input id="package_ids-${nextId}" name="package_ids-${nextId}" type="hidden" value="${id}">
						<input id="package_removed-${nextId}" name="package_removed-${nextId}" type="hidden" value="0">
						<div>
							<label for="descriptions-${nextId}" class="form-label">Short Description</label>
							<input class="form-control" id="descriptions-${nextId}" maxlength="500" minlength="0"
								name="descriptions-${nextId}" type="text" value="">
							<small class="form-text text-muted">You can replace the description with your own</small>
						</div>
					</div>
				</div>
			</div>
		</article>
	`;

	const card = temp.children[0];
	document.getElementById("package_list").appendChild(card);
	card.scrollIntoView();

	const button = card.querySelector(".btn-danger");
	button.addEventListener("click", () => removePackage(card));

	updateOrder();
}


function updateResults(packages) {
	const results = document.getElementById("add_package_results");
	results.innerHTML = "";
	document.getElementById("add_package_empty").style.display = packages.length === 0 ? "block" : "none";

	const alreadyAdded = getAddedPackages();
	packages.slice(0, 5).forEach(pkg => {
		const result = document.createElement("a");
		result.classList.add("list-group-item");
		result.classList.add("list-group-item-action");
		result.innerText = `${pkg.title} by ${pkg.author}`;
		if (alreadyAdded.includes(`${pkg.author}/${pkg.name}`)) {
			result.classList.add("active");
			result.innerHTML = "<i class='fas fa-check me-3 text-success'></i>" + result.innerHTML;
		}
		result.addEventListener("click", () => addPackage(pkg));
		results.appendChild(result);
	});
}


let currentRequestId;

async function fetchPackagesAndUpdateResults(query) {
	const requestId = Math.random() * 1000000;
	currentRequestId = requestId;
	if (query === "") {
		updateResults([]);
		return;
	}

	const url = new URL("/api/packages/", window.location.origin);
	url.searchParams.set("q", query);
	const resp = await fetch(url.toString());
	if (!resp.ok) {
		return;
	}

	const packages = await resp.json();
	if (currentRequestId !== requestId) {
		return;
	}

	updateResults(packages);
}


let timeoutHandle;
function onPackageQueryUpdate() {
	const query = document.getElementById("add_package").value.trim();
	if (timeoutHandle) {
		clearTimeout(timeoutHandle);
	}
	timeoutHandle = setTimeout(
		() => fetchPackagesAndUpdateResults(query).catch(console.error),
		200);
}


window.addEventListener("load", () => {
	document.querySelectorAll(".remove-package").forEach(button => {
		const card = button.parentNode.parentNode.parentNode.parentNode;
		console.assert(card.classList.contains("card"));

		const field = card.querySelector("input[name^=package_removed]");

		// Reloading/validation errors will cause this to be 1 at load
		if (field && field.value === "1") {
			card.classList.add("d-none");
		} else {
			button.addEventListener("click", () => removePackage(card));
		}
	});

	const addPackageQuery = document.getElementById("add_package");
	addPackageQuery.value = "";
	addPackageQuery.classList.remove("d-none");
	addPackageQuery.addEventListener("input", onPackageQueryUpdate);
	addPackageQuery.addEventListener('keydown',(e)=>{
		if (e.key === "Enter") {
			onPackageQueryUpdate();
			e.preventDefault();
		}
	})

	updateOrder();
	$(".sortable").sortable({
		update: updateOrder,
	});
});
