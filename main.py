
import os
from bot.bot import run_bot
from database.db import init_db

if __name__ == "__main__":
    # Ensure DB is initialized
    init_db()
    
    # Run Bot
    run_bot()
