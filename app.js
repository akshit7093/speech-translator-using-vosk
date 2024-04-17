document.addEventListener("DOMContentLoaded", function() {
    const sentenceDropdown = document.getElementById("sentenceDropdown");
    const languageDropdown = document.getElementById("languageDropdown");
    const proceedBtn = document.getElementById("proceedBtn");
    const outputDiv = document.getElementById("output");
    const audioPlayer = document.getElementById("audioPlayer");

    proceedBtn.addEventListener("click", function() {
        const selectedSentence = sentenceDropdown.value;
        const selectedLanguage = languageDropdown.value;

        if (!selectedSentence) {
            outputDiv.innerText = "Please select a sentence.";
            return;
        }

        if (!selectedLanguage) {
            outputDiv.innerText = "Please select a language.";
            return;
        }

        fetch(`sentences/${selectedSentence}/${selectedLanguage}.txt`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.text();
            })
            .then(data => {
                outputDiv.innerText = data;
            })
            .catch(error => {
                console.error("Error fetching text:", error);
                outputDiv.innerText = "Error fetching text. Please try again.";
            });

        // Play audio
        const audioFilePath = `audio/${selectedSentence}/${selectedLanguage}.mp3`;
        audioPlayer.src = audioFilePath;
        audioPlayer.play();
    });
});
