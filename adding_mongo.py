import pandas as pd
import requests
import json

API_URL = "http://localhost:3000/users"


def send_user(handle: str):
    """Send a user entry with only handle to API."""
    payload = {
        "handle": handle,
        "email": f"{handle}@example.com",  # dummy email
        "followers": 0,
        "platforms": {"twitter": 0, "instagram": 0},
        "country": "Unknown",
        "gender_split": {"male": 0, "female": 0},
        "name": handle,
        "bio": "",
        "profile_image": "",
        "banner_image": "",
        "rating": 0,
        "wallet_address": "",
        "tags": [],
        "social_links": {
            "twitter": f"https://twitter.com/{handle}"
        }
    }
    try:
        r = requests.post(API_URL, json=payload, timeout=10)
        if r.status_code in (200, 201):
            print(f"✅ Success for {handle}")
        else:
            print(f"⚠️ Failed for {handle}: {r.status_code} {r.text}")
    except Exception as e:
        print(f"❌ Error for {handle}: {e}")


if __name__ == "__main__":
    # Load CSV (assume it has a column "handle" or "username")
    df = pd.read_csv("twitter_check_results.csv")

    for handle in df["handle"]:  # change column name if needed
        if pd.notna(handle) and str(handle).strip():
            send_user(str(handle).strip())
