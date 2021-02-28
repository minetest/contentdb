// @author rubenwardy
// @license magnet:?xt=urn:btih:1f739d935676111cfff4b4693e3816e664797050&dn=gpl-3.0.txt GPL-v3-or-Later

$(function() {
	function finish() {
		$(".pkg_wiz_1").hide()
		$(".pkg_wiz_2").hide()
		$(".pkg_repo").show()
		$(".pkg_meta").show()
	}

	$(".pkg_meta").hide()
	$(".pkg_wiz_1").show()

	$("#pkg_wiz_1_skip").click(finish)
	$("#pkg_wiz_1_next").click(function() {
		const repoURL = $("#repo").val();
		if (repoURL.trim() != "") {
			$(".pkg_wiz_1").hide()
			$(".pkg_wiz_2").show()
			$(".pkg_repo").hide()

			function setField(id, value) {
				if (value && value != "") {
					const ele = $(id);
					ele.val(value);
					ele.trigger("change");

					// EasyMDE doesn't always refresh the codemirror correctly
					if (ele[0].easy_mde) {
						setTimeout(() => {
							ele[0].easy_mde.value(value);
							ele[0].easy_mde.codemirror.refresh()
						}, 100);
					}
				}
			}

			performTask("/tasks/getmeta/new/?url=" + encodeURI(repoURL)).then(function(result) {
				setField("#name", result.name);
				setField("#title", result.title);
				setField("#repo", result.repo || repoURL);
				setField("#issueTracker", result.issueTracker);
				setField("#desc", result.desc);
				setField("#short_desc", result.short_desc);
				setField("#forums", result.forums);
				if (result.type && result.type.length > 2) {
					$("#type").val(result.type);
				}

				finish();
			}).catch(function(e) {
				alert(e);
				$(".pkg_wiz_1").show();
				$(".pkg_wiz_2").hide();
				$(".pkg_repo").show();
				// finish()
			});
		} else {
			finish()
		}
	})
})
