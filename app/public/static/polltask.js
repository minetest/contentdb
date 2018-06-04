// @author rubenwardy
// @license magnet:?xt=urn:btih:1f739d935676111cfff4b4693e3816e664797050&dn=gpl-3.0.txt GPL-v3-or-Later

function getJSON(url, method) {
	return new Promise(function(resolve, reject) {
		fetch(new Request(url, {
			method: method || "get",
			credentials: "same-origin",
			headers: {
				"Accept": "application/json",
			},
		})).then(function(response) {
			response.text().then(function(txt) {
				resolve(JSON.parse(txt))
			}).catch(reject)
		}).catch(reject)
	})
}

function pollTask(poll_url, disableTimeout) {
	return new Promise(function(resolve, reject) {
		var tries = 0;
		function retry() {
			tries++;
			if (!disableTimeout && tries > 20) {
				reject("timeout")
			} else {
				const interval = Math.min(tries*100, 1000)
				console.log("Polling task in " + interval + "ms")
				setTimeout(step, interval)
			}
		}
		function step() {
			getJSON(poll_url).then(function(res) {
				if (res.status == "SUCCESS") {
					console.log("Got result")
					resolve(res.result)
				} else if (res.status == "FAILURE" || res.status == "REVOKED") {
					reject(res.error || "Unknown server error")
				} else {
					retry()
				}
			}).catch(retry)
		}
		retry()
	})
}


function performTask(url) {
	return new Promise(function(resolve, reject) {
		getJSON(url, "post").then(function(startResult) {
			console.log(startResult)
			if (typeof startResult.poll_url == "string") {
				pollTask(startResult.poll_url).then(resolve).catch(reject)
			} else {
				reject("Start task didn't return string!")
			}
		}).catch(reject)
	})
}
