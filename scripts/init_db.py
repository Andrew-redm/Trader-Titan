import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def create_database():

    db_host = os.environ.get('MYSQL_HOST')
    db_user = os.environ.get('MYSQL_USER')
    db_password = os.environ.get('MYSQL_PASSWORD')
    db_name = os.environ.get('MYSQL_DATABASE')
    print(db_password)
    conn = None
    try:
        conn = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name
        )
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                question TEXT NOT NULL,
                answer REAL NOT NULL,
                units TEXT NOT NULL,
                tags TEXT
            )
        """)

        conn.commit()
        print("Database and table created successfully.")

    except mysql.connector.Error as e:
        print(f"An error occurred: {e}")

    finally:
        if conn:
            cursor.close()
            conn.close()

if __name__ == '__main__':
    create_database()