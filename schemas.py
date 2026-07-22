from pydantic import BaseModel, Field
from typing import List, Optional


class UserCreate(BaseModel):
    full_name: str
    phone: str
    field: str
    grade: str
    target_major: Optional[str] = ""
    target_university: Optional[str] = ""
    daily_hours: float = 2.0


class CustomLesson(BaseModel):
    name: str
    topics: Optional[List[str]] = []


class PlanRequest(BaseModel):
    user_id: int
    plan_type: str = Field(default="week")  # week / month / six_month / year
    custom_lessons: Optional[List[CustomLesson]] = []


class StudyLogCreate(BaseModel):
    user_id: int
    hours: float
    subject: Optional[str] = ""


class QuizRequest(BaseModel):
    user_id: int
    subject: str
    lesson: Optional[str] = ""
    grade: str
    question_count: int = 10
    difficulty: str = "متوسط"       # آسان / متوسط / سخت
    question_type: str = "تستی"     # تستی / تشریحی


class QuizSubmit(BaseModel):
    user_id: int
    subject: str
    lesson: Optional[str] = ""
    grade: Optional[str] = ""
    difficulty: Optional[str] = "متوسط"
    answers: List[int]          # اندیس گزینه انتخابی کاربر برای هر سوال
    correct_answers: List[int]  # اندیس گزینه صحیح (از سمت کلاینت برگردانده می‌شود)
    questions: Optional[List[dict]] = []  # متن کامل سوالات برای تحلیل هوش مصنوعی


class EssayAnswer(BaseModel):
    question: str
    student_answer: str
    model_answer: Optional[str] = ""


class EssaySubmit(BaseModel):
    user_id: int
    subject: str
    grade: Optional[str] = ""
    difficulty: Optional[str] = "متوسط"
    answers: List[EssayAnswer]


class SupportCreate(BaseModel):
    name: str
    phone: str
    subject: str
    message: str


class SubscribeRequest(BaseModel):
    user_id: int
    plan_id: str


class ChatPlanRequest(BaseModel):
    user_id: int
    message: str
    days_of_week: Optional[List[str]] = []   # مثلا ["یکشنبه", "سه‌شنبه"]
    start_date: Optional[str] = ""           # YYYY-MM-DD
    end_date: Optional[str] = ""             # YYYY-MM-DD


class ChatPlanPdfRequest(BaseModel):
    plan: dict
