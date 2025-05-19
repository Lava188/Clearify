import speech_recognition as sr
import threading
import time

class VoiceController:
    def __init__(self, callback_function=None):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.is_listening = False
        self.listen_thread = None
        self.callback_function = callback_function
        self.commands = {
            "capture": "capture",
            "read": "read",
            "stop": "stop"
        }
        
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
        
    def start_listening(self):
        if not self.is_listening:
            self.is_listening = True
            self.listen_thread = threading.Thread(target=self._listen_loop)
            self.listen_thread.daemon = True
            self.listen_thread.start()
            return "Voice recognition started"
        return "Already listening"
    
    def stop_listening(self):
        if self.is_listening:
            self.is_listening = False
            if self.listen_thread:
                self.listen_thread.join(timeout=1)
            return "Voice recognition stopped"
        return "Not currently listening"
    
    def _listen_loop(self):
        while self.is_listening:
            try:
                with self.microphone as source:
                    print("Listening for commands...")
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=3)
                
                try:
                    text = self.recognizer.recognize_google(audio, language='en-US').lower()
                    print(f"Recognized: {text}")
                    self._process_command(text)
                except sr.UnknownValueError:
                    print("Google Speech Recognition could not understand audio")
                except sr.RequestError as e:
                    print(f"Could not request results from Google Speech Recognition service; {e}")
            except (sr.WaitTimeoutError, Exception) as e:
                print(f"Listening error: {e}")
                continue
    
    def _process_command(self, text):
        command = None
        for cmd_key, cmd_value in self.commands.items():
            if cmd_key in text:
                command = cmd_value
                break
        if command and self.callback_function:
            print(f"Executing command: {command}")
            self.callback_function(command)