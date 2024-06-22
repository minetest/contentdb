// @author rubenwardy
// @license magnet:?xt=urn:btih:1f739d935676111cfff4b4693e3816e664797050&dn=gpl-3.0.txt GPL-v3-or-Later

"use strict";

window.addEventListener("load", () => {
	function check_opt() {
		if (document.querySelector("input[name='upload_mode']:checked").value === "vcs") {
			document.getElementById("file_upload").parentElement.classList.add("d-none");
			document.getElementById("vcs_label").parentElement.classList.remove("d-none");
		} else {
			document.getElementById("file_upload").parentElement.classList.remove("d-none");
			document.getElementById("vcs_label").parentElement.classList.add("d-none");
		}
	}

	document.querySelectorAll("input[name='upload_mode']").forEach(x => x.addEventListener("change", check_opt));
	check_opt();
});
