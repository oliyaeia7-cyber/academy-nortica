from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(200), nullable=False)
    phone = Column(String(20), nullable=False, unique=True, index=True)
    field = Column(String(100), nullable=False)          # گروه تحصیلی (رشته)
    grade = Column(String(20), nullable=False)            # پایه (دهم/یازدهم/دوازدهم)
    target_major = Column(String(200), nullable=True)     # رشته هدف دانشگاهی
    target_university = Column(String(200), nullable=True)
    daily_hours = Column(Float, default=2.0)              # تعداد ساعت مطالعه روزانه
    created_at = Column(DateTime, default=datetime.utcnow)

    study_logs = relationship("StudyLog", back_populates="user", cascade="all, delete-orphan")
    exam_results = relationship("ExamResult", back_populates="user", cascade="all, delete-orphan")
    plans = relationship("StudyPlan", back_populates="user", cascade="all, delete-orphan")
    subscription = relationship("Subscription", back_populates="user", uselist=False, cascade="all, delete-orphan")


class StudyPlan(Base):
    __tablename__ = "study_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    plan_type = Column(String(20))   # week / month / six_month / year
    content = Column(JSON)           # ساختار کامل برنامه (روز به روز)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="plans")


class StudyLog(Base):
    __tablename__ = "study_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    hours = Column(Float, default=0.0)
    subject = Column(String(150), nullable=True)
    logged_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="study_logs")


class ExamResult(Base):
    __tablename__ = "exam_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    subject = Column(String(150))
    lesson = Column(String(150), nullable=True)
    question_count = Column(Integer)
    correct_count = Column(Integer)
    score_percent = Column(Float)
    taken_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="exam_results")


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150))
    phone = Column(String(20))
    subject = Column(String(200))
    message = Column(Text)
    status = Column(String(20), default="در حال بررسی")
    created_at = Column(DateTime, default=datetime.utcnow)


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    plan_id = Column(String(30), default="free_week")
    plan_title = Column(String(100), default="برنامه هفتگی رایگان")
    is_active = Column(Integer, default=1)
    started_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="subscription")
