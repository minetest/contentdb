// @author rubenwardy
// @license magnet:?xt=urn:btih:1f739d935676111cfff4b4693e3816e664797050&dn=gpl-3.0.txt GPL-v3-or-Later

"use strict";

function hide(sel) {
	document.querySelectorAll(sel).forEach(x => x.classList.add("d-none"));
}

function show(sel) {
	document.querySelectorAll(sel).forEach(x => x.classList.remove("d-none"));
}


window.addEventListener("load", () => {
	function finish() {
		hide(".pkg_wiz_1");
		hide(".pkg_wiz_2");
		show(".pkg_repo");
		show(".pkg_meta");
	}

	hide(".pkg_meta");
	show(".pkg_wiz_1");

	document.getElementById("pkg_wiz_1_skip").addEventListener("click", finish);
	document.getElementById("pkg_wiz_1_next").addEventListener("click", () => {
		const repoURL = document.getElementById("repo").value;
		if (repoURL.trim() !== "") {
			hide(".pkg_wiz_1");
			show(".pkg_wiz_2");
			hide(".pkg_repo");

			function setField(sel, value) {
				if (value && value !== "") {
					const ele = document.querySelector(sel);
					ele.value = value;
					ele.dispatchEvent(new Event("change"));

					// EasyMDE doesn't always refresh the codemirror correctly
					if (ele.easy_mde) {
						setTimeout(() => {
							ele.easy_mde.value(value);
							ele.easy_mde.codemirror.refresh()
						}, 100);
					}
				}
			}

			performTask("/tasks/getmeta/new/?url=" + encodeURI(repoURL)).then(function(result) {
				setField("#name", result.name);
				setField("#title", result.title);
				setField("#repo", result.repo || repoURL);
				setField("#issueTracker", result.issueTracker);
				setField("#desc", result.desc);
				setField("#short_desc", result.short_desc);
				setField("#forums", result.forums);
				if (result.type && result.type.length > 2) {
					setField("[name='type']", result.type);
				}

				finish();
			}).catch(function(e) {
				alert(e);
				show(".pkg_wiz_1");
				hide(".pkg_wiz_2");
				show(".pkg_repo");
				// finish()
			});
		} else {
			finish();
		}
	})
})
