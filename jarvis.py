import speech_recognition as sr
from groq import Groq
import os
from gtts import gTTS
import subprocess

client = Groq(api_key=os.environ.get("GROQ_KEY"))
recognizer = sr.Recognizer()
history = []
REPLY_FILE = os.path.expanduser("~/tmp/reply.mp3")
SYSTEM_PROMPT = "You are Jarvis, a smart personal AI assistant. Be concise, helpful and friendly."

print("🤖 JARVIS IS ONLINE! Say something...\n")

def speak(text):
    tts = gTTS(text=text, lang='en')
    tts.save(REPLY_FILE)
    subprocess.run(["mpv", "--no-terminal", "--speed=1.3", REPLY_FILE])

def listen():
    with sr.Microphone() as source:
        print("🔴 Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        try:
            audio = recognizer.listen(source, timeout=5)
            text = recognizer.recognize_google(audio)
            print(f"🗣️ You said: {text}")
            return text
        except sr.WaitTimeoutError:
            print("⏱️ No speech detected, try again")
            return None
        except sr.UnknownValueError:
            print("❌ Couldn't understand, try again")
            return None

while True:
    user_input = listen()
    if not user_input:
        continue
    if "goodbye jarvis" in user_input.lower():
        speak("Goodbye! Have a great day!")
        break
    history.append({"role": "user", "content": user_input})
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": SYSTEM_PROMPT}] + history,
        max_tokens=256
    )
    reply = response.choices[0].message.content
    history.append({"role": "assistant", "content": reply})
    print(f"\n🤖 Jarvis: {reply}\n")
    speak(reply)
