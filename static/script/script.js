<!DOCTYPE html>
<html>
<head>
  <title>Live Audio Transcription</title>
  <script src="//cdnjs.cloudflare.com/ajax/libs/socket.io/2.2.0/socket.io.js" integrity="sha256-yr4fRk/GU1ehYJPAs8P4JlTgu0Hdsp4ZKrx8bDEDC3I=" crossorigin="anonymous"></script>
  <style>
    body {
      font-family: Arial, sans-serif;
      text-align: center;
    }

    #transcript {
      margin-top: 20px;
      padding: 20px;
      border: 1px solid #ccc;
      border-radius: 10px;
      box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
      max-width: 600px;
      margin-left: auto;
      margin-right: auto;
    }

    button {
      margin: 10px;
      padding: 10px 20px;
      border: none;
      border-radius: 5px;
      background-color: #4CAF50;
      color: #fff;
      cursor: pointer;
    }

    button:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  </style>
</head>
<body>
  <h1>Live Audio Transcription</h1>
  <button id="start-btn">Start Recording</button>
  <button id="stop-btn" disabled>Stop Recording</button>
  <div id="transcript"></div>

  <script>
    var socket = io();

    var audioContext = new (window.AudioContext || window.webkitAudioContext)();
    var audioStream = null;
    var audioProcessor = null;
    var mediaStreamSource = null;


    function setupAudioProcessor() {
      audioProcessor = audioContext.createScriptProcessor(4096, 1, 1);
      audioProcessor.onaudioprocess = function(event) {
        var audioData = event.inputBuffer.getChannelData(0);
        // Send audio data to server
        socket.emit('audio_data', audioData);
      };
    }

    // Set up event listener for text data from server
    socket.on('text_data', function(text) {
      // Append received text to transcript div
      document.getElementById('transcript').innerHTML += '<p>' + text + '</p>';
    });

    // Set up event listener for start button
    document.getElementById('start-btn').addEventListener('click', function() {
      // Request access to user's microphone
      navigator.mediaDevices.getUserMedia({ audio: true })
        .then(function(stream) {
          // Create audio stream source
          audioStream = stream;
          mediaStreamSource = audioContext.createMediaStreamSource(audioStream);

          // Set up and connect audio processor
          setupAudioProcessor();
          mediaStreamSource.connect(audioProcessor);
          audioProcessor.connect(audioContext.destination);

          // Enable stop button
          document.getElementById('stop-btn').disabled = false;
          document.getElementById('start-btn').disabled = true;
        })
        .catch(function(error) {
          console.error('Error accessing microphone:', error);
        });
    });

    // Set up event listener for stop button
    document.getElementById('stop-btn').addEventListener('click', function() {
      // Stop audio processing
      if (audioProcessor) {
        audioProcessor.disconnect();
      }
      if (mediaStreamSource) {
        mediaStreamSource.disconnect();
      }

      // Stop microphone stream
      if (audioStream) {
        const tracks = audioStream.getTracks();
        tracks.forEach(track => track.stop());
      }

      // Disable stop button
      document.getElementById('stop-btn').disabled = true;
      document.getElementById('start-btn').disabled = false;
    });
  </script>
</body>
</html>
