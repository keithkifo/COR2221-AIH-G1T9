import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

connection = pymysql.connect(
    host = os.getenv('DB_HOST'),
    user = os.getenv('DB_USER'),
    password = os.getenv('DB_PASSWORD'),
    database = os.getenv('DB_NAME')
)

def check_user_status( chat_id ):
    with connection.cursor() as cursor:
        query = """
            SELECT chat_id
            FROM users
            WHERE chat_id = '{chat_id}'
        """.format( chat_id = chat_id )

        cursor.execute( query )
        result = cursor.fetchone()

        if result == None:
            return 'new_user'
        
        return 'existing_user'