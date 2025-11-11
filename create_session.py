#!/usr/bin/env python3
"""
Script to create a Telegram session file for Cloud Run deployment
Run this locally to create a valid session file
"""

from telethon import TelegramClient
import os

# Your API credentials
API_ID = 28700349
API_HASH = 'ef8fb06cffda02c80d4fda3b782e6fd6'
SESSION_NAME = 'cloud_run_production'


def create_session():
    print("🚀 Creating Telegram session for Cloud Run...")
    print(f"Session name: {SESSION_NAME}")
    
    # Create client
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    
    try:
        # Start the client (this will prompt for phone number and code)
        print("📱 Starting Telegram client...")
        print("You will be prompted to enter your phone number and verification code.")
        print("This is a one-time setup for Cloud Run deployment.")
        
        client.start()
        
        print(f"✅ Session file '{SESSION_NAME}.session' created successfully!")
        print("📁 You can now use this session file for Cloud Run deployment.")
        
        # Test the session
        me = client.get_me()
        print(f"👤 Logged in as: {me.first_name} (@{me.username})")
        
    except Exception as e:
        print(f"❌ Error creating session: {e}")
        return False
    finally:
        client.disconnect()
    
    return True


if __name__ == "__main__":
    success = create_session()
    if success:
        print("\n🎉 Session creation completed!")
        print("Next steps:")
        print("1. Upload the session file to your project")
        print("2. Redeploy to Cloud Run")
    else:
        print("\n❌ Session creation failed!")
