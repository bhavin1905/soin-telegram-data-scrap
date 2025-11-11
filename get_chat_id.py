"""
Helper script to get your Telegram chat ID for error notifications.

Steps to set up error notifications:
1. Create a bot using @BotFather on Telegram
2. Get the bot token and add it to your .env file as ERROR_NOTIFICATION_BOT_TOKEN
3. Start a chat with your bot or add it to a group
4. Send a message to the bot or group
5. Run this script to get your chat ID
6. Add the chat ID to your .env file as ERROR_NOTIFICATION_CHAT_ID
"""

import os
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv()


async def get_chat_id():
    bot_token = os.getenv("ERROR_NOTIFICATION_BOT_TOKEN")
    
    if not bot_token:
        print("❌ ERROR_NOTIFICATION_BOT_TOKEN not found in .env file")
        print("Please add your bot token to the .env file first")
        return
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            data = response.json()
        
        if not data.get("ok"):
            print(f"❌ Error: {data.get('description', 'Unknown error')}")
            return
        
        updates = data.get("result", [])
        
        if not updates:
            print("❌ No messages found!")
            print("Please send a message to your bot first, then run this script again.")
            return
        
        print("✅ Found chat IDs:")
        print("-" * 50)
        
        seen_chats = set()
        for update in updates:
            if "message" in update:
                chat = update["message"]["chat"]
                chat_id = chat["id"]
                chat_type = chat["type"]
                
                if chat_id not in seen_chats:
                    seen_chats.add(chat_id)
                    
                    if chat_type == "private":
                        first_name = chat.get("first_name", "")
                        last_name = chat.get("last_name", "")
                        username = chat.get("username", "")
                        print(f"Private chat: {first_name} {last_name} (@{username})")
                    elif chat_type in ["group", "supergroup"]:
                        title = chat.get("title", "")
                        print(f"Group: {title}")
                    
                    print(f"Chat ID: {chat_id}")
                    print("-" * 50)
        
        print("\n💡 Copy one of the Chat IDs above and add it to your .env file as:")
        print("ERROR_NOTIFICATION_CHAT_ID=your_chat_id_here")
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(get_chat_id())
