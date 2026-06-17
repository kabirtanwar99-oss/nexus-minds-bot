import os
import time
import datetime
import requests
from groq import Groq
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("NEXUS_TOKEN")
GROQ_KEY = os.environ.get("GROQ_KEY")
client = Groq(api_key=GROQ_KEY)

user_histories = {}
user_topics = {}
user_stats = {}

TOPICS = {
    "anime": {"emoji": "⛩️", "label": "Anime", "prompt": "You are an expert anime advisor. Suggest the best anime, explain plots, recommend based on preferences, discuss characters and storylines. Always be enthusiastic and detailed about anime."},
    "entertainment": {"emoji": "🎬", "label": "Entertainment", "prompt": "You are an entertainment expert covering movies, TV shows, music, celebrities, memes and pop culture. Give exciting recommendations and discuss trends."},
    "sports": {"emoji": "⚽", "label": "Sports", "prompt": "You are a sports expert covering football, cricket, basketball, tennis and all sports. Discuss matches, players, stats, history and predictions."},
    "politics": {"emoji": "🏛️", "label": "Politics", "prompt": "You are a neutral political analyst. Discuss world politics, news, policies and events in a balanced informative way without taking sides."},
    "studies": {"emoji": "📚", "label": "Studies Mentor", "prompt": "You are a patient and smart study mentor. Help with any subject, explain concepts simply, give examples, solve problems and motivate students."},
    "tech": {"emoji": "💻", "label": "Tech & AI", "prompt": "You are a tech expert covering AI, gadgets, coding, apps and latest technology trends. Explain complex tech simply and excitingly."},
    "fitness": {"emoji": "💪", "label": "Fitness & Health", "prompt": "You are a fitness and health coach. Give workout tips, diet advice, motivation and answer health questions in an encouraging way."},
    "gaming": {"emoji": "🎮", "label": "Gaming", "prompt": "You are a gaming expert. Discuss games, strategies, reviews, esports, game recommendations and gaming news with passion."},
    "finance": {"emoji": "💰", "label": "Money & Finance", "prompt": "You are a friendly finance advisor. Explain investing, saving, crypto, budgeting and money tips in a simple understandable way."},
    "motivation": {"emoji": "🔥", "label": "Motivation", "prompt": "You are an energetic life coach and motivator. Inspire people, give life advice, help with mindset, confidence and achieving goals."},
    "websearch": {"emoji": "🌐", "label": "Web Search", "prompt": "You are a helpful assistant. Use the web search results provided to answer questions accurately with latest real-time information. Always summarize the results clearly."}
}

def init_user_stats(user_id, name):
    if user_id not in user_stats:
        user_stats[user_id] = {
            "name": name,
            "total_messages": 0,
            "topics_used": {},
            "joined": datetime.datetime.now().strftime("%d %b %Y"),
            "last_active": datetime.datetime.now().strftime("%d %b %Y %H:%M")
        }

def update_stats(user_id, topic_key):
    if user_id in user_stats:
        user_stats[user_id]["total_messages"] += 1
        user_stats[user_id]["last_active"] = datetime.datetime.now().strftime("%d %b %Y %H:%M")
        if topic_key not in user_stats[user_id]["topics_used"]:
            user_stats[user_id]["topics_used"][topic_key] = 0
        user_stats[user_id]["topics_used"][topic_key] += 1

def get_favourite_topic(user_id):
    if user_id not in user_stats:
        return "None"
    topics = user_stats[user_id]["topics_used"]
    if not topics:
        return "None"
    fav = max(topics, key=topics.get)
    return f"{TOPICS[fav]['emoji']} {TOPICS[fav]['label']}"

def web_search(query):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        params = {"q": query, "format": "json", "no_html": 1, "skip_disambig": 1}
        res = requests.get("https://api.duckduckgo.com/", params=params, headers=headers, timeout=10)
        data = res.json()
        results = []
        if data.get("AbstractText"):
            results.append(data["AbstractText"])
        for topic in data.get("RelatedTopics", [])[:3]:
            if "Text" in topic:
                results.append(topic["Text"])
        if results:
            return "\n\n".join(results[:3])
        return None
    except Exception as e:
        print(f"Search error: {e}")
        return None

