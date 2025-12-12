import re
import logging
import os
import traceback
import datetime
import asyncio
import httpx
import asyncpg
import uuid
from datetime import datetime as dt, timezone
from aiohttp import web
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

# Debug print environment variables (same as telegram_listener.py)
print("DEBUG ENV VARIABLES:")
print("TELEGRAM_API_ID:", os.getenv("TELEGRAM_API_ID"))
print("TELEGRAM_API_HASH:", os.getenv("TELEGRAM_API_HASH"))
print("TELEGRAM_SESSION:", os.getenv("TELEGRAM_SESSION"))

logging.basicConfig(level=logging.INFO)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def check_image_exists(dest_path):
    """Check if image already exists in Supabase storage"""
    try:
        # Try to get the file - if it exists, this won't raise an error
        folder = '/'.join(dest_path.split('/')[:-1])  # Get folder path
        file_name = dest_path.split('/')[-1]  # Get file name
        
        # List files in the folder
        files = supabase.storage.from_("images").list(folder if folder else "")
        
        # Check if our file exists
        for file in files:
            if file.get('name') == file_name:
                return True
        return False
    except Exception as e:
        # If there's an error (folder doesn't exist, etc.), assume file doesn't exist
        logging.debug(f"Error checking if image exists (assuming it doesn't): {e}")
        return False


def get_image_url(dest_path):
    """Get public URL for an image in Supabase storage"""
    try:
        return supabase.storage.from_("images").get_public_url(dest_path)
    except Exception as e:
        logging.error(f"Error getting image URL: {e}")
        return None


def upload_image(local_file_path, dest_path):
    """Upload image to Supabase storage"""
    try:
        with open(local_file_path, "rb") as f:
            supabase.storage.from_("images").upload(dest_path, f, file_options={"upsert": "true"})
        return supabase.storage.from_("images").get_public_url(dest_path)
    except Exception as e:
        logging.error(f"Error uploading image: {e}")
        return None

# Use same client initialization as telegram_listener.py
client = TelegramClient(TELEGRAM_SESSION, int(TELEGRAM_API_ID), TELEGRAM_API_HASH)

# Address extraction patterns
patterns = {
    "Ethereum": r"0x[a-fA-F0-9]{40}",
    "Solana": r"[1-9A-HJ-NP-Za-km-z]{32,44}",
    "pairAddress": r"0x[a-fA-F0-9]{64}",
    "Polkadot": r"[1-9A-HJ-NP-Za-km-z]{47}",
    "Tezos": r"(tz1|tz2|tz3|KT1)[1-9A-HJ-NP-Za-km-z]{33}",
}
compiled_patterns = {k: re.compile(v) for k, v in patterns.items()}

# Global variables for health monitoring (same as telegram_listener.py)
telegram_client_status = {"connected": False, "last_heartbeat": None}
app_status = {"healthy": True, "startup_time": dt.now(timezone.utc)}




# Health check web server for Cloud Run
async def health_check(request):
    """Health check endpoint for Cloud Run"""
    status = {
        "status": "healthy" if app_status["healthy"] else "unhealthy",
        "telegram_connected": telegram_client_status["connected"],
        "uptime_seconds": (dt.now(timezone.utc) - app_status["startup_time"]).total_seconds(),
        "last_heartbeat": telegram_client_status["last_heartbeat"].isoformat() if telegram_client_status["last_heartbeat"] else None,
        "timestamp": dt.now(timezone.utc).isoformat()
    }
    
    if app_status["healthy"] and telegram_client_status["connected"]:
        return web.json_response(status, status=200)
    else:
        return web.json_response(status, status=503)


async def root_handler(request):
    """Root endpoint"""
    return web.json_response({
        "service": "telegram-userbot",
        "status": "running",
        "version": "1.0.0",
        "timestamp": dt.now(timezone.utc).isoformat()
    })


async def create_web_app():
    """Create aiohttp web application for health checks"""
    app = web.Application()
    app.router.add_get('/', root_handler)
    app.router.add_get('/health', health_check)
    app.router.add_get('/ready', health_check)
    return app


