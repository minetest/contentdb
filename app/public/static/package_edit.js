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
			var pasteData = e.originalEvent.clipboardData.getData('text')
			var url = new URL(pasteData);
			if (url.hostname == "forum.minetest.net") {
				$(this).val(url.searchParams.get("t"));
				e.preventDefault();
			}
		} catch (e) {
			console.log("Not a URL");
		}
	});

	var btn = $("#forums").parent().find("label").append("<a class='ml-3 btn btn-sm btn-primary'>Open</a>");
	btn.click(function() {
		var id = $("#forums").val();
		if (/^\d+$/.test(id)) {
			window.open("https://forum.minetest.net/viewtopic.php?t=" + id, "_blank");
		}
	});
})
