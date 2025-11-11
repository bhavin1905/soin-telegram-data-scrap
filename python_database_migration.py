from pymongo import MongoClient
from datetime import datetime

# --- Configuration ---
SOURCE_URI = "mongodb+srv://bhavinparmar1953:123qwerty@cluster0.qndu4.mongodb.net/soin-pump"
# TARGET_URI = "mongodb+srv://globalsoin20:Uu5mmE9pqEtfBB1a@cluster0.6k3hcco.mongodb.net/soin-pump?retryWrites=true&w=majority&appName=Cluster0/"
TARGET_URI = "mongodb+srv://globalsoin20:Uu5mmE9pqEtfBB1a@cluster0.6k3hcco.mongodb.net/soin-pump?retryWrites=true&w=majority&appName=Cluster0/"

# SOURCE_COLLECTION = "dexscreener_cache_new"
SOURCE_COLLECTION = "telegram_influencer_data"
# TARGET_COLLECTION = "dexscreener_cache_new"
TARGET_COLLECTION = "telegram_influencer_data"


# --- Migration Function ---
def migrate_data():
    # Connect to source and target MongoDB
    source_client = MongoClient(SOURCE_URI)
    target_client = MongoClient(TARGET_URI)

    source_db = source_client.get_default_database()
    target_db = target_client.get_default_database()

    source_col = source_db[SOURCE_COLLECTION]
    target_col = target_db[TARGET_COLLECTION]

    print(f"🚀 Starting migration from {SOURCE_COLLECTION} → {TARGET_COLLECTION}")

    count = 0

    # Cursor for all documents in the source collection
    for doc in source_col.find():
        # Optional: remove _id if you want MongoDB to generate new ones
        doc.pop("_id", None)

        # Optional: add or transform fields
        doc["migratedAt"] = datetime.utcnow()

        target_col.insert_one(doc)
        count += 1

        # Print progress occasionally
        if count % 100 == 0:
            print(f"✅ Migrated {count} documents so far...")

    print(f"\n🎉 Migration completed successfully! Total documents migrated: {count}")

    # Close connections
    source_client.close()
    target_client.close()


if __name__ == "__main__":
    migrate_data()
