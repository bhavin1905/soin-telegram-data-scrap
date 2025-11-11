import requests
import asyncio
import logging
from datetime import datetime
from app_config import test_collection
import time

CACHE_TTL_SECONDS = 600  # 10 minutes
BATCH_SIZE = 300  # Dexscreener rate limit
RATE_LIMIT_WAIT = 60  # Wait 60 seconds between batches


def fetch_dexscreener_data(contract_address: str):
    url = f"https://api.dexscreener.com/latest/dex/search/?q={contract_address}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json().get('pairs', [])
    except Exception:
        pass
    return []

