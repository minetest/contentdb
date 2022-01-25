document.querySelectorAll(".video-embed").forEach(ele => {
	try {
		const href = ele.getAttribute("href");
		const url = new URL(href);

		if (url.host == "www.youtube.com") {
			ele.addEventListener("click", () => {
				ele.parentNode.classList.add("d-block");
				ele.classList.add("embed-responsive");
				ele.classList.add("embed-responsive-16by9");
				ele.innerHTML = `
					<iframe title="YouTube video player" frameborder="0"
							allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
							allowfullscreen>
					</iframe>`;

				const embedURL = new URL("https://www.youtube.com/");
				embedURL.pathname = "/embed/" + url.searchParams.get("v");
				embedURL.searchParams.set("autoplay", "1");

				const iframe = ele.children[0];
				iframe.setAttribute("src", embedURL);
			});

			ele.setAttribute("data-src", href);
			ele.removeAttribute("href");
		}
	} catch (e) {
		console.error(url);
		return;
	}
});
