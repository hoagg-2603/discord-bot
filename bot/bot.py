
import discord
from discord.ext import commands
from config.settings import DISCORD_TOKEN

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print("Bot is ready and running!")

async def load_extensions():
    # Load Cogs
    await bot.load_extension("bot.commands.general")
    await bot.load_extension("bot.commands.schedule")
    await bot.load_extension("bot.commands.email")
    # Load Tasks (as Cogs or just start them?)
    # Usually tasks are better started in on_ready of a specific Cog or main.
    # Let's make a 'TasksCog' to handle scheduling.
    await bot.load_extension("bot.tasks.scheduler")

def run_bot():
    if not DISCORD_TOKEN:
        print("Error: DISCORD_TOKEN not found in .env or settings")
        return
    
    import asyncio
    asyncio.run(load_extensions())
    bot.run(DISCORD_TOKEN)
