import telebot
from telebot import types
import requests
import random
import threading
import http.server
import os

# --- تنظیمات ---
BOT_TOKEN = "8905355459:AAHrZqJMqWiBnt5h--VuAiJsOW1yHirxG7I"
API_KEY = "f3c39c23"
CHANNEL_ID = "@zhuug"
# ----------------

bot = telebot.TeleBot(BOT_TOKEN)

# ===== وب‌سرور زنده نگه‌دارنده برای Render =====
class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

    def log_message(self, *args):
        pass

def run_keep_alive():
    port = int(os.environ.get('PORT', 10000))
    server = http.server.HTTPServer(('', port), Handler)
    server.serve_forever()

threading.Thread(target=run_keep_alive, daemon=True).start()
# ===============================================

def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

def translate_genre(genre_string):
    fa_genres = {
        "Action": "اکشن", "Drama": "درام", "Comedy": "کمدی", "Horror": "ترسناک",
        "Thriller": "هیجانی", "War": "جنگی", "Crime": "جنایی", "Adventure": "ماجراجویی",
        "Sci-Fi": "علمی-تخیلی", "Fantasy": "فانتزی", "Romance": "عاشقانه",
        "Mystery": "معمایی", "Animation": "انیمیشن", "Biography": "زندگینامه"
    }
    genres = genre_string.split(", ")
    return ", ".join([fa_genres.get(g, g) for g in genres])

def get_movie_details(search_term, is_random=False):
    try:
        if is_random:
            term = random.choice(["action", "drama", "comedy", "war", "thriller", "sci-fi"])
            url = f"http://www.omdbapi.com/?s={term}&page={random.randint(1, 3)}&apikey={API_KEY}"
        else:
            url = f"http://www.omdbapi.com/?s={search_term}&apikey={API_KEY}"

        data = requests.get(url, timeout=10).json()
        if 'Search' in data:
            movie = random.choice(data['Search'])
            details = requests.get(f"http://www.omdbapi.com/?i={movie['imdbID']}&plot=full&apikey={API_KEY}", timeout=10).json()
            return details
    except:
        return None
    return None

def generate_caption(details):
    return (f"🎬 نام: {details.get('Title', 'N/A')}\n"
            f"🎭 ژانر: {translate_genre(details.get('Genre', 'N/A'))}\n"
            f"📅 تاریخ اکران: {details.get('Released', 'N/A')}\n"
            f"⏳ مدت زمان: {details.get('Runtime', 'N/A')}\n"
            f"👤 کارگردان: {details.get('Director', 'N/A')}\n"
            f"🌍 کشور: {details.get('Country', 'N/A')}\n"
            f"⭐ امتیاز: {details.get('imdbRating', 'N/A')}\n\n"
            f"📝 خلاصه: {details.get('Plot', 'اطلاعاتی نیست.')}")

def build_markup(details):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("تریلر 🎬", url=f"https://www.youtube.com/results?search_query={details.get('Title')}+trailer"),
               types.InlineKeyboardButton("زیرنویس 🔎", url=f"https://subdl.com/search?q={details.get('Title')}"))
    markup.add(types.InlineKeyboardButton("یک فیلم دیگر 🎲", callback_data="random_movie"))
    return markup

def send_movie(chat_id, details):
    try:
        bot.send_photo(chat_id, details.get('Poster'), caption=generate_caption(details), reply_markup=build_markup(details))
    except Exception:
        bot.send_message(chat_id, generate_caption(details), reply_markup=build_markup(details))

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("یک فیلم خوب پیشنهاد بده! 🎲")
    bot.reply_to(message, "سلام! به ربات فیلم خوش آمدی.\n\nبرای شروع، از دکمه زیر استفاده کن:", reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def handle_all(message):
    if not is_subscribed(message.from_user.id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🚀 ورود به کانال", url=f"https://t.me/{CHANNEL_ID.replace('@', '')}"))
        bot.reply_to(message, f"⚠️ ابتدا باید در کانال ما ({CHANNEL_ID}) عضو شوی.", reply_markup=markup)
        return

    if message.text == "یک فیلم خوب پیشنهاد بده! 🎲":
        details = get_movie_details("", is_random=True)
    else:
        details = get_movie_details(message.text)

    if details:
        send_movie(message.chat.id, details)
    else:
        bot.reply_to(message, "فیلمی با این نام پیدا نشد.")

@bot.callback_query_handler(func=lambda call: call.data == "random_movie")
def callback_random(call):
    details = get_movie_details("", is_random=True)
    if details:
        send_movie(call.message.chat.id, details)
    bot.answer_callback_query(call.id)

print("ربات روشن شد...")
bot.infinity_polling()
