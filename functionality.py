import random
import json
import asyncio
import pandas as pd
import discord
import os
from discord.ext import commands
from dotenv import load_dotenv

PLAYER_DATABASE = "data/players.csv"
DATA  = pd.read_csv(PLAYER_DATABASE)
FILTERED_DATA = DATA[(DATA['OVR'] >= 81) & (DATA['OVR'] <= 89)]  

load_dotenv()

player_objects = {}
picked_players = set()

draft_channel: discord.TextChannel = None
teams_channel: discord.TextChannel = None

# Draft State
draft_state = {
    "players": {},
    "positions": ["LW", "ST", "RW", "LM", "RM", "CAM", "CDM", "CM", "LB", "RB", "CB", "CB", "GK"],
    # "positions": ["LW"],
    "free_picks": 11
}

SAVE_FILE = "teams.json"

# with open(SAVE_FILE, "r") as file:
#     draft_state["players"] = json.load(file)
#     keys = list(draft_state["players"].keys())
#     print(keys)
#     random.shuffle(keys)
#     randomized_dict = {key: draft_state["players"][key] for key in keys}
#     print(draft_state['players'])
#     print(randomized_dict)
#     draft_state['players'] = randomized_dict

# Helper Functions
def init_draft(player_names):
    """Initialize draft state."""
    draft_state["players"] = {name: [] for name in player_names}
    save_to_json()
    
def save_to_json():
    """Save current teams to JSON."""
    with open(SAVE_FILE, "w") as file:
        json.dump(draft_state["players"], file, indent=4)

def load_json():
    """Load teams from JSON."""
    try:
        with open(SAVE_FILE, "r") as file:
            draft_state["players"] = json.load(file)
    except FileNotFoundError:
        save_to_json()
        
def get_random_positions():
    """Return positions in random order."""
    return random.sample(draft_state["positions"], len(draft_state["positions"]))
        
def get_random_players(position=None, count=5):
    """Get random players filtered by position or any."""
    global picked_players

    # Filter the pool based on position and already picked players
    if position:
        pool = FILTERED_DATA[(FILTERED_DATA['Position'] == position) & 
                             (~FILTERED_DATA['Name'].isin(picked_players))]
    else:
        pool = FILTERED_DATA[~FILTERED_DATA['Name'].isin(picked_players)]
    
    # Safeguard against running out of players
    available_count = len(pool)
    if available_count == 0:
        print("No more players available in this category!")
        return []

    # Randomly sample players (up to the available number)
    chosen_players = pool.sample(n=min(count, available_count), replace=False)[['Name', 'Position', 'OVR', 'url']]
        
    # Return players as a dictionary
    return chosen_players.to_dict(orient='records')

def random_player_selection(player_pool, num_choices=5):
    """
    Selects random players from the player pool, ensuring no duplicates.
    """
    # Filter out already picked players
    available_players = [player for player in player_pool if player not in picked_players]

    # If not enough players left, adjust the number of choices
    if len(available_players) < num_choices:
        num_choices = len(available_players)

    # Randomly pick players from the available pool
    chosen_players = random.sample(available_players, num_choices)

    return chosen_players

async def get_num_players(ctx: commands.Context, bot: commands.Bot):
    """Prompt for the number of players."""
    global draft_channel, teams_channel
    draft_channel = bot.get_channel(int(os.getenv("DRAFT_CHANNEL_ID")))
    teams_channel = bot.get_channel(int(os.getenv("TEAMS_CHANNEL_ID")))

    def check(m: discord.Message):
        return m.author == ctx.author and m.content.isdigit()

    try:
        msg = await bot.wait_for('message', check=check)
        return int(msg.content)
    except asyncio.TimeoutError:
        return None

async def get_player_names(ctx: commands.Context, bot: commands.Bot, num_players: int):
    """Prompt for player names."""
    player_names = []
    await ctx.send(f"Can the {num_players} players send any message one at a time?")

    while len(player_names) < num_players:
        try:
            msg: discord.Message = await bot.wait_for('message')
            if(msg.author == bot.user):
                continue
            else:
                player_objects[msg.author] = msg.author.name  # Store the user object
                player_names.append(msg.author.name)
        except asyncio.TimeoutError:
            return None
    return player_names

