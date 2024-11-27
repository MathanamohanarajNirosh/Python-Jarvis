import json
import pyttsx3
import datetime
import pywhatkit as kit
import wikipedia
import webbrowser
import pyjokes
import pyautogui
import random
import speech_recognition as sr
import logging
import spacy
import torch
from transformers import BertTokenizer, BertForMaskedLM, pipeline
import time
from pyfirmata import Arduino
import serial


# Initialize Arduino
ser = serial.Serial('COM7', 9600)


# Load NLP models
nlp = spacy.load('en_core_web_sm')
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
model = BertForMaskedLM.from_pretrained('bert-base-uncased')
sentiment_analyzer = pipeline('sentiment-analysis')

class Jarvis:
    def __init__(self):
        self.engine = pyttsx3.init('sapi5')
        voices = self.engine.getProperty('voices')
        self.engine.setProperty('voice', voices[1].id)  
        self.recognizer = sr.Recognizer()
        self.setup_logging()
        self.knowledge_base = self.load_knowledge_base()
        
        # LED control parameters
        self.led_pin = 13
        self.blink_times = 5
        self.blink_delay = 0.5

    def setup_logging(self):
        logging.basicConfig(filename="jarvis_log.txt", level=logging.ERROR,
                            format='%(asctime)s - %(levelname)s - %(message)s')

    def log_error(self, error_message):
        logging.error(error_message)

    def speak(self, message):
        self.engine.say(message)
        self.engine.runAndWait()

    def greet(self):
        hour = int(datetime.datetime.now().hour)
        if hour < 12:
            self.speak("Good Morning!")
        elif hour < 18:
            self.speak("Good Afternoon!")
        else:
            self.speak("Good Evening!")

    def listen(self):
        with sr.Microphone() as source:
            print("Listening...")
            self.recognizer.pause_threshold = 1
            audio = self.recognizer.listen(source, timeout=5)
        try:
            print("Recognizing...")
            command = self.recognizer.recognize_google(audio, language='en-in')
            print(f"You said: {command}\n")
            return command.lower()
        except sr.UnknownValueError:
            self.speak("Sorry, I didn't catch that. Can you say it again?")
            return None
        except sr.RequestError:
            self.speak("Oops! There seems to be a connection issue.")
            return None

    def load_knowledge_base(self):
        try:
            with open('knowledge_base.json', 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return {}

    def save_knowledge_base(self):
        with open('knowledge_base.json', 'w') as file:
            json.dump(self.knowledge_base, file, indent=2)

    def analyze_sentiment(self, text):
        result = sentiment_analyzer(text)[0]
        return result['score'], result['label'].lower()

    def get_response(self, question):
        similar_question = self.find_similar_question(question)
        if similar_question:
            response = self.knowledge_base[similar_question]
            self.speak(response)
            return response
        return None

    def find_similar_question(self, question):
        question_vector = torch.tensor(nlp(question).vector)
        highest_similarity = 0
        closest_match = None

        for stored_question in self.knowledge_base:
            stored_vector = torch.tensor(nlp(stored_question).vector)
            similarity = torch.dot(question_vector, stored_vector) / (torch.norm(question_vector) * torch.norm(stored_vector))
            if similarity > highest_similarity:
                highest_similarity = similarity
                closest_match = stored_question

        return closest_match if highest_similarity > 0.7 else None

    def learn_new_response(self, question):
        self.speak("What's the answer?")
        answer = self.listen()
        if answer:
            self.knowledge_base[question] = answer
            self.save_knowledge_base()
            self.speak("Got it! I've noted that down.")

    def tell_time(self):
        now = datetime.datetime.now()
        self.speak(f"The time is {now.strftime('%H:%M')}")

    def play_youtube(self):
        self.speak("What do you want to watch on YouTube?")
        query = self.listen()
        if query:
            kit.playonyt(query)
            self.speak(f"Now playing {query} on YouTube.")

    def google_search(self):
        self.speak("What do you want to search on Google?")
        query = self.listen()
        if query:
            kit.search(query)
            self.speak(f"Searching for {query} on Google.")

    def open_website(self, site):
        websites = {
            'google': 'https://www.google.com',
            'youtube': 'https://www.youtube.com',
            'whatsapp': 'https://web.whatsapp.com',
            'viber': 'https://www.viber.com',
            'bbc': 'https://www.bbc.com'
        }
        if site in websites:
            webbrowser.open(websites[site])
            self.speak(f"Opening {site}.")
        else:
            self.speak("I can't open that website.")

    def get_news(self, news_source):
        news_sources = {
            'bbc': 'https://www.bbc.com/news',
            'cnn': 'https://www.cnn.com/',
            'reuters': 'https://www.reuters.com/',
            'al jazeera': 'https://www.aljazeera.com/',
            'the guardian': 'https://www.theguardian.com/',
            'fox news': 'https://www.foxnews.com/',
            'nbc news': 'https://www.nbcnews.com/'
        }
        if news_source in news_sources:
            webbrowser.open(news_sources[news_source])
            self.speak(f"Opening news from {news_source}.")
        else:
            self.speak("I don't have that news source.")

    def tell_joke(self):
        joke = pyjokes.get_joke()
        self.speak(joke)
        print(joke)

    def search_wikipedia(self):
        self.speak("What do you want to find on Wikipedia?")
        query = self.listen()
        if query:
            try:
                result = wikipedia.summary(query, sentences=2)
                print(result)
                self.speak(result)
            except Exception as e:
                self.speak("Sorry, I couldn't find anything about that.")
                self.log_error(f"Wikipedia search failed: {e}")

    def take_screenshot(self):
        screenshot = pyautogui.screenshot()
        screenshot.save("screenshot.png")
        self.speak("Screenshot taken and saved as screenshot.png.")

    def close_tab(self):
        time.sleep(2)
        pyautogui.hotkey('ctrl', 'w')
        self.speak("Tab closed.")

    def blink_led(self):
        for _ in range(5):
            ser.write(b'H')  
            time.sleep(0.5)
            ser.write(b'L')  
            time.sleep(0.5)

    def control_speaker(self, command):
    
        if command == 'on':
            ser.write(b'S') 
            self.speak("Speaker is now ON.")
        elif command == 'off':
            ser.write(b'O') 
            self.speak("Speaker is now OFF.")

    def handle_commands(self):
        motivational_quotes = [
            "Disappointment is just a reminder that things can always get better.",
            "Failure is not the opposite of success; it's part of success.",
            "Every setback is a setup for a comeback.",
            "In the middle of every difficulty lies opportunity."
        ]

        while True:
            command = self.listen()
            if command is None:
                continue

            if "time" in command:
                self.tell_time()
            elif "close tab" in command:
                self.close_tab()
            elif "play" in command and "youtube" in command:
                self.play_youtube()
            elif "search" in command and "google" in command:
                self.google_search()
            elif "open" in command:
                self.open_website(command.split("open")[-1].strip())
            elif "news" in command:
                self.get_news(command.split("get news from")[-1].strip())
            elif "joke" in command:
                self.tell_joke()
            elif "wikipedia" in command:
                self.search_wikipedia()
            elif "screenshot" in command:
                self.take_screenshot()
            elif "blink led" in command: 
                self.blink_led()
            elif "On speaker" in command:
                self.control_speaker()
            elif "exit" in command or "stop" in command:
                self.speak("See you later!")
                break
            else:
                score, sentiment = self.analyze_sentiment(command)
                if sentiment == 'negative':
                    quote = random.choice(motivational_quotes)
                    self.speak(quote)
                    continue  

                self.get_response(command)

if __name__ == "__main__":
    assistant = Jarvis()
    assistant.greet()
    assistant.handle_commands()
