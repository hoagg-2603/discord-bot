
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Discord
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Database
DB_NAME = "schedule.db"
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), DB_NAME) # e:/discord_bot/schedule.db

# Scraper / School
# SCHOOL_USERNAME/PASSWORD are now in DB, but we keep env for backward compatibility or simple setup if needed.
SCHOOL_USERNAME = os.getenv("SCHOOL_USERNAME")
SCHOOL_PASSWORD = os.getenv("SCHOOL_PASSWORD")

# Gmail
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")

# Timezones
TIMEZONE = "Asia/Ho_Chi_Minh" # Not strictly used yet, but good practice

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SCRAPER_DIR = os.path.join(BASE_DIR, 'scraper')
OUTLOOK_STATE_FILE = os.path.join(BASE_DIR, 'outlook_state.json')
