import os
import random
from curriculum import get_subjects, ALL_GRADES
import ai_client

FIELD_KEYS = ["عمومی", "ریاضی فیزیک", "علوم تجربی", "علوم انسانی", "فنی حرفه‌ای"]

DIFFICULTY_LABELS = {"آسان": "easy", "متوسط": "medium", "سخت": "hard"}

QUESTION_TEMPLATES = {
    "آسان": [
        "کدام گزینه در مورد «{topic}» در درس {subject} صحیح است؟ (سطح آسان)",
        "تعریف ساده «{topic}» در درس {subject} کدام است؟",
    ],
    "متوسط": [
        "کدام گزینه در ارتباط با «{topic}» در درس {subject} صحیح است؟",
        "مفهوم «{topic}» در درس {subject} به کدام مورد اشاره دارد؟",
        "در بررسی «{topic}» ({subject})، کدام گزینه نادرست است؟",
    ],
    "سخت": [
        "در یک مسئله ترکیبی از «{topic}» در درس {subject}، کدام گزینه با تحلیل دقیق صحیح است؟ (سطح سخت / کنکوری)",
        "کدام یک از موارد زیر جزو نکات کلیدی و کمتردیده‌شده‌ی «{topic}» در {subject} محسوب می‌شود؟",
    ],
}

CORRECT_PATTERNS = [
    "بیانی دقیق و منطبق با تعریف اصلی «{topic}»",
    "کاربرد صحیح مفهوم «{topic}» در حل مسئله",
    "ارتباط درست «{topic}» با سایر مباحث درس {subject}",
]

DISTRACTOR_PATTERNS = [
    "بیانی نادرست و متناقض با تعریف «{topic}»",
    "مفهومی نامرتبط با «{topic}»",
    "برداشت اشتباه رایج درباره «{topic}»",
    "تعریفی مربوط به مبحث دیگری از درس {subject}",
]


def _fallback_topics(subject_name):
    return ["مفاهیم پایه", "نکات تستی مهم", "کاربردهای درس", "جمع‌بندی فصل"]


def _generate_rule_based_quiz(subject, lesson, grade, question_count, difficulty="متوسط"):
    topics = None
    search_order = ([grade] + ALL_GRADES) if grade else ALL_GRADES
    for g in search_order:
        all_subjects = []
        for fk in FIELD_KEYS:
            all_subjects += get_subjects(g, fk)
        for field_subjects in all_subjects:
            if field_subjects["name"] == subject or subject in field_subjects["name"]:
                topics = field_subjects.get("topics")
                break
        if topics:
            break
    if not topics:
        topics = _fallback_topics(subject)

    templates = QUESTION_TEMPLATES.get(difficulty, QUESTION_TEMPLATES["متوسط"])

    questions = []
    for i in range(question_count):
        topic = topics[i % len(topics)]
        template = random.choice(templates)
        question_text = template.format(topic=topic, subject=subject)

        correct_text = random.choice(CORRECT_PATTERNS).format(topic=topic, subject=subject)
        distractors = random.sample(DISTRACTOR_PATTERNS, 3)
        options_texts = [correct_text] + [d.format(topic=topic, subject=subject) for d in distractors]

        correct_index = 0
        indices = list(range(4))
        random.shuffle(indices)
        shuffled_options = [None] * 4
        new_correct_index = 0
        for pos, orig_idx in enumerate(indices):
            shuffled_options[pos] = options_texts[orig_idx]
            if orig_idx == correct_index:
                new_correct_index = pos

        questions.append({
            "id": i + 1,
            "question": question_text,
            "options": shuffled_options,
            "correct_index": new_correct_index,
            "topic": topic,
        })

    return {
        "subject": subject,
        "lesson": lesson or subject,
        "grade": grade,
        "question_count": question_count,
        "difficulty": difficulty,
        "question_type": "تستی",
        "engine": "rule_based",
        "questions": questions,
    }


