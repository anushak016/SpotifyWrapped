document.addEventListener("DOMContentLoaded", () => {
    let currentIndex = 0;
    const slides = document.querySelectorAll(".slide");
    const totalSlides = slides.length;


    function showSlide(index) {
        slides.forEach((slide, i) => {
            slide.classList.toggle("active", i === index);
        });
    }

    document.getElementById("next").addEventListener("click", () => {
        currentIndex = (currentIndex + 1) % totalSlides;
        showSlide(currentIndex);
    });

    document.getElementById("previous").addEventListener("click", () => {
        currentIndex = (currentIndex - 1 + totalSlides) % totalSlides;
        showSlide(currentIndex);
    });

    // Optional: Auto-transition slides every few seconds
    // setInterval(() => {
    //     currentIndex = (currentIndex + 1) % totalSlides;
    //     showSlide(currentIndex);
    // }, 5000);  // Adjust timing as desired
});
