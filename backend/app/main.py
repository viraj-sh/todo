from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi_mcp import FastApiMCP
from app.exception_handler import validation_exception_handler
from app.database import init_db, close_db
from app.routes import system, list, user, auth, workspace, item
from app.config import settings


@asynccontextmanager
async def lifespan(app_: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown
    close_db()


app = FastAPI(
    lifespan=lifespan,
    title=settings.api_title,
    description="Self-hosted Gruvbox-themed todo app made using FARM stack, with MCP server and LLM integration.",
    version=settings.api_version,
)

origins = [settings.cors_origin]

app.add_middleware(
    middleware_class=CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    middleware_class=SessionMiddleware,
    secret_key=settings.secret_key.get_secret_value(),
)
app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore
app.include_router(router=system.router, prefix="", tags=["system"])
app.include_router(router=auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(router=user.router, prefix="/api/user", tags=["user"])
app.include_router(
    router=workspace.router, prefix="/api/workspaces", tags=["workspace"]
)
app.include_router(router=list.router, prefix="/api", tags=["list"])
app.include_router(router=item.router, prefix="/api", tags=["item"])

mcp = FastApiMCP(
    app,
    name="Todo MCP",
    description="MCP server for the Todo API",
    include_operations=[
        "get_current_user",
        "list_workspaces",
        "create_workspace",
        "get_workspace",
        "update_workspace",
        "delete_workspace",
        "list_todo_lists",
        "create_todo_list",
        "get_todo_list",
        "update_todo_list",
        "delete_todo_list",
        "create_todo_item",
        "update_todo_item",
        "delete_todo_item",
        "list_tags",
    ],
)
mcp.mount_http()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=5001, reload=True)