def _generate_rule_based_essay(subject, lesson, grade, question_count, difficulty="متوسط"):
    topics = None
    search_order = ([grade] + ALL_GRADES) if grade else ALL_GRADES
    for g in search_order:
        all_subjects = []
        for fk in FIELD_KEYS:
            all_subjects += get_subjects(g, fk)
        for field_subjects in all_subjects:
            if field_subjects["name"] == subject or subject in field_subjects["name"]:
                topics = field_subjects.get("topics")
                break
        if topics:
            break
    if not topics:
        topics = _fallback_topics(subject)

    questions = []
    for i in range(question_count):
        topic = topics[i % len(topics)]
        questions.append({
            "id": i + 1,
            "question": f"«{topic}» را در درس {subject} با ذکر جزئیات و مثال توضیح دهید. (سطح {difficulty})",
            "model_answer": f"پاسخ کامل باید تعریف «{topic}»، ارتباط آن با مباحث درس {subject} و حداقل یک مثال کاربردی را شامل شود.",
            "topic": topic,
        })

    return {
        "subject": subject,
        "lesson": lesson or subject,
        "grade": grade,
        "question_count": question_count,
        "difficulty": difficulty,
        "question_type": "تشریحی",
        "engine": "rule_based",
        "questions": questions,
    }


def _try_real_ai_quiz(subject, lesson, grade, question_count, difficulty, question_type, fallback):
    if not ai_client.has_ai_key():
        return fallback
    try:
        grade_note = ""
        if grade == "دوازدهم":
            grade_note = "این دانش‌آموز پایه دوازدهم است؛ سوالات باید کاملاً واقع‌گرایانه و در حد و سطح سوالات کنکور سراسری ایران باشند."
        elif grade in ("هفتم", "هشتم", "نهم"):
            grade_note = f"این دانش‌آموز پایه {grade} (متوسطه اول) است؛ سوالات باید دقیقاً مطابق کتاب درسی همان پایه و مناسب سن دانش‌آموز متوسطه اول باشد، نه سطح کنکور."
        else:
            grade_note = f"این دانش‌آموز پایه {grade} (متوسطه دوم) است؛ سوالات باید مطابق کتاب درسی همین پایه و کمی نزدیک به سطح آزمون‌های جامع باشد."

        difficulty_note = {
            "آسان": "سوالات باید ساده، مفهومی و مقدماتی باشند.",
            "متوسط": "سوالات باید در سطح متوسط و استاندارد کتاب درسی باشند.",
            "سخت": "سوالات باید چالشی، ترکیبی و تحلیلی و در سطح سخت (نزدیک به کنکور) باشند.",
        }.get(difficulty, "سوالات باید در سطح متوسط باشند.")

        if question_type == "تشریحی":
            prompt = (
                f"شما یک معلم متخصص طراحی سوال تشریحی هستید. برای درس «{subject}» پایه {grade} "
                f"({lesson or subject})، دقیقاً {question_count} سوال تشریحی (کوتاه‌پاسخ یا تحلیلی، نه چهارگزینه‌ای) طراحی کن. "
                f"{grade_note} {difficulty_note}\n"
                "خروجی را فقط به صورت JSON خالص (بدون هیچ متن اضافه یا Markdown) با این ساختار بده:\n"
                '[{"question": "متن سوال تشریحی", "model_answer": "پاسخ کامل و صحیح نمونه"}]'
            )
        else:
            prompt = (
                f"شما طراح سوالات آزمون ایران هستید. برای درس «{subject}» پایه {grade} "
                f"({lesson or subject})، دقیقاً {question_count} سوال تستی چهارگزینه‌ای طراحی کن. "
                f"{grade_note} {difficulty_note}\n"
                "خروجی را فقط به صورت JSON خالص (بدون هیچ متن اضافه یا Markdown) با این ساختار بده:\n"
                '[{"question": "متن سوال", "options": ["گزینه۱","گزینه۲","گزینه۳","گزینه۴"], "correct_index": 0}]'
            )

        parsed = ai_client.ask_ai_json(prompt, max_tokens=3000)
        if not parsed:
            return fallback

        questions = []
        if question_type == "تشریحی":
            for i, q in enumerate(parsed[:question_count]):
                questions.append({
                    "id": i + 1,
                    "question": q["question"],
                    "model_answer": q.get("model_answer", ""),
                    "topic": lesson or subject,
                })
        else:
            for i, q in enumerate(parsed[:question_count]):
                questions.append({
                    "id": i + 1,
                    "question": q["question"],
                    "options": q["options"],
                    "correct_index": q["correct_index"],
                    "topic": lesson or subject,
                })

        if not questions:
            return fallback
        return {
            "subject": subject, "lesson": lesson or subject, "grade": grade,
            "difficulty": difficulty, "question_type": question_type,
            "question_count": len(questions), "engine": "gemini_ai", "questions": questions,
        }
    except Exception:
        return fallback


