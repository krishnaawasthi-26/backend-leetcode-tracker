import hashlib
import re
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from database.connection import collection

router = APIRouter(prefix="/api/auth", tags=["Auth"])

GRAPHQL_URL = "https://leetcode.com/graphql"
LEETCODE_USER_QUERY = {
    "query": """
        query userPublicProfile($username: String!) {
            matchedUser(username: $username) {
                username
            }
        }
    """
}


class LoginRequest(BaseModel):
    username: str = Field(min_length=3)
    password: str = Field(min_length=4)
    leetcode_url: str = Field(min_length=10)
    switch_account: bool = False


def _extract_leetcode_username(leetcode_url: str) -> str:
    normalized = leetcode_url.strip()

    patterns = [
        r"^https?://(www\.)?leetcode\.com/([A-Za-z0-9_-]+)/?$",
        r"^https?://(www\.)?leetcode\.com/u/([A-Za-z0-9_-]+)/?$",
    ]

    for pattern in patterns:
        match = re.match(pattern, normalized)
        if match:
            return match.group(2).lower()

    raise HTTPException(
        status_code=400,
        detail="Provide a valid LeetCode profile URL (example: https://leetcode.com/u/your_username/)"
    )


async def _verify_leetcode_user_exists(leetcode_username: str) -> bool:
    payload = {
        **LEETCODE_USER_QUERY,
        "variables": {"username": leetcode_username},
    }
    headers = {
        "Content-Type": "application/json",
        "Referer": f"https://leetcode.com/u/{leetcode_username}/",
        "User-Agent": "Mozilla/5.0"
    }

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(GRAPHQL_URL, json=payload, headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to verify LeetCode profile")

    matched_user = response.json().get("data", {}).get("matchedUser")
    return bool(matched_user and matched_user.get("username"))


@router.post("/login")
async def login_or_register(payload: LoginRequest):
    leetcode_username = _extract_leetcode_username(payload.leetcode_url)
    exists = await _verify_leetcode_user_exists(leetcode_username)
    if not exists:
        raise HTTPException(status_code=404, detail="LeetCode profile does not exist")

    password_hash = hashlib.sha256(payload.password.encode("utf-8")).hexdigest()
    current_time = datetime.now(timezone.utc).isoformat()

    existing_user = await collection.find_one({
        "type": "tracked_user",
        "username": payload.username,
    })

    if existing_user and existing_user.get("password_hash") != password_hash:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    previous_leetcode_username = existing_user.get("leetcode_username") if existing_user else None
    is_switching = bool(
        existing_user
        and previous_leetcode_username
        and previous_leetcode_username != leetcode_username
    )

    if is_switching and not payload.switch_account:
        raise HTTPException(
            status_code=409,
            detail=(
                f"This user is already linked to '{previous_leetcode_username}'. "
                "Enable switch_account to replace with the new LeetCode URL."
            ),
        )

    linked_accounts = []
    if existing_user:
        linked_accounts = existing_user.get("linked_accounts", [])
        if previous_leetcode_username and previous_leetcode_username not in linked_accounts:
            linked_accounts.append(previous_leetcode_username)

    if leetcode_username not in linked_accounts:
        linked_accounts.append(leetcode_username)

    await collection.update_one(
        {"type": "tracked_user", "username": payload.username},
        {
            "$set": {
                "type": "tracked_user",
                "username": payload.username,
                "password_hash": password_hash,
                "leetcode_username": leetcode_username,
                "leetcode_url": f"https://leetcode.com/u/{leetcode_username}/",
                "linked_accounts": linked_accounts,
                "verified": True,
                "verified_at": current_time,
                "updated_at": current_time,
            },
            "$setOnInsert": {
                "created_at": current_time,
            },
        },
        upsert=True,
    )

    if is_switching:
        message = "Login successful. LeetCode account switched and tracking updated."
    elif existing_user:
        message = "Login successful. Tracking continues on the linked LeetCode account."
    else:
        message = "Account created successfully. Tracking started."

    return {
        "message": message,
        "username": payload.username,
        "leetcode_username": leetcode_username,
        "leetcode_url": f"https://leetcode.com/u/{leetcode_username}/",
        "verified": True,
        "switched": is_switching,
    }


class SwitchProfileRequest(BaseModel):
    username: str = Field(min_length=3)
    password: str = Field(min_length=4)
    target_leetcode_username: str = Field(min_length=1)


@router.get("/profiles/{username}")
async def get_profiles(username: str):
    user_doc = await collection.find_one(
        {"type": "tracked_user", "username": username},
        {"_id": 0, "username": 1, "leetcode_username": 1, "linked_accounts": 1},
    )
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "username": user_doc["username"],
        "active_profile": user_doc.get("leetcode_username"),
        "linked_profiles": user_doc.get("linked_accounts", []),
    }


@router.post("/switch-profile")
async def switch_profile(payload: SwitchProfileRequest):
    target = payload.target_leetcode_username.strip().lower()

    user_doc = await collection.find_one({"type": "tracked_user", "username": payload.username})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")

    password_hash = hashlib.sha256(payload.password.encode("utf-8")).hexdigest()
    if user_doc.get("password_hash") != password_hash:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    linked_accounts = user_doc.get("linked_accounts", [])
    if target not in linked_accounts:
        raise HTTPException(status_code=400, detail="Profile is not linked with this user")

    now = datetime.now(timezone.utc).isoformat()
    await collection.update_one(
        {"type": "tracked_user", "username": payload.username},
        {
            "$set": {
                "leetcode_username": target,
                "leetcode_url": f"https://leetcode.com/u/{target}/",
                "updated_at": now,
            }
        },
    )

    return {
        "message": "Active profile switched successfully",
        "username": payload.username,
        "active_profile": target,
    }
