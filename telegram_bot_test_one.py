import logging
import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters
)
import json
import os
import re
import httpx
from aiohttp import web
from utils import extract_dexscreener_fields, fetch_dexscreener_data
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient   # <-- MONGODB IMPORT

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ==============================
# MongoDB Setup
# ==============================
MONGO_URI = "mongodb+srv://bhavinparmar1953:123qwerty@cluster0.qndu4.mongodb.net/"
mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client["kol_metrics"]   # DB Name

# ==============================
# Token + Regex + Webhook
# ==============================
TOKEN = "8246342571:AAGxzf3OIGrZEpCRW3Vkqxcoq7f3X3IZOjI"
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

ETH_REGEX = r"0x[a-fA-F0-9]{40}"
SOL_REGEX = r"[1-9A-HJ-NP-Za-km-z]{32,44}"
PAIR_REGEX = r"0x[a-fA-H0-9]{64}"
POLKADOT_REGEX = r"[1-9A-HJ-NP-Za-km-z]{47}"
TEZOS_REGEX = r"(tz1|tz2|tz3|KT1)[1-9A-HJ-NP-Za-km-z]{33}"

# ==============================
# Health Check Status
# ==============================
bot_status = {"connected": False, "last_heartbeat": None}
app_status = {"healthy": True, "startup_time": datetime.now(timezone.utc)}
bot_application = None  # Will be set when bot starts

# ==============================
# MongoDB Functions
# ==============================

async def save_group_to_db(group_info):
    """Upsert group metadata"""
    await db.groups.update_one(
        {"_id": group_info["chat_id"]},
        {"$set": group_info},
        upsert=True
    )

async def save_message_to_db(chat_id, user, text, contracts, msg_link):
    """Insert message containing a contract"""
    doc = {
        "_id": f"msg_{chat_id}_{user.id}_{datetime.now().timestamp()}",
        "chat_id": chat_id,
        "user_id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "text": text,
        "contracts": contracts,
        "timestamp": datetime.now().isoformat(),
        "message_link": msg_link
    }
    await db.messages.insert_one(doc)

async def save_contract_to_db(contract, dex_data, group_id):
    """Upsert contract & attach group_id without duplicating"""
    await db.contracts.update_one(
        {"_id": contract},
        {
            "$set": {
                "dexscreener_data": dex_data,
                "updated_at": datetime.now().isoformat()
            },
            "$addToSet": {
                "first_seen_in": group_id
            }
        },
        upsert=True
    )


async def update_group_stats(group_id):
    """Compute and store total + unique contract calls inside groups DB"""
    
    # Total messages that contained a contract in this group
    total_calls = await db.messages.count_documents({"chat_id": group_id})

    # Total unique tokens mentioned in this group
    unique_calls = await db.contracts.count_documents({"first_seen_in": group_id})

    # Update group record with these stats
    await db.groups.update_one(
        {"_id": group_id},
        {
            "$set": {
                "total_contract_calls": total_calls,
                "unique_contract_calls": unique_calls,
                "stats_updated_at": datetime.now().isoformat()
            }
        }
    )


# ==============================
# Commands
# ==============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Bot active. Add me to a group!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start - Start\n/info - Group Info\n/admin - Admin Check\n/help - Help Menu"
    )

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    await update.message.reply_text(
        f"Chat ID: `{chat.id}`\nTitle: {chat.title}",
        parse_mode="Markdown"
    )

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    bot_member = await chat.get_member(context.bot.id)

    if bot_member.status in ["administrator", "creator"]:
        await update.message.reply_text("✅ Bot is admin")
    else:
        await update.message.reply_text("❌ Bot is NOT admin")

# ==============================
# Message Handler
# ==============================

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if msg is None:
        return

    user = msg.from_user
    if user is None:
        return

    text = msg.text or ""
    chat = update.effective_chat

    # Detect contract addresses
    eth = re.findall(ETH_REGEX, text)
    sol = re.findall(SOL_REGEX, text)
    pair = re.findall(PAIR_REGEX, text)
    polkadot = re.findall(POLKADOT_REGEX, text)
    tezos = re.findall(TEZOS_REGEX, text)

    all_addresses = eth + sol + pair + polkadot + tezos
    if not all_addresses:
        return

    # Fetch DexScreener for each
    final_dex_data = {}
    for addr in all_addresses:
        dex_raw = fetch_dexscreener_data(addr)
        dex_data = extract_dexscreener_fields(dex_raw)
        final_dex_data[addr] = dex_data
        
        logging.info(f"Dex Data for {addr}: {dex_data}")

    # Collect group info
    try:
        member_count = await context.bot.get_chat_member_count(chat.id)
    except:
        member_count = "Unknown"

    try:
        photos = await context.bot.get_chat(chat.id)
        photo = photos.photo.big_file_id if photos.photo else None
    except:
        photo = None

    group_info = {
        "chat_id": chat.id,
        "title": chat.title,
        "username": chat.username,
        "type": chat.type,
        "member_count": member_count,
        "profile_photo_id": photo,
        "updated_at": datetime.now().isoformat()
    }

    # Save to MongoDB
    await save_group_to_db(group_info)
    
    # Get message link
    message_link = None
    if chat.username:
        message_link = f"https://t.me/{chat.username}/{msg.message_id}"
    elif str(chat.id).startswith("-100"):
        message_link = f"https://t.me/c/{str(chat.id)[4:]}/{msg.message_id}"
    
    # Process contracts and prepare webhook data
    contracts_for_payload = []
    dex_data_for_webhook = []
    
    for addr in all_addresses:
        try:
            if addr in final_dex_data and len(final_dex_data[addr]) > 0:
                real_token_addr = final_dex_data[addr][0].get("baseToken", {}).get("address")
                if real_token_addr:
                    await save_contract_to_db(real_token_addr, final_dex_data[addr], chat.id)
                    
                    contracts_for_payload.append({"address": addr})
                    dex_data_for_webhook.append({
                        "contract_address": addr,
                        "dexscreener": final_dex_data[addr]
                    })
        except Exception as addr_error:
            logging.error(f"Error processing address {addr}: {str(addr_error)}")
            continue
    
    # Save message to DB (use first contract address if available)
    if contracts_for_payload:
        first_addr = contracts_for_payload[0]["address"]
        if first_addr in final_dex_data and len(final_dex_data[first_addr]) > 0:
            real_token_addr = final_dex_data[first_addr][0].get("baseToken", {}).get("address")
            if real_token_addr:
                await save_message_to_db(chat.id, user, text, real_token_addr, message_link)
    
    await update_group_stats(chat.id)
    
    # Build webhook payload (similar to telegram_listener.py)
    payload = {
        "channel": chat.title or str(chat.id),
        "message": text,
        "contracts": contracts_for_payload,
        "username": user.username or user.full_name or str(user.id),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message_link": message_link,
        "dexscreener_data": dex_data_for_webhook,
    }
    
    # Send webhook (similar to telegram_listener.py)
    if WEBHOOK_URL and contracts_for_payload:
        try:
            async with httpx.AsyncClient(timeout=30.0) as async_client:
                response = await async_client.post(WEBHOOK_URL, json=payload)
            logging.info(f"📬 Payload sent, webhook responded with status {response.status_code}")
        except Exception as webhook_error:
            error_msg = f"Webhook error: {str(webhook_error)}"
            logging.error(f"❌ {error_msg}")
    
    logging.info(f"📌 Stored to MongoDB: group={group_info.get('title')}, addresses={len(all_addresses)}")