def get_main_menu():
    keyboard = []
    items = list(TOPICS.items())
    for i in range(0, len(items), 2):
        row = []
        key1, val1 = items[i]
        row.append(InlineKeyboardButton(f"{val1['emoji']} {val1['label']}", callback_data=key1))
        if i + 1 < len(items):
            key2, val2 = items[i+1]
            row.append(InlineKeyboardButton(f"{val2['emoji']} {val2['label']}", callback_data=key2))
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("📊 My Stats", callback_data="stats")])
    keyboard.append([InlineKeyboardButton("🏠 Main Menu", callback_data="menu")])
    return InlineKeyboardMarkup(keyboard)

def ask_groq(topic, histories):
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": topic["prompt"]}] + histories,
                max_tokens=512,
                timeout=60
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Attempt {attempt+1} failed: {e}")
            time.sleep(2)
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    init_user_stats(user.id, user.first_name)
    await update.message.reply_text(
        f"👋 Welcome *{user.first_name}*!\n\n"
        f"🤖 I'm *Nexus Minds* — your AI companion for everything!\n\n"
        f"Pick a topic below and let's talk! 👇",
        parse_mode="Markdown",
        reply_markup=get_main_menu()
    )

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    user_id = user.id
    init_user_stats(user_id, user.first_name)
    data = query.data
    if data == "menu":
        user_topics.pop(user_id, None)
        user_histories.pop(user_id, None)
        await query.message.reply_text(
            "🏠 *Main Menu* — Pick a topic!",
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )
        return
    if data == "stats":
        stats = user_stats.get(user_id, {})
        total = stats.get("total_messages", 0)
        joined = stats.get("joined", "Today")
        last = stats.get("last_active", "Now")
        fav = get_favourite_topic(user_id)
        topics_count = len(stats.get("topics_used", {}))
        await query.message.reply_text(
            f"📊 *Your Stats — {user.first_name}*\n\n"
            f"💬 Total Messages: *{total}*\n"
            f"🗂️ Topics Explored: *{topics_count}*\n"
            f"❤️ Favourite Topic: *{fav}*\n"
            f"📅 Joined: *{joined}*\n"
            f"⏰ Last Active: *{last}*\n\n"
            f"Keep exploring! 🚀",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 Main Menu", callback_data="menu")
            ]])
        )
        return
    if data in TOPICS:
        user_topics[user_id] = data
        user_histories[user_id] = []
        topic = TOPICS[data]
        await query.message.reply_text(
            f"{topic['emoji']} *{topic['label']} Mode ON!*\n\n"
            f"Ask me anything about *{topic['label']}*!\n"
            f"Type your question below 👇\n\n"
            f"_Tap 🏠 Main Menu anytime to switch topic_",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 Main Menu", callback_data="menu")
            ]])
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    text = update.message.text
    init_user_stats(user_id, user.first_name)
    if user_id not in user_topics:
        await update.message.reply_text(
            "👇 Please pick a topic first!",
            reply_markup=get_main_menu()
        )
        return
    topic_key = user_topics[user_id]
    topic = TOPICS[topic_key]
    if user_id not in user_histories:
        user_histories[user_id] = []
    update_stats(user_id, topic_key)
    await update.message.chat.send_action("typing")
    if topic_key == "websearch":
        search_results = web_search(text)
        if search_results:
            enhanced = f"User asked: {text}\n\nWeb results:\n{search_results}\n\nAnswer based on these results clearly."
        else:
            enhanced = text
        user_histories[user_id].append({"role": "user", "content": enhanced})
    else:
        user_histories[user_id].append({"role": "user", "content": text})
    reply = ask_groq(topic, user_histories[user_id])
    if reply:
        user_histories[user_id].append({"role": "assistant", "content": reply})
        await update.message.reply_text(
            f"{topic['emoji']} {reply}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 Main Menu", callback_data="menu"),
                InlineKeyboardButton("📊 My Stats", callback_data="stats")
            ]])
        )
    else:
        await update.message.reply_text(
            "⚠️ Network issue, please try again!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 Main Menu", callback_data="menu")
            ]])
        )

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(handle_button))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("🚀 Nexus Minds Bot is ONLINE!")
app.run_polling()
