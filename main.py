import os

import telebot
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    raise ValueError("No se encontró TELEGRAM_BOT_TOKEN en el .env")

bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.reply_to(message, "Hi there, I am helpertron.")


print("Bot iniciado...")
bot.infinity_polling()
