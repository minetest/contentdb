// @author rubenwardy
// @license magnet:?xt=urn:btih:1f739d935676111cfff4b4693e3816e664797050&dn=gpl-3.0.txt GPL-v3-or-Later

const min = $("#min_rel");
const max = $("#max_rel");
const none = parseInt($("#min_rel option:first-child").attr("value"));
const warning = $("#minmax_warning");

function ver_check() {
	const minv = parseInt(min.val());
	const maxv = parseInt(max.val());

	if (minv != none && maxv != none && minv > maxv) {
		warning.show();
	} else {
		warning.hide();
	}
}

min.change(ver_check);
max.change(ver_check);
