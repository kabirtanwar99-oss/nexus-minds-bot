from groq import Groq
import os

client = Groq(api_key=os.environ.get("GROQ_KEY"))
history = []

print("🤖 Your FREE AI Chatbot is running! Type 'quit' to exit.\n")

while True:
    user_input = input("You: ")
    if user_input.lower() == "quit":
        break

    history.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=history,
        max_tokens=1024
    )

    reply = response.choices[0].message.content
    history.append({"role": "assistant", "content": reply})
    print(f"\n🤖 AI: {reply}\n")
