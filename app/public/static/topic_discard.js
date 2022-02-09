// @author rubenwardy
// @license magnet:?xt=urn:btih:1f739d935676111cfff4b4693e3816e664797050&dn=gpl-3.0.txt GPL-v3-or-Later

$(".topic-discard").click(function() {
	const ele = $(this);
	const tid = ele.attr("data-tid");
	const discard = !ele.parent().parent().hasClass("discardtopic");
	fetch(new Request("/api/topic_discard/?tid=" + tid +
			"&discard=" + (discard ? "true" : "false"), {
		method: "post",
		credentials: "same-origin",
		headers: {
			"Accept": "application/json",
			"X-CSRFToken": csrf_token,
		},
	})).then(function(response) {
		response.text().then(function(txt) {
			console.log(JSON.parse(txt));
			if (JSON.parse(txt).discarded) {
				ele.parent().parent().addClass("discardtopic");
				ele.removeClass("btn-danger");
				ele.addClass("btn-success");
				ele.text("Show");
			} else {
				ele.parent().parent().removeClass("discardtopic");
				ele.removeClass("btn-success");
				ele.addClass("btn-danger");
				ele.text("Discard");
			}
		}).catch(console.log)
	}).catch(console.log)
});
