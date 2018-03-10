from datetime import datetime
from functools import wraps
from telegram.ext import *
from telegram import *
from models import *
import settings
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

updater = Updater(token=settings.TOKEN)
dp = updater.dispatcher

def registered(func):
    @wraps(func)
    def wrapped(bot, update, *args, **kwargs):
        if update.callback_query:
            message = update.callback_query.message
            update.callback_query.answer()
        else:
            message = update.message
        try:
            student = Student.get(user_id=update.effective_chat.id)
        except Student.DoesNotExist:
            try:
                student = Student.get(invite_code=message.text)
                student.user_id = update.effective_chat.id
                student.save()
            except Student.DoesNotExist:
                message.reply_text('Invalid code.\n'+
                                        'Try again.')
            else:
                message.reply_text(f'Welcome, {student.name}!\n'+
                                    'There is a Beta-version of the Bot now. Please be careful about spaces, register and all of the punctuation marks in your answers. It is better to copy-paste fragments from the tasks into your answers. Also, in the task with puzzles give just a number or a word. If you have any questions, write to @eugeniaustinova')
                show_help(bot, update)
                show_menu(bot, update)
        else:
            return func(bot, update, message, student, *args, **kwargs)
    return wrapped

def start(bot, update):
    update.message.reply_text(text="I'll help you improve your English :) \n\
        Write your invitation code, please")


def show_task(bot, update, message, student):
    task = student.on_task
    block = task.data['blocks'][student.on_stage]
    markup = None
    if 'answers' in block.keys():
        markup = InlineKeyboardMarkup([[InlineKeyboardButton(answer, callback_data=answer)
                                            for answer in block['answers']]])
    message.reply_text(block['text'], reply_markup=markup)

def task_handler(bot, update, message, student):
    task = student.on_task
    if task.due_to < datetime.now().date():
        message.reply_text('Task is not available anymore')
        student.on_task = None
        student.on_stage = None
        student.save()
        return
    block = task.data['blocks'][student.on_stage]
    if update.callback_query:
        student_answer = update.callback_query.data
    else:
        student_answer = message.text

    sub, created = Submission.get_or_create(student=student, task=task)
    sub.answers.append(student_answer)
    sub.save()

    if student_answer in block["correct"]:
        message.reply_text(text="That's right :)")
    else:
        message.reply_text(text=f"That's not right :(\nThe right answer(s): {', '.join(block['correct'])}")

    if student.on_stage < len(task.data["blocks"])-1:
        student.on_stage += 1
        student.save()
        show_task(bot, update, message, student)
    else:
        student.on_stage = None
        student.on_task = None
        student.save()
        sub.is_completed = True
        sub.save()
        message.reply_text(text="Task completed!")
        show_menu(bot, update)
    
@registered
def show_menu(bot, update, message, student):
    if student.on_task:
        student.on_task = None
        student.on_stage = None
        student.save()
    completed = Task.select().join(Submission).where((Submission.student == student) & Submission.is_completed)
    available_tasks = Task.select().where((Task.available_at <= datetime.now().date()) &
                                            (Task.due_to >= datetime.now().date()) &
                                            Task.id.not_in(completed))
    if available_tasks.count() > 0:
        keyboard = [[InlineKeyboardButton(task.data['type'], callback_data=task.id)
                        for task in available_tasks]]

        message.reply_text(
            'Here you can choose which exercise to complete. ',
            reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        message.reply_text('No tasks to solve.\nCome back next week!')

def menu_handler(bot, update, message, student):
    query = update.callback_query
    try:
        task = Task[query.data]
    except Task.DoesNotExist:
        message.reply_text('Invalid task')
        return
    if task.available_at > datetime.now().date():
        message.reply_text('Task is not available yet')
        return
    if task.due_to < datetime.now().date():
        message.reply_text('Task is not available anymore')
        return

    sub, created = Submission.get_or_create(student=student, task=task)
    if sub.is_completed:
        message.reply_text('You have already completed this task!')
        return

    bot.edit_message_text(text=f"Selected task: {task.data['type']}",
                                  chat_id=query.message.chat_id,
                                  message_id=query.message.message_id)
    student.on_task = task
    student.on_stage = len(sub.answers)
    student.save()
    message.reply_text(task.data["instructions"])
    if task.text !='':
        message.reply_text(task.text)
    show_task(bot, update, message, student)


@registered
def main_handler(bot, update, message, student):
    if student.on_task:
        return task_handler(bot, update, message, student)
    return menu_handler(bot, update, message, student)

@registered
def logout(bot, update, message, student):
    student.user_id = None
    student.on_task = None
    student.on_stage = None
    student.save()
    message.reply_text('Logged out successfully!')

@registered
def show_help(bot, update, message, student):
    text = " The following commands are available:\n"
    commands = [["/menu", "Show available tasks"],
            ["/help", "Show this help"],
            ["/logout", "Cancel all activities and logout"]
            ]

    for command in commands:
        text += command[0] + " " + command[1] + "\n"
    update.message.reply_text(text)


dp.add_handler(CommandHandler('start', start))
dp.add_handler(CommandHandler('help', show_help))
dp.add_handler(CommandHandler('menu', show_menu))
dp.add_handler(CommandHandler('logout', logout))
dp.add_handler(MessageHandler(Filters.text, main_handler))
dp.add_handler(CallbackQueryHandler(main_handler))

if settings.DEBUG:
    updater.start_polling()
else:
    updater.start_webhook(listen="0.0.0.0",
                          port=settings.PORT,
                          url_path=settings.TOKEN)
    updater.bot.set_webhook(f"https://{settings.APP_NAME}.herokuapp.com/{settings.TOKEN}")
updater.idle()
