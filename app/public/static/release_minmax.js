// @author rubenwardy
// @license magnet:?xt=urn:btih:1f739d935676111cfff4b4693e3816e664797050&dn=gpl-3.0.txt GPL-v3-or-Later

"use strict";

window.addEventListener("load", () => {
	const min = document.getElementById("min_rel");
	const max = document.getElementById("max_rel");
	const none = parseInt(document.querySelector("#min_rel option:first-child").value);
	const warning = document.getElementById("minmax_warning");

	function ver_check() {
		const minv = parseInt(min.value);
		const maxv = parseInt(max.value);
		if (minv != none && maxv != none && minv > maxv) {
			warning.style.display = "block";
		} else {
			warning.style.display = "none";
		}
	}

	min.addEventListener("change", ver_check);
	max.addEventListener("change", ver_check);
	ver_check();
});
