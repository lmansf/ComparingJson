import os
import sys
import json
import requests
import mysql.connector
from dotenv import load_dotenv

# Load configuration form .env file
load_dotenv()

# Configuration Variables
API_KEY = os.getenv("RIOT_API_KEY")
# Region used for Account-V1 (lookup by Riot ID)
REGION = os.getenv("RIOT_REGION", "americas")
# Platform used for Summoner-V4 (lookup by PUUID)
PLATFORM = os.getenv("RIOT_PLATFORM", "na1")

GAME_NAME = os.getenv("TARGET_GAME_NAME")
TAG_LINE = os.getenv("TARGET_TAG_LINE")

def validate_config():
    if not API_KEY or API_KEY == "RGAPI-YOUR-KEY-HERE":
        print("Error: RIOT_API_KEY is not set correctly in .env file.")
        return False
    if not GAME_NAME or not TAG_LINE:
        print("Error: TARGET_GAME_NAME or TARGET_TAG_LINE (Riot ID) not set in .env file.")
        return False
    return True

def get_headers():
    return {
        "X-Riot-Token": API_KEY
    }

def get_account_puuid(game_name, tag_line):
    """
    Step 1: Get PUUID from Riot ID (Account-V1)
    Endpoint: /riot/account/v1/accounts/by-riot-id/{gameName}/{tagLine}
    """
    url = f"https://{REGION}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
    print(f"Requesting Account V1: {url}")
    response = requests.get(url, headers=get_headers())
    
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 404:
        print(f"Error: Riot ID '{game_name}#{tag_line}' not found.")
        sys.exit(1)
    elif response.status_code == 403:
        print("Error: 403 Forbidden. Check your API Key validity.")
        sys.exit(1)
    else:
        print(f"Account API Error ({response.status_code}): {response.text}")
        sys.exit(1)

def get_summoner_details(puuid):
    """
    Step 2: Get Summoner Details from PUUID (Summoner-V4)
    Endpoint: /lol/summoner/v4/summoners/by-puuid/{encryptedPUUID}
    """
    url = f"https://{PLATFORM}.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"
    print(f"Requesting Summoner V4: {url}")
    response = requests.get(url, headers=get_headers())
    
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 404:
        print(f"Error: Summoner details not found for PUUID on platform {PLATFORM}.")
        sys.exit(1)
    else:
        print(f"Summoner API Error ({response.status_code}): {response.text}")
        sys.exit(1)

def save_to_database(account_data, summoner_data):
    """Step 3: Save merged data to MySQL"""
    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            database=os.getenv("DB_NAME", "riot_data"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", "")
        )
        cursor = connection.cursor()

        # Combine the data into one structure for the JSON column
        # account_data has 'puuid', 'gameName', 'tagLine'
        # summoner_data has 'id', 'accountId', 'summonerLevel', etc.
        full_data = {
            "account": account_data,
            "summoner": summoner_data
        }
        json_str = json.dumps(full_data)

        # Upsert Logic: Insert, or Update if PUUID exists
        query = """
        INSERT INTO summoners 
        (puuid, game_name, tag_line, summoner_level, profile_icon_id, full_response) 
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            game_name = VALUES(game_name),
            tag_line = VALUES(tag_line),
            summoner_level = VALUES(summoner_level),
            profile_icon_id = VALUES(profile_icon_id),
            full_response = VALUES(full_response),
            last_updated = CURRENT_TIMESTAMP
        """

        values = (
            account_data['puuid'],
            account_data['gameName'],
            account_data['tagLine'],
            summoner_data['summonerLevel'],
            summoner_data['profileIconId'],
            json_str
        )

        cursor.execute(query, values)
        connection.commit()
        print(f"Successfully saved data for {account_data['gameName']}#{account_data['tagLine']} to database.")

    except mysql.connector.Error as err:
        print(f"Database Error: {err}")
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

def main():
    if not validate_config():
        return

    print(f"--- Starting Lookup for {GAME_NAME}#{TAG_LINE} ---")
    
    # 1. Get Account info (PUUID)
    # The API returns 'gameName' and 'tagLine' which might correct casing
    account_info = get_account_puuid(GAME_NAME, TAG_LINE)
    masked_puuid = account_info['puuid'][:5] + "..." + account_info['puuid'][-5:]
    print(f"Found PUUID: {masked_puuid}")
    
    # 2. Get Summoner info
    summoner_info = get_summoner_details(account_info['puuid'])
    print(f"Found Summoner Level: {summoner_info['summonerLevel']}")
    
    # 3. Save to DB
    save_to_database(account_info, summoner_info)
    print("--- Done ---")

if __name__ == "__main__":
    main()
