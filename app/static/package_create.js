$(function() {
	function finish() {
		$(".pkg_wiz_1").hide()
		$(".pkg_wiz_2").hide()
		$(".pkg_repo").show()
		$(".pkg_meta").show()
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
				$("#name").val(result.name || "")
				$("#title").val(result.title || "")
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
