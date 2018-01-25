from datetime import datetime, date, time
from envparse import env
from telegram.ext import CommandHandler, ConversationHandler
from telegram.ext import MessageHandler, Filters
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import Updater
from models import Student
import logging

env.read_envfile()

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

updater = Updater(token=env('TOKEN'))

dp = updater.dispatcher

AUTH = 0

def start(bot, update):
    update.message.reply_text(text="I'll help you improve your English :) \n\
        Write your invite code, please")
    return AUTH

def auth(bot, update):
    code = update.message.text
    print(code)
    try:
        student = Student.get(invite_code=code.strip())
    except Student.DoesNotExist:
        update.message.reply_text(text="Invite code is invalid.")
    else:
        update.message.reply_text(text=f"Hi, {student.name}")

conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],

    states={
        AUTH: [MessageHandler(Filters.text, auth)]
    },

    fallbacks=[]
)

dp.add_handler(conv_handler)


updater.start_polling()