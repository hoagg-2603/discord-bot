
from discord.ext import commands
from datetime import datetime, timedelta
from database.operations import save_user, save_schedule, get_schedule_by_date
from scraper.client import PTITClient

class Schedule(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def tkb(self, ctx, date_arg="homnay"):
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
        
        # Use a generic user for retrieval or the specific user? 
        # Current logic in db.operations.get_schedule_by_date ignores user_id basically (queries by date).
        # But if we support multi-user, we might want to filter by user_id if schedules differ (same class, different modules?).
        # For now, keep existing behavior (global schedule query by date).
        schedules = await self.bot.loop.run_in_executor(None, get_schedule_by_date, "global_bot_user", date_str)
        
        if not schedules:
            await ctx.send(f"📅 **{date_str}**: Không có lịch học (hoặc chưa đồng bộ dữ liệu).")
            return

        msg = f"📅 **Lịch học ngày {date_str}**:\n"
        msg += "--------------------------------------\n"
        for s in schedules:
            start_period = s['start']
            end_period = start_period + s['count'] - 1
            msg += f"⏰ **Tiết {start_period}-{end_period}**: {s['subject']}\n"
            msg += f"   🏫 Phòng: {s['room']} | 👨‍🏫 GV: {s['teacher']}\n\n"
        
        await ctx.send(msg)

    @commands.command()
    async def force_sync(self, ctx):
        await ctx.send("🔄 Đang đồng bộ dữ liệu...")
        # We need to trigger the sync job. 
        # Ideally, we call the job function from the Tasks Cog or shared module.
        # But we can't easily import from another Cog instance.
        # So we should put the sync logic in a shared utility or static method, OR import the job function.
        # Let's import the job function from bot.tasks.scheduler (circular import risk?).
        # Better: Put core logic in utils or just re-implement simple trigger here.
        # Actually, let's keep it simple: Just run the sync logic here or better yet, make the Sync Job a standalone function we can import.
        
        from bot.tasks.scheduler import run_sync_schedule
        try:
             await run_sync_schedule(self.bot)
             await ctx.send("✅ Đồng bộ hoàn tất!")
        except Exception as e:
             await ctx.send(f"❌ Đồng bộ thất bại: {e}")

    @commands.command()
    async def schoolsetup(self, ctx, student_code: str, password: str):
        """
        Cài đặt tài khoản trường (Portal/Outlook).
        Sử dụng: !schoolsetup B22CNxxx matkhau
        """
        try:
            await ctx.message.delete()
        except:
            pass
            
        success = await self.bot.loop.run_in_executor(None, save_user, str(ctx.author.id), student_code, password)
        
        if success:
            await ctx.send(f"✅ Đã lưu tài khoản trường cho `{student_code}`.\n- Bot sẽ tự động sync lịch học.\n- Bot sẽ tự động check mail Outlook.", delete_after=15)
        else:
            await ctx.send("❌ Lưu thất bại.", delete_after=10)

    @commands.command()
    async def schoolinfo(self, ctx):
        await ctx.send("ℹ️ Nếu bạn đã chạy `!schoolsetup`, bot sẽ tự động làm việc (Sync & Check Mail).")

async def setup(bot):
    await bot.add_cog(Schedule(bot))
