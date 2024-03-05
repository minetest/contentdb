// @author rubenwardy
// @license magnet:?xt=urn:btih:1f739d935676111cfff4b4693e3816e664797050&dn=gpl-3.0.txt GPL-v3-or-Later

"use strict";

const disableAll = document.getElementById("disable-all");
disableAll.classList.remove("d-none");
disableAll.addEventListener("click", () => {
	document.querySelectorAll("input[type='checkbox']").forEach(x => { x.checked = false; });
});
