from pymongo import MongoClient

# 1. Connect to your MongoDB Atlas cluster
# Replace <username>, <password>, <cluster-url>, and <database>
client = MongoClient("mongodb+srv://bhavinparmar1953:123qwerty@cluster0.qndu4.mongodb.net/")

db = client["telegram_tokens"]  # Database name
collection = db["group_user_counts_webhook_test"]  # Replace with your collection name

# 2. Find duplicates
pipeline = [
    {
        "$group": {
            "_id": {
                "groupName": "$Group Name",
                "contractAddress": "$Contract Address",
                "messageDateTime": "$Message DateTime"
            },
            "ids": {"$push": "$_id"},
            "count": {"$sum": 1}
        }
    },
    {
        "$match": {
            "count": {"$gt": 1}
        }
    }
]

duplicates = list(collection.aggregate(pipeline))

# 3. Delete all but the first record in each duplicate group
deleted_count = 0
for doc in duplicates:
    ids_to_delete = doc["ids"][1:]  # Keep the first, delete the rest
    if ids_to_delete:
        result = collection.delete_many({"_id": {"$in": ids_to_delete}})
        deleted_count += result.deleted_count

print(f"✅ Duplicate removal complete. Deleted {deleted_count} documents.")
