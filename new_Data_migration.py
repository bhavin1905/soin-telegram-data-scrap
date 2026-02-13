import asyncio
from datetime import datetime, UTC
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

# ================= ENV =================
load_dotenv()
MONGO_URI = os.getenv("MONGODB_URI")

SRC_DB = "soin-pump"
SRC_COL = "telegram_influencer_data"
DST_DB = "telegram_alpha"

client = AsyncIOMotorClient(MONGO_URI)

src = client[SRC_DB][SRC_COL]
groups = client[DST_DB]["groups"]
tokens = client[DST_DB]["tokens"]
calls = client[DST_DB]["calls"]


# ================= HELPERS =================
def safe_username(username, fallback):
    return username if username else f"tg_{fallback}"


def utc(dt):
    if not dt:
        return datetime.now(UTC)
    if dt.tzinfo:
        return dt
    return dt.replace(tzinfo=UTC)

def is_valid_url(url: str | None) -> bool:
    if not url:
        return False
    return url.startswith("http://") or url.startswith("https://")



# ================= INDEXES =================
async def ensure_indexes():
    print("🔧 Checking indexes...")

    await groups.create_index("telegram_id", unique=True, sparse=True)
    await tokens.create_index([("chain", 1), ("contract_address", 1)], unique=True)
    await calls.create_index([("group_id", 1), ("token_id", 1), ("message_link", 1)], unique=True)

    print("✅ Index setup complete\n")


# ================= UPSERT =================
async def upsert_group_legacy(doc):
    username = safe_username(doc.get("Username"), doc.get("Group Name"))
    name = doc.get("Group Name")
    member_count = doc.get("Group User Count")
    msg_time = utc(doc.get("Message DateTime"))
    profile_image_url = doc.get("Profile Image URL")
    profile_image_url = profile_image_url if is_valid_url(profile_image_url) else None


    return await groups.find_one_and_update(
        {"username": username},
        {
            "$set": {
                "name": name,
                "username": username,
                "current_member_count": member_count,
                "updated_at": msg_time,
                **({"profile_image_url": profile_image_url} if profile_image_url else {}),
            },
            "$max": {"max_member_count_seen": member_count or 0},
            "$setOnInsert": {
                "total_calls": 0,
                "unique_tokens": [],
                "created_at": msg_time,
            },
        },
        upsert=True,
        return_document=True,
    )


async def upsert_token_legacy(pair, msg_time):
    chain = pair.get("chainId")
    contract = pair.get("baseToken", {}).get("address")

    if not chain or not contract:
        return None

    msg_time = utc(msg_time)

    return await tokens.find_one_and_update(
        {"chain": chain, "contract_address": contract},
        {
            "$set": {
                "symbol": pair.get("baseToken", {}).get("symbol"),
                "name": pair.get("baseToken", {}).get("name"),
                "last_called_at": msg_time,
            },
            "$setOnInsert": {
                "first_seen_at": msg_time,
                "total_calls": 0,
                "groups_called": [],
            },
        },
        upsert=True,
        return_document=True,
    )


async def insert_call_legacy(group_doc, token_doc, doc):
    try:
        await calls.insert_one(
            {
                "group_id": group_doc["_id"],
                "token_id": token_doc["_id"],
                "message_text": doc.get("Full Message"),
                "message_link": doc.get("Message Link"),
                "created_at": utc(doc.get("Message DateTime")),
            }
        )
    except Exception:
        return False

    await groups.update_one(
        {"_id": group_doc["_id"]},
        {"$inc": {"total_calls": 1}, "$addToSet": {"unique_tokens": token_doc["_id"]}},
    )

    await tokens.update_one(
        {"_id": token_doc["_id"]},
        {"$inc": {"total_calls": 1}, "$addToSet": {"groups_called": group_doc["_id"]}},
    )

    return True


# ================= PAGINATED MIGRATION =================
BATCH_SIZE = 500


async def migrate():
    await ensure_indexes()

    last_id = None
    scanned = 0
    migrated = 0

    while True:
        query = {"_id": {"$gt": last_id}} if last_id else {}

        batch = await src.find(query).sort("_id", 1).limit(BATCH_SIZE).to_list(length=BATCH_SIZE)

        if not batch:
            break

        for doc in batch:
            scanned += 1
            last_id = doc["_id"]

            try:
                group_doc = await upsert_group_legacy(doc)

                dex_list = doc.get("Dexscreener Data") or []
                if not dex_list:
                    continue

                token_doc = await upsert_token_legacy(dex_list[0], doc.get("Message DateTime"))
                if not token_doc:
                    continue

                if await insert_call_legacy(group_doc, token_doc, doc):
                    migrated += 1

            except Exception as e:
                print("❌ Error:", e)

        print(f"✅ Migrated {migrated} | Scanned {scanned}")

    print("\n🎉 MIGRATION COMPLETE")
    print("Total scanned:", scanned)
    print("Total inserted:", migrated)


if __name__ == "__main__":
    asyncio.run(migrate())
