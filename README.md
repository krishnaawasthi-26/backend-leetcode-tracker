# LeetCode Progress Tracker & Analytics Dashboard

A FastAPI + MongoDB project to track LeetCode submissions, manage linked profiles, and visualize progress in a dashboard.

## Live App

- **App Home (Login):** https://backend-leetcode-tracker--krishnaasfafav.replit.app/
- **Sample Dashboard:** https://backend-leetcode-tracker--krishnaasfafav.replit.app/dashboard?username=krishnaawasthi_26

---

## Features

- App-level login/register with profile verification against LeetCode GraphQL.
- Multi-profile support per user (switch linked LeetCode profile).
- Background sync loop to fetch and store recent accepted submissions.
- Dashboard analytics with charts:
  - Daily solves
  - Weekday distribution (pie)
  - Monthly solves
  - Hourly solve pattern
- API filters by `username` and `profile` to inspect specific user data.

---

## Tech Stack

- **Backend:** FastAPI
- **Database:** MongoDB (Atlas/cloud supported)
- **Driver:** Motor + PyMongo
- **Frontend:** Static HTML + Chart.js

---

## Project Structure

```text
backend-leetcode-tracker/
├── backend/
│   ├── api/
│   │   ├── main.py
│   │   ├── routes/
│   │   │   ├── auth.py
│   │   │   ├── report.py
│   │   │   ├── submissions.py
│   │   │   └── recent_submission.py
│   │   └── static/
│   │       ├── login.html
│   │       └── dashboard.html
│   ├── database/
│   │   └── connection.py
│   ├── sync_submissions.py
│   └── main.py
├── requirements.txt
└── README.md
```

---

## Environment Variables

Create a `.env` file in the project root (or `backend/`):

```env
MONGO_URI=your_mongodb_connection_string
DB_NAME=leetcode_tracker
COLLECTION_NAME=submissions
```

---

## Run Locally

From repo root:

```bash
python -m pip install -r backend/requirements.txt
python backend/main.py
```

Then open:

- `http://127.0.0.1:8002/` (login page)
- `http://127.0.0.1:8002/dashboard?username=<app_username>`
- `http://127.0.0.1:8002/docs` (Swagger)

---

## API Overview

### Auth

- `POST /api/auth/login`
  - Create/login app user, verify LeetCode URL, optionally switch linked account.
- `GET /api/auth/profiles/{username}`
  - Get active + linked profiles.
- `POST /api/auth/switch-profile`
  - Switch active linked profile.

### Reporting

- `GET /api/report/summary?username=<app_username>&profile=<leetcode_username_optional>`
  - Returns chart-ready stats for dashboard.

### Submissions

- `GET /api/submissions/?username=<app_username>&skip=0&limit=10`
- `GET /api/recent/?username=<app_username>`

---

## Data Format (MongoDB)

### Tracked User Document

```json
{
  "type": "tracked_user",
  "username": "krishnaawasthi_26",
  "password_hash": "<sha256>",
  "leetcode_username": "krishnaawasthi_26",
  "leetcode_url": "https://leetcode.com/u/krishnaawasthi_26/",
  "linked_accounts": ["krishnaawasthi_26"],
  "verified": true,
  "created_at": "2026-03-25T16:07:46.762975+00:00",
  "updated_at": "2026-03-25T16:07:46.762975+00:00"
}
```

### Submission Document

```json
{
  "type": "leetcode_submission",
  "data": {
    "title": "Maximal Rectangle",
    "time": "2026-03-21 11:42 AM",
    "leetcode_username": "krishnaawasthi_26",
    "leetcode_url": "https://leetcode.com/u/krishnaawasthi_26/",
    "app_username": "krishnaawasthi_26"
  }
}
```

---

## Manual Data Insert Tips

- Keep `app_username` exactly same as login username (case-sensitive).
- Keep `leetcode_username` lowercase.
- Prefer **not** setting `_id` manually; let MongoDB generate it.

---

## Deployment Notes (Replit)

- Your app is already running on Replit links above.
- Ensure `.env` values are set in Replit Secrets.
- If Mongo DNS errors appear (`SERVFAIL`, `NXDOMAIN`), verify:
  - Atlas cluster host is correct
  - Atlas network access allows your deployment environment
  - `MONGO_URI` is copied correctly

---

## Future Improvements

- JWT/session auth for persistent login.
- Difficulty/topic analytics if more metadata is stored.
- Export reports (CSV/PDF).
- Scheduled worker separation for production deployments.
