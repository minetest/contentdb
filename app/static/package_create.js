$(function() {
	function finish() {
		$(".pkg_wiz_1").hide()
		$(".pkg_wiz_2").hide()
		$(".pkg_repo").show()
		$(".pkg_meta").show()
	}

	function getJSON(url) {
		return new Promise(function(resolve, reject) {
			fetch(url).then(function(response) {
				response.text().then(function(txt) {
					resolve(JSON.parse(txt))
				}).catch(reject)
			}).catch(reject)
		})
	}

	function performTask(url) {
		return new Promise(function(resolve, reject) {
			getJSON(url).then(function(startResult) {
				console.log(startResult)
				if (typeof startResult.poll_url == "string") {
					var tries = 0;
					function retry() {
						tries++;
						if (tries > 10) {
							reject("timeout")
						} else {
							console.log("Polling task in " + (tries*100) + "ms")
							setTimeout(step, tries*100)
						}
					}
					function step() {
						getJSON(startResult.poll_url).then(function(res) {
							if (res.status == "SUCCESS") {
								console.log("Got result")
								resolve(res.result)
							} else {
								retry()
							}
						}).catch(retry)
					}
					retry()
				} else {
					reject("Start task didn't return string!")
				}
			}).catch(reject)
		})
	}

	function repoIsSupported(url) {
		try {
			return URI(url).hostname() == "github.com"
		} catch(e) {
			return false
		}
	}

	$(".pkg_meta").hide()
	$(".pkg_wiz_1").show()
	$("#pkg_wiz_1_next").click(function() {
		const repoURL = $("#repo").val();
		if (repoIsSupported(repoURL)) {
			$(".pkg_wiz_1").hide()
			$(".pkg_wiz_2").show()
			$(".pkg_repo").hide()

			performTask("/tasks/getmeta/new/?url=" + encodeURI(repoURL)).then(function(result) {
				console.log(result)
				$("#name").val(result.name)
				const desc = result.description || ""
				if (desc.length > 0) {
					const idx = desc.indexOf(".")
					$("#shortDesc").val((idx < 5 || idx > 100) ? desc.substring(0, Math.min(desc.length, 100)) : desc.substring(0, idx))
					$("#desc").val(desc)
				}
				finish()
			}).catch(function(e) {
				alert(e)
				$(".pkg_wiz_1").show()
				$(".pkg_wiz_2").hide()
				$(".pkg_repo").show()
				// finish()
			})
		} else {
			finish()
		}
	})
})
