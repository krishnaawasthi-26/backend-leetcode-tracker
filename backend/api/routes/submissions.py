from fastapi import APIRouter, Query
from database.connection import collection

router = APIRouter(prefix="/api/submissions", tags=["Submissions"])

@router.get("/")
async def get_submissions(skip: int = Query(0), limit: int = Query(10)):
    cursor = collection.find({}, {"_id": 1, "data": 1}).sort("_id", -1).skip(skip).limit(limit)
    submissions = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        submissions.append(doc)
    return submissions

