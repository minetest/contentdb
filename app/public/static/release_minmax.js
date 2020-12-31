const min = $("#min_rel");
const max = $("#max_rel");
const none = $("#min_rel option:first-child").attr("value");
const warning = $("#minmax_warning");

function ver_check() {
	const minv = min.val();
	const maxv = max.val();

	if (minv != none && maxv != none && minv > maxv) {
		warning.show();
	} else {
		warning.hide();
	}
}

min.change(ver_check);
max.change(ver_check);
