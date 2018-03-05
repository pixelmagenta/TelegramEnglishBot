import os

TOKEN = os.environ['TELEGRAM_TOKEN']
DEBUG = os.environ.get('DEBUG', '0') == '1'
DATABASE_URL = os.environ['DATABASE_URL']
if not DEBUG:
    APP_NAME = os.environ['APP_NAME']
    PORT = int(os.environ.get('PORT', '8443'))
