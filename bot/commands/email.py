
from discord.ext import commands
from database.operations import add_gmail_account, get_gmail_accounts, delete_gmail_account
from bot.tasks.scheduler import run_check_gmail # We will define this

class Email(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def mailnew(self, ctx, email: str, app_password: str):
        """
        Thêm tài khoản Gmail mới.
        Sử dụng: !mailnew user@gmail.com app_password
        """
        try:
            await ctx.message.delete()
        except:
            pass
            
        success = await self.bot.loop.run_in_executor(None, add_gmail_account, str(ctx.author.id), email, app_password)
        
        if success:
            await ctx.send(f"✅ Đã thêm tài khoản `{email}` thành công!", delete_after=10)
        else:
            await ctx.send("❌ Thêm tài khoản thất bại/Đã tồn tại.", delete_after=10)

    @commands.command()
    async def mailall(self, ctx):
        accounts = await self.bot.loop.run_in_executor(None, get_gmail_accounts, str(ctx.author.id))
        
        if not accounts:
            await ctx.send("📭 Bạn chưa thêm tài khoản nào. Dùng `!mailnew`.")
            return
            
        msg = "**📋 Danh sách Gmail của bạn:**\n"
        for acc in accounts:
            msg += f"- 📧 `{acc['email']}` (Last check: {acc['last_checked']})\n"
            
        await ctx.send(msg)

    @commands.command()
    async def maildel(self, ctx, email: str):
        success = await self.bot.loop.run_in_executor(None, delete_gmail_account, str(ctx.author.id), email)
        if success:
            await ctx.send(f"✅ Đã xóa tài khoản `{email}`.")
        else:
            await ctx.send(f"❌ Không tìm thấy tài khoản `{email}`.")

    @commands.command()
    async def mailcheck(self, ctx):
        await ctx.send("🔄 Đang kiểm tra mail...", delete_after=5)
        try:
            # Import dynamically to avoid circular if needed, but here it's fine
            await run_check_gmail(self.bot) 
            await ctx.send("✅ Đã kiểm tra xong.", delete_after=5)
        except Exception as e:
            print(f"Manual check failed: {e}")

async def setup(bot):
    await bot.add_cog(Email(bot))
