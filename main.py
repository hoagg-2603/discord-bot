import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from database.operations import save_schedule, save_user, get_schedule_by_date
from scraper.client import PTITClient
from datetime import datetime, timedelta

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
SCHOOL_USER = os.getenv("SCHOOL_USERNAME")
SCHOOL_PASS = os.getenv("SCHOOL_PASSWORD")

if not TOKEN:
    print("Error: DISCORD_TOKEN not found in .env")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
scheduler = AsyncIOScheduler()

async def sync_schedule_job():
    """
    Job to run at 00:00 and 12:00.
    1. Scrapes data.
    2. Saves to DB.
    3. (Optional) Notifies users of updates.
    """
    print("Starting scheduled sync job...")
    client = PTITClient(headless=True)
    try:
        await client.start()
        await client.login(SCHOOL_USER, SCHOOL_PASS)
        data = await client.get_schedule()
        
        # Save for a default user or iterate all users?
        # For now, hardcode to the configured user or a system user
        # In a real multi-user bot, we would iterate over registered users in DB.
        # Let's save to a "system_default" or similar, OR passing the discord user ID if we knew it.
        # Since this is a specialized bot, maybe we link the .env credentials to a specific discord ID?
        # Or just update the DB and let the notification logic handle it.
        
        # Assumption: The .env credentials belong to the main user.
        # We need a way to link this. For now, let's use a placeholder 'global_sync' ID
        # or rely on the user having registered via command.
        
        # Let's just print for now as we don't know WHICH discord user to save for without a mapping.
        # But we can try to save for ALL users who have these credentials? 
        # Actually, the credentials in .env are likely for ONE student.
        # So we save for that student code.
        
        # Offload blocking DB call
        await bot.loop.run_in_executor(None, save_schedule, "global_bot_user", data)
        print("Scheduled sync completed.")
        
    except Exception as e:
        print(f"Scheduled sync failed: {e}")
    finally:
        await client.close()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    
    # Start Scheduler
    # 00:00
    scheduler.add_job(sync_schedule_job, CronTrigger(hour=0, minute=0))
    # 12:00
    scheduler.add_job(sync_schedule_job, CronTrigger(hour=12, minute=0))
    
    # Testing: Run immediately on startup to verify (Uncomment to test)
    # await sync_schedule_job()
    
    scheduler.start()
    print("Scheduler started (00:00 and 12:00 scan configured).")

@bot.command()
async def ping(ctx):
    await ctx.send('Pong!')

from datetime import datetime, timedelta
from database.operations import save_schedule, save_user, get_schedule_by_date

# ... existing imports ...

@bot.command()
async def tkb(ctx, date_arg="homnay"):
    """
    Xem thời khóa biểu. 
    Sử dụng: !tkb [homnay | mai | yyyy-mm-dd]
    """
    target_date = datetime.now()
    
    if date_arg.lower() in ["homnay", "today"]:
        target_date = datetime.now()
    elif date_arg.lower() in ["mai", "tomorrow"]:
        target_date = datetime.now() + timedelta(days=1)
    else:
        # Try multiple formats
        formats = ["%Y-%m-%d", "%d%m%Y", "%d/%m/%Y"]
        parsed = False
        for fmt in formats:
            try:
                target_date = datetime.strptime(date_arg, fmt)
                parsed = True
                break
            except ValueError:
                continue
        
        if not parsed:
            await ctx.send("Lỗi: Định dạng ngày không đúng. Hãy dùng `ddmmyyyy` (vd: 22012026), `YYYY-MM-DD` hoặc `homnay`, `mai`.")
            return

    date_str = target_date.strftime("%Y-%m-%d")
    
    # Offload blocking DB call
    schedules = await bot.loop.run_in_executor(None, get_schedule_by_date, "global_bot_user", date_str)
    
    if not schedules:
        await ctx.send(f"📅 **{date_str}**: Không có lịch học (hoặc chưa đồng bộ dữ liệu).")
        return

    msg = f"📅 **Lịch học ngày {date_str}**:\n"
    msg += "--------------------------------------\n"
    for s in schedules:
        # Convert period to time (approximate)
        # Period 1 starts 7:00, +50min per period?
        # Just show periods for now.
        start_period = s['start']
        end_period = start_period + s['count'] - 1
        msg += f"⏰ **Tiết {start_period}-{end_period}**: {s['subject']}\n"
        msg += f"   🏫 Phòng: {s['room']} | 👨‍🏫 GV: {s['teacher']}\n\n"
    
    await ctx.send(msg)

@bot.command()
async def force_sync(ctx):
    await ctx.send("Force syncing data...")
    try:
        await sync_schedule_job()
        await ctx.send("Sync complete!")
    except Exception as e:
        await ctx.send(f"Sync failed: {e}")

if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
