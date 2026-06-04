from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db, close_db
from app.routes import system, list, user, auth, workspace
from app.config import settings


@asynccontextmanager
async def lifespan(app_: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown
    close_db()


app = FastAPI(lifespan=lifespan)

origins = [settings.cors_origin]

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

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=5001, reload=True)