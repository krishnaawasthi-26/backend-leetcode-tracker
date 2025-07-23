from fastapi import APIRouter
from database.connection import collection

router = APIRouter(prefix="/api/recent", tags=["Recent Submission"])

@router.get("/")
async def get_recent_submission():
    doc = await collection.find_one({}, {"_id": 0, "title": 1, "time": 1, "profile_link": 1}, sort=[("_id", -1)])
    if doc:
        return doc
    return {"message": "No submissions yet."}

