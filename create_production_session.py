#!/usr/bin/env python3
"""
Script to create a new Telegram session specifically for Cloud Run production deployment
This will create a separate session file to avoid conflicts with local development
"""

import asyncio
from telethon import TelegramClient

# Your API credentials (same as in config)
API_ID = 28700349
API_HASH = "ef8fb06cffda02c80d4fda3b782e6fd6"

# New session name for production (different from local)
PRODUCTION_SESSION = "cloud_run_production"


async def create_production_session():
    """Create a new Telegram session specifically for Cloud Run deployment"""
    print("🔐 Creating new Telegram session for Cloud Run production...")
    print("📱 You will need to enter your phone number and verification code.")
    print("⚠️  This session will be ONLY for the Cloud Run server.")
    print()
    
    client = TelegramClient(PRODUCTION_SESSION, API_ID, API_HASH)
    
    try:
        await client.start()
        
        print("✅ Production session created successfully!")
        print(f"📁 Session file: {PRODUCTION_SESSION}.session")
        print()
        print("🚀 Next steps:")
        print("1. This session file will be uploaded with your code")
        print("2. Update deployment to use TELEGRAM_SESSION=cloudrun_production")
        print("3. Redeploy your service")
        print()
        print("⚠️  IMPORTANT: Do NOT use this session locally!")
        print("   Keep using 'your_session_name' for local development")
        
    except Exception as e:
        print(f"❌ Error creating session: {e}")
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(create_production_session())