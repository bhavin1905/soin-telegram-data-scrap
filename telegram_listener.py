# import re
# import logging
# import asyncio
# import traceback
# from datetime import datetime
# from aiohttp import web
# import os

# import httpx
# from telethon import TelegramClient, events
# from telethon.tl.functions.channels import GetFullChannelRequest
# from supabase import create_client

# from app_config import (
#     WEBHOOK_URL, TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_SESSION,
#     ERROR_NOTIFICATION_CHAT_ID, ERROR_NOTIFICATION_BOT_TOKEN
# )
# from app_config import test_collection
# from utils import fetch_dexscreener_data, extract_dexscreener_fields
# print("DEBUG ENV VARIABLES:")
# print("TELEGRAM_API_ID:", os.getenv("TELEGRAM_API_ID"))
# print("TELEGRAM_API_HASH:", os.getenv("TELEGRAM_API_HASH"))
# print("TELEGRAM_SESSION:", os.getenv("TELEGRAM_SESSION"))

# logging.basicConfig(level=logging.INFO)

# # Supabase setup for image storage
# SUPABASE_URL = os.getenv("SUPABASE_URL")
# SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# def check_image_exists(dest_path):
#     """Check if image already exists in Supabase storage"""
#     try:
#         folder = '/'.join(dest_path.split('/')[:-1])
#         file_name = dest_path.split('/')[-1]
#         files = supabase.storage.from_("images").list(folder if folder else "")
#         for file in files:
#             if file.get('name') == file_name:
#                 return True
#         return False
#     except Exception as e:
#         logging.debug(f"Error checking if image exists (assuming it doesn't): {e}")
#         return False


# def get_image_url(dest_path):
#     """Get public URL for an image in Supabase storage"""
#     try:
#         return supabase.storage.from_("images").get_public_url(dest_path)
#     except Exception as e:
#         logging.error(f"Error getting image URL: {e}")
#         return None


# def upload_image(local_file_path, dest_path):
#     """Upload image to Supabase storage"""
#     try:
#         with open(local_file_path, "rb") as f:
#             supabase.storage.from_("images").upload(dest_path, f, file_options={"upsert": "true"})
#         return supabase.storage.from_("images").get_public_url(dest_path)
#     except Exception as e:
#         logging.error(f"Error uploading image: {e}")
#         return None


# client = TelegramClient(TELEGRAM_SESSION, int(TELEGRAM_API_ID), TELEGRAM_API_HASH)

# patterns = {
#     "Ethereum": r"0x[a-fA-F0-9]{40}",
#     "Solana": r"[1-9A-HJ-NP-Za-km-z]{32,44}",
#     "pairAddress": r"0x[a-fA-F0-9]{64}",
#     "Polkadot": r"[1-9A-HJ-NP-Za-km-z]{47}",
#     "Tezos": r"(tz1|tz2|tz3|KT1)[1-9A-HJ-NP-Za-km-z]{33}",
# }
# compiled_patterns = {k: re.compile(v) for k, v in patterns.items()}

# # Global variables for health monitoring
# telegram_client_status = {"connected": False, "last_heartbeat": None}
# app_status = {"healthy": True, "startup_time": datetime.now(UTC)}


# # Health check web server for Cloud Run
# async def health_check(request):
#     """Health check endpoint for Cloud Run"""
#     status = {
#         "status": "healthy" if app_status["healthy"] else "unhealthy",
#         "telegram_connected": telegram_client_status["connected"],
#         "uptime_seconds": (datetime.now(UTC) - app_status["startup_time"]).total_seconds(),
#         "last_heartbeat": telegram_client_status["last_heartbeat"].isoformat() if telegram_client_status["last_heartbeat"] else None,
#         "timestamp": datetime.now(UTC).isoformat()
#     }
    
#     if app_status["healthy"] and telegram_client_status["connected"]:
#         return web.json_response(status, status=200)
#     else:
#         return web.json_response(status, status=503)


# async def root_handler(request):
#     """Root endpoint"""
#     return web.json_response({
#         "service": "telegram-listener",
#         "status": "running",
#         "version": "1.0.0",
#         "timestamp": datetime.now(UTC).isoformat()
#     })


# async def create_web_app():
#     """Create aiohttp web application for health checks"""
#     app = web.Application()
#     app.router.add_get('/', root_handler)
#     app.router.add_get('/health', health_check)
#     app.router.add_get('/ready', health_check)
#     return app


