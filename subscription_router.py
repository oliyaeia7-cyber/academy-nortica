from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas

router = APIRouter(prefix="/api/subscription", tags=["subscription"])

PLANS = [
    {"id": "free_week", "title": "برنامه هفتگی", "duration": "week",
     "description": "برنامه‌ای ساده و جزئی برای یک هفته", "price": 0, "price_label": "رایگان"},
    {"id": "month", "title": "برنامه یک ماهه", "duration": "month",
     "description": "برنامه دقیق‌تر با جزئیات بیشتر", "price": 500000, "price_label": "۵۰۰,۰۰۰ تومان"},
    {"id": "six_month", "title": "برنامه شش ماهه", "duration": "six_month",
     "description": "برنامه‌ای عالی و کامل با موتور هوش مصنوعی دقیق‌تر", "price": 1000000, "price_label": "۱,۰۰۰,۰۰۰ تومان"},
    {"id": "year", "title": "برنامه یک ساله", "duration": "year",
     "description": "برنامه بسیار قدرتمند همراه با پنل اختصاصی", "price": 2000000, "price_label": "۲,۰۰۰,۰۰۰ تومان"},
]


@router.get("/plans")
def list_plans():
    return {"plans": PLANS}


@router.post("/subscribe")
def subscribe(payload: schemas.SubscribeRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="کاربر یافت نشد.")

    plan = next((p for p in PLANS if p["id"] == payload.plan_id), None)
    if not plan:
        raise HTTPException(status_code=400, detail="پلن نامعتبر است.")

    sub = db.query(models.Subscription).filter(models.Subscription.user_id == user.id).first()
    if not sub:
        sub = models.Subscription(user_id=user.id)
        db.add(sub)

    sub.plan_id = plan["id"]
    sub.plan_title = plan["title"]
    sub.is_active = 1
    db.commit()

    return {
        "message": f"پرداخت نمادین برای «{plan['title']}» با موفقیت انجام شد. (این یک تراکنش آزمایشی است و مبلغ واقعی کسر نشده است)",
        "plan": plan,
    }


@router.get("/status/{user_id}")
def subscription_status(user_id: int, db: Session = Depends(get_db)):
    sub = db.query(models.Subscription).filter(models.Subscription.user_id == user_id).first()
    if not sub:
        return {"plan_id": "free_week", "plan_title": "برنامه هفتگی"}
    return {"plan_id": sub.plan_id, "plan_title": sub.plan_title}
