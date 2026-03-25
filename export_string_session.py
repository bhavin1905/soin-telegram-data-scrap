#!/usr/bin/env python3
"""
Export TELEGRAM_STRING_SESSION from an existing file session (run locally once).

Usage:
  1. Ensure .env has TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_SESSION (file name).
  2. python export_string_session.py
  3. Copy the printed string into Railway/GCP as TELEGRAM_STRING_SESSION (keep secret).
  4. Remove TELEGRAM_SESSION from prod env or leave unset when using string session.
"""
import asyncio
import os

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession

load_dotenv()

API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
SESSION_NAME = os.getenv("TELEGRAM_SESSION", "cloud_run_production")


async def main():
    if not API_HASH or not API_ID:
        print("Set TELEGRAM_API_ID and TELEGRAM_API_HASH in .env")
        return

    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    await client.connect()
    if not await client.is_user_authorized():
        print("Session not authorized. Run create_production_session.py first.")
        await client.disconnect()
        return

    exported = StringSession.save(client.session)
    print()
    print("Add this to your host as TELEGRAM_STRING_SESSION (single line, secret):")
    print()
    print(exported)
    print()
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
