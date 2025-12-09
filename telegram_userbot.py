import re
import logging
import os
import traceback
import datetime
import httpx
import asyncpg
import uuid
from telethon import TelegramClient, events
from telethon.tl.functions.channels import GetFullChannelRequest, GetParticipantsRequest
from supabase import create_client
from telethon.tl.types import ChannelParticipantsSearch

from app_config import (
    WEBHOOK_URL, TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_SESSION,
    ERROR_NOTIFICATION_CHAT_ID, ERROR_NOTIFICATION_BOT_TOKEN, test_collection,
    DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME
)
from utils import fetch_dexscreener_data, extract_dexscreener_fields

logging.basicConfig(level=logging.INFO)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def upload_image(local_file_path, dest_path):
    with open(local_file_path, "rb") as f:
        supabase.storage.from_("images").upload(dest_path, f)
    return supabase.storage.from_("images").get_public_url(dest_path)

# Use environment variables if available, otherwise fallback to hardcoded values
api_id = int(TELEGRAM_API_ID) if TELEGRAM_API_ID else 28700349
api_hash = TELEGRAM_API_HASH if TELEGRAM_API_HASH else "ef8fb06cffda02c80d4fda3b782e6fd6"
session_name = TELEGRAM_SESSION if TELEGRAM_SESSION else 'session'

client = TelegramClient(session_name, api_id, api_hash)

# Address extraction patterns
patterns = {
    "Ethereum": r"0x[a-fA-F0-9]{40}",
    "Solana": r"[1-9A-HJ-NP-Za-km-z]{32,44}",
    "pairAddress": r"0x[a-fA-F0-9]{64}",
    "Polkadot": r"[1-9A-HJ-NP-Za-km-z]{47}",
    "Tezos": r"(tz1|tz2|tz3|KT1)[1-9A-HJ-NP-Za-km-z]{33}",
}
compiled_patterns = {k: re.compile(v) for k, v in patterns.items()}

# PostgreSQL connection pool (will be initialized on first use)




async def send_error_notification(error_message: str, error_details: str = None):
    """Send error notification to admin via Telegram bot"""
    if not ERROR_NOTIFICATION_BOT_TOKEN or not ERROR_NOTIFICATION_CHAT_ID:
        logging.warning("Error notification bot token or chat ID not configured")
        return
    
    try:
        timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        notification_text = "🚨 **USERBOT ERROR ALERT** 🚨\n\n"
        notification_text += f"**Time:** {timestamp}\n"
        notification_text += f"**Error:** {error_message}\n"
        
        if error_details:
            if len(error_details) > 1000:
                error_details = error_details[:1000] + "... (truncated)"
            notification_text += f"**Details:**\n```{error_details}```\n"
        
        notification_text += "\n⚠️ Please check the server logs for more information."
        
        bot_url = f"https://api.telegram.org/bot{ERROR_NOTIFICATION_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": ERROR_NOTIFICATION_CHAT_ID,
            "text": notification_text,
            "parse_mode": "Markdown"
        }
        
        async with httpx.AsyncClient(timeout=10.0) as http_client:
            response = await http_client.post(bot_url, json=payload)
            if response.status_code == 200:
                logging.info("Error notification sent successfully")
            else:
                logging.error(f"Failed to send error notification: {response.status_code}")
    
    except Exception as e:
        logging.error(f"Failed to send error notification: {e}")


