from fastapi import APIRouter
from pydantic import BaseModel
from database.connection import collection

router = APIRouter(prefix="/api/add", tags=["Add Submission"])

class Submission(BaseModel):
    title: str
    time: str
    profile_link: str

@router.post("/")
async def add_submission(submission: Submission):
    result = await collection.insert_one(submission.dict())
    return {"inserted_id": str(result.inserted_id)}
