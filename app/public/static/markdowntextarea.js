$("textarea.markdown").each(function() {
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

	this.easy_mde = new EasyMDE({
		element: this,
		hideIcons: ["image"],
		showIcons: ["code", "table"],
		forceSync: true,
		previewRender: (plainText, preview) => {
			if (timeout_id) {
				clearTimeout(timeout_id);
			}

			timeout_id = setTimeout(() => {
				render(plainText, preview);
				timeout_id = null;
			}, 500);

			return preview.innerHTML;
		}
	});
})
