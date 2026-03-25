from fastapi import APIRouter, Query

from database.connection import collection

router = APIRouter(prefix="/api/submissions", tags=["Submissions"])


@router.get("/")
async def get_submissions(
    username: str | None = Query(default=None, description="App username filter"),
    skip: int = Query(0),
    limit: int = Query(10),
):
    query = {"type": "leetcode_submission"}
    if username:
        query["data.app_username"] = username

    cursor = (
        collection.find(query, {"_id": 1, "data": 1})
        .sort("_id", -1)
        .skip(skip)
        .limit(limit)
    )

    submissions = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        submissions.append(doc)

    return submissions
