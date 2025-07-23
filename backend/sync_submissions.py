# backend/sync_submissions.py

import asyncio
import httpx
import traceback
from datetime import datetime
from database.connection import collection
from utils.notification import send_web_push

USERNAME = "krishna-jangid"
# your own API to fetch the newest stored submission
API_URL = "http://localhost:8002/api/submissions/?skip=0&limit=1"

GRAPHQL_URL = "https://leetcode.com/graphql"
HEADERS = {
    "Content-Type": "application/json",
    "Referer": f"https://leetcode.com/{USERNAME}/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}
QUERY = {
    "query": """
        query recentAcSubmissions($username: String!) {
            recentAcSubmissionList(username: $username) {
                title
                timestamp
            }
        }
    """,
    "variables": {"username": USERNAME}
}


async def fetch_recent_leetcode():
    async with httpx.AsyncClient() as client:
        r = await client.post(GRAPHQL_URL, json=QUERY, headers=HEADERS)
        if r.status_code != 200:
            print("LeetCode fetch failed:", r.status_code)
            return []
        arr = r.json().get("data", {}).get("recentAcSubmissionList", [])
        return [
            {
                "title": item["title"],
                "time": datetime.fromtimestamp(int(item["timestamp"])).strftime("%Y-%m-%d %I:%M %p"),
                "profile_link": f"https://leetcode.com/{USERNAME}/"
            }
            for item in arr if item.get("title")
        ]


async def fetch_latest_db_entry():
    async with httpx.AsyncClient() as client:
        r = await client.get(API_URL)
        if r.status_code != 200:
            return None
        arr = r.json()
        return arr[0] if isinstance(arr, list) and arr else None


async def sync_once():
    recent = await fetch_recent_leetcode()
    if not recent:
        print("No recent LeetCode data fetched.")
        return

    latest = await fetch_latest_db_entry()
    new_count = 0

    # process from oldest to newest
    for entry in reversed(recent):
        is_new = (
            latest is None
            or entry["title"] != latest.get("title")
            or entry["time"]  != latest.get("time")
        )
        if not is_new:
            # once we hit an already‐stored entry, older ones are also stored
            break

        # ensure not duplicated in DB
        exists = await collection.find_one({
            "type": "leetcode_submission",
            "data.title": entry["title"],
            "data.time":  entry["time"]
        })
        if exists:
            continue

        # insert and notify
        await collection.insert_one({
            "type": "leetcode_submission",
            "data": entry
        })
        print(f"Inserted new submission: {entry['title']} at {entry['time']}")
        new_count += 1

        subs = await collection.find({"type": "subscription"}).to_list(length=None)
        for sub in subs:
            try:
                send_web_push(sub["subscription"], f"✅ New LeetCode problem solved: {entry['title']}")
            except Exception as e:
                print("Failed to notify", sub.get("_id"), ":", e)

    if new_count == 0:
        print("No new submissions to insert.")


async def main_loop():
    while True:
        try:
            await sync_once()
        except Exception as e:
            print("❌ Error in sync_once:", e)
            traceback.print_exc()
        await asyncio.sleep(10)


if __name__ == "__main__":
    print("Starting LeetCode sync loop (every 10s)...")
    asyncio.run(main_loop())