# async def start_health_server():
#     """Start the health check web server"""
#     try:
#         app = await create_web_app()
#         port = int(os.getenv('PORT', 8080))
        
#         runner = web.AppRunner(app)
#         await runner.setup()
        
#         site = web.TCPSite(runner, '0.0.0.0', port)
#         await site.start()
        
#         logging.info(f"🏥 Health check server started on port {port}")
#         return runner
#     except Exception as e:
#         logging.error(f"Failed to start health server: {e}")
#         await send_error_notification(
#             "Health Server Startup Error",
#             f"Failed to start health check server: {str(e)}"
#         )
#         raise


# async def heartbeat_monitor():
#     """Monitor Telegram client connection and update status"""
#     while True:
#         try:
#             if client.is_connected():
#                 telegram_client_status["connected"] = True
#                 telegram_client_status["last_heartbeat"] = datetime.now(UTC)
#             else:
#                 telegram_client_status["connected"] = False
#                 logging.warning("Telegram client disconnected")
            
#             await asyncio.sleep(30)  # Check every 30 seconds
#         except Exception as e:
#             logging.error(f"Heartbeat monitor error: {e}")
#             telegram_client_status["connected"] = False
#             await asyncio.sleep(30)


# async def send_error_notification(error_message: str, error_details: str=None):
#     """Send error notification to admin via Telegram bot"""
#     if not ERROR_NOTIFICATION_BOT_TOKEN or not ERROR_NOTIFICATION_CHAT_ID:
#         logging.warning("Error notification bot token or chat ID not configured")
#         return
    
#     try:
#         # Format error message
#         timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
#         notification_text = "🚨 **SERVER ERROR ALERT** 🚨\n\n"
#         notification_text += f"**Time:** {timestamp}\n"
#         notification_text += f"**Error:** {error_message}\n"
        
#         if error_details:
#             # Truncate error details if too long
#             if len(error_details) > 1000:
#                 error_details = error_details[:1000] + "... (truncated)"
#             notification_text += f"**Details:**\n```{error_details}```\n"
        
#         notification_text += "\n⚠️ Please check the server logs for more information."
        
#         # Send via Telegram Bot API
#         bot_url = f"https://api.telegram.org/bot{ERROR_NOTIFICATION_BOT_TOKEN}/sendMessage"
#         payload = {
#             "chat_id": ERROR_NOTIFICATION_CHAT_ID,
#             "text": notification_text,
#             "parse_mode": "Markdown"
#         }
        
#         async with httpx.AsyncClient(timeout=10.0) as client:
#             response = await client.post(bot_url, json=payload)
#             if response.status_code == 200:
#                 logging.info("Error notification sent successfully")
#             else:
#                 logging.error(f"Failed to send error notification: {response.status_code}")
    
#     except Exception as e:
#         logging.error(f"Failed to send error notification: {e}")


# @client.on(events.NewMessage)
# async def handler(event):
#     try:
#         message = event.message
#         if not message.message:
#             return

#         msg_text = message.message
#         all_addresses = []
#         for _, regex in compiled_patterns.items():
#             matches = regex.findall(msg_text)
#             for addr in matches:
#                 all_addresses.append(addr)

#         if not all_addresses:
#             return

#         group_entity = await event.get_chat()
#         group_name = getattr(group_entity, 'title', str(group_entity.id))
#         group_username = getattr(group_entity, 'username', None)

#         # Generate message link
#         message_link = (
#             f"https://t.me/{group_username}/{message.id}"
#             if group_username else
#             f"https://t.me/c/{str(group_entity.id)[4:]}/{message.id}"
#             if str(group_entity.id).startswith("-100") else None
#         )
        
#         user_count = None
#         try:
#             full_info = await client(GetFullChannelRequest(channel=group_entity))
#             logging.info(f"Full info: {full_info}")
#             user_count = getattr(full_info.full_chat, 'participants_count', None)
#         except Exception:
#             pass

#         influencer = (
#             message.sender.username if message.sender and hasattr(message.sender, 'username')
#             else str(message.sender_id) if message.sender_id
#             else "Unknown"
#         )

