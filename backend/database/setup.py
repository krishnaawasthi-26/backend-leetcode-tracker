from database.connection import db, collection

import asyncio

async def insert_sample():
    sample_data = {
        "title": "Test Problem",
        "time": "2025-07-16 12:00 PM",
        "profile_link": "https://leetcode.com/krishna_jangir/"
    }
    await collection.insert_one(sample_data)
    print("Sample data inserted")

if __name__ == "__main__":
    asyncio.run(insert_sample())
