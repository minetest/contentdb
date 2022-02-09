// @author rubenwardy
// @license magnet:?xt=urn:btih:1f739d935676111cfff4b4693e3816e664797050&dn=gpl-3.0.txt GPL-v3-or-Later

window.addEventListener("load", event => {
	document.querySelectorAll(".gallery").forEach(gallery => {
		const primary = gallery.querySelector(".primary-image img");
		const images = gallery.querySelectorAll("a[data-image]");

		images.forEach(image => {
			const imageFullUrl = image.getAttribute("data-image");
			image.removeAttribute("href");
			image.addEventListener("click", event => {
				primary.src = imageFullUrl;
			})
		});
	});
});