async def start_health_server():
    """Start the health check web server"""
    try:
        app = await create_web_app()
        port = int(os.getenv('PORT', 8080))
        
        runner = web.AppRunner(app)
        await runner.setup()
        
        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        
        logging.info(f"🏥 Health check server started on port {port}")
        return runner
    except Exception as e:
        logging.error(f"Failed to start health server: {e}")
        await send_error_notification(
            "Health Server Startup Error",
            f"Failed to start health check server: {str(e)}"
        )
        raise


async def heartbeat_monitor():
    """Monitor Telegram client connection and update status"""
    while True:
        try:
            if client.is_connected():
                telegram_client_status["connected"] = True
                telegram_client_status["last_heartbeat"] = dt.now(timezone.utc)
            else:
                telegram_client_status["connected"] = False
                logging.warning("Telegram client disconnected")
            
            await asyncio.sleep(30)  # Check every 30 seconds
        except Exception as e:
            logging.error(f"Heartbeat monitor error: {e}")
            telegram_client_status["connected"] = False
            await asyncio.sleep(30)


async def send_error_notification(error_message: str, error_details: str = None):
    """Send error notification to admin via Telegram bot"""
    if not ERROR_NOTIFICATION_BOT_TOKEN or not ERROR_NOTIFICATION_CHAT_ID:
        logging.warning("Error notification bot token or chat ID not configured")
        return
    
    try:
        timestamp = dt.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        notification_text = "🚨 **USERBOT ERROR ALERT** 🚨\n\n"
        notification_text += f"**Time:** {timestamp}\n"
        notification_text += f"**Error:** {error_message}\n"
        
        if error_details:
            if len(error_details) > 1000:
                error_details = error_details[:1000] + "... (truncated)"
            notification_text += f"**Details:**\n```{error_details}```\n"
        
        notification_text += "\n⚠️ Please check the server logs for more information."
        
        # Clean URL to remove any line endings or whitespace
        bot_token = ERROR_NOTIFICATION_BOT_TOKEN.strip() if ERROR_NOTIFICATION_BOT_TOKEN else None
        chat_id = ERROR_NOTIFICATION_CHAT_ID.strip() if ERROR_NOTIFICATION_CHAT_ID else None
        
        if not bot_token or not chat_id:
            return
            
        bot_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
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

        # Group full info (same as telegram_listener.py)
        user_count = None
        full_info = None
        try:
            # Try to get full channel info - this may fail for private groups or if bot lacks permissions
            full_info = await client(GetFullChannelRequest(channel=chat))
            logging.info(f"Full info: {full_info}")
            user_count = getattr(full_info.full_chat, 'participants_count', None)
        except (ValueError, TypeError) as ve:
            # This usually means the entity couldn't be resolved (private group, no access, etc.)
            # This is normal and expected for many groups, so we don't log it as an error
            pass
        except Exception as full_info_error:
            # Log other errors but don't fail the entire message processing
            error_str = str(full_info_error)
            error_type = type(full_info_error).__name__
            # Suppress common resolution errors that are expected
            if "get_input_entity" in error_str or "resolve" in error_str or "get_peer" in error_str:
                # These are common and expected for private groups
                pass
            else:
                # Log unexpected errors
                logging.warning(f"Could not get full channel info ({error_type}): {error_str[:200]}")
            pass

        # Print group details (existing functionality)
        print("\n--- Group Details ---")
        print("Message: ", message)
        print("Name:", chat.title)
        print("Username:", chat.username)
        print("Members:", user_count)
        if full_info:
            print("About:", getattr(full_info.full_chat, 'about', 'N/A'))
        else:
            print("About: N/A")
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

        # Get user profile image - always store URL
        # First, check if we already have a profile_image URL for this user from previous messages
        profile_image_url = None
        try:
            # Check existing documents for this user to find existing profile_image URL
            existing_user_docs = await test_collection.find({"Username": influencer}).to_list(length=1)
            if existing_user_docs and len(existing_user_docs) > 0:
                existing_profile_image = existing_user_docs[0].get("profile_image")
                # Check if it's a valid URL (not None, not empty, and not just a photo ID)
                if existing_profile_image and existing_profile_image.strip() and not existing_profile_image.startswith("telegram_photo_id_"):
                    profile_image_url = existing_profile_image
                    logging.info(f"Reusing existing profile image URL for user {influencer} from previous message")
        except Exception as check_error:
            logging.debug(f"Could not check existing profile image: {str(check_error)}")
        
        # If we don't have an existing URL, try to get/download the profile image
        if not profile_image_url:
            try:
                if message_obj.sender:
                    photos = await client.get_profile_photos(message_obj.sender, limit=1)
                    if photos and len(photos) > 0:
                        latest_photo = photos[0]
                        file_name = f"profile/{message_obj.sender_id}_{latest_photo.id}.jpg"
                        
                        # Check if image already exists in storage
                        if check_image_exists(file_name):
                            # Image exists, get the URL
                            profile_image_url = get_image_url(file_name)
                            if profile_image_url:
                                logging.info(f"Profile image already exists in storage for user {influencer}, using existing URL")
                            else:
                                # If we can't get URL, try to re-upload
                                logging.warning(f"Could not get URL for existing image, will re-upload")
                                profile_image_url = None  # Will trigger re-upload below
                    
                    # If image doesn't exist or URL retrieval failed, download and upload
                    if not profile_image_url:
                        max_retries = 2
                        for attempt in range(max_retries):
                            try:
                                # Download photo to temporary location
                                os.makedirs("tmp", exist_ok=True)
                                temp_photo_path = f"tmp/profile_{message_obj.sender_id}_{latest_photo.id}.jpg"
                                photo_path = await client.download_profile_photo(
                                    message_obj.sender,
                                    file=temp_photo_path
                                )
                                
                                if photo_path and os.path.exists(photo_path):
                                    # Upload to storage with retry
                                    profile_image_url = upload_image(photo_path, file_name)
                                    if profile_image_url:
                                        logging.info(f"Profile image uploaded to storage for user {influencer} (attempt {attempt + 1})")
                                        # Clean up temporary file
                                        try:
                                            os.remove(photo_path)
                                        except Exception as cleanup_error:
                                            logging.warning(f"Could not clean up temporary file {photo_path}: {str(cleanup_error)}")
                                        break  # Success, exit retry loop
                                    else:
                                        logging.warning(f"Upload failed for user {influencer}, attempt {attempt + 1}/{max_retries}")
                                        if attempt < max_retries - 1:
                                            await asyncio.sleep(1)  # Wait before retry
                                else:
                                    logging.warning(f"Download failed for user {influencer}, attempt {attempt + 1}/{max_retries}")
                                    if attempt < max_retries - 1:
                                        await asyncio.sleep(1)  # Wait before retry
                            except Exception as download_error:
                                logging.warning(f"Error processing profile photo for user {influencer}, attempt {attempt + 1}/{max_retries}: {str(download_error)}")
                                if attempt < max_retries - 1:
                                    await asyncio.sleep(1)  # Wait before retry
                        
                        # If all attempts failed, construct a Supabase URL anyway (even if file doesn't exist)
                        # This ensures we always have a URL format, not just a photo ID
                        if not profile_image_url:
                            try:
                                # Try to get URL using Supabase client (even if file doesn't exist, it returns the URL structure)
                                profile_image_url = get_image_url(file_name)
                                if not profile_image_url:
                                    # Construct the expected Supabase public URL
                                    # Format: https://{project_ref}.supabase.co/storage/v1/object/public/{bucket}/{path}
                                    if SUPABASE_URL:
                                        # Extract project ref from SUPABASE_URL
                                        # SUPABASE_URL format: https://{project_ref}.supabase.co
                                        base_url = SUPABASE_URL.rstrip('/')
                                        # Remove /rest/v1 if present
                                        base_url = base_url.replace('/rest/v1', '')
                                        profile_image_url = f"{base_url}/storage/v1/object/public/images/{file_name}"
                                        logging.warning(f"Using constructed Supabase URL for user {influencer} (file may not exist yet): {profile_image_url}")
                                    else:
                                        # Last resort: use a placeholder URL structure
                                        profile_image_url = f"https://storage.supabase.co/images/{file_name}"
                                        logging.warning(f"Using placeholder URL for user {influencer}: {profile_image_url}")
                            except Exception as url_error:
                                # If URL construction fails, still create a proper URL format
                                if SUPABASE_URL:
                                    base_url = SUPABASE_URL.rstrip('/').replace('/rest/v1', '')
                                    profile_image_url = f"{base_url}/storage/v1/object/public/images/{file_name}"
                                else:
                                    profile_image_url = f"https://storage.supabase.co/images/{file_name}"
                                logging.error(f"Error constructing URL, using fallback: {str(url_error)}")
                    else:
                        # No profile photo found
                        logging.debug(f"No profile photo found for user {influencer}")
            except Exception as photo_error:
                logging.warning(f"Could not get profile photo for user {influencer}: {str(photo_error)}")
        
        # Always store profile_image_url (even if None) - this ensures we always have the field

        msg_time_dt = message_obj.date if message_obj.date else dt.now(timezone.utc)

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
                            # If match found, increment Call Count and update profile_image if needed
                            update_data = {"$inc": {"Call Count": 1}}
                            
                            # Always update profile_image if we have one (even if it's the same)
                            # This ensures profile_image is always stored/updated
                            if profile_image_url:
                                update_data["$set"] = {"profile_image": profile_image_url}
                            
                            await test_collection.update_one(
                                {"_id": doc["_id"]},
                                update_data
                            )
                            found_match = True
                            logging.info(f"Incremented Call Count for {addr} for user {influencer}")
                            if profile_image_url:
                                logging.info(f"Updated profile_image for user {influencer}")
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


