import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("RIOT_API_KEY")
PLATFORM = os.getenv("RIOT_PLATFORM", "na1")

def debug_league_entry():
    url = f"https://{PLATFORM}.api.riotgames.com/lol/league/v4/challengerleagues/by-queue/RANKED_SOLO_5x5"
    headers = {"X-Riot-Token": API_KEY}
    
    print(f"Requesting: {url}")
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        entries = data.get('entries', [])
        if entries:
            first_entry = entries[0]
            print("Keys available in entry:", first_entry.keys())
            print("First entry sample:", first_entry)
        else:
            print("No entries found.")
    else:
        print(f"Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    debug_league_entry()