async def run_draft_round(ctx: commands.Context, bot: commands.Bot, position: int):
    """Run a single position-based draft round."""
    global draft_channel, teams_channel, draft_state
    await draft_channel.send(f"## Drafting for {position} position")
    
    keys = list(draft_state["players"].keys())
    random.shuffle(keys)
    randomized_dict = {key: draft_state["players"][key] for key in keys}
    draft_state['players'] = randomized_dict
    
    for player_name in draft_state["players"]:
        # Get 5 random players for this position, avoiding duplicates
        options = get_random_players(position)

        # If no players are available, end the draft round for this player
        if not options:
            await draft_channel.send(f"No more players available for the {position} position.")
            continue

        embed = discord.Embed(
            title=f"**{player_name}, choose a player:**\n",
            description="Here are your choices:\n-------------------",
            color=discord.Color.blue()
        )

        for idx, p in enumerate(options):
            embed.add_field(
                name=f"{idx+1}. {p['Name']}",
                value=(
                    f"({p['Position']}) - {p['OVR']}\n"
                    f"[View Stats]({p['url']})\n"  # Clickable link
                    f"-------------------"
                ),
                inline=False
            )

        # Send the embed
        message = await draft_channel.send(embed=embed)

        emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣']
        for idx, emoji in enumerate(emojis[:len(options)]):
            await message.add_reaction(emoji)


        # Check function to validate the player's response
        def check(reaction: discord.Reaction, user: discord.User):
            return user.name == player_name and str(reaction.emoji) in emojis[:len(options)]

        try:
            # Wait for the player's choice
            reaction, user = await bot.wait_for('reaction_add', check=check)
            choice = emojis.index(str(reaction.emoji))
            chosen_player = options[choice]
            draft_state["players"][player_name].append(chosen_player)
            picked_players.add(chosen_player['Name'])
            save_to_json()
            await message.delete()
            await draft_channel.send(f"```{player_name} picked {chosen_player['Name']} ({chosen_player['Position']}) - {chosen_player['OVR']}```")
            

        except (asyncio.TimeoutError, ValueError, IndexError):
            await draft_channel.send(f"{player_name} missed their pick!")

async def run_free_pick_round(ctx: commands.Context, bot: commands.Bot, round_num: int):
    """Run a single free pick round."""
    global draft_channel, teams_channel, draft_state
    await draft_channel.send(f"## Free Pick Round {round_num}")
    
    keys = list(draft_state["players"].keys())
    random.shuffle(keys)
    randomized_dict = {key: draft_state["players"][key] for key in keys}
    draft_state['players'] = randomized_dict
    
    for player_name in draft_state["players"]:
        # Get 5 random players, avoiding duplicates
        options = get_random_players()

        # If no players are available, end the free pick round for this player
        if not options:
            await draft_channel.send(f"No more players available for selection.")
            continue

        embed = discord.Embed(
            title=f"**{player_name}, choose a player:**\n",
            description="Here are your choices:\n-------------------",
            color=discord.Color.blue()
        )

        for idx, p in enumerate(options):
            embed.add_field(
                name=f"{idx+1}. {p['Name']}",
                value=(
                    f"({p['Position']}) - {p['OVR']}\n"
                    f"[View Stats]({p['url']})\n"  # Clickable link
                    f"-------------------"
                ),
                inline=False
            )

        # Send the embed
        message = await draft_channel.send(embed=embed)

        emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣']
        for idx, emoji in enumerate(emojis[:len(options)]):
            await message.add_reaction(emoji)


        # Check function to validate the player's response
        def check(reaction: discord.Reaction, user: discord.User):
            return user.name == player_name and str(reaction.emoji) in emojis[:len(options)]

        try:
            # Wait for the player's choice
            reaction, user = await bot.wait_for('reaction_add', check=check)
            choice = emojis.index(str(reaction.emoji))
            chosen_player = options[choice]
            draft_state["players"][player_name].append(chosen_player)
            picked_players.add(chosen_player['Name'])
            save_to_json()
            await message.delete()
            await draft_channel.send(f"```{player_name} picked {chosen_player['Name']} ({chosen_player['Position']}) - {chosen_player['OVR']}```")

        except (asyncio.TimeoutError, ValueError, IndexError):
            await draft_channel.send(f"{player_name} missed their pick!")

def get_player_team(player_name: str):
    """Retrieve a player's team."""
    load_json()
    return draft_state["players"].get(player_name, [])