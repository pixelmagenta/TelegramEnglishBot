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
            message.reply_text('You are not registered yet.\n'+
                                        'Write your invite code, please')
            return State.AUTH
        else:
            return func(bot, update, *args, **kwargs, student=student)
    return wrapped

def needs_mesage(func):
    @wraps(func)
    def wrapped(bot, update, *args, **kwargs):
        return func(bot, update, *args, **kwargs, message=update.message or update.callback_query.message)
    return wrapped

class State(Enum):
    AUTH = auto()
    MENU = auto()
    EX1 = auto()
    EX2 = auto()
    EX3 = auto()

@needs_mesage
def start(bot, update, message):
    message.reply_text(text="I'll help you improve your English :) \n\
        Write your invite code, please")
    return State.AUTH

@needs_mesage
def auth(bot, update, message):
    code = message.text
    print(code)
    try:
        student = Student.get(invite_code=code.strip())
        student.user_id = update.effective_chat.id
        student.save()
    except Student.DoesNotExist:
        message.reply_text(text="Invite code is invalid.")
    else:
        message.reply_text(text=f"Hi, {student.name}")
    return menu(bot, update)

@registered
@needs_mesage
def menu(bot, update, student, message):
    reply_keyboard = [['Ex1', 'Ex2', 'Ex3']]

    message.reply_text(
        'Here you can choose which exercise to complete. ',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return State.MENU

@registered
@needs_mesage
def menu_action(bot, update, student, message):
    if message.text == 'Ex1':
        task=Task.select().where((Task.available_at <= datetime.now()) & (Task.due_to >= datetime.now()) & (Task.data["type"] == "choose_right")).get()
        message.reply_text(text=task.data["instructions"])
        message.reply_text(text=task.text)
        student.on_task = task
        student.on_stage = 0
        student.save()
        return ex1(update, student, message)
    if message.text == 'Ex2':
        task=Task.select().where((Task.available_at <= datetime.now()) & (Task.due_to >= datetime.now()) & (Task.data["type"] == "make_sentence")).get()
        message.reply_text(text=task.data["instructions"])
        student.on_task = task
        student.on_stage = 0
        student.save()
        return ex2(bot, update, student, message)
    if message.text == 'Ex3':
        task=Task.select().where((Task.available_at <= datetime.now()) & (Task.due_to >= datetime.now()) & (Task.data["type"] == "solve_problem")).get()
        message.reply_text(text=task.data["instructions"])
        student.on_task = task
        student.on_stage = 0
        student.save()
        return ex3(bot, update, student, message)

def ex1(update, student, message):
    task=student.on_task
    block = task.data["blocks"][student.on_stage]
    keyboard = [[InlineKeyboardButton(answer, callback_data=answer) for answer in block["answers"]]]

    reply_markup = InlineKeyboardMarkup(keyboard)

    message.reply_text(block["text"], reply_markup=reply_markup)
    return State.EX1

@registered
@needs_mesage
def ex1_handler(bot, update, student, message):
    query = update.callback_data
    print(query)
    task=student.on_task
    block = task.data["blocks"][student.on_stage]
    if query.data in block["correct"]:
        message.reply_text(text="That's right :)")
    else:
        message.reply_text(text="That's not right :(")
    if student.on_stage < len(task.data["blocks"])-1:
        student.on_stage += 1
        student.save()
        return ex1(update, student, message)
    student.on_stage = None
    student.on_task = None
    student.save()
    message.reply_text(text="Exercise 1 is finished.")
    return menu(bot, update, message)

def ex2(bot, update, student, message):
    block = student.on_task.data["blocks"][student.on_stage]
    message.reply_text(block["text"])
    return State.EX2

@registered
@needs_mesage
def ex2_handler(bot, update, student, message):
    answer = message.text
    task = student.on_task
    block = task.data["blocks"][student.on_stage]
    if answer in block["correct"]:
        message.reply_text(text="That's right :)")
    else:
        message.reply_text(text="That's not right :(")
    if student.on_stage < len(task.data["blocks"])-1:
        student.on_stage += 1
        student.save()
        return ex2(bot, update, student, message)
    student.on_stage = None
    student.on_task = None
    student.save()
    return menu(bot, update, message)

def ex3(bot, update, student, message):
    task=student.on_task
    message.reply_text(task.data["text"])
    return State.EX3

@registered
@needs_mesage
def ex3_handler(bot, update, student, message):
    answer = message.text
    task=student.on_task
    if answer == task.data["correct"]:
        message.reply_text(text="That's right :)")
    else:
        message.reply_text(text="That's not right :(")
    return menu(bot, update, message)

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
