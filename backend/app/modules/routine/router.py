from datetime import time

from fastapi import APIRouter, Depends, HTTPException, status

from app.db.session import get_db
from app.modules.auth.router import get_current_user
from app.models.routine import Routine
from app.modules.routine.schemas import RoutineCreate
from app.modules.routine.service import apply_completion
from sqlalchemy import select
from sqlalchemy.orm import Session


router = APIRouter(prefix="/routines", tags=["routines"])


def _serialize(r: Routine) -> dict:
    return {
        "id": str(r.id),
        "title": r.title,
        "time": str(r.time),
        "frequency": r.frequency,
        "notes": r.notes,
        "category": r.category,
        "xp": r.xp,
        "completed": bool(r.completed),
        "completed_at": r.completed_at.isoformat() if r.completed_at else None,
        "last_completed_on": str(r.last_completed_on) if r.last_completed_on else None,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
    }


@router.get("")
def list_routines(user=Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    rows = db.execute(select(Routine).where(Routine.user_id == user.id)).scalars().all()
    return [_serialize(r) for r in rows]


@router.post("")
def create_routine(payload: RoutineCreate, user=Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    try:
        raw_time = time.fromisoformat(payload.time)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="time must be in HH:MM format",
        )

    routine = Routine(
        user_id=user.id,
        title=payload.title,
        time=raw_time,
        frequency=payload.frequency,
        notes=payload.notes or "",
        xp=payload.xp,
        category=payload.category,
    )
    db.add(routine)
    db.commit()
    db.refresh(routine)
    return _serialize(routine)


@router.patch("/{routine_id}")
def update_routine(
    routine_id: str,
    payload: dict,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Update a routine.  ``completed`` toggles completion and awards XP."""
    routine = db.get(Routine, routine_id)
    if routine is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Routine not found")
    if routine.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not your routine"
        )

    if "title" in payload and payload["title"]:
        routine.title = str(payload["title"])[:128]
    if "notes" in payload:
        routine.notes = str(payload["notes"] or "")
    if "frequency" in payload and payload["frequency"]:
        routine.frequency = str(payload["frequency"])[:32]
    if "category" in payload and payload["category"]:
        routine.category = str(payload["category"])[:64]
    if "time" in payload and payload["time"]:
        try:
            routine.time = time.fromisoformat(str(payload["time"]))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="time must be in HH:MM format",
            )
    if "xp" in payload and payload["xp"] is not None:
        try:
            routine.xp = max(0, int(payload["xp"]))
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="xp must be an integer"
            )

    result = None
    if "completed" in payload:
        from app.models.user import UserPreference

        prefs = (
            db.execute(
                select(UserPreference).where(UserPreference.user_id == user.id)
            )
            .scalars()
            .first()
        )
        tz = prefs.timezone if prefs else "UTC"
        result = apply_completion(
            db, user, routine, bool(payload["completed"]), user_timezone=tz
        )
    else:
        db.commit()

    db.refresh(routine)
    payload_out = _serialize(routine)
    if result:
        payload_out.update(
            {
                "xp_awarded": result["xp_awarded"],
                "leveled_up": result["leveled_up"],
                "level": result["level"],
                "current_streak": result["current_streak"],
                "longest_streak": result["longest_streak"],
            }
        )
    return payload_out


@router.delete("/{routine_id}")
def delete_routine(
    routine_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)
) -> dict:
    routine = db.get(Routine, routine_id)
    if routine is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Routine not found")
    if routine.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not your routine"
        )
    db.delete(routine)
    db.commit()
    return {"id": str(routine_id), "deleted": True}
