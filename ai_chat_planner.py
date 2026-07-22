import os
import json as _json
from datetime import datetime, timedelta

from curriculum import get_subjects, get_weight_for_subject
import ai_client

# نگاشت weekday پایتون (دوشنبه=0) به نام روز هفته فارسی
PY_WEEKDAY_TO_FA = {
    0: "دوشنبه",
    1: "سه‌شنبه",
    2: "چهارشنبه",
    3: "پنجشنبه",
    4: "جمعه",
    5: "شنبه",
    6: "یکشنبه",
}

FIELD_KEYS = ["عمومی", "ریاضی فیزیک", "علوم تجربی", "علوم انسانی", "فنی حرفه‌ای"]


def _all_user_subjects(grade, field):
    subjects = list(get_subjects(grade, field))
    if not subjects:
        # اگر رشته دقیق پیدا نشد، در همه گروه‌های همان پایه بگرد
        for fk in FIELD_KEYS:
            subjects = list(get_subjects(grade, fk))
            if subjects:
                break
    return subjects


def _detect_focus_subjects(message, grade, field):
    """از روی متن آزاد کاربر، درس(های) مدنظر را پیدا می‌کند."""
    all_subjects = _all_user_subjects(grade, field)
    if not all_subjects:
        return []
    found = []
    msg = (message or "").strip()
    for s in all_subjects:
        base_name = s["name"].split(" (")[0].strip()
        if base_name and base_name in msg:
            found.append(s)
    return found or all_subjects


def _default_analysis(user, message, focus_subjects):
    names = "، ".join(s["name"] for s in focus_subjects[:4]) or "دروس اصلی"
    return (
        f"بر اساس درخواستت، یک برنامه مطالعاتی برای {names} با توجه به پایه {user.grade} "
        f"و ساعت مطالعه روزانه {user.daily_hours or 2} ساعت طراحی کردم. برنامه به‌گونه‌ای چیده شده که "
        "هم مباحث جدید پوشش داده بشه و هم زمان کافی برای مرور و حل تست در نظر گرفته بشه."
    )


def _default_subject_distribution(focus_subjects):
    if not focus_subjects:
        return [{"subject": "مرور عمومی", "percent": 100}]
    equal = round(100 / len(focus_subjects))
    dist = [{"subject": s["name"], "percent": equal} for s in focus_subjects]
    diff = 100 - sum(d["percent"] for d in dist)
    if dist:
        dist[0]["percent"] += diff
    return dist


def _default_growth_table(weeks_count):
    weeks_count = max(1, weeks_count)
    table = []
    start = 30
    step = max(5, int(50 / weeks_count))
    for w in range(1, weeks_count + 1):
        table.append({
            "week": w,
            "expected_mastery_percent": min(95, start + step * (w - 1)),
            "note": "مرور، تمرین و رفع اشکال" if w > 1 else "شروع و آشنایی با مباحث",
        })
    return table


def _try_ai_chat_analysis(user, message, focus_subjects, weeks_count):
    fallback = {
        "analysis": _default_analysis(user, message, focus_subjects),
        "subject_distribution": _default_subject_distribution(focus_subjects),
        "growth_table": _default_growth_table(weeks_count),
        "engine": "rule_based",
    }
    if not ai_client.has_ai_key():
        return fallback

    prompt = (
        "شما دستیار هوشمند برنامه‌ریزی تحصیلی نورتیکا هستی و مثل یک چت هوشمند به دانش‌آموز پاسخ می‌دهی.\n"
        f"مشخصات دانش‌آموز: پایه {user.grade}، رشته {user.field}، رشته هدف دانشگاهی {user.target_major or 'مشخص نشده'}، "
        f"ساعت مطالعه روزانه {user.daily_hours or 2} ساعت.\n"
        f"درخواست دانش‌آموز (متن آزاد): «{message}»\n"
        f"دروس شناسایی‌شده مرتبط با درخواست: {', '.join(s['name'] for s in focus_subjects) or 'نامشخص'}\n"
        f"بازه برنامه تقریباً {weeks_count} هفته است.\n\n"
        "خروجی را فقط به‌صورت JSON خالص (بدون Markdown و بدون متن اضافه) با این ساختار دقیق بده:\n"
        '{"analysis": "یک پاراگراف تحلیلی و انگیزشی درباره این برنامه، مثل پاسخ یک مشاور در چت",'
        ' "subject_distribution": [{"subject": "نام درس", "percent": عدد}],'
        ' "growth_table": [{"week": 1, "expected_mastery_percent": عدد, "note": "توضیح کوتاه پیشرفت آن هفته"}]}'
    )
    parsed = ai_client.ask_ai_json(prompt, max_tokens=1800)
    if not parsed:
        return fallback

    parsed["engine"] = "gemini_ai"
    if not parsed.get("subject_distribution"):
        parsed["subject_distribution"] = fallback["subject_distribution"]
    if not parsed.get("growth_table"):
        parsed["growth_table"] = fallback["growth_table"]
    return parsed


