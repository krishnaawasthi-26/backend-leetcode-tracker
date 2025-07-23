from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import submissions, add_submission, recent_submission,notifications,leetcode_submissions
app = FastAPI(title="LeetCode Tracker API")

# Allow frontend on any origin (change for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(submissions.router)
app.include_router(notifications.router)
app.include_router(add_submission.router)
app.include_router(recent_submission.router)
app.include_router(leetcode_submissions.router)
@app.get("/")
async def root():
    return {"message": "LeetCode Tracker API is running"}
