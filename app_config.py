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

# Setup your MongoDB client here or elsewhere

MONGODB_URI = os.getenv("MONGODB_URI")
mongo_client = AsyncIOMotorClient(MONGODB_URI)
test_collection = mongo_client["soin-pump"]["telegram_influencer_data"]
