import pandas as pd
import json


PLAYER_DATABASE = "data/players.csv"
DATA  = pd.read_csv(PLAYER_DATABASE)
FILTERED_DATA = DATA[(DATA['OVR'] >= 81)]  

SAVE_FILE = "teams.json"

draft_state = {
    "players": {}
}

chosen_list = []
available_list = []
lonely_list = []
count = 20

with open(SAVE_FILE, "r") as file:
    draft_state["players"] = json.load(file)
    keys = list(draft_state["players"].values())
    for key in keys:
        for i in range(0, len(key) - 1):
            chosen_list.append(key[i]['Name'])
    available_list = list(FILTERED_DATA['Name'])
    for player in available_list:
        if player not in chosen_list:
            lonely_list.append(player)
    print(len(lonely_list))            
    for i in range(0, count):
        print(f"{i+1} - {lonely_list[i]}")
        