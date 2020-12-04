// @author rubenwardy
// @license magnet:?xt=urn:btih:1f739d935676111cfff4b4693e3816e664797050&dn=gpl-3.0.txt GPL-v3-or-Later

$(function() {
	$("#type").change(function() {
		$(".not_mod, .not_game, .not_txp").show()
		$(".not_" + this.value.toLowerCase()).hide()
	})
	$(".not_mod, .not_game, .not_txp").show()
	$(".not_" + $("#type").val().toLowerCase()).hide()

	$("#forums").on('paste', function(e) {
		try {
			const pasteData = e.originalEvent.clipboardData.getData('text');
			const url = new URL(pasteData);
			if (url.hostname == "forum.minetest.net") {
				$(this).val(url.searchParams.get("t"));
				e.preventDefault();
			}
		} catch (e) {
			console.log("Not a URL");
		}
	});

	let hint = null;
	function showHint(ele, text) {
		if (hint) {
			hint.remove();
		}

		hint = ele.parent()
				.append(`<div class="alert alert-warning my-3">${text}</div>`)
				.find(".alert");
	}

	let hint_mtmods = `Tip:
		Don't include <i>Minetest</i>, <i>mod</i>, or <i>modpack</i> anywhere in the short description.
		It is unnecessary and wastes characters.`;

	let hint_thegame = `Tip:
		It's obvious that this adds something to Minetest,
		there's no need to use phrases such as \"adds X to the game\".`

	$("#short_desc").on("change paste keyup", function() {
		const val = $(this).val().toLowerCase();
		if (val.indexOf("minetest") >= 0 || val.indexOf("mod") >= 0 ||
				val.indexOf("modpack") >= 0 || val.indexOf("mod pack") >= 0) {
			showHint($(this), hint_mtmods);
		} else if (val.indexOf("the game") >= 0) {
			showHint($(this), hint_thegame);
		} else if (hint) {
			hint.remove();
			hint = null;
		}
	})

	const btn = $("#forums").parent().find("label").append("<a class='ml-3 btn btn-sm btn-primary'>Open</a>");
	btn.click(function() {
		const id = $("#forums").val();
		if (/^\d+$/.test(id)) {
			window.open("https://forum.minetest.net/viewtopic.php?t=" + id, "_blank");
		}
	});
})
