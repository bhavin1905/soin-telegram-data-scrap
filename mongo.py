from pymongo import MongoClient

client = MongoClient("mongodb+srv://globalsoin20:Uu5mmE9pqEtfBB1a@cluster0.6k3hcco.mongodb.net/")
db = client["soin-pump"]
coll = db["telegram_influencer_data"]

# Step 1: find unique usernames
usernames = coll.distinct("Username")

for username in usernames:
    # Step 2: find one doc that already has a profile_image
    doc = coll.find_one(
        {"Username": username, "profile_image": {"$regex": "^https"}},
        {"profile_image": 1}
    )

    if not doc:
        print(f"No profile image found for {username}, skipping...")
        continue

    image = doc["profile_image"]

    # Step 3: update ALL docs of that username to align the image
    result = coll.update_many(
        {"Username": username},
        {"$set": {"profile_image": image}}
    )

    print(f"Updated {result.modified_count} docs for {username}")
