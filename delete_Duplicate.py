from pymongo import MongoClient

# 1. Connect to your MongoDB Atlas cluster
# Replace <username>, <password>, <cluster-url>, and <database>
client = MongoClient("mongodb+srv://globalsoin20:Uu5mmE9pqEtfBB1a@cluster0.6k3hcco.mongodb.net/")

db = client["soin-pump"]  # Database name
collection = db["telegram_influencer_data"]  # Replace with your collection name

print("Connected to MongoDB")

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
