
import urllib.request, json
import logging, threading, time
from telegram import *
from telegram.ext import *
from my_keys import  *

# Initialize the telegram bot
bot = Bot(TELEGRAM_TOKEN)
# print(bot.get_me())

updater = Updater(TELEGRAM_TOKEN, use_context=True)
dispatcher = updater.dispatcher
chat_list = []

def start_watch(update: Update, context: CallbackContext):
  chat = update.effective_chat.id
  print("someone typed to the chat")
  bot.send_message(
        chat_id = chat,
        text = "hello again",
    )


start_price_watch = CommandHandler('start',start_watch)
dispatcher.add_handler(start_price_watch)

updater.start_polling()