#         # Get user profile image - upload to Supabase storage
#         profile_image_url = None
#         # First, check if we already have a profile_image URL for this user from previous messages
#         try:
#             existing_user_docs = await test_collection.find({"Username": influencer}).to_list(length=1)
#             if existing_user_docs and len(existing_user_docs) > 0:
#                 existing_profile_image = existing_user_docs[0].get("profile_image")
#                 if existing_profile_image and existing_profile_image.strip() and not existing_profile_image.startswith("telegram_photo_id_"):
#                     profile_image_url = existing_profile_image
#                     logging.info(f"Reusing existing profile image URL for user {influencer} from previous message")
#         except Exception as check_error:
#             logging.debug(f"Could not check existing profile image: {str(check_error)}")

#         # If we don't have an existing URL, try to get/download the profile image
#         if not profile_image_url:
#             try:
#                 if message.sender:
#                     photos = await client.get_profile_photos(message.sender, limit=1)
#                     if photos and len(photos) > 0:
#                         latest_photo = photos[0]
#                         file_name = f"profile/{message.sender_id}_{latest_photo.id}.jpg"

#                         # Check if image already exists in Supabase storage
#                         if check_image_exists(file_name):
#                             profile_image_url = get_image_url(file_name)
#                             if profile_image_url:
#                                 logging.info(f"Profile image already exists in storage for user {influencer}, using existing URL")
#                             else:
#                                 logging.warning(f"Could not get URL for existing image, will re-upload")
#                                 profile_image_url = None

#                         # If image doesn't exist or URL retrieval failed, download and upload
#                         if not profile_image_url:
#                             max_retries = 2
#                             for attempt in range(max_retries):
#                                 try:
#                                     os.makedirs("tmp", exist_ok=True)
#                                     temp_photo_path = f"tmp/profile_{message.sender_id}_{latest_photo.id}.jpg"
#                                     photo_path = await client.download_profile_photo(
#                                         message.sender,
#                                         file=temp_photo_path
#                                     )
#                                     if photo_path and os.path.exists(photo_path):
#                                         profile_image_url = upload_image(photo_path, file_name)
#                                         if profile_image_url:
#                                             logging.info(f"Profile image uploaded to storage for user {influencer} (attempt {attempt + 1})")
#                                             try:
#                                                 os.remove(photo_path)
#                                             except Exception as cleanup_error:
#                                                 logging.warning(f"Could not clean up temporary file {photo_path}: {str(cleanup_error)}")
#                                             break
#                                         else:
#                                             logging.warning(f"Upload failed for user {influencer}, attempt {attempt + 1}/{max_retries}")
#                                             if attempt < max_retries - 1:
#                                                 await asyncio.sleep(1)
#                                     else:
#                                         logging.warning(f"Download failed for user {influencer}, attempt {attempt + 1}/{max_retries}")
#                                         if attempt < max_retries - 1:
#                                             await asyncio.sleep(1)
#                                 except Exception as download_error:
#                                     logging.warning(f"Error processing profile photo for user {influencer}, attempt {attempt + 1}/{max_retries}: {str(download_error)}")
#                                     if attempt < max_retries - 1:
#                                         await asyncio.sleep(1)

#                             # If all attempts failed, construct a Supabase URL anyway
#                             if not profile_image_url:
#                                 try:
#                                     profile_image_url = get_image_url(file_name)
#                                     if not profile_image_url and SUPABASE_URL:
#                                         base_url = SUPABASE_URL.rstrip('/').replace('/rest/v1', '')
#                                         profile_image_url = f"{base_url}/storage/v1/object/public/images/{file_name}"
#                                         logging.warning(f"Using constructed Supabase URL for user {influencer} (file may not exist yet)")
#                                 except Exception as url_error:
#                                     if SUPABASE_URL:
#                                         base_url = SUPABASE_URL.rstrip('/').replace('/rest/v1', '')
#                                         profile_image_url = f"{base_url}/storage/v1/object/public/images/{file_name}"
#                                     logging.error(f"Error constructing URL, using fallback: {str(url_error)}")
#                     else:
#                         logging.debug(f"No profile photo found for user {influencer}")
#             except Exception as photo_error:
#                 logging.warning(f"Could not get profile photo for user {influencer}: {str(photo_error)}")

#         msg_time_dt = message.date if message.date else datetime.now(UTC)

#         dex_data_for_webhook = []
#         contracts_for_payload = []

