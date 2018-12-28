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
				if (value != "") {
					var ele = $(id);
					ele.val(value);
					ele.trigger("change");
				}
			}

			performTask("/tasks/getmeta/new/?url=" + encodeURI(repoURL)).then(function(result) {
				setField("#name", result.name);
				setField("#provides_str", result.provides);
				setField("#title", result.title);
				setField("#repo", result.repo || repoURL);
				setField("#issueTracker", result.issueTracker);
				setField("#desc", result.description);
				setField("#shortDesc", result.short_description);
				setField("#harddep_str", result.depends);
				setField("#softdep_str", result.optional_depends);
				setField("#shortDesc", result.short_description);
				setField("#forums", result.forumId);
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
