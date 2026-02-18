import os
import sys
import json
import time
import requests
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

# Configuration
API_KEY = os.getenv("RIOT_API_KEY")
REGION = os.getenv("RIOT_REGION", "americas")
PLATFORM = os.getenv("RIOT_PLATFORM", "na1")

# Rate Limiting configuration (Conservative for Dev Keys)
# 20 requests every 1 second, 100 requests every 2 minutes
# We'll sleep 1.2 seconds between calls to be safe.
SLEEP_TIME = 1.2 

def get_headers():
    return {
        "X-Riot-Token": API_KEY
    }

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "riot_data"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "")
    )

def fetch_challenger_league(queue="RANKED_SOLO_5x5"):
    """
    Fetches the Challenger League for the given queue.
    Returns a list of LeagueEntryDTOs.
    """
    url = f"https://{PLATFORM}.api.riotgames.com/lol/league/v4/challengerleagues/by-queue/{queue}"
    print(f"Fetching Challenger League from {url}...")
    
    response = requests.get(url, headers=get_headers())
    
    if response.status_code == 200:
        return response.json().get('entries', [])
    elif response.status_code == 429:
        retry_after = int(response.headers.get("Retry-After", 10))
        print(f"Rate limited. Sleeping for {retry_after} seconds.")
        time.sleep(retry_after)
        return fetch_challenger_league(queue)
    else:
        print(f"Error fetching league: {response.status_code} - {response.text}")
        return []

def get_summoner_by_puuid(puuid):
    """
    Fetches summoner details (summonerLevel, profileIconId) using PUUID.
    """
    url = f"https://{PLATFORM}.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"
    
    response = requests.get(url, headers=get_headers())
    
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 429:
        retry_after = int(response.headers.get("Retry-After", 10))
        print(f"Rate limited fetching summoner. Sleeping for {retry_after} seconds.")
        time.sleep(retry_after)
        return get_summoner_by_puuid(puuid)
    elif response.status_code == 404:
        print(f"Summoner for PUUID {puuid} not found (might have transferred).")
        return None
    else:
        print(f"Error fetching summoner for PUUID {puuid}: {response.status_code}")
        return None

def get_account_by_puuid(puuid):
    """
    Fetches account details (gameName, tagLine) using PUUID.
    Needed because Summoner-V4 no longer guarantees returning the correct current name/tag.
    """
    url = f"https://{REGION}.api.riotgames.com/riot/account/v1/accounts/by-puuid/{puuid}"
    
    response = requests.get(url, headers=get_headers())
    
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 429:
        retry_after = int(response.headers.get("Retry-After", 10))
        print(f"Rate limited fetching account. Sleeping for {retry_after} seconds.")
        time.sleep(retry_after)
        return get_account_by_puuid(puuid)
    else:
        print(f"Error fetching account for PUUID {puuid}: {response.status_code}")
        return None

def save_player(cursor, connection, summoner_data, account_data):
    """
    Saves the fetched player data into the database.
    """
    # Create the full JSON object similar to main.py
    full_data = {
        "account": account_data,
        "summoner": summoner_data
    }
    json_str = json.dumps(full_data)

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
    
    # Check if account_data is None (sometimes Account API fails but Summoner API succeeded)
    game_name = account_data.get('gameName') if account_data else "Unknown"
    tag_line = account_data.get('tagLine') if account_data else "Unknown"

    values = (
        summoner_data['puuid'],
        game_name,
        tag_line,
        summoner_data['summonerLevel'],
        summoner_data['profileIconId'],
        json_str
    )

    try:
        cursor.execute(query, values)
        connection.commit()
        print(f"Saved: {game_name}#{tag_line} (Level {summoner_data['summonerLevel']})")
    except mysql.connector.Error as err:
        print(f"DB Error saving {game_name}: {err}")

def main():
    print("--- Starting Bulk Population ---")
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # 1. Get a list of players (Challenger League)
        # This returns ~300 high-elo players
        entries = fetch_challenger_league()
        print(f"Found {len(entries)} entries in Challenger League.")

        for i, entry in enumerate(entries):
            puuid = entry['puuid']
            
            # Simple progress log
            print(f"[{i+1}/{len(entries)}] Processing PUUID: {puuid[:8]}...")

            # 2. Get Summoner Details
            summoner_data = get_summoner_by_puuid(puuid)
            if not summoner_data:
                continue

            # Respect rate limit
            time.sleep(SLEEP_TIME)

            # 3. Get Account Details (GameName/TagLine)
            # This requires another API call.
            # If you want to go faster and blindly trust legacy names or skip names, you could skip this.
            # But for a good dataset, we want accurate Riot IDs.
            account_data = get_account_by_puuid(summoner_data['puuid'])
            
            # Respect rate limit again
            time.sleep(SLEEP_TIME)

            # 4. Save
            if summoner_data:
                save_player(cursor, connection, summoner_data, account_data)

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        cursor.close()
        connection.close()
        print("Done.")

if __name__ == "__main__":
    main()
