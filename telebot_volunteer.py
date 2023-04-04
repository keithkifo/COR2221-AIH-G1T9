import os
import time
from dotenv import load_dotenv

import telebot
from telebot.types import BotCommand
from database import *


# ========== INSTANTIATE SUPPORTING SERVICES ==========
### Load .env file
load_dotenv()

### Telegram Bot
TOKEN = os.getenv('VOLUNTEER_TELE_TOKEN')
bot = telebot.TeleBot(token=TOKEN)
bot.set_my_commands( [
    BotCommand("start", "Start bot"),
    BotCommand("connect", "Enable matching with Migrant Worker"),
    BotCommand("pause", "Disable matching with Migrant Worker"),
    BotCommand("cancel", "Terminate conversation with a matched Migrant Worker"),
    BotCommand("instructions", "Send bot instructions"),
])


# ========== INITIAL WELCOME MESSAGE ==========
@bot.message_handler( commands=['start'] )
def send_welcome(message):
    # === Retrieve User Info ===
    tele_handle = message.chat.username
    chat_id = message.chat.id
    first_name = message.chat.first_name

    print(first_name, tele_handle, chat_id)

    # ==== Check if new_user or existing_user ====
    user_status = check_user_status( 'volunteer', tele_handle )

    if user_status == 'new_user':
        create_user( 'volunteer', first_name, chat_id, tele_handle )

        # Step 1: Send Hello
        bot.send_chat_action(chat_id, action='typing')
        bot.send_message(chat_id,
            f"Hello {first_name} (@{tele_handle}),\n" +
            f"Thank you for volunteering your time to connect with a migrant worker :)"
        )

        # Step 2: Send Instructions on how to use the bot
        bot.send_chat_action(chat_id, action='typing')
        time.sleep(2)
        bot.send_message(chat_id,
        "Here are some instructions on how to use the bot:\n\n" +
        "*(1) Matching with a Migrant Worker*\n" +
        "Whenever you are ready, you may use the /connect command to start getting matched with a migrant worker. When a migrant worker is ready to connect, you will be automatically paired.\n\n" +

        "*(2) Chatting with Matched Migrant Worker*\n" +
        "Once you matched, you may chat with each other through this Telegram Bot. Your messages will be forwarded and received here!\n\n" +

        "*(3) Terminating the conversation*\n" +
        "At any point in time, you may use the /close command to terminate the conversation with a migrant worker\n\n" +

        "*(4) Repeating this instructions*\n" +
        "To see this instruction sheet again, use the /instructions command ~\n",
        parse_mode="markdown")
        time.sleep(5)
        bot.send_message(chat_id, "Have fun!")

    else:
        # Step 1: Send Hello
        bot.send_chat_action(chat_id, action='typing')
        bot.send_message(chat_id, f"Welcome back, {first_name} (@{tele_handle}) !" )

        # Step 2: Check whether user is matched with any migrant worker
        MW_CHAT_ID = retrieve_pairing( tele_handle, 'volunteer' )

        if MW_CHAT_ID != None:
            bot.send_message(chat_id, f"You are still paired. Enjoy!")
        else:
            bot.send_message(chat_id, f"To start pairing, use /connect!")


# ========== START CONNECTING STATUS ==========
@bot.message_handler( commands=['connect'] )
def start_connecting( message ):
    # === Retrieve Info ===
    tele_handle = message.chat.username
    chat_id = message.chat.id
    first_name = message.chat.first_name

    # === Update Database ===
    update_availability( tele_handle, 'match')

    # === Inform User ===
    bot.send_message(chat_id, "Alright! When a Migrant Worker is ready to pair up, you will be notified ~")
    bot.send_message(chat_id, "In the mean time, hang tight!!")


# ========== PAUSE CONNECTING STATUS  ==========
@bot.message_handler( commands=['pause'] )
def pause_connecting( message ):
    # === Retrieve Info ===
    tele_handle = message.chat.username
    chat_id = message.chat.id
    first_name = message.chat.first_name

    # === Update Database ===
    update_availability( tele_handle, 'paused')

    # === Inform User ===
    bot.send_message(chat_id, "Okayyy, matching is now pause!")
    bot.send_message(chat_id, "When you're ready again, use /connect to start matching again.")


# ========== CANCEL PAIRING WITH A MIGRANT WORKER ==========
@bot.message_handler( commands=['cancel'] )
def terminate_pairing( message ):
    # === Retrieve Info ===
    tele_handle = message.chat.username
    chat_id = message.chat.id
    first_name = message.chat.first_name

    # === Update Database ===
    status = delete_pairing( tele_handle, 'volunteer')

    if status == True:
        # === Inform User ===
        bot.send_message(chat_id, "========== CONVERSATION HAS ENDED ==========")
        time.sleep(2)
        bot.send_message(chat_id, "If you want to pause matching with a migrant worker, use /pause.")
        time.sleep(1.5)
        bot.send_message(chat_id, "If not, you will be paired with another migrant worker whenever someone wants to connect ~")


# ========== SEND INSTRUCTIONS ==========
@bot.message_handler( commands=['instructions'] )
def connect_with_migrant_worker( message ):
    # === Retrieve Info ===
    tele_handle = message.chat.username
    chat_id = message.chat.id
    first_name = message.chat.first_name

    # === Send Instructions Again ===
    bot.send_chat_action(chat_id, action='typing')
    time.sleep(2)
    bot.send_message(chat_id,
    "Here are some instructions on how to use the bot:\n\n" +
    "*(1) Matching with a Migrant Worker*\n" +
    "Whenever you are ready, you may use the /connect command to start getting matched with a migrant worker. When a migrant worker is ready to connect, you will be automatically paired.\n\n" +

    "*(2) Chatting with Matched Migrant Worker*\n" +
    "Once you matched, you may chat with each other through this Telegram Bot. Your messages will be forwarded and received here!\n\n" +

    "*(3) Terminating the conversation*\n" +
    "At any point in time, you may use the /close command to terminate the conversation with a migrant worker\n" +

    "*(4) Repeating this instructions*\n" +
    "To see this instruction sheet again, use the /instructions command ~\n",
    parse_mode="markdown")


# ========== HANDLES ALL MESSAGES RECEIVED ==========
@bot.message_handler(func=lambda m: True, content_types=['text'])
def get_message_reply(message):
    # === Retrieve Info ===
    tele_handle = message.chat.username
    chat_id = message.chat.id
    first_name = message.chat.first_name
    user_msg = message.json['text']

    # ==== Retrieve Paired Migrant Worker ====
    MW_CHAT_ID = retrieve_pairing( tele_handle, 'volunteer' )
    print( MW_CHAT_ID )

    # Depending on the user state, see what they want to do
    TOKEN = os.getenv('MW_TELE_TOKEN')
    mw_bot = telebot.TeleBot(token=TOKEN)
    mw_bot.send_message(MW_CHAT_ID, f'From Volunteer:\n {user_msg}')
    mw_bot.close()


bot.polling()