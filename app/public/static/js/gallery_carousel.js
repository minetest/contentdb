// @author recluse4615
// @license magnet:?xt=urn:btih:1f739d935676111cfff4b4693e3816e664797050&dn=gpl-3.0.txt GPL-v3-or-Later

"use strict";

const galleryCarousel = new bootstrap.Carousel(document.getElementById("galleryCarousel"));
document.querySelectorAll(".gallery-image").forEach(el => {
	el.addEventListener("click", function(e) {
		galleryCarousel.to(el.dataset.bsSlideTo);
		e.preventDefault();
	});
});
