from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from api.routes import (
    add_submission,
    auth,
    leetcode_submissions,
    notifications,
    recent_submission,
    submissions,
)

app = FastAPI(title="LeetCode Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(submissions.router)
app.include_router(notifications.router)
app.include_router(add_submission.router)
app.include_router(recent_submission.router)
app.include_router(leetcode_submissions.router)
app.include_router(auth.router)


@app.get("/", response_class=HTMLResponse)
async def root():
    login_path = Path(__file__).resolve().parent / "static" / "login.html"
    return login_path.read_text(encoding="utf-8")