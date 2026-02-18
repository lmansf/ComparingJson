import mysql.connector
from mysql.connector import errorcode
from dotenv import load_dotenv
import os
import sys

# Load environment variables
load_dotenv()

def create_database():
    try:
        # Connect to MySQL Server (no database selected yet)
        print("Connecting to MySQL server...")
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", "")
        )
        
        cursor = connection.cursor()
        db_name = os.getenv("DB_NAME", "riot_data")

        # Create Database
        print(f"Creating database '{db_name}' if it doesn't exist...")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        
        # Connect to the specific database
        connection.database = db_name
        
        # Create Table
        print("Creating table 'summoners'...")
        # We store puuid as PK.
        # full_response stores the raw JSON blob.
        table_query = """
        CREATE TABLE IF NOT EXISTS summoners (
            puuid VARCHAR(78) PRIMARY KEY,
            game_name VARCHAR(50),
            tag_line VARCHAR(10),
            summoner_level BIGINT,
            profile_icon_id INT,
            full_response JSON,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """
        cursor.execute(table_query)
        
        print("Database schema initialized successfully!")

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Error: Something is wrong with your user name or password.")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Error: Database does not exist (and failed to create).")
        else:
            print(f"Error: {err}")
        sys.exit(1)
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    create_database()
