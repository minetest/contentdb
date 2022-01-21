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

	function urlInserter(url) {
		return (editor) => {
			var cm = editor.codemirror;
			var stat = getState(cm);
			var options = editor.options;
			_replaceSelection(cm, stat.table, `[](${url})`);
		};
	}

	this.easy_mde = new EasyMDE({
		element: this,
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
//			{
//				name: "rules",
//				className: "fa fa-book",
//				title: "others buttons",
//				children: [
//					{
//						name: "rules",
//						action: urlInserter("/policy_and_guidance/#2-accepted-content"),
//						className: "fa fa-star",
//						title: "2. Accepted content",
//						text: "2. Accepted content",
//					},
//				]
//			},
		],
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
