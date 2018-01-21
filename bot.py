from envparse import env
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
from telegram.ext import Updater
import logging

env.read_envfile()

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

updater = Updater(token=env('TOKEN'))

dispatcher = updater.dispatcher

def start(bot, update):
	update.message.reply_text(text="I'll help you improve your English :)")

start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

def echo(bot, update):
	update.message.reply_text(text="I'm not so smart yet, but I'm learning to talk with you")
echo_handler = MessageHandler(Filters.text, echo)
dispatcher.add_handler(echo_handler)







def unknown(bot, update):
	update.message.reply_text(text="Sorry, I didn't understand that command.")
unknown_handler = MessageHandler(Filters.command, unknown)
dispatcher.add_handler(unknown_handler)

updater.start_polling()