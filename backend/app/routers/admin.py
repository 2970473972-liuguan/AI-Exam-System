"""Admin endpoints: manual refresh and refresh log."""

from fastapi import APIRouter, Depends

from database import db

from ..deps import get_current_user, get_db
from ..generator_service import generate_and_save
from ..schemas import RefreshIn

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/refresh")
def refresh(payload: RefreshIn, user=Depends(get_current_user), conn=Depends(get_db)):
    generated = generate_and_save(conn, payload.subject, payload.count)
    db.log_refresh(conn, payload.subject, "manual", generated)
    return {"subject": payload.subject, "generated": generated}


@router.get("/refresh-log")
def refresh_log(user=Depends(get_current_user), conn=Depends(get_db)):
    return [dict(r) for r in db.refresh_log(conn)]
