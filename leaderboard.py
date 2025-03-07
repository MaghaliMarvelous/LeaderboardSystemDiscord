import discord
from discord.ext import commands, tasks
import json
import os
import time

intents = discord.Intents.default()
intents.presences = True
intents.members = True  

bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "activity_leaderboard.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

activity_data = load_data()
user_active_times = {}

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    track_activity.start()

@bot.event
async def on_member_update(before, after):
    user_id = str(after.id)
    
    if after.status in [discord.Status.online, discord.Status.idle, discord.Status.dnd]:
        if user_id not in user_active_times:
            user_active_times[user_id] = time.time()
    else:
        if user_id in user_active_times:
            elapsed_time = time.time() - user_active_times[user_id]
            minutes_active = int(elapsed_time / 60)
            
            if minutes_active > 0:
                if user_id not in activity_data:
                    activity_data[user_id] = {"name": after.name, "points": 0}
                
                activity_data[user_id]["points"] += minutes_active
                save_data(activity_data)
            
            del user_active_times[user_id]

@tasks.loop(minutes=1)
async def track_activity():
    for user_id, start_time in list(user_active_times.items()):
        elapsed_time = time.time() - start_time
        minutes_active = int(elapsed_time / 60)
        
        if minutes_active > 0:
            if user_id not in activity_data:
                member = bot.get_user(int(user_id))
                activity_data[user_id] = {"name": member.name if member else "Unknown", "points": 0}
            
            activity_data[user_id]["points"] += minutes_active
            user_active_times[user_id] = time.time()
            save_data(activity_data)

@bot.command()
async def leaderboard(ctx):
    if not activity_data:
        await ctx.send("No active time recorded yet.")
        return

    sorted_data = sorted(activity_data.items(), key=lambda x: x[1]["points"], reverse=True)
    leaderboard_text = "**⏳ Active Time Leaderboard ⏳**\n"

    for rank, (user_id, data) in enumerate(sorted_data, 1):
        leaderboard_text += f"**{rank}. {data['name']}** - {data['points']} minutes\n"

    await ctx.send(leaderboard_text)

@bot.command()
async def mytime(ctx):
    user_id = str(ctx.author.id)
    if user_id in activity_data:
        await ctx.send(f"🕒 {ctx.author.mention}, you have **{activity_data[user_id]['points']}** minutes of activity time.")
    else:
        await ctx.send(f"{ctx.author.mention}, you don't have any recorded activity time yet.")

bot.run("YOUR_BOT_TOKEN")
