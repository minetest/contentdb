var min = $("#min_rel");
var max = $("#max_rel");
var none = $("#min_rel option:first-child").attr("value");
var warning = $("#minmax_warning");

function ver_check() {
	var minv = min.val();
	var maxv = max.val();

	if (minv != none && maxv != none && minv > maxv) {
		warning.show();
	} else {
		warning.hide();
	}
}

min.change(ver_check);
max.change(ver_check);
