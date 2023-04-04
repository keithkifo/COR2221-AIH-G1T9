import os
import time
import datetime
import random
from dotenv import load_dotenv

import telebot
from telebot import types
import requests
import google.cloud.dialogflow_v2 as dialogflow
from google.api_core.exceptions import InvalidArgument
from database import *
import config
import shutil


# ========== INSTANTIATE SUPPORTING SERVICES ==========
### Load .env file
load_dotenv()

### Load Environment Variables
STB_API_KEY = os.getenv('STB_API_KEY')
TOKEN = os.getenv('MW_TELE_TOKEN')

DIALOGFLOW_PROJECT_ID = os.getenv('DIALOGFLOW_PROJECT_ID')
DIALOGFLOW_LANGUAGE_CODE = 'en'
SESSION_ID = 'me'
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = 'dialogflow_key.json'

### Telegram Bot
bot = telebot.TeleBot(config.TOKEN)

### SOME STATE TRACKING VARIABLES
CHATTING_WITH_LOCAL = False
ANOTHER_RECO_BUTTON = False
VOLUNTEER_BOT = False


# @@@@@@@@@@@@@@@@@@@@ TELEGRAM STUFF @@@@@@@@@@@@@@@@@@@@
# ========== INITIAL WELCOME MESSAGE ==========
@bot.message_handler( commands=['start'] )
def send_welcome(message):
    # === Retrieve user info ===
    tele_handle = message.chat.username
    chat_id = message.chat.id
    first_name = message.chat.first_name

    # === Check if new_user or existing_user ===
    user_status = check_user_status( 'migrant_worker', chat_id )
    print(user_status)

    if user_status == 'new_user':
        print(user_status)
        # Step 0: Create user in the database
        create_user( 'migrant_worker', first_name, chat_id, tele_handle )

        # Step 0: Instantiate FSM

        # Step 1: Send Hello
        bot.send_chat_action(chat_id, action='typing')
        bot.send_message(chat_id,
            f"Hey {first_name} (@{tele_handle}),\n" +
            f"Welcome to MigrantLink :)"
        )

        # Step 2: Send Instructions on how to use the bot
        bot.send_chat_action(chat_id, action='typing')
        time.sleep(2)
        bot.send_message(chat_id,
        "Here are some things I can do:\n\n" +

        "*(1) Public Transportation Guide*\n" +
        "Curated Guide to learn how to navigate around Singapore\n\n" +

        "*(2) Recommendations - Food / Places To Visit*\n" +
        "Recommend food or places to visit\n\n" +

        "*(3) Connecting with a Volunteer*\n" +
        "Talk to a Volunteer\n",
        parse_mode="markdown")
        time.sleep(3)
        bot.send_message(chat_id, "Have fun!")
    else:
        bot.send_message(chat_id, f"Welcome Back {first_name} (@{tele_handle})")


# ========== CANCEL PAIRING WITH A VOLUNTEER ==========
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
        bot.send_message(chat_id, "========== CONVERSATION MODE HAS ENDED ==========")
        time.sleep(1.5)
        bot.send_message(chat_id, "You may use the bot as per normal again!")
    


