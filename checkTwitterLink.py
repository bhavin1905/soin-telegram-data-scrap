import re
import requests
import pandas as pd

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

USERNAME_RE = re.compile(
    r'(?:https?://)?(?:www\.)?(?:x\.com|twitter\.com)/@?([A-Za-z0-9_]{1,50})',
    re.IGNORECASE
)


def extract_username(url: str):
    url = str(url).strip()
    if not url or url.lower() == "nan":
        return None
    m = USERNAME_RE.search(url)
    if m:
        return m.group(1)
    # fallback: maybe raw username
    if re.fullmatch(r'@?[A-Za-z0-9_]{1,50}', url):
        return url.lstrip("@")
    return None


def check_user(username: str):
    url = f"https://x.com/{username}"
    try:
        r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=15)
    except Exception as e:
        return {"username": username, "exists": False, "reason": f"request_error: {e}"}

    if r.status_code == 404:
        return {"username": username, "exists": False, "reason": "404 not found"}
    if "account suspended" in r.text.lower():
        return {"username": username, "exists": False, "reason": "suspended"}
    if "account doesn’t exist" in r.text.lower() or "account doesn't exist" in r.text.lower():
        return {"username": username, "exists": False, "reason": "does_not_exist"}
    
    return {"username": username, "exists": True, "reason": f"HTTP {r.status_code}"}


if __name__ == "__main__":
    # 👇 load your pandas file (CSV or Excel)
    df = pd.read_csv("XURL.csv")  # or pd.read_excel("twitter_links.xlsx")

    results = []

    for url in df["Link"]:  # replace 'url' with your column name
        username = extract_username(url)
        if username:
            result = check_user(username)
        else:
            result = {"username": url, "exists": False, "reason": "invalid url"}
        results.append(result)

    # Save results back into a DataFrame
    results_df = pd.DataFrame(results)

    # Join back to original dataframe (optional)
    final_df = df.copy()
    final_df["username"] = results_df["username"]
    final_df["exists"] = results_df["exists"]
    final_df["reason"] = results_df["reason"]

    # Save to CSV
    final_df.to_csv("twitter_check_results.csv", index=False)

    print(final_df.head())