def _iter_dates(start_date, end_date):
    cur = start_date
    while cur <= end_date:
        yield cur
        cur += timedelta(days=1)


def _build_dated_schedule(user, focus_subjects, days_of_week, start_date, end_date):
    subjects = focus_subjects or [{"name": "مرور عمومی", "topics": []}]
    weighted = []
    for s in subjects:
        w = get_weight_for_subject(s["name"], user.target_major or "")
        weighted.append({"name": s["name"], "topics": s.get("topics") or ["مرور کلی درس"], "weight": w})
    weighted.sort(key=lambda x: x["weight"], reverse=True)

    daily_hours = user.daily_hours or 2.0
    topic_cursor = {s["name"]: 0 for s in weighted}

    schedule = []
    day_counter = 0
    for d in _iter_dates(start_date, end_date):
        fa_day = PY_WEEKDAY_TO_FA[d.weekday()]
        if days_of_week and fa_day not in days_of_week:
            continue
        day_counter += 1
        subjects_per_day = min(len(weighted), 3) or 1
        chosen = []
        for i in range(subjects_per_day):
            s = weighted[(day_counter + i) % len(weighted)]
            topic_list = s["topics"] or ["مرور کلی درس"]
            idx = topic_cursor[s["name"]] % len(topic_list)
            topic_cursor[s["name"]] += 1
            chosen.append({
                "subject": s["name"],
                "focus": topic_list[idx],
                "minutes": int((daily_hours * 60) / subjects_per_day),
            })
        schedule.append({
            "date": d.strftime("%Y-%m-%d"),
            "day_name": fa_day,
            "type": "آزمون و جمع‌بندی" if day_counter % 7 == 0 else "مطالعه",
            "items": chosen,
        })
    return schedule


def generate_chat_plan(user, message, days_of_week=None, start_date_str=None, end_date_str=None):
    focus_subjects = _detect_focus_subjects(message, user.grade, user.field)

    today = datetime.utcnow().date()
    if start_date_str:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    else:
        start_date = today
    if end_date_str:
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    else:
        end_date = start_date + timedelta(days=6)

    if end_date < start_date:
        start_date, end_date = end_date, start_date

    total_span_days = (end_date - start_date).days + 1
    weeks_count = max(1, round(total_span_days / 7))

    ai_part = _try_ai_chat_analysis(user, message, focus_subjects, weeks_count)
    schedule = _build_dated_schedule(user, focus_subjects, days_of_week, start_date, end_date)

    return {
        "message": message,
        "grade": user.grade,
        "field": user.field,
        "focus_subjects": [s["name"] for s in focus_subjects],
        "days_of_week": days_of_week or [],
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "analysis": ai_part.get("analysis", ""),
        "subject_distribution": ai_part.get("subject_distribution", []),
        "growth_table": ai_part.get("growth_table", []),
        "engine": ai_part.get("engine", "rule_based"),
        "schedule": schedule,
    }