@client.on(events.NewMessage)
async def reader(event):
    try:
        chat = event.chat
        message_obj = event.message
        
        if not event.is_group and not event.is_channel:
            return

        if not message_obj.message:
            return

        message = message_obj.message
        msg_text = message_obj.message

        # Group full info
        full = await client(GetFullChannelRequest(chat))
        user_count = getattr(full.full_chat, 'participants_count', None)

        # Print group details (existing functionality)
        print("\n--- Group Details ---")
        print("Message: ", message)
        print("Name:", chat.title)
        print("Username:", chat.username)
        print("Members:", user_count)
        print("About:", full.full_chat.about)
        print("ID:", chat.id)
        print("Message Datetime: ", datetime.datetime.now())

        # Extract contract addresses
        all_addresses = []
        for _, regex in compiled_patterns.items():
            matches = regex.findall(msg_text)
            for addr in matches:
                all_addresses.append(addr)

        # If no addresses found, just print and return (keep existing behavior)
        if not all_addresses:
            print("\n--- No contract addresses found in message ---")
            return

        print(f"\n--- Found {len(all_addresses)} contract address(es) ---")

        # Get group information
        group_name = getattr(chat, 'title', str(chat.id))
        group_username = getattr(chat, 'username', None)

        # Generate message link
        message_link = (
            f"https://t.me/{group_username}/{message_obj.id}"
            if group_username else
            f"https://t.me/c/{str(chat.id)[4:]}/{message_obj.id}"
            if str(chat.id).startswith("-100") else None
        )

        # Get influencer information
        influencer = (
            message_obj.sender.username if message_obj.sender and hasattr(message_obj.sender, 'username')
            else str(message_obj.sender_id) if message_obj.sender_id
            else "Unknown"
        )

        # Get user profile image and store in PostgreSQL
        profile_image_url = None
        try:
            if message_obj.sender:
                photos = await client.get_profile_photos(message_obj.sender, limit=1)
                if photos and len(photos) > 0:
                    latest_photo = photos[0]
                    try:
                        # Download photo to temporary location
                        os.makedirs("tmp", exist_ok=True)
                        temp_photo_path = f"tmp/profile_{message_obj.sender_id}_{latest_photo.id}.jpg"
                        photo_path = await client.download_profile_photo(
                            message_obj.sender,
                            file=temp_photo_path
                        )
                        
                        if photo_path:
                            file_name = f"profile/{message_obj.sender_id}_{latest_photo.id}.jpg"
                            profile_image_url = upload_image(photo_path, file_name)
                            
                            # Clean up temporary file
                            try:
                                if os.path.exists(photo_path):
                                    os.remove(photo_path)
                            except Exception as cleanup_error:
                                logging.warning(f"Could not clean up temporary file {photo_path}: {str(cleanup_error)}")
                        else:
                            profile_image_url = f"telegram_photo_id_{latest_photo.id}"
                            logging.info(f"Profile photo found for user {influencer}, photo ID: {latest_photo.id} (not downloaded)")
                    except Exception as download_error:
                        profile_image_url = f"telegram_photo_id_{latest_photo.id}"
                        logging.warning(f"Could not download profile photo for user {influencer}: {str(download_error)}")
        except Exception as photo_error:
            logging.warning(f"Could not get profile photo for user {influencer}: {str(photo_error)}")

        msg_time_dt = message_obj.date if message_obj.date else datetime.datetime.utcnow()

        dex_data_for_webhook = []
        contracts_for_payload = []

        # Process each address
        for addr in all_addresses:
            try:
                print(f"\n--- Processing address: {addr} ---")
                
                # Find existing docs for this contract address and user
                existing_docs = await test_collection.find({"Contract Address": addr, "Username": influencer}).to_list(length=10)

                found_match = False

                for doc in existing_docs:
                    dex_data = doc.get("Dexscreener Data", {})
                    pairs = dex_data if isinstance(dex_data, list) else []

                    for pair in pairs:
                        chain_id = pair.get("chainId") or pair.get("chain")
                        base_token_address = pair.get("baseToken", {}).get("address")
                        if chain_id and base_token_address:
                            # If match found, increment Call Count and skip fetching new data
                            await test_collection.update_one(
                                {"_id": doc["_id"]},
                                {"$inc": {"Call Count": 1}}
                            )
                            found_match = True
                            logging.info(f"Incremented Call Count for {addr} for user {influencer}")
                            print(f"✓ Incremented Call Count for existing document")
                            break
                    if found_match:
                        break

                if not found_match:
                    # Fetch new Dexscreener data
                    print(f"Fetching Dexscreener data for {addr}...")
                    dexscreener_data = fetch_dexscreener_data(addr)
                    
                    logging.info(f"Dexscreener data: {dexscreener_data}")
                    # Extract only the specified fields
                    extracted_dex_data = extract_dexscreener_fields(dexscreener_data)
                    logging.info(f"Fetched and extracted Dexscreener data for {addr}: {len(extracted_dex_data)} pairs")
                    print(f"✓ Fetched {len(extracted_dex_data)} Dexscreener pairs")

                    first_pair = extracted_dex_data[0] if isinstance(extracted_dex_data, list) and len(extracted_dex_data) > 0 else {}

                    chain_id = first_pair.get("chainId") or first_pair.get("chain")
                    base_token_address = first_pair.get("baseToken", {}).get("address") if first_pair.get("baseToken") else None

                    doc = {
                        "Group Name": group_name,
                        "Chain": chain_id,
                        "Contract Address": base_token_address,
                        "Group User Count": user_count,
                        "Username": influencer,
                        "profile_image": profile_image_url,
                        "Message DateTime": msg_time_dt,
                        "Full Message": msg_text,
                        "Dexscreener Data": extracted_dex_data,
                        "Call Count": 1,
                        "Message Link": message_link,
                    }
                    await test_collection.insert_one(doc)
                    logging.info(f"Inserted new document for {addr} user {influencer}")
                    print(f"✓ Inserted new document into database")

                    dex_data_for_webhook.append({
                        "contract_address": addr,
                        "dexscreener": extracted_dex_data
                    })

                contracts_for_payload.append({"address": addr})
            
            except Exception as addr_error:
                error_msg = f"Error processing address {addr}: {str(addr_error)}"
                logging.error(error_msg)
                print(f"✗ {error_msg}")
                await send_error_notification(
                    "Address Processing Error",
                    f"Error processing address {addr} from user {influencer} in group {group_name}: {str(addr_error)}"
                )
                continue

        # Build webhook payload
        if contracts_for_payload and WEBHOOK_URL:
            payload = {
                "channel": group_name,
                "message": msg_text,
                "contracts": contracts_for_payload,
                "username": influencer,
                "timestamp": str(msg_time_dt),
                "message_link": message_link,
                "dexscreener_data": dex_data_for_webhook,
            }

            # Async POST to webhook
            try:
                async with httpx.AsyncClient(timeout=30.0) as async_client:
                    response = await async_client.post(WEBHOOK_URL, json=payload)
                logging.info(f"📬 Payload sent, webhook responded with status {response.status_code}")
                print(f"✓ Webhook notification sent (status: {response.status_code})")
            except Exception as webhook_error:
                error_msg = f"Webhook error: {str(webhook_error)}"
                logging.error(f"❌ {error_msg}")
                print(f"✗ {error_msg}")
                await send_error_notification(
                    "Webhook Communication Error",
                    f"Failed to send data to webhook {WEBHOOK_URL}: {str(webhook_error)}"
                )

    except Exception as e:
        error_msg = f"Critical error in message handler: {str(e)}"
        error_details = traceback.format_exc()
        logging.error(f"❌ {error_msg}")
        logging.error(f"Error details: {error_details}")
        print(f"✗ {error_msg}")
        
        # Send error notification
        await send_error_notification(
            "Critical Message Handler Error",
            f"Telegram Userbot encountered a critical error: {str(e)}\n\nFull traceback:\n{error_details}"
        )


if __name__ == "__main__":
    try:
        client.start()
        print("Userbot started...")
        client.run_until_disconnected()
    except KeyboardInterrupt:
        logging.info("🛑 Userbot stopped by user")
    except Exception as e:
        logging.error(f"❌ Fatal error: {str(e)}")
        exit(1)
    finally:
        # Cleanup database connection pool
        if _db_pool:


            try:
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is running, schedule the close
                    asyncio.create_task(_db_pool.close())
                else:
                    # If loop is not running, run the close
                    loop.run_until_complete(_db_pool.close())
                logging.info("Database connection pool closed")
            except Exception as cleanup_error:
                logging.warning(f"Error closing database pool: {str(cleanup_error)}")
