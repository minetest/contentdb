// @author rubenwardy
// @license magnet:?xt=urn:btih:1f739d935676111cfff4b4693e3816e664797050&dn=gpl-3.0.txt GPL-v3-or-Later

"use strict";

window.addEventListener("load", () => {
	function setup_toggle(type) {
		const toggle = document.getElementById("set_" + type);

		function on_change() {
			const rel = document.getElementById(type + "_rel");
			if (toggle.checked) {
				rel.parentElement.style.opacity = "1";
			} else {
				// $("#" + type + "_rel").attr("disabled", "disabled");
				rel.parentElement.style.opacity = "0.4";
				rel.value = document.querySelector(`#${type}_rel option:first-child`).value;
				rel.dispatchEvent(new Event("change"));
			}
		}

		toggle.addEventListener("change", on_change);
		on_change();
	}

	setup_toggle("min");
	setup_toggle("max");
});
