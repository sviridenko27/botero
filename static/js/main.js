document.addEventListener("DOMContentLoaded", () => {
  const scrollButtons = document.querySelectorAll("[data-scroll-target]");
  scrollButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const targetSelector = button.getAttribute("data-scroll-target");
      if (!targetSelector) {
        return;
      }
      const target = document.querySelector(targetSelector);
      if (!target) {
        return;
      }

      const header = document.querySelector(".site-header");
      const headerOffset = header instanceof HTMLElement ? header.offsetHeight + 8 : 0;
      const targetTop = target.getBoundingClientRect().top + window.scrollY - headerOffset;
      window.scrollTo({ top: targetTop, behavior: "smooth" });
    });
  });

  const sliders = document.querySelectorAll("[data-slider]");

  sliders.forEach((slider) => {
    const slides = Array.from(slider.querySelectorAll("[data-slide]"));
    const nextButton = slider.querySelector("[data-slider-next]");
    const prevButton = slider.querySelector("[data-slider-prev]");
    const intervalMs = Number.parseInt(slider.dataset.sliderInterval || "5000", 10);
    const hasAutoplay = Number.isFinite(intervalMs) && intervalMs > 0;

    if (slides.length === 0) {
      return;
    }

    let activeIndex = 0;
    let timerId = null;

    const setActive = (index) => {
      activeIndex = (index + slides.length) % slides.length;
      slides.forEach((slide, i) => {
        slide.classList.toggle("is-active", i === activeIndex);
      });
    };

    setActive(0);

    if (slides.length <= 1) {
      return;
    }

    const nextSlide = () => setActive(activeIndex + 1);
    const prevSlide = () => setActive(activeIndex - 1);

    const startAutoplay = () => {
      if (!hasAutoplay) {
        return;
      }
      timerId = window.setInterval(nextSlide, intervalMs);
    };

    const stopAutoplay = () => {
      if (timerId !== null) {
        window.clearInterval(timerId);
        timerId = null;
      }
    };

    nextButton?.addEventListener("click", () => {
      stopAutoplay();
      nextSlide();
      startAutoplay();
    });

    prevButton?.addEventListener("click", () => {
      stopAutoplay();
      prevSlide();
      startAutoplay();
    });

    if (hasAutoplay) {
      slider.addEventListener("mouseenter", stopAutoplay);
      slider.addEventListener("mouseleave", startAutoplay);
      startAutoplay();
    }
  });
});