#         for addr in all_addresses:
#             try:
#                 # Find existing docs for this contract address and user
#                 existing_docs = await test_collection.find({"Contract Address": addr, "Username": influencer}).to_list(length=10)

#                 found_match = False

#                 for doc in existing_docs:
#                     dex_data = doc.get("Dexscreener Data", {})
#                     pairs = dex_data if isinstance(dex_data, list) else []

#                     for pair in pairs:
#                         chain_id = pair.get("chainId") or pair.get("chain")
#                         base_token_address = pair.get("baseToken", {}).get("address")
#                         if chain_id and base_token_address:
#                             # If match found, increment Call Count and update profile_image
#                             update_data = {"$inc": {"Call Count": 1}}
#                             if profile_image_url:
#                                 update_data["$set"] = {"profile_image": profile_image_url}
#                             await test_collection.update_one(
#                                 {"_id": doc["_id"]},
#                                 update_data
#                             )
#                             found_match = True
#                             logging.info(f"Incremented Call Count for {addr} for user {influencer}")
#                             if profile_image_url:
#                                 logging.info(f"Updated profile_image for user {influencer}")
#                             break
#                     if found_match:
#                         break

#                 if not found_match:
#                     # Fetch new Dexscreener data
#                     dexscreener_data = fetch_dexscreener_data(addr)

#                     logging.info(f"Dexscreener data: {dexscreener_data}")
#                     # Extract only the specified fields: chainId, dexId, url, pairAddress, 
#                     # baseToken, priceNative, priceUsd, volume, liquidity, fdv, marketCap, info
#                     extracted_dex_data = extract_dexscreener_fields(dexscreener_data)
#                     logging.info(f"Fetched and extracted Dexscreener data for {addr}: {len(extracted_dex_data)} pairs")

#                     first_pair = extracted_dex_data[0] if isinstance(extracted_dex_data, list) and len(extracted_dex_data) > 0 else {}

#                     chain_id = first_pair.get("chainId") or first_pair.get("chain")
#                     base_token_address = first_pair.get("baseToken", {}).get("address") if first_pair.get("baseToken") else None

#                     doc = {
#                         "Group Name": group_name,
#                         "Chain": chain_id,
#                         "Contract Address": base_token_address,
#                         "Group User Count": user_count,
#                         "Username": influencer,
#                         "Profile Image URL": profile_image_url,
#                         "Message DateTime": msg_time_dt,
#                         "Full Message": msg_text,
#                         "Dexscreener Data": extracted_dex_data,
#                         "Call Count": 1,
#                         "Message Link": message_link,
#                     }
#                     await test_collection.insert_one(doc)
#                     logging.info(f"Inserted new document for {addr} user {influencer}")

#                     dex_data_for_webhook.append({
#                         "contract_address": addr,
#                         "dexscreener": extracted_dex_data
#                     })

#                 contracts_for_payload.append({"address": addr})
            
#             except Exception as addr_error:
#                 error_msg = f"Error processing address {addr}: {str(addr_error)}"
#                 logging.error(error_msg)
#                 await send_error_notification(
#                     "Address Processing Error",
#                     f"Error processing address {addr} from user {influencer} in group {group_name}: {str(addr_error)}"
#                 )
#                 continue

#         # Build webhook payload
#         payload = {
#             "channel": group_name,
#             "message": msg_text,
#             "contracts": contracts_for_payload,
#             "username": influencer,
#             "timestamp": str(msg_time_dt),
#             "message_link": message_link,
#             "dexscreener_data": dex_data_for_webhook,
#         }

#         # Async POST to webhook
#         try:
#             async with httpx.AsyncClient(timeout=30.0) as async_client:
#                 response = await async_client.post(WEBHOOK_URL, json=payload)
#             logging.info(f"📬 Payload sent, webhook responded with status {response.status_code}")
#         except Exception as webhook_error:
#             error_msg = f"Webhook error: {str(webhook_error)}"
#             logging.error(f"❌ {error_msg}")
#             await send_error_notification(
#                 "Webhook Communication Error",
#                 f"Failed to send data to webhook {WEBHOOK_URL}: {str(webhook_error)}"
#             )

#     except Exception as e:
#         error_msg = f"Critical error in message handler: {str(e)}"
#         error_details = traceback.format_exc()
#         logging.error(f"❌ {error_msg}")
#         logging.error(f"Error details: {error_details}")
        
