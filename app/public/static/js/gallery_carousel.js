"use strict";

const galleryCarousel = new bootstrap.Carousel(document.querySelector('#galleryCarousel'));
document.querySelectorAll('.gallery-image').forEach(el => {
    el.addEventListener('click', function(e) {
        galleryCarousel.to(el.dataset.bsSlideTo);
    });
});