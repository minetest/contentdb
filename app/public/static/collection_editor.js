// @author rubenwardy
// @license magnet:?xt=urn:btih:1f739d935676111cfff4b4693e3816e664797050&dn=gpl-3.0.txt GPL-v3-or-Later


function handleRemovePackage(card) {
	if (!confirm(card.getAttribute("data-delete-confirm"))) {
		return;
	}
	card.querySelector("input[name^=package_removed]").value = "1";
	card.classList.add("d-none");
}

window.onload = () => {
	console.log("Loaded");
	document.querySelectorAll(".remove-package").forEach(button => {
		const card = button.parentNode.parentNode;
		const field = card.querySelector("input[name^=package_removed]");

		// Reloading/validation errors will cause this to be 1 at load
		if (field && field.value === "1") {
			card.classList.add("d-none");
		} else {
			button.addEventListener("click", () => handleRemovePackage(card));
		}
	});
};
