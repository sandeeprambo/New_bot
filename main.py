import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import os
from dotenv import load_dotenv
from keep_alive import keep_alive  # Keeps the bot alive

load_dotenv()  # Load .env variables

TOKEN = os.getenv("DISCORD_TOKEN")
SCOREBOARD_CHANNEL_ID = int(os.getenv("SCOREBOARD_CHANNEL_ID"))

GOALS = {
    "train_heist": {"label": "Train Heist", "target": 2, "count": 0},
    "10v10": {"label": "10v10", "target": 5, "count": 0},
    "6v6": {"label": "6v6", "target": 10, "count": 0},
    "2v2": {"label": "2v2", "target": 20, "count": 0}
}

ALLOWED_ROLE_NAMES = ["IRUMBUKOTTAI HEAD", "Admin"]
PROGRESS_VIEW_ROLES = ["Only IK", "IRUMBUKOTTAI HEAD", "Admin"]

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

scoreboard_message = None

def format_progress():
    return "\n".join([
        f"**{data['label']}**: {data['count']} / {data['target']}"
        for data in GOALS.values()
    ])

async def update_scoreboard(bot):
    global scoreboard_message
    channel = bot.get_channel(SCOREBOARD_CHANNEL_ID)
    if not channel:
        print("Scoreboard channel not found!")
        return

    content = "\U0001F4CA **Weekly Goal Progress:**\n" + format_progress()

    try:
        if scoreboard_message:
            await scoreboard_message.edit(content=content)
        else:
            scoreboard_message = await channel.send(content)
    except discord.Forbidden:
        print("Bot lacks permissions to post/edit scoreboard.")

class GoalButton(discord.ui.Button):
    def __init__(self, goal_key: str):
        super().__init__(label=GOALS[goal_key]["label"], style=discord.ButtonStyle.success)
        self.goal_key = goal_key

    async def callback(self, interaction: discord.Interaction):
        member = interaction.user
        role_names = [role.name for role in member.roles]

        if not any(role in role_names for role in ALLOWED_ROLE_NAMES):
            await interaction.response.send_message("\u274C You don't have permission to mark goals.", ephemeral=True)
            return

        GOALS[self.goal_key]["count"] += 1
        await interaction.response.defer(ephemeral=True)
        await update_scoreboard(bot)

class GoalView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        for goal_key in GOALS:
            self.add_item(GoalButton(goal_key))

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await bot.wait_until_ready()
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Error syncing commands: {e}")
    try:
        await update_scoreboard(bot)
    except Exception as e:
        print(f"Scoreboard update error: {e}")

@bot.tree.command(name="done", description="Mark a goal as completed")
async def done(interaction: discord.Interaction):
    member = interaction.user
    role_names = [role.name for role in member.roles]
    if not any(role in role_names for role in ALLOWED_ROLE_NAMES):
        await interaction.response.send_message("\u274C You don't have permission to initiate goal marking.", ephemeral=True)
        return

    await interaction.response.send_message("Select a goal to mark as done:", view=GoalView(), ephemeral=False)

@bot.tree.command(name="progress", description="Show current weekly goal progress")
async def progress(interaction: discord.Interaction):
    member = interaction.user
    role_names = [role.name for role in member.roles]
    if not any(role in role_names for role in PROGRESS_VIEW_ROLES):
        await interaction.response.send_message("\u274C You don't have permission to view progress.", ephemeral=True)
        return

    await interaction.response.send_message("\U0001F4CA **Weekly Goal Progress:**\n" + format_progress())

@bot.tree.command(name="resetweek", description="Reset all weekly progress (Restricted roles only)")
async def resetweek(interaction: discord.Interaction):
    member = interaction.user
    role_names = [role.name for role in member.roles]
    if not any(role in role_names for role in ALLOWED_ROLE_NAMES):
        await interaction.response.send_message("\u274C You don't have permission to reset goals.", ephemeral=True)
        return

    for goal in GOALS:
        GOALS[goal]["count"] = 0

    await update_scoreboard(bot)
    await interaction.response.send_message("\U0001F501 Weekly goals have been reset!")

# Keep the bot alive
keep_alive()
bot.run(TOKEN)
