// @author rubenwardy
// @license magnet:?xt=urn:btih:1f739d935676111cfff4b4693e3816e664797050&dn=gpl-3.0.txt GPL-v3-or-Later

"use strict";

document.querySelectorAll("textarea.markdown").forEach((element) => {
	async function render(plainText, preview) {
		const response = await fetch(new Request("/api/markdown/", {
			method: "POST",
			credentials: "same-origin",
			body: plainText,
			headers: {
				"Accept": "text/html; charset=UTF-8",
			},
		}));

		preview.innerHTML = await response.text();
	}

	let timeout_id = null;
	element.easy_mde = new EasyMDE({
		element: element,
		hideIcons: ["image"],
		showIcons: ["code", "table"],
		forceSync: true,
		toolbar: [
			"bold",
			"italic",
			"heading",
			"|",
			"code",
			"quote",
			"unordered-list",
			"ordered-list",
			"|",
			"link",
			"table",
			"|",
			"preview",
			"side-by-side",
			"fullscreen",
			"|",
			"guide",
		],
		previewRender: (plainText, preview) => {
			if (timeout_id) {
				clearTimeout(timeout_id);
			}

			timeout_id = setTimeout(() => {
				render(plainText, preview).catch(console.error);
				timeout_id = null;
			}, 500);

			return preview.innerHTML;
		}
	});
})
