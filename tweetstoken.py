import logging
import time
from pymongo import MongoClient
import re
import requests

# ---------- CONFIG ----------
MONGO_URI = "mongodb+srv://bhavinparmar1953:123qwerty@cluster0.qndu4.mongodb.net/"
DB_NAME = "twitter_data"
TWEETS_COLLECTION = "tweets_data_test"
MENTIONS_COLLECTION = "token_mentions_tweet_level"   # NEW COLLECTION

# PROCESS_LIMIT = 
DEXSLEEP = 0.2

# ---------- LOGGER ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("tweet_token_extractor")

# ---------- DB ----------
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
tweets = db[TWEETS_COLLECTION]
mentions = db[MENTIONS_COLLECTION]

# ---------- HELPERS ----------
TOKEN_REGEX = re.compile(r"\$([^\s.,;:!?]+)")

def extract_tokens(text):
    if not text:
        return []
    return TOKEN_REGEX.findall(text)


def fetch_dexscreener_data(token):
    url = f"https://api.dexscreener.com/latest/dex/search/?q={token}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return []
        pairs = resp.json().get("pairs", [])
        return pairs
    except:
        return []


# ---------- MAIN ----------
def main():
    logger.info("Starting ONE-DOC-PER-TWEET extraction")

    cursor = tweets.find()
    processed = 0

    for doc in cursor:
        processed += 1

        text = str(doc.get("text") or "")
        tweet_id = doc.get("id")
        created_at = doc.get("createdAt")
        username = doc.get("otherData", {}).get("core", {}).get("user_results", {}).get("result", {}).get("legacy", {}).get("screen_name", "")

        logger.info("Processing tweet %d -> tweetId=%s user=%s", processed, tweet_id, username)

        tokens = extract_tokens(text)
        logger.info("  Tokens found: %s", tokens)

        if not tokens:
            logger.info("  No tokens found. Skipping.")
            continue

        token_list = []

        # Fetch Dex data per token
        for token in tokens:
            dexpairs = fetch_dexscreener_data(token)
            first_pair = dexpairs[0] if dexpairs else None

            token_list.append({
                "symbol": token,
                "dexPair": first_pair
            })

            logger.info("   Saved token %s (pair=%s)", token, first_pair["pairAddress"] if first_pair else "None")

            time.sleep(DEXSLEEP)

        # Build final tweet-level document
        final_doc = {
            "tweetId": tweet_id,
            "username": username,
            "tweetText": text,
            "timestamp": created_at,
            "extractedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),

            # list of token + dex data
            "tokens": token_list
        }

        # UPSERT → Avoid inserting duplicates if re-run
        mentions.update_one(
            {"tweetId": tweet_id},
            {"$set": final_doc},
            upsert=True
        )

        logger.info("  Saved tweet-level doc for tweetId=%s with %d tokens",
                    tweet_id, len(token_list))

    logger.info("FINISHED. Tweets processed: %d", processed)


if __name__ == "__main__":
    main()
