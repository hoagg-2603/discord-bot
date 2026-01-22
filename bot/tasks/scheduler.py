
import os
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from database.operations import save_schedule, get_users, get_upcoming_classes, get_gmail_accounts
from scraper.client import PTITClient
from scraper.outlook_client import OutlookClient
from config.settings import GMAIL_USER, GMAIL_PASSWORD, SCHOOL_PASSWORD, SCHOOL_USERNAME

# Global SEEN_EMAILS
SEEN_EMAILS = set()

# --- JOB FUNCTIONS ---

async def run_sync_schedule(bot):
    print("Starting scheduled sync job (Multi-user)...")
    users = await bot.loop.run_in_executor(None, get_users)
    if not users:
        print("No users registered.")
        return

    for user_data in users:
        discord_id = user_data['discord_id']
        student_code = user_data['student_code']
        password = user_data['password']
        
        if not password:
            continue
            
        print(f"Syncing for {student_code}...")
        client = PTITClient(headless=True)
        try:
            await client.start()
            await client.login(student_code, password)
            data = await client.get_schedule()
            await bot.loop.run_in_executor(None, save_schedule, discord_id, data)
            print(f"Synced for {student_code}.")
            
            # Notify
            user = await bot.fetch_user(int(discord_id))
            if user:
                try:
                    await user.send(f"✅ Đã đồng bộ lịch học mới cho mã SV: {student_code}")
                except:
                    pass
        except Exception as e:
            print(f"Sync failed for {student_code}: {e}")
        finally:
            await client.close()

async def run_check_gmail(bot):
    from scraper.gmail_client import GmailClient
    print("Checking Gmail (Multi-account)...")
    
    accounts = await bot.loop.run_in_executor(None, get_gmail_accounts)
    
    # Fallback to env if needed (though we migrated, but safe to keep logic robust)
    if not accounts and GMAIL_USER and GMAIL_PASSWORD:
         accounts.append({"email": GMAIL_USER, "app_password": GMAIL_PASSWORD})
    
    if not accounts: 
        return

    for acc in accounts:
        user_email = acc['email']
        pwd = acc['app_password']
        user_id = acc.get('user_id')
        
        def run_check_for_acc(u, p):
            client = GmailClient(u, p)
            found = []
            if client.connect():
                 found = client.check_emails(look_back=5)
                 client.close()
            return found
            
        try:
            emails = await bot.loop.run_in_executor(None, run_check_for_acc, user_email, pwd)
        except Exception as e:
            print(f"Error checking {user_email}: {e}")
            continue
        
        if emails:
            new_emails = []
            for subj in emails:
                unique_key = f"{user_email}:{subj}"
                if unique_key not in SEEN_EMAILS:
                    new_emails.append(subj)
                    SEEN_EMAILS.add(unique_key)
                    
            if new_emails:
                print(f"Found new Gmails for {user_email}.")
                target_channel = None
                
                # If associated with a user, dm them
                if user_id:
                    try:
                        u = await bot.fetch_user(int(user_id))
                        if u:
                             msg = f"📧 **EMAIL MỚI ({user_email})!**\n"
                             for subject in new_emails:
                                 msg += f"📩 {subject}\n"
                             msg += "\nCheck mail: https://mail.google.com/"
                             await u.send(msg)
                             continue
                    except:
                        pass
                
                # Fallback to guild system channel if not directed
                if bot.guilds:
                    target_channel = bot.guilds[0].system_channel or bot.guilds[0].text_channels[0]
                    if target_channel:
                         msg = f"📧 **EMAIL MỚI ({user_email})!**\n"
                         for subject in new_emails:
                             msg += f"📩 {subject}\n"
                         await target_channel.send(msg)

async def run_check_outlook(bot):
    print("Checking Outlook emails...")
    users = await bot.loop.run_in_executor(None, get_users)
    if not users:
        return

    for user_data in users:
        discord_id = user_data['discord_id']
        student_code = user_data['student_code']
        email = f"{student_code}@stu.ptit.edu.vn"
        password = user_data['password']
        
        if not password: continue

        client = OutlookClient(headless=True)
        try:
            await client.start()
            await client.login(email, password)
            current_emails = await client.check_recent_emails()
            new_emails = []
            for email_subject in current_emails:
                unique_key = f"{discord_id}:outlook:{email_subject}"
                if unique_key not in SEEN_EMAILS:
                    new_emails.append(email_subject)
                    SEEN_EMAILS.add(unique_key)
            
            if new_emails:
                print(f"New Outlook emails for {discord_id}.")
                discord_user = await bot.fetch_user(int(discord_id))
                if discord_user:
                    msg = "📧 **EMAIL MỚI TỪ OUTLOOK!**\n"
                    for subject in new_emails:
                        msg += f"📥 {subject}\n"
                    msg += "\nCheck mail ngay: https://outlook.office.com/mail/"
                    try: 
                        await discord_user.send(msg)
                    except: pass
        except Exception as e:
            print(f"Outlook check failed for {email}: {e}")
        finally:
            await client.close()

async def run_reminder_job(bot):
    print("Checking reminders...")
    # This logic sends to channel, but ideally should send to specific users.
    upcoming = await bot.loop.run_in_executor(None, get_upcoming_classes, 60)
    if not upcoming: return

    for cls in upcoming:
        user_id = cls.get('user_id')
        msg = (f"🔔 **SẮP ĐI HỌC!** (> {cls['minutes_left']} phút nữa)\n"
               f"📚 Môn: **{cls['subject']}**\n"
               f"🏫 Phòng: **{cls['room']}**\n"
               f"⏰ Bắt đầu: **{cls['time']}**")
        
        # Try to DM user
        if user_id:
            try:
                u = await bot.fetch_user(int(user_id))
                await u.send(msg)
                print(f"Sent reminder to {user_id}")
                continue
            except: 
                pass
        
        # Fallback to channel if needed (or just skip if multi-user privacy is key)
        # For now, let's just print/log if DM fails.
        
# --- COG ---

class Scheduler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler()

    async def cog_load(self):
        # Schedule jobs
        self.scheduler.add_job(run_sync_schedule, CronTrigger(hour=0, minute=0), args=[self.bot])
        self.scheduler.add_job(run_sync_schedule, CronTrigger(hour=12, minute=0), args=[self.bot])
        self.scheduler.add_job(run_reminder_job, 'interval', minutes=30, args=[self.bot])
        self.scheduler.add_job(run_check_gmail, 'interval', minutes=5, args=[self.bot])
        self.scheduler.add_job(run_check_outlook, 'interval', minutes=60, args=[self.bot])
        
        self.scheduler.start()
        print("Scheduler started.")

    async def cog_unload(self):
        self.scheduler.shutdown()

async def setup(bot):
    await bot.add_cog(Scheduler(bot))