#         # Send error notification
#         await send_error_notification(
#             "Critical Message Handler Error",
#             f"Telegram Listener encountered a critical error: {str(e)}\n\nFull traceback:\n{error_details}"
#         )


# async def main():
#     global app_status
    
#     try:
#         # Start health check server first
#         logging.info("🚀 Starting Telegram Listener service...")
#         health_runner = await start_health_server()
        
#         # Start Telegram client
#         await client.start()
#         telegram_client_status["connected"] = True
#         telegram_client_status["last_heartbeat"] = datetime.now(UTC)
#         logging.info("🚀 Telegram client connected successfully")
        
#         # Start heartbeat monitor
#         heartbeat_task = asyncio.create_task(heartbeat_monitor())
        
#         # Mark app as healthy
#         app_status["healthy"] = True
#         logging.info("🚀 Telegram live listener started and healthy...")
        
#         # Run until disconnected
#         try:
#             await client.run_until_disconnected()
#         finally:
#             # Cleanup
#             heartbeat_task.cancel()
#             if health_runner:
#                 await health_runner.cleanup()
                
#     except Exception as e:
#         error_msg = f"Critical error in main function: {str(e)}"
#         error_details = traceback.format_exc()
#         logging.error(f"❌ {error_msg}")
#         logging.error(f"Error details: {error_details}")
        
#         # Mark app as unhealthy
#         app_status["healthy"] = False
#         telegram_client_status["connected"] = False
        
#         # Send error notification
#         await send_error_notification(
#             "Critical Application Error",
#             f"Telegram Listener application crashed: {str(e)}\n\nFull traceback:\n{error_details}"
#         )
        
#         # Re-raise the exception to ensure proper exit codes
#         raise


# if __name__ == "__main__":
#     try:
#         asyncio.run(main())
#     except KeyboardInterrupt:
#         logging.info("🛑 Application stopped by user")
#         app_status["healthy"] = False
#         telegram_client_status["connected"] = False
#     except Exception as e:
#         logging.error(f"❌ Fatal error: {str(e)}")
#         app_status["healthy"] = False
#         telegram_client_status["connected"] = False
#         # For synchronous errors before asyncio.run, we can't use async error notification
#         # So just log and exit with error code
#         exit(1)


import re
import os
import asyncio
import logging
import traceback
from datetime import datetime, UTC
from aiohttp import web

import httpx
from telethon import TelegramClient, events
from telethon.tl.functions.channels import GetFullChannelRequest
from motor.motor_asyncio import AsyncIOMotorClient
from supabase import create_client

from utils import fetch_dexscreener_data, extract_dexscreener_fields


# ================= ENV =================
API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
SESSION = os.getenv("TELEGRAM_SESSION")

MONGO_URI = os.getenv("MONGODB_URI")
PORT = int(os.getenv("PORT", 8080))

ERROR_CHAT = os.getenv("ERROR_NOTIFICATION_CHAT_ID")
ERROR_BOT = os.getenv("ERROR_NOTIFICATION_BOT_TOKEN")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

logging.basicConfig(level=logging.INFO)


# ================= CLIENTS =================
tg = TelegramClient(SESSION, API_ID, API_HASH)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

mongo = AsyncIOMotorClient(MONGO_URI)
db = mongo["telegram_alpha"]

groups = db["groups"]
tokens = db["tokens"]
calls = db["calls"]


# ================= INDEXES =================
async def ensure_indexes():
    """
    Safe index creation.
    WILL NOT crash Cloud Run.
    """
    try:
        await groups.create_index("telegram_id", unique=True, sparse=True)
        await groups.create_index("total_calls")

        await tokens.create_index(
            [("chain", 1), ("contract_address", 1)],
            unique=True,
        )
        await tokens.create_index("total_calls")

        # 🔥 CRITICAL FIX → partial index ignores null message_link
        await calls.create_index(
            [("group_id", 1), ("token_id", 1), ("message_link", 1)],
            unique=True,
            partialFilterExpression={"message_link": {"$type": "string"}},
        )

        await calls.create_index("created_at")

        logging.info("✅ MongoDB indexes ensured")

    except Exception as e:
        logging.error(f"❌ Index creation failed (ignored): {e}")


