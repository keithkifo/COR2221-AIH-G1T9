import os
import time
from dotenv import load_dotenv

import telebot
from telebot import types
from fsm import FiniteStateMachine
from db import *

# ========== INSTANTIATE SUPPORTING SERVICES ==========
### Load .env file
load_dotenv()

### Telegram Bot
TOKEN = os.getenv('TELEGRAM_TOKEN')
bot = telebot.TeleBot(token=TOKEN)

### Finite State Machine
fsm_bot = FiniteStateMachine()
current_state = fsm_bot.state


# ========== INITIAL WELCOME MESSAGE ==========
@bot.message_handler( commands=['start'] )
def send_welcome(message):
    tele_handle = message.chat.username
    chat_id = message.chat.id
    first_name = message.chat.first_name

    # Check if new_user or existing_user
    user_status = check_user_status( chat_id )

    if user_status == 'new_user':
        # IF new_user - send instructions on how to use this bot
        bot.send_message(chat_id, f"Hello {first_name} (@{tele_handle})")
    else:
        bot.send_message(chat_id, f"Welcome Back {first_name} (@{tele_handle})")






while True:
    try:
        bot.polling()
    except:
        time.sleep(15)