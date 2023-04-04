import pymysql
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()


# ========== Instantiate DB if doesn't exist: Create database schema ==========
if 'backend.db' not in os.listdir('./'):
    with sqlite3.connect('backend.db') as conn:
        session = conn.cursor()
        with open('db_schema.sql', mode='r') as f:
            session.executescript(f.read())

        conn.commit()

# ========== Check whether user exists ==========
def check_user_status( user_type, tele_handle ):
    try:
        with sqlite3.connect('backend.db') as connection:
            session = connection.cursor()

            table = 'workers'
            if user_type == 'volunteer':
                table = 'volunteers'

            # ==== Check whether new user or not ====
            query = """
                SELECT chat_id
                FROM {table}
                WHERE tele_handle = '{tele_handle}'
            """.format( table = table, tele_handle = tele_handle )

            result = session.execute(query).fetchone()
            connection.commit()
            print(result)

            # IF new user, insert into DB
            if result == None:
                return 'new_user'
            
            return 'existing_user'
    except Exception as e:
        print('Error occurred - check_user_status:', e)

# ========== Create new user into DB ==========
def create_user( user_type, first_name, chat_id, tele_handle ):
    try:
        with sqlite3.connect('backend.db') as connection:
            session = connection.cursor()
            
            if user_type == 'volunteer':
                query = "INSERT INTO volunteers VALUES ( '{tele_handle}', '{first_name}', '{chat_id}', 1)".format( first_name = first_name, chat_id = chat_id, tele_handle = tele_handle )
            else:
                query = "INSERT INTO workers VALUES ( '{tele_handle}', '{first_name}', '{chat_id}' )".format( first_name = first_name, chat_id = chat_id, tele_handle = tele_handle )
            print(query)

            session.execute(query)
            connection.commit()
    except Exception as e:
        print('Error occurred:', e)
   

# ========== Update Volunteer Status==========
def update_availability( tele_handle, availability ):
    try:
        with sqlite3.connect('backend.db') as connection:
            if availability == 'match':
                avail = 1
            else:
                avail = 0

            session = connection.cursor()
            query = "UPDATE volunteers SET availability = {availability} WHERE tele_handle = '{tele_handle}'".format( tele_handle = tele_handle, availability = avail )
            print(query)
            session.execute(query)
            connection.commit()
    except Exception as e:
        print('Error occurred:', e)


# ========== Retrieve Pairing ==========
def retrieve_pairing( tele_handle, user_type ):
    try:
        with sqlite3.connect('backend.db') as connection:
            session = connection.cursor()

            if user_type == 'volunteer':
                query = "SELECT mw_chat_id FROM pairings WHERE volunteer_tele = '{tele_handle}'".format( tele_handle = tele_handle )
            else:
                query = "SELECT volunteer_chat_id FROM pairings WHERE mw_tele = '{tele_handle}'".format( tele_handle = tele_handle )

            result = session.execute(query).fetchone()
            connection.commit()
            if result != None:
                return result[0]
            return None
    except Exception as e:
        print('Error occurred:', e)


# ========== Delete Pairing ==========
def delete_pairing( tele_handle, user_type ):
    try:
        with sqlite3.connect('backend.db') as connection:
            session = connection.cursor()

            if user_type == 'volunteer':
                query = "DELETE FROM pairings WHERE volunteer_tele = '{tele_handle}'".format( tele_handle = tele_handle )
                check_query = "SELECT * FROM pairings WHERE volunteer_tele = '{tele_handle}'".format( tele_handle = tele_handle )
            else:
                query = "DELETE FROM pairings WHERE mw_tele = '{tele_handle}'".format( tele_handle = tele_handle )
                check_query = "SELECT * FROM pairings WHERE mw_tele = '{tele_handle}'".format( tele_handle = tele_handle )
            
            print(query)
            session.execute(query)
            connection.commit()

            print(check_query)
            result = session.execute(check_query).fetchone()
            connection.commit()

            if result == None:
                return True
            
            return False
    except Exception as e:
        print('Error occurred:', e)
        return False