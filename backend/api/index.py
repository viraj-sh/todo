from app.main import app

# Lightweight middleware to ensure the database is initialized on the first
# request. Some serverless platforms (including Vercel) may not reliably run
# FastAPI lifespan events, so calling `init_db()` lazily on first request
# improves compatibility.
try:
	import asyncio
	from starlette.middleware.base import BaseHTTPMiddleware
	from app.database import init_db, _initialized


	class _EnsureDBInitMiddleware(BaseHTTPMiddleware):
		async def dispatch(self, request, call_next):
			try:
				if not _initialized:
					await init_db()
			except Exception:
				# initialization problems should not block request handling
				pass
			return await call_next(request)


	app.add_middleware(_EnsureDBInitMiddleware)
except Exception:
	# If Starlette/Starlette middleware imports fail for any reason,
	# fall back to exposing `app` only. Initialization will occur lazily
	# when explicit calls are made.
	pass


__all__ = ("app",)
