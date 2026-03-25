from collections import Counter
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from database.connection import collection

router = APIRouter(prefix="/api/report", tags=["Report"])


TIME_FORMATS = [
    "%Y-%m-%d %I:%M %p",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
]


def _parse_submission_time(value: str) -> datetime | None:
    if not value:
        return None

    for fmt in TIME_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue

    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


@router.get("/summary")
async def get_summary(
    username: str = Query(..., description="App username"),
    profile: str | None = Query(default=None, description="LeetCode profile username"),
):
    user_doc = await collection.find_one(
        {"type": "tracked_user", "username": username},
        {"_id": 0, "username": 1, "leetcode_username": 1, "linked_accounts": 1},
    )

    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")

    linked_profiles = user_doc.get("linked_accounts", [])
    active_profile = (profile or user_doc.get("leetcode_username") or "").lower()

    if active_profile and linked_profiles and active_profile not in linked_profiles:
        raise HTTPException(status_code=400, detail="Requested profile is not linked with this user")

    query = {"type": "leetcode_submission", "data.app_username": username}
    if active_profile:
        query["data.leetcode_username"] = active_profile

    submissions = await collection.find(query, {"_id": 0, "data": 1}).to_list(length=None)

    parsed = []
    for item in submissions:
        data = item.get("data", {})
        ts = _parse_submission_time(data.get("time", ""))
        if ts:
            parsed.append((ts, data))

    parsed.sort(key=lambda x: x[0])

    total = len(parsed)
    if total == 0:
        return {
            "username": username,
            "active_profile": active_profile,
            "linked_profiles": linked_profiles,
            "total_submissions": 0,
            "today_count": 0,
            "best_day": None,
            "best_month": None,
            "daily_counts": [],
            "weekday_counts": [],
            "monthly_counts": [],
            "hourly_counts": [],
        }

    day_counter = Counter(dt.strftime("%Y-%m-%d") for dt, _ in parsed)
    month_counter = Counter(dt.strftime("%Y-%m") for dt, _ in parsed)
    weekday_counter = Counter(dt.strftime("%A") for dt, _ in parsed)
    hourly_counter = Counter(dt.strftime("%H") for dt, _ in parsed)

    today_key = datetime.now().strftime("%Y-%m-%d")

    best_day, best_day_count = max(day_counter.items(), key=lambda x: x[1])
    best_month, best_month_count = max(month_counter.items(), key=lambda x: x[1])

    weekday_order = [
        "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
    ]

    daily_counts = [{"label": k, "count": day_counter[k]} for k in sorted(day_counter.keys())]
    monthly_counts = [{"label": k, "count": month_counter[k]} for k in sorted(month_counter.keys())]
    weekday_counts = [{"label": day, "count": weekday_counter.get(day, 0)} for day in weekday_order]
    hourly_counts = [{"label": f"{h}:00", "count": hourly_counter.get(f"{h:02d}", 0)} for h in range(24)]

    return {
        "username": username,
        "active_profile": active_profile,
        "linked_profiles": linked_profiles,
        "total_submissions": total,
        "today_count": day_counter.get(today_key, 0),
        "best_day": {"date": best_day, "count": best_day_count},
        "best_month": {"month": best_month, "count": best_month_count},
        "daily_counts": daily_counts,
        "weekday_counts": weekday_counts,
        "monthly_counts": monthly_counts,
        "hourly_counts": hourly_counts,
    }
