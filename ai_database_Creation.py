import logging
import os
from dotenv import load_dotenv
from pymongo import MongoClient
load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
client = MongoClient(MONGODB_URI)
db = client["soin-pump"]
collection = db["telegram_influencer_data"]
target_collection = db["telegram_influencer_data_simplified"]

def get_token_data(doc):
    try:
        contract_address = doc.get("Contract Address")
        chain = doc.get("Chain")
        group_name = doc.get("Group Name")
        user_count = doc.get("Group User Count")
        username = doc.get("Username")
        call_count = doc.get("Call Count", 1)  # Default to 1
        message_datetime = doc.get("Message DateTime")
        dexscreener_data = doc.get("Dexscreener Data", [])
        full_message = doc.get("Full Message")

        # Initialize all fields with None/defaults
        token_name = None
        token_symbol = None
        token_image = None
        banner_image = None
        social_links = []
        price_usd = None
        market_cap = None
        dex_url = None

        # Only extract dexscreener data if it exists
        if dexscreener_data and len(dexscreener_data) > 0:
            first_pair = dexscreener_data[0]
            base_token = first_pair.get("baseToken", {})
            pair_address = first_pair.get("pairAddress", None)
            token_name = base_token.get("name")
            token_symbol = base_token.get("symbol")
            info = first_pair.get("info", {})
            token_image = info.get("imageUrl")
            banner_image = info.get("header")
            social_links = info.get("socials", [])
            price_usd = first_pair.get("priceUsd")
            market_cap = first_pair.get("marketCap")
            dex_url = first_pair.get("url")

        return {
            "contract_address": contract_address,
            "group_name": group_name,
            "user_count": user_count,
            "username": username,
            "full_message": full_message,
            "token_name": token_name,
            "token_symbol": token_symbol,
            "pair_address": pair_address,
            "chain": chain,
            "dex_url": dex_url,
            "social_links": social_links,
            "call_count": call_count,
            "token_image": token_image,
            "banner_image": banner_image,
            "price_usd": float(price_usd) if price_usd else None,
            "market_cap": float(market_cap) if market_cap else None,
            "message_datetime": message_datetime,
        }
        
    except Exception as e:
        print(f"Error getting token data: {e}")
        import traceback
        traceback.print_exc()
        return None


def create_simplified_collection():
    logging.info("🚀 Starting to create simplified token summary collection...")
    
    # Clear existing collection if you want to rebuild (optional)
    # target_collection.delete_many({})
    
    processed_count = 0
    inserted_count = 0
    updated_count = 0
    skipped_count = 0

    for doc in collection.find():
        processed_count += 1
        token_data = get_token_data(doc)
        
        if not token_data:
            skipped_count += 1
            continue
        
        # Use .get() with defaults to safely access all fields
        contract_address = token_data.get("contract_address")
        group_name = token_data.get("group_name")
        
        # Skip if essential fields are missing
        if not contract_address or not group_name:
            skipped_count += 1
            continue
        
        # Use .get() for all fields with appropriate defaults
        simplified_data = {
            "contract_address": contract_address,
            "group_name": group_name,
            "token_name": token_data.get("token_name"),
            "token_symbol": token_data.get("token_symbol"),
            "pair_address": token_data.get("pair_address"),
            "dex_url": token_data.get("dex_url"),
            "full_message": token_data.get("full_message"),
            "chain": token_data.get("chain"),
            "call_count": token_data.get("call_count", 1),
            "social_links": token_data.get("social_links", []),
            "token_image": token_data.get("token_image"),
            "banner_image": token_data.get("banner_image"),
            "price_usd": token_data.get("price_usd"),
            "market_cap": token_data.get("market_cap"),
            "user_count": token_data.get("user_count"),
            "username": token_data.get("username"),
            "message_datetime": token_data.get("message_datetime"),
        }

        # Check if this combination already exists
        existing = target_collection.find_one({
            "contract_address": contract_address,
            "group_name": group_name
        })
        
        if existing:
            # Update: increment call count and update other fields
            target_collection.update_one(
                {"contract_address": contract_address, "group_name": group_name},
                {
                    "$inc": {"call_count": simplified_data.get("call_count", 1)},
                    "$set": {
                        "token_name": simplified_data.get("token_name"),
                        "token_symbol": simplified_data.get("token_symbol"),
                        "pair_address": simplified_data.get("pair_address"),
                        "dex_url": simplified_data.get("dex_url"),
                        "token_image": simplified_data.get("token_image"),
                        "banner_image": simplified_data.get("banner_image"),
                        "price_usd": simplified_data.get("price_usd"),
                        "market_cap": simplified_data.get("market_cap"),
                        "user_count": simplified_data.get("user_count"),
                        "username": simplified_data.get("username"),
                        "message_datetime": simplified_data.get("message_datetime"),
                    }
                }
            )
            updated_count += 1
        else:
            target_collection.insert_one(simplified_data)
            inserted_count += 1

        # Progress logging
        if processed_count % 100 == 0:
            logging.info(f"✅ Processed {processed_count} documents... (Inserted: {inserted_count}, Updated: {updated_count}, Skipped: {skipped_count})")

    logging.info(f"🎉 Simplified token summary collection creation complete! Processed {processed_count} documents, inserted {inserted_count} documents, updated {updated_count} documents, and skipped {skipped_count} documents.")


if __name__ == "__main__":
    try:
        create_simplified_collection()
    except Exception as e:
        logging.error(f"Error creating simplified collection: {e}")
    finally:
        client.close()

    logging.info("🎉 Simplified token summary collection creation complete!")


