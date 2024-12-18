import discord
import os
import functionality as fn
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents: discord.Intents = discord.Intents.default()
intents.message_content = True
intents.typing = False
intents.presences = False
bot = commands.Bot(command_prefix="!", intents=intents)

draft_channel: discord.TextChannel = None
teams_channel: discord.TextChannel = None

@bot.event
async def on_ready():
    # Set the bot's activity to "Playing a game"
    activity = discord.Activity(type=discord.ActivityType.listening, name="!PlsHelp")
    await bot.change_presence(activity=activity)

    global draft_channel, teams_channel
    
    draft_channel = bot.get_channel(int(os.getenv("DRAFT_CHANNEL_ID")))
    teams_channel = bot.get_channel(int(os.getenv("TEAMS_CHANNEL_ID")))

    print(f"{bot.user} has connected to Discord!")

@bot.command(name="SD")
async def start_draft(ctx: commands.Context):
    await ctx.send("# Welcome to the FIFA Draft! How many players are playing?")

    # Get the number of players
    num_players = await fn.get_num_players(ctx, bot)
    if num_players is None:
        return await ctx.send("Timed out. Please restart the draft.")

    # Collect player names
    player_names = await fn.get_player_names(ctx, bot, num_players)
    if not player_names:
        return await ctx.send("Timed out. Please restart the draft.")

    await ctx.send(f"```Players joined: {', '.join(player_names)}```")
    fn.init_draft(player_names)

    # Run 12 position-based rounds
    await draft_channel.send("# Starting position-based draft...")
    for position in fn.get_random_positions():
        await fn.run_draft_round(ctx, bot, position)

    free_pick_count = int(fn.draft_state["free_picks"])
    # Run 10 free pick rounds
    await draft_channel.send(f"# Free Pick Rounds: {free_pick_count} rounds to pick any players")
    for round_num in range(1, free_pick_count + 1):
        await fn.run_free_pick_round(ctx, bot, round_num)

    await draft_channel.send("# Draft Complete! Here are the teams.")
    for player_name in player_names:
        await show_small_team(ctx, player_name, True)

@bot.command(name="SBT")
async def show_big_team(ctx: commands.Context, player_name: str):
    """Show the team of a specific player."""
    team = fn.get_player_team(player_name)
    position_order = [
        'GK', 'LB', 'CB', 'RB', 'CDM', 'LM', 'CM', 'RM', 'CAM', 'LW', 'ST', 'RW'
    ]
    if team:
        sorted_team = sorted(team, key=lambda p: position_order.index(p['Position']) if p['Position'] in position_order else len(position_order))
        # Create an embed
        embed = discord.Embed(
            title=f"{player_name}'s Team",
            description=f"Here are the players ({len(sorted_team)}) drafted:\n-------------------",
            color=discord.Color.blue()
        )
        for p in sorted_team:
            embed.add_field(
                name=f"{p['Name']}",
                value=(
                    f"{p['Position']} - {p['OVR']}\n"
                    f"[View Stats]({p['url']})\n"  # Clickable link
                    f"-------------------"
                ),
                inline=False
            )

        # Send the embed
        await teams_channel.send(embed=embed)
    else:
        await teams_channel.send(f"No team found for **{player_name}**.")

@bot.command(name="SST")
async def show_small_team(ctx: commands.Context, player_name: str, auto: bool = False):
    """Show the team of a specific player."""
    display_name = player_name
    if(not auto):
        mentioned_user = ctx.message.mentions[0]
        player_name = mentioned_user.name
        display_name = mentioned_user.display_name
    team = fn.get_player_team(player_name)
    position_order = [
        'GK', 'LB', 'CB', 'RB', 'CDM', 'LM', 'CM', 'RM', 'CAM', 'LW', 'ST', 'RW'
    ]
    if team:
        sorted_team = sorted(team, key=lambda p: position_order.index(p['Position']) if p['Position'] in position_order else len(position_order))
        # Create an embed
        embed = discord.Embed(
            title=f"{display_name}'s Team",
            description=f"Here are the players ({len(sorted_team)}) drafted:\n-------------------",
            color=discord.Color.blue()
        )
        for p in sorted_team:
            embed.add_field(
                name=f"{p['Name']}",
                value=(
                    f"{p['Position']} - {p['OVR']}\n"
                ),
                inline=True
            )

        # Send the embed
        await teams_channel.send(embed=embed)
    else:
        await teams_channel.send(f"No team found for **{player_name}**.")


@bot.command(name="PlsHelp")
async def help_text(ctx: commands.Context):
    """Sends the various commands to chat."""
    await ctx.send(f"```!SD - Starts the drafting mode\n!SBT <player_name> - Expanded view on player's squad\n!SST <player_name> - Brief view on player's squad```")

# Run the bot
bot.run(TOKEN) 
