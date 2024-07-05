document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('languageForm');
    const audioPlayer = document.getElementById('audioPlayer');
    const outputDiv = document.getElementById('output');

    form.addEventListener('submit', function(event) {
        event.preventDefault();

        // Reset audio player and output
        audioPlayer.pause();
        audioPlayer.currentTime = 0;
        outputDiv.textContent = '';

        // Send form data via AJAX
        const formData = new FormData(form);
        fetch('/process-audio', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.audio_file) {
                // Play audio file
                audioPlayer.src = data.audio_file;
                audioPlayer.style.display = 'block';
                audioPlayer.play();
                outputDiv.textContent = 'Playing: ' + data.audio_file;
            } else {
                outputDiv.textContent = 'Error: ' + data.error;
            }
        })
        .catch(error => {
            outputDiv.textContent = 'Error: ' + error.message;
        });
    });
});
