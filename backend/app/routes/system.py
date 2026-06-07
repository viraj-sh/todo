from fastapi import APIRouter, status, HTTPException
from app.database import db
from app.config import settings

router = APIRouter()


@router.get("/", status_code=status.HTTP_200_OK)
async def root_endpoint():
    return {
        "name": settings.api_title,
        "version": settings.api_version,
        "docs_url": settings.api_docs_url,
    }


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    try:
        pong = await db.command("ping")
        if pong.get("ok") != 1:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="database unavailable",
            )
        return {"status": "healthy"}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="database unavailable",
        )
