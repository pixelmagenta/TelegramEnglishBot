from datetime import datetime, date, time
from envparse import env
from telegram.ext import *
from telegram import *
from models import Student, Task
from enum import Enum, auto
import logging

env.read_envfile()

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

updater = Updater(token=env('TOKEN'))

dp = updater.dispatcher


class State(Enum):
    AUTH = auto()
    MENU = auto()
    EX1 = auto()
    EX2 = auto()
    EX3 = auto()
    EX4 = auto()

def start(bot, update):
    update.message.reply_text(text="I'll help you improve your English :) \n\
        Write your invite code, please")
    return State.AUTH

def auth(bot, update):
    code = update.message.text
    print(code)
    try:
        student = Student.get(invite_code=code.strip())
    except Student.DoesNotExist:
        update.message.reply_text(text="Invite code is invalid.")
    else:
        update.message.reply_text(text=f"Hi, {student.name}")
    return menu(bot, update)

def menu(bot, update):
    reply_keyboard = [['Ex1', 'Ex2', 'Ex3', 'Ex4']]

    update.message.reply_text(
        'Here you can choose which exercise to complete. ',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return State.MENU

def menu_action(bot, update):
    if update.message.text == 'Ex1':
        task = Task.get()
        update.message.reply_text(text=task.text)
        return ex1(bot, update, task)
    if update.message.text == 'Ex2':
        return State.EX2
    if update.message.text == 'Ex3':
        return State.EX3
    if update.message.text == 'Ex4':
        return State.EX4

def ex1(bot, update, task):
    keyboard = [[InlineKeyboardButton(answer, callback_data=answer) for answer in task.data["blocks"][0]["answers"]]]

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(task.data["blocks"][0]["text"], reply_markup=reply_markup)
    return State.EX1

def ex1_handler(bot, update):
    query = update.callback_query
    print(query.data)
    right_answer = 'may'
    if query.data == right_answer:
        query.message.reply_text(text="That's right :)")
    if query.data != right_answer:
        query.message.reply_text(text="That's not right :(")
    return ex1(bot, update)

conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],

    states={
        State.AUTH: [MessageHandler(Filters.text, auth)],
        State.MENU: [RegexHandler('^(Ex1|Ex2|Ex3|Ex4)$', menu_action)],
        State.EX1: [CallbackQueryHandler(ex1_handler)]
    },

    fallbacks=[]
)

dp.add_handler(conv_handler)


updater.start_polling()