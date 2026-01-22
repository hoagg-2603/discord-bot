import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from database.operations import save_schedule, save_user, get_schedule_by_date, get_upcoming_classes
from scraper.outlook_client import OutlookClient
from scraper.client import PTITClient

# ... existing imports ...

# ... existing code ...

# Track seen emails to avoid spamming the same ones (Global)
SEEN_EMAILS = set()

async def check_gmail_job():
    """
    Runs frequently to check for new emails in Gmail (IMAP is fast).
    """
    from scraper.gmail_client import GmailClient
    
    print("Checking Gmail...")
    user = os.getenv("GMAIL_USER")
    pwd = os.getenv("GMAIL_PASSWORD")
    
    if not user or not pwd:
        return

    def run_check():
        client = GmailClient(user, pwd)
        found = []
        if client.connect():
             found = client.check_emails(look_back=5)
             client.close()
        return found
        
    emails = await bot.loop.run_in_executor(None, run_check)
    
    if emails:
        new_emails = []
        for subj in emails:
            if subj not in SEEN_EMAILS:
                new_emails.append(subj)
                SEEN_EMAILS.add(subj)
                
        if new_emails:
            print(f"Found {len(new_emails)} NEW GMAILs!")
            target_channel = None
            if NOTIFICATION_CHANNEL_ID:
                target_channel = bot.get_channel(NOTIFICATION_CHANNEL_ID)
            
            if not target_channel and bot.guilds:
                target_channel = bot.guilds[0].system_channel or bot.guilds[0].text_channels[0]
                
            if target_channel:
                 msg = "📧 **EMAIL MỚI TỪ GMAIL!**\n"
                 msg += "--------------------------------------\n"
                 for subject in new_emails:
                     msg += f"📩 {subject}\n"
                 msg += "\nCheck mail: https://mail.google.com/"
                 await target_channel.send(msg)

async def check_outlook_job():
    """
    Runs periodically to check for Outlook emails.
    """
    print("Checking Outlook emails...")
    client = OutlookClient(headless=True)
    try:
        # Load credentials
        email = "HoangNH.B22CN336@stu.ptit.edu.vn"
        password = SCHOOL_PASS # From .env
        
        await client.start()
        await client.login(email, password)
        
        current_emails = await client.check_recent_emails()
        
        # Filter new emails
        new_emails = []
        for email_subject in current_emails:
            if email_subject not in SEEN_EMAILS:
                new_emails.append(email_subject)
                SEEN_EMAILS.add(email_subject)
        
        if new_emails:
            print(f"Found {len(new_emails)} NEW Outlook emails!")
            # Notify
            target_channel = None
            if NOTIFICATION_CHANNEL_ID:
                target_channel = bot.get_channel(NOTIFICATION_CHANNEL_ID)
            
            if not target_channel and bot.guilds:
                target_channel = bot.guilds[0].system_channel or bot.guilds[0].text_channels[0]
                
            if target_channel:
                msg = "📧 **EMAIL MỚI TỪ OUTLOOK!**\n"
                msg += "--------------------------------------\n"
                for subject in new_emails:
                    msg += f"📥 {subject}\n"
                msg += "\nCheck mail ngay: https://outlook.office.com/mail/"
                await target_channel.send(msg)
        else:
            print("No new Outlook emails.")
            
    except Exception as e:
        print(f"Outlook check failed: {e}")
    finally:
        await client.close()

# ... existing code ...



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

async def check_upcoming_classes_job():
    """
    Runs every 30 minutes to check for upcoming classes.
    """
    print("Checking for upcoming classes...")
    # Offload DB call
    upcoming = await bot.loop.run_in_executor(None, get_upcoming_classes, 60)
    
    if not upcoming:
        return
        
    print(f"Found {len(upcoming)} upcoming classes.")
    
    # Send notification
    # Strategy: Send to the last channel used for !tkb or a default channel
    target_channel = None
    if NOTIFICATION_CHANNEL_ID:
        target_channel = bot.get_channel(NOTIFICATION_CHANNEL_ID)
    
    # If no channel found, try first guild system channel
    if not target_channel and bot.guilds:
        target_channel = bot.guilds[0].system_channel or bot.guilds[0].text_channels[0]
        
    if target_channel:
        for cls in upcoming:
            # Simple deduplication could be added here (check if already noted)
            # But running every 30 mins with 45-75 min window might trigger twice?
            # 45 <= diff <= 75. 
            # If run at 7:00 (class 8:00, diff 60) -> Alert.
            # If run at 7:30 (class 8:00, diff 30) -> No alert (diff < 45).
            # So 30 min interval is safe.
            
             msg = (f"🔔 **SẮP ĐI HỌC!** (> {cls['minutes_left']} phút nữa)\n"
                    f"📚 Môn: **{cls['subject']}**\n"
                    f"🏫 Phòng: **{cls['room']}**\n"
                    f"⏰ Bắt đầu: **{cls['time']}** (Tiết {cls['start_period']})")
             await target_channel.send(msg)
             print(f"Sent notification for {cls['subject']}")
    else:
        print("No channel to send notifications!")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    
    # Start Scheduler
    # Sync data 00:00 & 12:00
    scheduler.add_job(sync_schedule_job, CronTrigger(hour=0, minute=0))
    scheduler.add_job(sync_schedule_job, CronTrigger(hour=12, minute=0))
    
    # Check for class reminders every 30 minutes
    scheduler.add_job(check_upcoming_classes_job, 'interval', minutes=30)
    
    # Check for Gmail messages every 5 minutes (IMAP is cheap)
    scheduler.add_job(check_gmail_job, 'interval', minutes=5)

    # Check for Outlook emails every 60 minutes (Heavy browser task)
    scheduler.add_job(check_outlook_job, 'interval', minutes=60)
    
    scheduler.start()
    print("Scheduler started (Sync: 00/12h, Remind: 30m, Gmail: 5m, Outlook: 60m).")

@bot.command()
async def ping(ctx):
    await ctx.send('Pong!')

@bot.command()
async def tkb(ctx, date_arg="homnay"):
    global NOTIFICATION_CHANNEL_ID
    # Update notification channel to where user interacts
    NOTIFICATION_CHANNEL_ID = ctx.channel.id
    
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
