from fastapi import APIRouter, Request, HTTPException
from database.connection import collection

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])

@router.post("/subscribe/")
async def subscribe(request: Request):
    try:
        subscription = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid subscription data")

    # Check if subscription already exists
    existing = await collection.find_one({
        "type": "subscription",
        "subscription.endpoint": subscription.get("endpoint")
    })

    if existing:
        return {"message": "Already subscribed."}

    # Save subscription in DB
    await collection.insert_one({
        "type": "subscription",
        "subscription": subscription
    })

    return {"message": "Subscribed successfully!"}