def generate_quiz(subject, lesson, grade, question_count=10, difficulty="متوسط", question_type="تستی"):
    question_count = max(1, min(question_count, 30))
    if difficulty not in ("آسان", "متوسط", "سخت"):
        difficulty = "متوسط"
    if question_type == "تشریحی":
        base = _generate_rule_based_essay(subject, lesson, grade, question_count, difficulty)
    else:
        base = _generate_rule_based_quiz(subject, lesson, grade, question_count, difficulty)
    return _try_real_ai_quiz(subject, lesson, grade, question_count, difficulty, question_type, base)


def analyze_wrong_answers(subject, grade, wrong_items):
    """
    wrong_items: لیستی از دیکشنری {question, options, correct_index, user_index}
    خروجی: تحلیل هوش مصنوعی برای هر سوال غلط، یا تحلیل ساده در صورت نبود کلید API
    """
    if not wrong_items:
        return []

    if not ai_client.has_ai_key():
        result = []
        for item in wrong_items:
            correct_text = item["options"][item["correct_index"]] if item.get("options") else ""
            result.append({
                "question": item["question"],
                "your_answer": item["options"][item["user_index"]] if item.get("options") and 0 <= item.get("user_index", -1) < len(item["options"]) else "بدون پاسخ",
                "correct_answer": correct_text,
                "explanation": f"پاسخ صحیح «{correct_text}» است. لطفاً مبحث مربوط به این سوال را در درس {subject} مجدداً مرور کنید.",
            })
        return result

    import json as _json
    items_text = _json.dumps(wrong_items, ensure_ascii=False)
    prompt = (
        f"شما دستیار آموزشی نورتیکا هستید. دانش‌آموز پایه {grade} در درس «{subject}» به سوالات زیر پاسخ غلط داده است "
        f"(هر آیتم شامل question، options، correct_index و user_index است):\n{items_text}\n\n"
        "برای هر سوال، توضیح بده چرا پاسخ دانش‌آموز غلط بوده و پاسخ صحیح چیست، به زبانی ساده و دلگرم‌کننده که دانش‌آموز اشتباهش را بفهمد و اصلاح کند. "
        "خروجی را فقط JSON خالص با این ساختار بده:\n"
        '[{"question": "...", "your_answer": "...", "correct_answer": "...", "explanation": "..."}]'
    )
    parsed = ai_client.ask_ai_json(prompt, max_tokens=2000)
    if parsed:
        return parsed

    result = []
    for item in wrong_items:
        correct_text = item["options"][item["correct_index"]] if item.get("options") else ""
        result.append({
            "question": item["question"],
            "your_answer": item["options"][item["user_index"]] if item.get("options") and 0 <= item.get("user_index", -1) < len(item["options"]) else "بدون پاسخ",
            "correct_answer": correct_text,
            "explanation": f"پاسخ صحیح «{correct_text}» است. لطفاً مبحث مربوط به این سوال را در درس {subject} مجدداً مرور کنید.",
        })
    return result


def analyze_essay_answers(subject, grade, answers):
    """
    answers: لیست {question, student_answer, model_answer}
    خروجی: تحلیل/نمره هر پاسخ تشریحی
    """
    if not ai_client.has_ai_key():
        result = []
        for a in answers:
            result.append({
                "question": a["question"],
                "student_answer": a["student_answer"],
                "correct_answer": a.get("model_answer", ""),
                "score_percent": 50,
                "explanation": "برای تحلیل دقیق پاسخ تشریحی، کلید هوش مصنوعی باید فعال باشد. این یک ارزیابی پیش‌فرض است.",
            })
        return result

    import json as _json
    items_text = _json.dumps(answers, ensure_ascii=False)
    prompt = (
        f"شما معلم درس «{subject}» پایه {grade} هستید. پاسخ‌های تشریحی زیر را ارزیابی کن "
        f"(هر آیتم شامل question، student_answer و model_answer است):\n{items_text}\n\n"
        "برای هر پاسخ، درصد صحت (0 تا 100)، پاسخ صحیح کامل و توضیح دلگرم‌کننده برای اصلاح اشتباه دانش‌آموز بده. "
        "خروجی را فقط JSON خالص با این ساختار بده:\n"
        '[{"question": "...", "student_answer": "...", "correct_answer": "...", "score_percent": 80, "explanation": "..."}]'
    )
    parsed = ai_client.ask_ai_json(prompt, max_tokens=2500)
    if parsed:
        return parsed

    result = []
    for a in answers:
        result.append({
            "question": a["question"],
            "student_answer": a["student_answer"],
            "correct_answer": a.get("model_answer", ""),
            "score_percent": 50,
            "explanation": "در حال حاضر امکان تحلیل هوشمند این پاسخ وجود نداشت.",
        })
    return result
