import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
load_dotenv()

TELEGRAM_API_ID = os.getenv("TELEGRAM_API_ID")
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH")
TELEGRAM_SESSION = os.getenv("TELEGRAM_SESSION")

WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# Error notification settings
ERROR_NOTIFICATION_CHAT_ID = os.getenv("ERROR_NOTIFICATION_CHAT_ID")  # Admin chat ID for error notifications
ERROR_NOTIFICATION_BOT_TOKEN = os.getenv("ERROR_NOTIFICATION_BOT_TOKEN")  # Bot token for sending error notifications

# PostgreSQL/Supabase settings
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:bh@vinJ1905@db.xlgjwdorrhptzrftvmns.supabase.co:5432/postgres")

# Parse DATABASE_URL if provided, otherwise use individual components
if DATABASE_URL:
    # Parse the connection string
    import re
    match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', DATABASE_URL)
    if match:
        DB_USER = match.group(1)
        DB_PASSWORD = match.group(2)
        DB_HOST = match.group(3)
        DB_PORT = match.group(4)
        DB_NAME = match.group(5)
    else:
        # Fallback to individual environment variables
        DB_USER = os.getenv("DB_USER", "postgres")
        DB_PASSWORD = os.getenv("DB_PASSWORD", "bh@vinJ1905")
        DB_HOST = os.getenv("DB_HOST", "db.xlgjwdorrhptzrftvmns.supabase.co")
        DB_PORT = os.getenv("DB_PORT", "5432")
        DB_NAME = os.getenv("DB_NAME", "postgres")
else:
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "bh@vinJ1905")
    DB_HOST = os.getenv("DB_HOST", "db.xlgjwdorrhptzrftvmns.supabase.co")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "postgres")

# Setup your MongoDB client here or elsewhere
MONGODB_URI = os.getenv("MONGODB_URI")

# Validate MONGODB_URI before creating client
if not MONGODB_URI or MONGODB_URI.strip() == "":
    raise ValueError(
        "MONGODB_URI environment variable is not set or is empty. "
        "Please set it in your environment variables or .env file."
    )

mongo_client = AsyncIOMotorClient(MONGODB_URI)
test_collection = mongo_client["soin-pump"]["telegram_influencer_data"]
