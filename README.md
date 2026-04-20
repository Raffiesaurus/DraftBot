# DraftBot

A Discord bot that automates a **FIFA player draft** for custom tournaments. Runs a structured draft across your server, position-based rounds followed by free picks and posts each manager's squad as a Discord embed when it's done.

---

## How It Works

1. A manager kicks off the draft with `!SD`
2. The bot asks how many players are participating and collects their names
3. It runs **12 position-based rounds** (GK, CB, ST, etc.) in random order each participant picks a real FIFA player for that position on their turn
4. It then runs a set of **free pick rounds** where anyone can grab any remaining player
5. Once complete, all squads are posted to your designated teams channel as formatted embeds

---

## Commands

| Command | Description |
|---------|-------------|
| `!SD` | Start a new draft session |
| `!SBT <player_name>` | Show a player's full squad (expanded view with stats + links) |
| `!SST @mention` | Show a player's squad (compact view) |
| `!PlsHelp` | List all available commands |

---

## Setup

1. Clone the repo:
   ```bash
   git clone https://github.com/Raffiesaurus/DraftBot.git
   cd DraftBot
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the root with the following:
```
DISCORD_TOKEN=your_bot_token_here
DRAFT_CHANNEL_ID=channel_id_for_draft_messages
TEAMS_CHANNEL_ID=channel_id_for_team_embeds
```

4. Run the bot:
```bash
python main.py
```

---

## Tech

- **Language:** Python
- **Library:** discord.py
- **Config:** python-dotenv

---

## License

MIT
