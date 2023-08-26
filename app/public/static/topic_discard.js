// @author rubenwardy
// @license magnet:?xt=urn:btih:1f739d935676111cfff4b4693e3816e664797050&dn=gpl-3.0.txt GPL-v3-or-Later

"use strict";

document.querySelectorAll(".topic-discard").forEach(ele => ele.addEventListener("click", (e) => {
	const row = ele.parentNode.parentNode;
	const tid = ele.getAttribute("data-tid");
	const discard = !row.classList.contains("discardtopic");
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
			if (JSON.parse(txt).discarded) {
				row.classList.add("discardtopic");
				ele.classList.remove("btn-danger");
				ele.classList.add("btn-success");
				ele.innerText = "Show";
			} else {
				row.classList.remove("discardtopic");
				ele.classList.remove("btn-success");
				ele.classList.add("btn-danger");
				ele.innerText = "Discard";
			}
		}).catch(console.error);
	}).catch(console.error);
}));
