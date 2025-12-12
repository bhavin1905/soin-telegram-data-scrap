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
