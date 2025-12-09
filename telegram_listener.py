import re
import logging
import asyncio
import traceback
from datetime import datetime
from aiohttp import web
import os

import httpx
from telethon import TelegramClient, events
from telethon.tl.functions.channels import GetFullChannelRequest

from app_config import (
    WEBHOOK_URL, TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_SESSION,
    ERROR_NOTIFICATION_CHAT_ID, ERROR_NOTIFICATION_BOT_TOKEN
)
from app_config import test_collection
from utils import fetch_dexscreener_data
print("DEBUG ENV VARIABLES:")
print("TELEGRAM_API_ID:", os.getenv("TELEGRAM_API_ID"))
print("TELEGRAM_API_HASH:", os.getenv("TELEGRAM_API_HASH"))
print("TELEGRAM_SESSION:", os.getenv("TELEGRAM_SESSION"))

logging.basicConfig(level=logging.INFO)

client = TelegramClient(TELEGRAM_SESSION, int(TELEGRAM_API_ID), TELEGRAM_API_HASH)

patterns = {
    "Ethereum": r"0x[a-fA-F0-9]{40}",
    "Solana": r"[1-9A-HJ-NP-Za-km-z]{32,44}",
    "pairAddress": r"0x[a-fA-F0-9]{64}",
    "Polkadot": r"[1-9A-HJ-NP-Za-km-z]{47}",
    "Tezos": r"(tz1|tz2|tz3|KT1)[1-9A-HJ-NP-Za-km-z]{33}",
}
compiled_patterns = {k: re.compile(v) for k, v in patterns.items()}

# Global variables for health monitoring
telegram_client_status = {"connected": False, "last_heartbeat": None}
app_status = {"healthy": True, "startup_time": datetime.utcnow()}


def extract_dexscreener_fields(dexscreener_data):
    """
    Extract only specific fields from dexscreener data:
    chainId, dexId, url, pairAddress, baseToken, priceNative, priceUsd, 
    volume, liquidity, fdv, marketCap, info
    """
    if not isinstance(dexscreener_data, list):
        return []
    
    extracted_pairs = []
    for pair in dexscreener_data:
        extracted_pair = {
            "chainId": pair.get("chainId"),
            "dexId": pair.get("dexId"),
            "url": pair.get("url"),
            "pairAddress": pair.get("pairAddress"),
            "baseToken": pair.get("baseToken"),
            "priceNative": pair.get("priceNative"),
            "priceUsd": pair.get("priceUsd"),
            "volume": pair.get("volume"),
            "liquidity": pair.get("liquidity"),
            "fdv": pair.get("fdv"),
            "marketCap": pair.get("marketCap"),
            "info": pair.get("info")
        }
        extracted_pairs.append(extracted_pair)
    
    return extracted_pairs