async def main():
    global app_status
    
    try:
        # Start health check server first
        logging.info("🚀 Starting Telegram Userbot service...")
        health_runner = await start_health_server()
        
        # Start Telegram client
        # Don't pass phone parameter - let Telethon use the session file
        # If session file exists and is valid, it will connect automatically
        try:
            # Check if session file exists
            session_file = f"{TELEGRAM_SESSION}.session"
            if os.path.exists(session_file):
                logging.info(f"📁 Found session file: {session_file}")
                file_size = os.path.getsize(session_file)
                logging.info(f"📁 Session file size: {file_size} bytes")
            else:
                logging.error(f"❌ Session file not found: {session_file}")
                logging.error("💡 Solution: Create a session file using create_production_session.py")
                raise FileNotFoundError(f"Session file not found: {session_file}")
            
            # Start client - don't pass phone=None, let it use session file
            # This will work if session file is valid
            await client.start()
            
            if client.is_connected():
                telegram_client_status["connected"] = True
                telegram_client_status["last_heartbeat"] = dt.now(timezone.utc)
                logging.info("🚀 Telegram client connected successfully")
            else:
                raise Exception("Client started but not connected")
                
        except Exception as client_error:
            error_msg = f"Failed to start Telegram client: {str(client_error)}"
            logging.error(f"❌ {error_msg}")
            logging.error(f"Error type: {type(client_error).__name__}")
            
            # Check if it's an authentication error
            if "EOF" in str(client_error) or "reading a line" in str(client_error):
                logging.error("❌ Authentication error: Session file may be invalid or expired")
                logging.error("💡 Solution: Create a new session file using create_production_session.py")
            elif "No phone number" in str(client_error):
                logging.error("❌ Session file is invalid or expired")
                logging.error("💡 Solution: Create a new session file using create_production_session.py")
            
            raise
        
        # Start heartbeat monitor
        heartbeat_task = asyncio.create_task(heartbeat_monitor())
        
        # Mark app as healthy
        app_status["healthy"] = True
        logging.info("🚀 Telegram userbot started and healthy...")
        
        # Run until disconnected
        try:
            await client.run_until_disconnected()
        finally:
            # Cleanup
            heartbeat_task.cancel()
            if health_runner:
                await health_runner.cleanup()
                
    except Exception as e:
        error_msg = f"Critical error in main function: {str(e)}"
        error_details = traceback.format_exc()
        logging.error(f"❌ {error_msg}")
        logging.error(f"Error details: {error_details}")
        
        # Mark app as unhealthy
        app_status["healthy"] = False
        telegram_client_status["connected"] = False
        
        # Send error notification
        await send_error_notification(
            "Critical Application Error",
            f"Telegram Userbot application crashed: {str(e)}\n\nFull traceback:\n{error_details}"
        )
        
        # Re-raise the exception to ensure proper exit codes
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("🛑 Application stopped by user")
        app_status["healthy"] = False
        telegram_client_status["connected"] = False
    except Exception as e:
        logging.error(f"❌ Fatal error: {str(e)}")
        app_status["healthy"] = False
        telegram_client_status["connected"] = False
        exit(1)