# ========== HANDLES ALL MESSAGES RECEIVED ==========
@bot.message_handler(func=lambda m: True)
def get_message_reply(message):
    global CHATTING_WITH_LOCAL
    global ANOTHER_RECO_BUTTON
    global VOLUNTEER_BOT

    # === Retrieve Info ===
    tele_handle = message.chat.username
    chat_id = message.chat.id
    first_name = message.chat.first_name
    user_response = message.text
    
    print( ANOTHER_RECO_BUTTON, user_response )
    if ANOTHER_RECO_BUTTON != False:
        if user_response == 'Yes!':
            if ANOTHER_RECO_BUTTON == 'food':
                # ==== Generate Recommendation ====
                food_category = random.choice( ['dim sum', 'korean cuisine', 'hawker', 'pizza',' western cuisine', 'malay cuisine', 'chinese cuisine'] )
                recommendation = food_recommendation_by_keyword( food_category )

                ANOTHER_RECO_BUTTON = 'food'
                send_recommendation( chat_id, 'food', recommendation )
            else:
                keyword = ANOTHER_RECO_BUTTON
                recommendation = places_recommendation_by_keyword( keyword.lower() )

                ANOTHER_RECO_BUTTON = keyword
                send_recommendation( chat_id, 'places', recommendation, keyword=keyword)
        elif user_response == 'No need':
            ANOTHER_RECO_BUTTON = False
            bot.send_message(chat_id, 'Okay ~')
    
    elif CHATTING_WITH_LOCAL == False:
        # ==== Intent Classification from Dialogflow API ====
        detected_intent, fulfillment_text = detect_intent( user_response )
        print(detected_intent, fulfillment_text)

        if detected_intent == "(2) Places to visit" or detected_intent == "(2) What to eat":
            bot.send_message(chat_id, fulfillment_text)


        elif detected_intent == "(1) Public transport":
            bot.send_message(chat_id, fulfillment_text)
        

        elif "(1) Public transport_" in detected_intent:
            bot.send_message(chat_id, fulfillment_text)
            if 'MRT Map' in detected_intent:
                photo = open(f'./mrt_map.png', 'rb')
                bot.send_photo(chat_id, photo)

        elif detected_intent == "(2) What to eat_Local Food":
            bot.send_message(chat_id,
            "Here are some top recommendations from our local Singaporean Team :)\n"+
            "Zam Zam Restaurant\n" +
            "King of Fried Rice\n" +
            "Kim Dae Mun\n" +
            "Tipo Pasta Bar\n"
        )
            

        elif detected_intent == "(2) What to eat_Spontaneous":
            # ==== Generate Recommendation ====
            food_category = random.choice( ['dim sum', 'korean cuisine', 'hawker', 'pizza',' western cuisine', 'malay cuisine', 'chinese cuisine'] )
            recommendation = food_recommendation_by_keyword( food_category )

            ANOTHER_RECO_BUTTON = 'food'
            send_recommendation( chat_id, 'food', recommendation )


        elif "(2) Places to visit_" in detected_intent:
            keyword = detected_intent.split("_")[1]
            recommendation = places_recommendation_by_keyword( keyword.lower() )

            ANOTHER_RECO_BUTTON = keyword
            send_recommendation( chat_id, 'places', recommendation, keyword=keyword)

        elif detected_intent == "(3) Talk with volunteer":
            CHATTING_WITH_LOCAL = True # Change Bot Mode
            bot.send_message(chat_id, fulfillment_text)

            # Step 1: Retrieve Paired Migrant Worker
            VOLUNTEER_CHAT_ID = retrieve_pairing( tele_handle, 'migrant_worker' )
            bot.send_message(chat_id, f'===== CONNECTED WITH A LOCAL VOLUNTEER =====')
            bot.send_message(chat_id, f'You may now begin chatting! If you want to terminate this conversation, use /cancel')

            # Step 2: Send Message
            TOKEN = os.getenv('VOLUNTEER_TELE_TOKEN')
            VOLUNTEER_BOT = telebot.TeleBot(token=TOKEN)
            VOLUNTEER_BOT.send_message(VOLUNTEER_CHAT_ID, f'===== CONNECTED WITH A MIGRANT WORKER =====')
            VOLUNTEER_BOT.send_message(VOLUNTEER_CHAT_ID, f'You may now begin chatting!')
            time.sleep(1)

        elif detected_intent == "Fallback":
            bot.send_message(chat_id, fulfillment_text)
    else:
        # ==== Chatting Mode ====
        # Step 1: Retrieve Paired Migrant Worker
        VOLUNTEER_CHAT_ID = retrieve_pairing( tele_handle, 'migrant_worker' )
        VOLUNTEER_BOT.send_message(VOLUNTEER_CHAT_ID, f'From Migrant Worker:\n{user_response}')
        time.sleep(1)


# ========== SEND RECOMMENDATION MESSAGE ==========
def send_recommendation( chat_id, type, recommendation, keyword=None):
    if type == 'food':
        if recommendation['image_uuid'] != False:
            file_name = get_media( recommendation['image_uuid'] )
            recommendation_photo = open(f'./{file_name}', 'rb')
            bot.send_photo(chat_id, recommendation_photo,
                f"Here is a recommendation:\n\n" +
                f"Name: { recommendation['name'] }\n" +
                f"Type: { recommendation['type'] }\n" +
                f"Address: { recommendation['address'] }\n\n" +
                f"Hashtags: { ' '.join( recommendation['tags'] ) }\n",
            )

        else:
            bot.send_message(chat_id,
                f"Here is a recommendation:\n\n" +
                f"Name: { recommendation['name'] }\n" +
                f"Type: { recommendation['type'] }\n" +
                f"Address: { recommendation['address'] }\n\n" +
                f"Hashtags: { ' '.join( recommendation['tags'] ) }\n",
            )

        bot.send_message(chat_id,
            "About:\n" +
            f"{ recommendation['description']}"
        )

    else:
        if recommendation['image_uuid'] != False:
            file_name = get_media( recommendation['image_uuid'] )
            recommendation_photo = open(f'./{file_name}', 'rb')
            bot.send_photo(chat_id, recommendation_photo,
                f"Here is a {keyword} recommendation:\n\n" +

                f"Name: { recommendation['name'] }\n" +
                f"Type: { recommendation['type'] }\n" +
                f"Website: { recommendation['website'] }\n\n" +
                f"Hashtags: { ' '.join( recommendation['tags'] ) }\n"
            )
        else:
            bot.send_message(chat_id,
                f"Here is a {keyword} recommendation:\n\n" +

                f"Name: { recommendation['name'] }\n" +
                f"Type: { recommendation['type'] }\n" +
                f"Website: { recommendation['website'] }\n\n" +
                f"Hashtags: { ' '.join( recommendation['tags'] ) }\n"
            )
        bot.send_message(chat_id,
            "About:\n" +
            f"{ recommendation['description']}"
        )
    
    time.sleep(2)
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2)
    yes = telebot.types.KeyboardButton('Yes!')
    no = telebot.types.KeyboardButton('No need')
    markup.add(no, yes)

    bot.send_message(chat_id, "Would you like another recommendation?", reply_markup=markup)



