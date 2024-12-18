document.addEventListener("DOMContentLoaded", () => {
    let currentIndex = 0;
    const slides = document.querySelectorAll(".slide");
    const totalSlides = slides.length;
    const nextButton = document.getElementById("next");
    const previousButton = document.getElementById("previous");

    function showSlide(index) {
        slides.forEach((slide, i) => {
            slide.classList.toggle("active", i === index);
        });

        // Change next button to exit on last slide
        if (currentIndex === totalSlides - 1) {
            nextButton.textContent = "Exit";
            nextButton.onclick = () => window.location.href = '/';
        } else {
            nextButton.textContent = "Next";
            nextButton.onclick = () => {
                currentIndex = (currentIndex + 1) % totalSlides;
                showSlide(currentIndex);
            };
        }
    }

    // Previous button handler
    previousButton.addEventListener("click", () => {
        currentIndex = (currentIndex - 1 + totalSlides) % totalSlides;
        showSlide(currentIndex);
    });

    // Initial slide display
    showSlide(currentIndex);
});

window.onSpotifyWebPlaybackSDKReady = () => {
    const token = "{{ access_token }}"; // Include your Spotify access token in the context
    const player = new Spotify.Player({
        name: 'Your Wrapped Player',
        getOAuthToken: cb => { cb(token); },
        volume: 0.8
    });

    // Error handling
    player.addListener('initialization_error', ({ message }) => console.error(message));
    player.addListener('authentication_error', ({ message }) => console.error(message));
    player.addListener('account_error', ({ message }) => console.error(message));
    player.addListener('playback_error', ({ message }) => console.error(message));

    // Playback status updates
    player.addListener('player_state_changed', state => {
        console.log(state);
    });

    // Ready
    player.addListener('ready', ({ device_id }) => {
        console.log('Ready with Device ID', device_id);

        // Attach event listener to the play button
        document.getElementById('play-top-songs').addEventListener('click', () => {
            fetch(`https://api.spotify.com/v1/me/player/play?device_id=${device_id}`, {
                method: 'PUT',
                body: JSON.stringify({ uris: topTracks }),
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                }
            }).then(response => {
                if (!response.ok) {
                    console.error('Error playing songs', response);
                }
            });
        });
    });

    // Connect to the player!
    player.connect();
};