# ==============================
# Health Check Functions
# ==============================

async def health_check(request):
    """Health check endpoint for Cloud Run"""
    status = {
        "status": "healthy" if app_status["healthy"] else "unhealthy",
        "bot_connected": bot_status["connected"],
        "uptime_seconds": (datetime.now(timezone.utc) - app_status["startup_time"]).total_seconds(),
        "last_heartbeat": bot_status["last_heartbeat"].isoformat() if bot_status["last_heartbeat"] else None,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    if app_status["healthy"] and bot_status["connected"]:
        return web.json_response(status, status=200)
    else:
        return web.json_response(status, status=503)


async def root_handler(request):
    """Root endpoint"""
    return web.json_response({
        "service": "telegram-bot",
        "status": "running",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
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
        raise


async def heartbeat_monitor():
    """Monitor bot connection and update status"""
    while True:
        try:
            # If bot_application exists, assume it's running (since run_polling is blocking)
            if bot_application:
                bot_status["connected"] = True
                bot_status["last_heartbeat"] = datetime.now(timezone.utc)
            else:
                bot_status["connected"] = False
            
            await asyncio.sleep(30)  # Check every 30 seconds
        except Exception as e:
            logging.error(f"Heartbeat monitor error: {e}")
            bot_status["connected"] = False
            await asyncio.sleep(30)


# ==============================
# Main
# ==============================

async def main():
    global bot_application
    
    try:
        # Start health check server first (MUST be in main process for Cloud Run)
        logging.info("🚀 Starting Telegram Bot service...")
        health_runner = await start_health_server()
        
        # Build and configure bot
        bot_application = ApplicationBuilder().token(TOKEN).build()
        
        bot_application.add_handler(CommandHandler("start", start))
        bot_application.add_handler(CommandHandler("help", help_command))
        bot_application.add_handler(CommandHandler("info", info))
        bot_application.add_handler(CommandHandler("admin", admin))
        bot_application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
        
        # Initialize app status
        app_status["healthy"] = True
        
        # Start heartbeat monitor
        heartbeat_task = asyncio.create_task(heartbeat_monitor())
        
        # Initialize and start bot using async API (runs in same event loop)
        await bot_application.initialize()
        await bot_application.start()
        await bot_application.updater.start_polling()
        
        # Update bot status
        bot_status["connected"] = True
        bot_status["last_heartbeat"] = datetime.now(timezone.utc)
        
        logging.info("🚀 Bot is running with MongoDB and health checks...")
        logging.info("🏥 Health check server is listening on port 8080")
        logging.info("🤖 Bot polling started")
        
        # Keep the main async loop running (this keeps both health server and bot alive)
        try:
            # Wait indefinitely, keeping both services running
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            logging.info("🛑 Application stopped by user")
        finally:
            # Cleanup
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass
            
            # Stop bot
            await bot_application.updater.stop()
            await bot_application.stop()
            await bot_application.shutdown()
            
            # Stop health server
            if health_runner:
                await health_runner.cleanup()
            
            bot_status["connected"] = False
            app_status["healthy"] = False
            
    except Exception as e:
        error_msg = f"Critical error in main function: {str(e)}"
        logging.error(f"❌ {error_msg}")
        import traceback
        logging.error(f"Error details: {traceback.format_exc()}")
        
        # Mark app as unhealthy
        app_status["healthy"] = False
        bot_status["connected"] = False
        
        # Re-raise the exception to ensure proper exit codes
        raise


if __name__ == "__main__":
    import traceback
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("🛑 Application stopped by user")
        app_status["healthy"] = False
        bot_status["connected"] = False
    except Exception as e:
        logging.error(f"❌ Fatal error: {str(e)}")
        app_status["healthy"] = False
        bot_status["connected"] = False
        exit(1)