# @@@@@@@@@@@@@@@@@@@@ DIALOGFLOW @@@@@@@@@@@@@@@@@@@@
# ========== DETECT INTENT - DIALOGFLOW API ==========
def detect_intent( user_utterance ):
    # === Instantiate Dialogflow ===
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(DIALOGFLOW_PROJECT_ID, SESSION_ID)
    text_input = dialogflow.types.TextInput(text=user_utterance, language_code=DIALOGFLOW_LANGUAGE_CODE)
    query_input = dialogflow.types.QueryInput(text=text_input)

    try:
        response = session_client.detect_intent(session=session, query_input=query_input)
    except InvalidArgument:
        raise
    
    # === Retrieve data from Dialogflow Response ===
    detected_intent = response.query_result.intent.display_name
    fulfillment_text = response.query_result.fulfillment_text

    # parameters = dict( response.query_result.parameters )

    return detected_intent, fulfillment_text



# @@@@@@@@@@@@@@@@@@@@ API STUFF @@@@@@@@@@@@@@@@@@@@
# ========== STB API: SEARCH BY KEYWORD ==========
def food_recommendation_by_keyword( keyword ):
    # ==== Call STB API ====
    endpoint = 'https://api.stb.gov.sg/content/common/v2/search'

    req = requests.get(
        endpoint,
        headers={'X-API-Key': STB_API_KEY},
        params={
            'dataset': 'food_beverages,bars_clubs',
            'keyword': keyword
        }
    )

    resp = req.json()['data']
    
    # ==== Choose a Recommendation ====
    recommendation = random.choice( resp ) 
    
    response_dict = {
        "name": recommendation['name'],
        "type": recommendation['type'],
        "description": recommendation['body'],
        "tags": [ '#' + tag.replace(' ', '_') + ' ' for tag in recommendation['tags'] ],
        "address": f"{recommendation['address']['streetName']} S({recommendation['address']['postalCode']})",
        "image_uuid": recommendation['thumbnails'][0]['uuid'] if len( recommendation['thumbnails'] ) != 0 else False
    }

    return response_dict


# ========== STB API: SEARCH BY KEYWORD ==========
def places_recommendation_by_keyword( keyword ):
    # ==== Call STB API ====
    endpoint = 'https://api.stb.gov.sg/content/common/v2/search'

    req = requests.get(
        endpoint,
        headers={'X-API-Key': STB_API_KEY},
        params={
            'dataset': 'walking_trails,tours,events',
            'keyword': keyword,
        }
    )

    resp = req.json()['data']
    
    # ==== Choose a Recommendation ====
    recommendation = random.choice( resp )

    response_dict = {
        "name": recommendation['name'],
        "type": recommendation['type'],
        "description": recommendation['description'],
        "tags": [ '#' + tag.replace(' ', '_') + ' ' for tag in recommendation['tags'] ],
        "website": recommendation['officialWebsite'],
        "image_uuid": recommendation['thumbnails'][0]['uuid'] if len( recommendation['thumbnails'] ) != 0 else False
    }

    return response_dict



# ========== STB API: GET IMAGE UUID ==========
def get_media( uuid ):
    media_endpoint = f'https://api.stb.gov.sg/media/download/v2/{uuid}'

    r = requests.get(
        media_endpoint,
        headers={'X-API-Key': STB_API_KEY},
        params={
            'fileType': 'Default',
        }
    )
    
    if r.status_code == 200:
        with open('./image.jpg', 'wb') as f:
            f.write(r.content)
    
    return 'image.jpg'


bot.polling()