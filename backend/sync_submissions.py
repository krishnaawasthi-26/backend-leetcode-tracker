import asyncio
import traceback
from datetime import datetime

import httpx
from pymongo.errors import ConfigurationError, ServerSelectionTimeoutError

from database.connection import collection
from utils.notification import send_web_push

GRAPHQL_URL = "https://leetcode.com/graphql"
QUERY_TEMPLATE = {
    "query": """
        query recentAcSubmissions($username: String!) {
            recentAcSubmissionList(username: $username) {
                title
                timestamp
            }
        }
    """
}


async def fetch_recent_leetcode(leetcode_username: str):
    payload = {
        **QUERY_TEMPLATE,
        "variables": {"username": leetcode_username},
    }
    headers = {
        "Content-Type": "application/json",
        "Referer": f"https://leetcode.com/{leetcode_username}/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    }

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(GRAPHQL_URL, json=payload, headers=headers)

    if response.status_code != 200:
        print(f"LeetCode fetch failed for {leetcode_username}: {response.status_code}")
        return []

    arr = response.json().get("data", {}).get("recentAcSubmissionList", [])
    return [
        {
            "title": item["title"],
            "time": datetime.fromtimestamp(int(item["timestamp"])).strftime("%Y-%m-%d %I:%M %p"),
            "leetcode_username": leetcode_username,
            "leetcode_url": f"https://leetcode.com/{leetcode_username}/",
        }
        for item in arr
        if item.get("title")
    ]


async def sync_user_submissions(user_doc: dict):
    app_username = user_doc["username"]
    leetcode_username = user_doc["leetcode_username"]

    recent = await fetch_recent_leetcode(leetcode_username)
    if not recent:
        return 0

    inserted = 0
    subscriptions = await collection.find({"type": "subscription"}).to_list(length=None)

    for entry in reversed(recent):
        exists = await collection.find_one(
            {
                "type": "leetcode_submission",
                "data.app_username": app_username,
                "data.leetcode_username": leetcode_username,
                "data.title": entry["title"],
                "data.time": entry["time"],
            }
        )

        if exists:
            continue

        payload = {
            **entry,
            "app_username": app_username,
        }

        await collection.insert_one({
            "type": "leetcode_submission",
            "data": payload,
        })

        inserted += 1
        print(f"Inserted {app_username} -> {entry['title']} at {entry['time']}")

        for sub in subscriptions:
            try:
                send_web_push(
                    sub["subscription"],
                    f"✅ {app_username} solved: {entry['title']}",
                )
            except Exception as exc:
                print("Failed to notify", sub.get("_id"), ":", exc)

    return inserted


async def sync_once():
    tracked_users = await collection.find({"type": "tracked_user", "verified": True}).to_list(length=None)
    if not tracked_users:
        print("No tracked users found. Log in via / and add a LeetCode URL first.")
        return

    total_inserted = 0
    for user_doc in tracked_users:
        total_inserted += await sync_user_submissions(user_doc)

    if total_inserted == 0:
        print("No new submissions to insert.")


async def main_loop():
    while True:
        try:
            await sync_once()
        except (ConfigurationError, ServerSelectionTimeoutError) as exc:
            print("⚠️ MongoDB connection failed. Check MONGO_URI / DNS / Atlas network settings.")
            print(f"Details: {exc}")
        except Exception as exc:
            print("❌ Error in sync_once:", exc)
            traceback.print_exc()

        await asyncio.sleep(10)


if __name__ == "__main__":
    print("Starting LeetCode sync loop (every 10s)...")
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        print("Sync loop stopped by user.")
