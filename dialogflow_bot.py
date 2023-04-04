import telebot
import json
import os
import google.cloud.dialogflow_v2 as dialogflow
from google.api_core.exceptions import InvalidArgument
import schedule
import time
from threading import Thread
from dotenv import load_dotenv

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = 'dialogflow_key.json'
DIALOGFLOW_PROJECT_ID = os.getenv('DIALOGFLOW_PROJECT_ID')
DIALOGFLOW_LANGUAGE_CODE = 'en'
SESSION_ID = 'me'

# ========== INSTANTIATE SUPPORTING SERVICES ==========
### Load .env file
load_dotenv()


### Telegram Bot
TOKEN = os.getenv('VOLUNTEER_TELE_TOKEN')
bot = telebot.TeleBot(token=TOKEN)


# ========== INITIAL WELCOME MESSAGE ==========
@bot.message_handler( commands=['start'] )
def send_welcome(message):
    tele_handle = message.chat.username
    chat_id = message.chat.id
    first_name = message.chat.first_name

    print( chat_id )
    bot.send_message(
        message.chat.id,
        'Hello! I am a Telegram bot that can answer your questions.\n' +
        'You may ask me anything about: .\n' +
        '- Singapore culture and customs \n' + 
        '- Find alternatives to your hometown\'s food and activities \n' +
        '- Upcoming events you may be interested \n' +
        '- Connect with a senior migrant worker or Singaporean! \n'
    )


@bot.message_handler(func=lambda m: True, content_types=['text'])
def echo_all(message):
    print('Calling Dialogflow API')
    user_response = message.text

    # === Instantiate Dialogflow ===
    session_client = dialogflow.SessionsClient(credentials='dialogflow_key.json')
    session = session_client.session_path(DIALOGFLOW_PROJECT_ID, SESSION_ID)
    text_input = dialogflow.types.TextInput(text=user_response, language_code=DIALOGFLOW_LANGUAGE_CODE)
    query_input = dialogflow.types.QueryInput(text=text_input)

    response = session_client.detect_intent(session=session, query_input=query_input)
    print('Response:', response)

    detected_intent = response.query_result.intent.display_name
    print('Intent:', detected_intent)

    if detected_intent == "Learn About SG":
        learn_SG(message)

    if detected_intent == "makeFriends":
        make_friends(message, response)



def learn_SG(message):
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.row(
        telebot.types.InlineKeyboardButton('Reserving seats', callback_data='chope'),
        telebot.types.InlineKeyboardButton('For rental', callback_data='rental')
    )
    keyboard.row(
        telebot.types.InlineKeyboardButton('They are free!', callback_data='free'),
        telebot.types.InlineKeyboardButton('Someone forget them :(', callback_data='forget')
    )
    photo = open('./chope_seats.jpg', 'rb')
    bot.send_photo(message.chat.id, photo,
                   "Can you guess what are the tissues and umbrella used for in this photo?",
                   reply_markup=keyboard)


def make_friends(message, response):
    fulfillment_messages = response.query_result.fulfillment_messages
    reply_msg = ""
    for msg in fulfillment_messages:
        reply_msg += msg.text.text[0] + "\n"

    bot.reply_to(message, reply_msg)

# @bot.message_handler(commands=['exchange'])
# def exchange_command(message):
#     keyboard = telebot.types.InlineKeyboardMarkup()
#     keyboard.row(
#         telebot.types.InlineKeyboardButton('USD', callback_data='get-USD')
#     )
#     keyboard.row(
#         telebot.types.InlineKeyboardButton('EUR', callback_data='get-EUR'),
#         telebot.types.InlineKeyboardButton('RUR', callback_data='get-RUR')
#     )

#     bot.send_message(
#         message.chat.id, "Click on the currency of choice:", reply_markup=keyboard)


# @bot.callback_query_handler(func=lambda call: True)
# def iq_callback(query):
#     data = query.data
#     if data.startswith('get-'):
#         get_ex_callback(query)


# def get_ex_callback(query):
#     bot.answer_callback_query(query.id)
#     send_exchange_result(query.message, query.data[4:])


# def send_exchange_result(message, ex_code):
#     bot.send_chat_action(message.chat.id, 'typing')
#     ex = pb.get_exchange(ex_code)
#     bot.send_message(
#         message.chat.id, serialize_ex(ex),
#         reply_markup=get_update_keyboard(ex),
#         parse_mode='HTML'
#     )


# def get_update_keyboard(ex):
#     keyboard = telebot.types.InlineKeyboardMarkup()
#     keyboard.row(
#         telebot.types.InlineKeyboardButton(
#             'Update',
#             callback_data=json.dumps({
#                 't': 'u',
#                 'e': {
#                     'b': ex['buy'],
#                     's': ex['sale'],
#                     'c': ex['ccy']
#                 }
#             }).replace(' ', '')
#         ),
#         telebot.types.InlineKeyboardButton(
#             'Share', switch_inline_query=ex['ccy'])
#     )
#     return keyboard

# def daily_news():
#     print("DAILY NEWS TIME!!")
#     bot.send_message(268332593, "Your daily news is here: ...")

# def schedule_checker():
#     while True:
#         schedule.run_pending()
#         time.sleep(1)

# schedule.every().day.at("17:18").do(daily_news)
# Thread(target=schedule_checker).start()

while True:
    try:
        bot.polling()
    except:
        time.sleep(15)