# ================= ERROR NOTIFY =================
async def notify_error(title, details=""):
    if not ERROR_CHAT or not ERROR_BOT:
        return

    try:
        url = f"https://api.telegram.org/bot{ERROR_BOT}/sendMessage"

        async with httpx.AsyncClient(timeout=10) as c:
            await c.post(
                url,
                json={
                    "chat_id": ERROR_CHAT,
                    "text": f"🚨 {title}\n\n{details[:1000]}",
                },
            )
    except Exception:
        pass


# ================= HEALTH =================
async def health(_):
    return web.json_response({"status": "ok"})


async def start_health():
    app = web.Application()
    app.router.add_get("/", health)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()


# ================= HELPERS =================
def safe_username(username, chat_id):
    return username if username else f"tg_{chat_id}"


def now():
    return datetime.now(UTC)


# ================= SUPABASE IMAGE OPS =================
def check_image_exists(dest_path):
    """Check if image already exists in Supabase storage"""
    if not supabase:
        return False
    try:
        folder = '/'.join(dest_path.split('/')[:-1])
        file_name = dest_path.split('/')[-1]
        files = supabase.storage.from_("images").list(folder if folder else "")
        return any(f.get('name') == file_name for f in files)
    except Exception:
        return False


def get_image_url(dest_path):
    """Get public URL for an image in Supabase storage"""
    if not supabase:
        return None
    try:
        return supabase.storage.from_("images").get_public_url(dest_path)
    except Exception:
        return None


def upload_image(local_file_path, dest_path):
    """Upload image to Supabase storage and return public URL"""
    if not supabase:
        return None
    try:
        with open(local_file_path, "rb") as f:
            supabase.storage.from_("images").upload(dest_path, f, file_options={"upsert": "true"})
        return supabase.storage.from_("images").get_public_url(dest_path)
    except Exception as e:
        logging.error(f"Error uploading image: {e}")
        return None


async def get_profile_image_url(sender, sender_id, username):
    """Download sender's profile photo, upload to Supabase, return URL."""
    if not supabase or not sender:
        return None

    try:
        photos = await tg.get_profile_photos(sender, limit=1)
        if not photos:
            return None

        latest = photos[0]
        dest = f"profile/{sender_id}_{latest.id}.jpg"

        if check_image_exists(dest):
            url = get_image_url(dest)
            if url:
                return url

        os.makedirs("tmp", exist_ok=True)
        tmp_path = f"tmp/profile_{sender_id}_{latest.id}.jpg"

        for attempt in range(2):
            try:
                path = await tg.download_profile_photo(sender, file=tmp_path)
                if path and os.path.exists(path):
                    url = upload_image(path, dest)
                    try:
                        os.remove(path)
                    except OSError:
                        pass
                    if url:
                        return url
            except Exception:
                if attempt == 0:
                    await asyncio.sleep(1)

        return get_image_url(dest)
    except Exception as e:
        logging.warning(f"Could not get profile photo for {username}: {e}")
        return None


# ================= DB OPS =================
async def upsert_group(chat, member_count):
    username = safe_username(getattr(chat, "username", None), chat.id)
    name = getattr(chat, "title", username)

    return await groups.find_one_and_update(
        {"telegram_id": chat.id},
        {
            "$set": {
                "name": name,
                "username": username,
                "current_member_count": member_count,
                "updated_at": now(),
            },
            "$max": {"max_member_count_seen": member_count or 0},
            "$setOnInsert": {
                "total_calls": 0,
                "unique_tokens": [],
                "created_at": now(),
            },
        },
        upsert=True,
        return_document=True,
    )


async def upsert_token(chain, contract, pair):
    price = pair.get("priceUsd")
    mc = pair.get("marketCap")
    liquidity = (pair.get("liquidity") or {}).get("usd")
    volume24h = (pair.get("volume") or {}).get("h24")

    return await tokens.find_one_and_update(
        {"chain": chain, "contract_address": contract},
        {
            "$set": {
                "symbol": pair.get("baseToken", {}).get("symbol"),
                "name": pair.get("baseToken", {}).get("name"),
                "last_called_at": now(),
                "dex": {
                    "priceUsd": price,
                    "pairAddress": pair.get("pairAddress"),
                    "liquidity": liquidity,
                    "marketCap": mc,
                    "fdv": pair.get("fdv"),
                    "volume24h": volume24h,
                    "volume6h": (pair.get("volume") or {}).get("h6"),
                    "volume1h": (pair.get("volume") or {}).get("h1"),
                    "volume5m": (pair.get("volume") or {}).get("m5"),
                    "image": (pair.get("info") or {}).get("imageUrl"),
                    "background_image": (pair.get("info") or {}).get("header"),
                    "socials": (pair.get("info") or {}).get("socials"),
                    "websites": (pair.get("info") or {}).get("websites"),
                    "url": pair.get("url"),
                },
            },
            "$setOnInsert": {
                "first_seen_at": now(),
                "first_seen_price": price,
                "first_seen_market_cap": mc,
                "first_seen_liquidity": liquidity,
                "first_seen_volume24h": volume24h,
                "total_calls": 0,
                "groups_called": [],
            },
        },
        upsert=True,
        return_document=True,
    )


