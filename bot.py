from datetime import datetime, date, time
from functools import wraps
from telegram.ext import *
from telegram import *
from models import Student, Task
from enum import Enum, auto
import logging
import os

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

APP_NAME = os.environ['APP_NAME']
TOKEN = os.environ['TELEGRAM_TOKEN']
PORT = int(os.environ.get('PORT', '8443'))
updater = Updater(token=TOKEN)

dp = updater.dispatcher

def registered(func):
    @wraps(func)
    def wrapped(bot, update, *args, **kwargs):
        try:
            student = Student.get(user_id=update.effective_chat.id)
        except Student.DoesNotExist:
            update.message.reply_text('You are not registered yet.\n'+
                                        'Write your invite code, please')
            return State.AUTH
        else:
            return func(bot, update, student, *args, **kwargs)
    return wrapped


class State(Enum):
    AUTH = auto()
    MENU = auto()
    EX1 = auto()
    EX2 = auto()
    EX3 = auto()

def start(bot, update):
    update.message.reply_text(text="I'll help you improve your English :) \n\
        Write your invite code, please")
    return State.AUTH

def auth(bot, update):
    code = update.message.text
    print(code)
    try:
        student = Student.get(invite_code=code.strip())
        student.user_id = update.effective_chat.id
        student.save()
    except Student.DoesNotExist:
        update.message.reply_text(text="Invite code is invalid.")
    else:
        update.message.reply_text(text=f"Hi, {student.name}")
    return menu(bot, update)

@registered
def menu(bot, update, student):
    reply_keyboard = [['Ex1', 'Ex2', 'Ex3']]

    update.message.reply_text(
        'Here you can choose which exercise to complete. ',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return State.MENU

@registered
def menu_action(bot, update, student):
    if update.message.text == 'Ex1':
        task=Task.select().where((Task.available_at <= datetime.now()) & (Task.due_to >= datetime.now()) & (Task.data["type"] == "choose_right")).get()
        update.message.reply_text(text=task.data["instructions"])
        update.message.reply_text(text=task.text)
        student.on_task = task
        student.on_stage = 0
        student.save()
        return ex1(bot, update, student)
    if update.message.text == 'Ex2':
        task=Task.select().where((Task.available_at <= datetime.now()) & (Task.due_to >= datetime.now()) & (Task.data["type"] == "make_sentence")).get()
        update.message.reply_text(text=task.data["instructions"])
        student.on_task = task
        student.on_stage = 0
        student.save()
        return ex2(bot, update, student)
    if update.message.text == 'Ex3':
        task=Task.select().where((Task.available_at <= datetime.now()) & (Task.due_to >= datetime.now()) & (Task.data["type"] == "solve_problem")).get()
        update.message.reply_text(text=task.data["instructions"])
        student.on_task = task
        student.on_stage = 0
        student.save()
        return ex3(bot, update, student)

def ex1(bot, update, student):
    task=student.on_task
    block = task.data["blocks"][student.on_stage]
    keyboard = [[InlineKeyboardButton(answer, callback_data=answer) for answer in block["answers"]]]

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(block["text"], reply_markup=reply_markup)
    return State.EX1

@registered
def ex1_handler(bot, update, student):
    query = update.callback_query
    task=student.on_task
    block = task.data["blocks"][student.on_stage]
    if query.data in block["correct"]:
        query.message.reply_text(text="That's right :)")
    else:
        query.message.reply_text(text="That's not right :(")
    if student.on_stage < len(task.data["blocks"])-1:
        student.on_stage += 1
        student.save()
        return ex1(bot, update, student)
    student.on_stage = None
    student.on_task = None
    student.save()
    return menu(bot, update)

def ex2(bot, update, student):
    update.message.reply_text(task.data["blocks"][0]["text"])
    return State.EX2

@registered
def ex2_handler(bot, update, student):
    answer = update.message.text
    if answer in task.data["blocks"][0]["correct"]:
        update.message.reply_text(text="That's right :)")
    else:
        update.message.reply_text(text="That's not right :(")
    return ex2(bot, update, student)

def ex3(bot, update, student):
    update.message.reply_text(task.data["text"])
    return State.EX3

@registered
def ex3_handler(bot, update, student):
    answer = update.message.text
    if answer == task.data["correct"]:
        update.message.reply_text(text="That's right :)")
    else:
        update.message.reply_text(text="That's not right :(")
    return menu(bot, update, student)

conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],

    states={
        State.AUTH: [MessageHandler(Filters.text, auth)],
        State.MENU: [RegexHandler('^(Ex1|Ex2|Ex3)$', menu_action)],
        State.EX1: [CallbackQueryHandler(ex1_handler)],
        State.EX2: [MessageHandler(Filters.text, ex2_handler)],
        State.EX3: [MessageHandler(Filters.text, ex3_handler)]
    },

    fallbacks=[]
)

dp.add_handler(conv_handler)

updater.start_webhook(listen="0.0.0.0",
                      port=PORT,
                      url_path=TOKEN)
updater.bot.set_webhook(f"https://{APP_NAME}.herokuapp.com/{TOKEN}")
updater.idle()