# Health check web server for Cloud Run
async def health_check(request):
    """Health check endpoint for Cloud Run"""
    status = {
        "status": "healthy" if app_status["healthy"] else "unhealthy",
        "telegram_connected": telegram_client_status["connected"],
        "uptime_seconds": (datetime.utcnow() - app_status["startup_time"]).total_seconds(),
        "last_heartbeat": telegram_client_status["last_heartbeat"].isoformat() if telegram_client_status["last_heartbeat"] else None,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if app_status["healthy"] and telegram_client_status["connected"]:
        return web.json_response(status, status=200)
    else:
        return web.json_response(status, status=503)


async def root_handler(request):
    """Root endpoint"""
    return web.json_response({
        "service": "telegram-listener",
        "status": "running",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
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
                telegram_client_status["last_heartbeat"] = datetime.utcnow()
            else:
                telegram_client_status["connected"] = False
                logging.warning("Telegram client disconnected")
            
            await asyncio.sleep(30)  # Check every 30 seconds
        except Exception as e:
            logging.error(f"Heartbeat monitor error: {e}")
            telegram_client_status["connected"] = False
            await asyncio.sleep(30)


async def send_error_notification(error_message: str, error_details: str=None):
    """Send error notification to admin via Telegram bot"""
    if not ERROR_NOTIFICATION_BOT_TOKEN or not ERROR_NOTIFICATION_CHAT_ID:
        logging.warning("Error notification bot token or chat ID not configured")
        return
    
    try:
        # Format error message
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        notification_text = "🚨 **SERVER ERROR ALERT** 🚨\n\n"
        notification_text += f"**Time:** {timestamp}\n"
        notification_text += f"**Error:** {error_message}\n"
        
        if error_details:
            # Truncate error details if too long
            if len(error_details) > 1000:
                error_details = error_details[:1000] + "... (truncated)"
            notification_text += f"**Details:**\n```{error_details}```\n"
        
        notification_text += "\n⚠️ Please check the server logs for more information."
        
        # Send via Telegram Bot API
        bot_url = f"https://api.telegram.org/bot{ERROR_NOTIFICATION_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": ERROR_NOTIFICATION_CHAT_ID,
            "text": notification_text,
            "parse_mode": "Markdown"
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(bot_url, json=payload)
            if response.status_code == 200:
                logging.info("Error notification sent successfully")
            else:
                logging.error(f"Failed to send error notification: {response.status_code}")
    
    except Exception as e:
        logging.error(f"Failed to send error notification: {e}")


@client.on(events.NewMessage)
async def handler(event):
    try:
        message = event.message
        if not message.message:
            return

        msg_text = message.message
        all_addresses = []
        for _, regex in compiled_patterns.items():
            matches = regex.findall(msg_text)
            for addr in matches:
                all_addresses.append(addr)

        if not all_addresses:
            return

        group_entity = await event.get_chat()
        group_name = getattr(group_entity, 'title', str(group_entity.id))
        group_username = getattr(group_entity, 'username', None)

        # Generate message link
        message_link = (
            f"https://t.me/{group_username}/{message.id}"
            if group_username else
            f"https://t.me/c/{str(group_entity.id)[4:]}/{message.id}"
            if str(group_entity.id).startswith("-100") else None
        )
        
        user_count = None
        try:
            full_info = await client(GetFullChannelRequest(channel=group_entity))
            logging.info(f"Full info: {full_info}")
            user_count = getattr(full_info.full_chat, 'participants_count', None)
        except Exception:
            pass

        influencer = (
            message.sender.username if message.sender and hasattr(message.sender, 'username')
            else str(message.sender_id) if message.sender_id
            else "Unknown"
        )

        # Get user profile image
        profile_image_url = None
        try:
            if message.sender:
                # Get profile photos
                photos = await client.get_profile_photos(message.sender, limit=1)
                if photos and len(photos) > 0:
                    # Get the latest profile photo
                    latest_photo = photos[0]
                    # Download the photo to a temporary location or get the file reference
                    # For now, we'll store the photo file ID and download path
                    try:
                        # Ensure tmp directory exists
                        os.makedirs("tmp", exist_ok=True)
                        # Download the photo file
                        photo_path = await client.download_profile_photo(
                            message.sender,
                            file=f"tmp/profile_{message.sender_id}_{latest_photo.id}.jpg"
                        )
                        if photo_path:
                            profile_image_url = photo_path
                            logging.info(f"Profile photo downloaded for user {influencer}, path: {photo_path}")
                        else:
                            # Fallback: store photo ID if download fails
                            profile_image_url = f"telegram_photo_id_{latest_photo.id}"
                            logging.info(f"Profile photo found for user {influencer}, photo ID: {latest_photo.id} (stored as ID only)")
                    except Exception as download_error:
                        # Fallback: store photo ID if download fails
                        profile_image_url = f"telegram_photo_id_{latest_photo.id}"
                        logging.warning(f"Could not download profile photo for user {influencer}, storing ID only: {str(download_error)}")
        except Exception as photo_error:
            logging.warning(f"Could not get profile photo for user {influencer}: {str(photo_error)}")

        msg_time_dt = message.date if message.date else datetime.utcnow()

        dex_data_for_webhook = []
        contracts_for_payload = []

        for addr in all_addresses:
            try:
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
                            break
                    if found_match:
                        break

                if not found_match:
                    # Fetch new Dexscreener data
                    dexscreener_data = fetch_dexscreener_data(addr)

                    logging.info(f"Dexscreener data: {dexscreener_data}")
                    # Extract only the specified fields: chainId, dexId, url, pairAddress, 
                    # baseToken, priceNative, priceUsd, volume, liquidity, fdv, marketCap, info
                    extracted_dex_data = extract_dexscreener_fields(dexscreener_data)
                    logging.info(f"Fetched and extracted Dexscreener data for {addr}: {len(extracted_dex_data)} pairs")

                    first_pair = extracted_dex_data[0] if isinstance(extracted_dex_data, list) and len(extracted_dex_data) > 0 else {}

                    chain_id = first_pair.get("chainId") or first_pair.get("chain")
                    base_token_address = first_pair.get("baseToken", {}).get("address") if first_pair.get("baseToken") else None

                    doc = {
                        "Group Name": group_name,
                        "Chain": chain_id,
                        "Contract Address": base_token_address,
                        "Group User Count": user_count,
                        "Username": influencer,
                        "Profile Image URL": profile_image_url,
                        "Message DateTime": msg_time_dt,
                        "Full Message": msg_text,
                        "Dexscreener Data": extracted_dex_data,
                        "Call Count": 1,
                        "Message Link": message_link,
                    }
                    await test_collection.insert_one(doc)
                    logging.info(f"Inserted new document for {addr} user {influencer}")

                    dex_data_for_webhook.append({
                        "contract_address": addr,
                        "dexscreener": extracted_dex_data
                    })

                contracts_for_payload.append({"address": addr})
            
            except Exception as addr_error:
                error_msg = f"Error processing address {addr}: {str(addr_error)}"
                logging.error(error_msg)
                await send_error_notification(
                    "Address Processing Error",
                    f"Error processing address {addr} from user {influencer} in group {group_name}: {str(addr_error)}"
                )
                continue

        # Build webhook payload
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
        except Exception as webhook_error:
            error_msg = f"Webhook error: {str(webhook_error)}"
            logging.error(f"❌ {error_msg}")
            await send_error_notification(
                "Webhook Communication Error",
                f"Failed to send data to webhook {WEBHOOK_URL}: {str(webhook_error)}"
            )

    except Exception as e:
        error_msg = f"Critical error in message handler: {str(e)}"
        error_details = traceback.format_exc()
        logging.error(f"❌ {error_msg}")
        logging.error(f"Error details: {error_details}")
        
        # Send error notification
        await send_error_notification(
            "Critical Message Handler Error",
            f"Telegram Listener encountered a critical error: {str(e)}\n\nFull traceback:\n{error_details}"
        )


async def main():
    global app_status
    
    try:
        # Start health check server first
        logging.info("🚀 Starting Telegram Listener service...")
        health_runner = await start_health_server()
        
        # Start Telegram client
        await client.start()
        telegram_client_status["connected"] = True
        telegram_client_status["last_heartbeat"] = datetime.utcnow()
        logging.info("🚀 Telegram client connected successfully")
        
        # Start heartbeat monitor
        heartbeat_task = asyncio.create_task(heartbeat_monitor())
        
        # Mark app as healthy
        app_status["healthy"] = True
        logging.info("🚀 Telegram live listener started and healthy...")
        
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
            f"Telegram Listener application crashed: {str(e)}\n\nFull traceback:\n{error_details}"
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
        # For synchronous errors before asyncio.run, we can't use async error notification
        # So just log and exit with error code
        exit(1)
