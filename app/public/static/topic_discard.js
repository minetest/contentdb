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