async def insert_call(group_doc, token_doc, msg, link, caller_username=None, profile_image_url=None):
    try:
        call_doc = {
            "group_id": group_doc["_id"],
            "token_id": token_doc["_id"],
            "message_text": msg,
            "message_link": link,
            "created_at": now(),
        }
        if caller_username:
            call_doc["caller_username"] = caller_username
        if profile_image_url:
            call_doc["profile_image"] = profile_image_url

        await calls.insert_one(call_doc)
    except Exception:
        return  # duplicate safely ignored

    group_update = {"$inc": {"total_calls": 1}, "$addToSet": {"unique_tokens": token_doc["_id"]}}
    await groups.update_one({"_id": group_doc["_id"]}, group_update)

    await tokens.update_one(
        {"_id": token_doc["_id"]},
        {"$inc": {"total_calls": 1}, "$addToSet": {"groups_called": group_doc["_id"]}},
    )


# ================= REGEX =================
ADDRESS_REGEX = {
   "Ethereum": r"0x[a-fA-F0-9]{40}",
    "Solana": r"[1-9A-HJ-NP-Za-km-z]{32,44}",
    "pairAddress": r"0x[a-fA-F0-9]{64}",
    "Polkadot": r"[1-9A-HJ-NP-Za-km-z]{47}",
    "Tezos": r"(tz1|tz2|tz3|KT1)[1-9A-HJ-NP-Za-km-z]{33}",
}

compiled_patterns = {k: re.compile(v) for k, v in ADDRESS_REGEX.items()}


# ================= TELEGRAM HANDLER =================
@tg.on(events.NewMessage)
async def handler(event):
    try:
        text = event.message.message
        if not text:
            return

        addresses = {
            addr
            for regex in compiled_patterns.values()
            for addr in regex.findall(text)
        }

        if not addresses:
            return

        chat = await event.get_chat()

        member_count = None
        try:
            full = await tg(GetFullChannelRequest(channel=chat))
            member_count = getattr(full.full_chat, "participants_count", None)
        except Exception:
            pass

        group_doc = await upsert_group(chat, member_count)

        link = (
            f"https://t.me/{group_doc['username']}/{event.message.id}"
            if not group_doc["username"].startswith("tg_")
            else None
        )

        # Get caller info and profile image
        sender = event.message.sender
        sender_id = event.message.sender_id
        caller_username = (
            sender.username if sender and hasattr(sender, 'username') and sender.username
            else str(sender_id) if sender_id
            else "Unknown"
        )

        profile_image_url = await get_profile_image_url(sender, sender_id, caller_username)

        for addr in addresses:
            dex_raw = fetch_dexscreener_data(addr)
            pairs = extract_dexscreener_fields(dex_raw)

            if not pairs:
                continue

            pair = pairs[0]
            chain = pair.get("chainId")
            contract = pair.get("baseToken", {}).get("address")

            if not chain or not contract:
                continue

            token_doc = await upsert_token(chain, contract, pair)
            await insert_call(group_doc, token_doc, text, link, caller_username, profile_image_url)

            logging.info(f"Stored call {contract} from {group_doc['name']} by {caller_username}")

    except Exception:
        await notify_error("Handler Crash", traceback.format_exc())


# ================= MAIN =================
async def main():
    # 1️⃣ Start health server FIRST (Cloud Run stability)
    await start_health()
    logging.info("Health server started on port %s", PORT)

    # 2️⃣ Ensure indexes WITHOUT crashing startup
    asyncio.create_task(ensure_indexes())

    # 3️⃣ Start Telegram
    await tg.start()
    logging.info("Telegram connected")

    await tg.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
