# Backend Vercel Serverless Notes

This file documents the minimal steps to attempt deploying the FastAPI backend to Vercel as a serverless Python function.

Important: This repository currently contains a committed `.env` file. Do NOT leave secrets in git — remove the file from the repo and rotate any leaked credentials before production.

Prerequisites
- Vercel account connected to this GitHub repository
- Environment variables set in Vercel project (see list below)

Files added for serverless
- `api/index.py` — minimal ASGI wrapper that exposes `app`.
- `vercel.json` — instructs Vercel to build `api/index.py` with `@vercel/python`.

Environment variables to set on Vercel (Project → Settings → Environment Variables):
- `MONGO_URL` — MongoDB connection string (no credentials in repo)
- `MONGO_DB` — database name
- `SECRET_KEY` — JWT secret
- `ALGORITHM` — e.g. `HS256`
- `ACCESS_TOKEN_EXPIRE_MINUTES` — e.g. `30`
- `BASE_URL` — public base URL for the API (optional)

How to deploy (quick):
1. In Vercel dashboard, create a new Project → Import Git Repository → choose this repo.
2. Set the Project Root to `backend` (so `vercel.json` and `api/index.py` are visible to the builder).
3. Ensure Build & Output settings are left to automatic/detected. `vercel.json` instructs Vercel to use `@vercel/python` on `api/index.py`.
4. Add the environment variables listed above in the Vercel project settings (both Preview and Production as needed).
5. Deploy and test the endpoints (e.g., `/api/health` or other routes).

Notes & caveats
- FastAPI lifespan events may not fire reliably on Vercel serverless. The codebase was adjusted to lazily initialize and cache the Motor client and Beanie initialization to improve compatibility with serverless runtimes.
- Cold starts will still run initialization logic; expect higher latency on first request to a warm instance.
- If Vercel does not support your desired Python runtime (check supported runtimes), consider deploying the backend as a container on Render or Railway instead.
