$(function() {
	function readConfig(text) {
		var retval = {}

		const lines = text.split("\n")
		for (var i = 0; i < lines.length; i++) {
			const idx = lines[i].indexOf("=")
			if (idx > 0) {
				const name = lines[i].substring(0, idx - 1).trim()
				const value = lines[i].substring(idx + 1).trim()
				retval[name] = value
			}
		}

		return retval
	}

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

	function getFile(url) {
		return new Promise(function(resolve, reject) {
			fetch(url).then(function(response) {
				response.text().then(resolve).catch(reject)
			}).catch(reject)
		})
	}

	function getInfo(baseUrl) {
		return new Promise(function(resolve, reject) {
			getFile(baseUrl + "/mod.conf").then(function(text) {
				var config = readConfig(text)

				if (config["name"]) {
					$("#name").val(config["name"])
				}

				if (config["description"]) {
					const desc = config["description"]
					const idx = desc.indexOf(".")
					$("#shortDesc").val((idx < 5 || idx > 100) ? desc.substring(0, 100) : desc.substring(0, idx))
					$("#desc").val(desc)
				}

				resolve()
			}).catch(function() {
				reject()
			})
		})
	}

	function importInfo(urlstr) {
		// Convert to HTTPs
		try {
			var url = URI(urlstr).scheme("https")
				.username("")
				.password("")
		} catch(e) {
			return Promise.reject(e)
		}
		// Change domain
		url = url.hostname("raw.githubusercontent.com")

		// Rewrite path
		const re = /^\/([^\/]+)\/([^\/]+)\/?$/
		const results = re.exec(url.path())
		if (results == null || results.length != 3) {
			return Promise.reject("Unable to parse URL - please provide a direct URL to the repo")
		}
		url.path("/" + results[1] + "/" + results[2].replace(".git", "") + "/master")

		return getInfo(url.toString())
	}

	$(".pkg_meta").hide()
	$(".pkg_wiz_1").show()
	$("#pkg_wiz_1_next").click(function() {
		const repoURL = $("#repo").val();
		if (repoIsSupported(repoURL)) {
			$(".pkg_wiz_1").hide()
			$(".pkg_wiz_2").show()
			$(".pkg_repo").hide()

			importInfo(repoURL).then(finish).catch(function(x) {
				alert(x)
				$(".pkg_wiz_1").show()
				$(".pkg_wiz_2").hide()
				$(".pkg_repo").show()
			})
		} else {
			finish()
		}
	})
})
