from fastapi import APIRouter, status, HTTPException
from app.database import db

router = APIRouter()


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    try:
        pong = await db.command("ping")
        if pong.get("ok") != 1:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="database unavailable",
            )
        return {"status": f"healthy"}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="database unavailable",
        )
