from fastapi import APIRouter, Query

from database.connection import collection

router = APIRouter(prefix="/api/recent", tags=["Recent Submission"])


@router.get("/")
async def get_recent_submission(username: str | None = Query(default=None)):
    query = {"type": "leetcode_submission"}
    if username:
        query["data.app_username"] = username

    doc = await collection.find_one(
        query,
        {"_id": 0, "data": 1},
        sort=[("_id", -1)],
    )

    if doc:
        return doc["data"]
    return {"message": "No submissions yet."}
