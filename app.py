import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.spinner import Spinner
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.core.audio import SoundLoader
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.clock import Clock
import os
from vosk import Model, KaldiRecognizer
import pyaudio
import json
import threading

class SpeechRecognitionApp(App):
    def build(self):
        # Main layout
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Language selection dropdown
        self.language_spinner = Spinner(text='Select Language', values=('English', 'Spanish', 'French'))
        layout.add_widget(self.language_spinner)

        # Input device selection dropdown
        self.input_devices = self.get_input_devices()
        self.device_spinner = Spinner(text='Select Input Device', values=self.input_devices)
        layout.add_widget(self.device_spinner)

        # Text display
        self.text_display = TextInput(text='Recognized text will appear here', readonly=True, multiline=True)
        layout.add_widget(self.text_display)

        # Start listening button
        self.listen_button = Button(text='Start Listening')
        self.listen_button.bind(on_press=self.toggle_listening)
        layout.add_widget(self.listen_button)

        self.is_listening = False
        self.stream = None
        self.p = None

        return layout

    def get_input_devices(self):
        p = pyaudio.PyAudio()
        info = p.get_host_api_info_by_index(0)
        num_devices = info.get('deviceCount')
        
        devices = []
        for i in range(num_devices):
            device_info = p.get_device_info_by_host_api_device_index(0, i)
            if device_info.get('maxInputChannels') > 0:  # if it's an input device
                devices.append(f"{device_info.get('name')} - {i}")
        
        p.terminate()
        return devices

    def toggle_listening(self, instance):
        if self.is_listening:
            self.stop_listening()
        else:
            self.start_listening()

    def start_listening(self):
        if not self.device_spinner.text or self.device_spinner.text == 'Select Input Device':
            self.show_error("Please select an input device")
            return

        # Get the selected device index
        device_index = int(self.device_spinner.text.split(' - ')[-1])

        # Initialize Vosk model
        model = Model(r"C:\Users\DELL\Documents\code\webapp-2\webapp-3\copy\gitt\lang_convert\vosk-model-small-en-us-0.15\vosk-model-small-en-us-0.15")
        self.recognizer = KaldiRecognizer(model, 16000)

        # Initialize PyAudio
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, 
                        frames_per_buffer=8000, input_device_index=device_index, stream_callback=self.audio_callback)

        self.text_display.text = "Listening... Speak now."
        self.listen_button.text = "Stop Listening"
        self.is_listening = True
        self.stream.start_stream()

    def stop_listening(self):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.p:
            self.p.terminate()
        self.listen_button.text = "Start Listening"
        self.is_listening = False
        self.text_display.text += "\nStopped listening."

    def audio_callback(self, in_data, frame_count, time_info, status):
        if self.recognizer.AcceptWaveform(in_data):
            result = self.recognizer.Result()
            result_dict = json.loads(result)
            recognized_text = result_dict.get('text', '')
            if recognized_text:
                Clock.schedule_once(lambda dt: self.update_display(recognized_text), 0)
        return (in_data, pyaudio.paContinue)

    def update_display(self, text):
        self.text_display.text += f"\n{text}"
        self.process_recognized_text(text)

    def process_recognized_text(self, recognized_text):
        # TODO: Implement matching with predefined sentences
        matched_sentence, sentence_id = self.match_sentence(recognized_text)

        if matched_sentence:
            self.play_audio(sentence_id)
            self.execute_text_file(sentence_id)

    def match_sentence(self, recognized_text):
        # TODO: Implement sentence matching logic
        # For now, we'll just return a dummy result
        return recognized_text, "dummy_id"

    def play_audio(self, sentence_id):
        language = self.language_spinner.text
        audio_path = f"audio/{language}/{sentence_id}.mp3"
        if os.path.exists(audio_path):
            sound = SoundLoader.load(audio_path)
            if sound:
                sound.play()

    def execute_text_file(self, sentence_id):
        language = self.language_spinner.text
        text_path = f"text/{language}/{sentence_id}/{sentence_id}.txt"
        if os.path.exists(text_path):
            with open(text_path, 'r') as file:
                content = file.read()
                self.display_text_content(content)
        else:
            self.show_error(f"Text file not found: {text_path}")

    def display_text_content(self, content):
        popup = Popup(title='Text File Content',
                      content=Label(text=content),
                      size_hint=(0.8, 0.8))
        popup.open()

    def show_error(self, message):
        popup = Popup(title='Error',
                      content=Label(text=message),
                      size_hint=(0.6, 0.4))
        popup.open()

if __name__ == '__main__':
    SpeechRecognitionApp().run()