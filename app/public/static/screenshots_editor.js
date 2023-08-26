// @author rubenwardy
// @license magnet:?xt=urn:btih:1f739d935676111cfff4b4693e3816e664797050&dn=gpl-3.0.txt GPL-v3-or-Later

"use strict";

window.addEventListener("load", () => {
	function update() {
		const elements = [...document.querySelector(".sortable").children];
		const ids = elements.map(x => x.dataset.id).filter(x => x);
		document.querySelector("input[name='order']").value = ids.join(",");
	}

	update();
	$(".sortable").sortable({
		update: update
	});
})
