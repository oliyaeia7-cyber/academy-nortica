# نورتیکا (Noortika) 🌙✨
**نوری در مسیر تاریکی تو!**

نسخه تخت (flat) پروژه: همه فایل‌های پایتون مستقیماً کنار `requirements.txt` قرار دارند و
هیچ زیرپوشه‌ای (`app/`, `templates/`, `static/`) وجود ندارد. کدهای HTML، CSS و جاوااسکریپت
همگی داخل کد بک‌اند پایتون (`assets.py` و `pages.py`) قرار گرفته‌اند تا آپلود روی گیت‌هاب و
دیپلوی روی Render ساده‌تر و بی‌خطاتر باشد.

## ساختار فایل‌ها (همه در یک پوشه، بدون زیرپوشه)
```
noortika/
├── main.py                 # ورودی اصلی FastAPI و صفحات HTML
├── database.py              # اتصال SQLite
├── models.py                 # مدل‌های دیتابیس
├── schemas.py                 # مدل‌های ورودی/خروجی API
├── curriculum.py               # سرفصل دروس دهم تا دوازدهم
├── ai_planner.py                # موتور هوشمند ساخت برنامه درسی
├── ai_quiz.py                     # موتور تولید آزمون تستی
├── assets.py                       # CSS + JS + لوگو (به صورت رشته پایتون)
├── pages.py                         # تولید HTML صفحات
├── users_router.py
├── plans_router.py
├── study_router.py
├── exams_router.py
├── leaderboard_router.py
├── support_router.py
├── subscription_router.py
├── requirements.txt
├── Dockerfile
├── render.yaml
└── README.md
```

## چرا این تغییر؟
خطای قبلی `ModuleNotFoundError: No module named 'app'` به این دلیل بود که پوشه `app/`
هنگام آپلود در گیت‌هاب کامل منتقل نشده بود. با تخت کردن ساختار، این ریسک کاملاً از بین می‌رود.

## اجرای محلی
```bash
pip install -r requirements.txt
uvicorn main:app --reload
```
سپس به آدرس `http://localhost:8000` بروید.

## اجرا با Docker
```bash
docker build -t noortika .
docker run -p 8000:8000 noortika
```

## دیپلوی روی Render
1. تمام فایل‌های همین پوشه (نه پوشه‌ی بیرونی، بلکه محتوای داخلش) را در ریشه ریپازیتوری گیت‌هاب آپلود کنید.
2. در Render یک **Web Service** با **Environment: Docker** بسازید.
3. نیازی به تنظیم PORT نیست؛ Render خودش تزریق می‌کند.
4. (اختیاری) متغیر `GEMINI_API_KEY` را برای فعال‌سازی هوش مصنوعی واقعی و رایگان (Gemini از Google AI Studio) اضافه کنید.

## نکات مهم
- پایگاه‌داده SQLite در پوشه `data/` ذخیره می‌شود؛ در پلن رایگان Render با هر ری‌استارت پاک می‌شود (مناسب برای دموی نمادین).
- پرداخت اشتراک کاملاً **نمادین** است.
