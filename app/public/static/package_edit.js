// @author rubenwardy
// @license magnet:?xt=urn:btih:1f739d935676111cfff4b4693e3816e664797050&dn=gpl-3.0.txt GPL-v3-or-Later

$(function() {
	$("#type").change(function() {
		$(".not_mod, .not_game, .not_txp").show()
		$(".not_" + this.value.toLowerCase()).hide()
	})
	$(".not_mod, .not_game, .not_txp").show()
	$(".not_" + $("#type").val().toLowerCase()).hide()
})
