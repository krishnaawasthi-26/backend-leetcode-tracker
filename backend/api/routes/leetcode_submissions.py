from fastapi import APIRouter, Request, HTTPException
from database.connection import collection
from utils.notification import send_web_push

router = APIRouter(prefix="/api", tags=["LeetCode"])

@router.post("/leetcode/submit/")
async def submit_leetcode(request: Request):
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON data")

    try:
        # Save the submission into the DB
        await collection.insert_one({
            "type": "leetcode_submission",
            "data": data
        })

        # Fetch all subscriptions
        subscriptions = await collection.find({"type": "subscription"}).to_list(length=None)

        for sub in subscriptions:
            try:
                if "subscription" in sub:
                    send_web_push(sub["subscription"], "✅ New LeetCode submission done!")
                else:
                    print(f"Skipped invalid subscription document: {sub}")
            except Exception as e:
                print(f"Error sending push notification to {sub}: {e}")

        return {"message": "Submission saved and notifications sent!"}

    except Exception as e:
        print(f"Unexpected server error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
