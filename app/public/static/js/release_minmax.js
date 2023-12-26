// @author rubenwardy
// @license magnet:?xt=urn:btih:1f739d935676111cfff4b4693e3816e664797050&dn=gpl-3.0.txt GPL-v3-or-Later

"use strict";

window.addEventListener("load", () => {
	const min = document.getElementById("min_rel");
	const max = document.getElementById("max_rel");
	const none = parseInt(document.querySelector("#min_rel option:first-child").value);
	const latestMax = parseInt(document.querySelector("#max_rel option:last-child").value);
	const warningMinMax = document.getElementById("minmax_warning");
	const warningMax = document.getElementById("latest_release");

	function ver_check() {
		const minv = parseInt(min.value);
		const maxv = parseInt(max.value);
		if (minv != none && maxv != none && minv > maxv) {
			warningMinMax.classList.remove("d-none");
		} else {
			warningMinMax.classList.add("d-none");
		}

		if (maxv == latestMax) {
			warningMax.classList.remove("d-none");
		} else {
			warningMax.classList.add("d-none");
		}
	}

	min.addEventListener("change", ver_check);
	max.addEventListener("change", ver_check);
	ver_check();
});
