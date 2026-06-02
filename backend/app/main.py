from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db, close_db
from app.routes import system, list, user, auth, workspace


@asynccontextmanager
async def lifespan(app_: FastAPI):
    # Do not run DB initialization at startup in serverless environments.
    # Initialization will be performed lazily by the middleware on first
    # request. This avoids process exit when external DB is unreachable
    # during function startup (e.g., Vercel environments).
    yield
    # Shutdown: attempt to close DB if available
    try:
        close_db()
    except Exception:
        pass


app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5500",
    "https://todo-lac-six-80.vercel.app",
]

app.add_middleware(
    middleware_class=CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(router=system.router, prefix="", tags=["system"])
app.include_router(router=auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(router=user.router, prefix="/api/user", tags=["user"])
app.include_router(
    router=workspace.router, prefix="/api/workspaces", tags=["workspace"]
)
app.include_router(router=list.router, prefix="/api", tags=["todo list"])
