from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("")
def create_user(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.phone == payload.phone).first()
    if existing:
        # کاربر تکراری -> بروزرسانی اطلاعات و بازگرداندن همان کاربر
        for field, value in payload.dict().items():
            setattr(existing, field, value)
        db.commit()
        db.refresh(existing)
        return {"user_id": existing.id, "message": "اطلاعات کاربر بروزرسانی شد."}

    user = models.User(**payload.dict())
    db.add(user)
    db.commit()
    db.refresh(user)

    sub = models.Subscription(user_id=user.id, plan_id="free_week", plan_title="برنامه هفتگی رایگان")
    db.add(sub)
    db.commit()

    return {"user_id": user.id, "message": "ثبت‌نام با موفقیت انجام شد."}


@router.get("/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="کاربر یافت نشد.")
    return {
        "id": user.id,
        "full_name": user.full_name,
        "phone": user.phone,
        "field": user.field,
        "grade": user.grade,
        "target_major": user.target_major,
        "target_university": user.target_university,
        "daily_hours": user.daily_hours,
    }
