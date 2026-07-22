"""
تولید خروجی PDF فارسی (راست‌به‌چپ) برای برنامه مطالعاتی.
از reportlab برای ساخت PDF و از arabic_reshaper + python-bidi برای
شکل‌دهی درست حروف فارسی/عربی استفاده می‌شود (چون reportlab به‌صورت
پیش‌فرض حروف فارسی را به‌هم‌چسبیده و جهت‌دار نمایش نمی‌دهد).
"""
import os
import io
import urllib.request

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)

import arabic_reshaper
from bidi.algorithm import get_display

FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
FONT_REGULAR_PATH = os.path.join(FONT_DIR, "Vazirmatn-Regular.ttf")
FONT_BOLD_PATH = os.path.join(FONT_DIR, "Vazirmatn-Bold.ttf")

FONT_URLS = {
    FONT_REGULAR_PATH: "https://raw.githubusercontent.com/rastikerdar/vazirmatn/master/fonts/ttf/Vazirmatn-Regular.ttf",
    FONT_BOLD_PATH: "https://raw.githubusercontent.com/rastikerdar/vazirmatn/master/fonts/ttf/Vazirmatn-Bold.ttf",
}

FONT_NAME = "Vazirmatn"
FONT_NAME_BOLD = "Vazirmatn-Bold"

_fonts_ready = False


def _ensure_fonts():
    """در صورت نبود فونت فارسی روی دیسک، آن را دانلود و رجیستر می‌کند.
    اگر دانلود ممکن نبود، از فونت پیش‌فرض Helvetica استفاده می‌شود
    (در این حالت حروف فارسی ممکن است درست نمایش داده نشوند)."""
    global _fonts_ready
    if _fonts_ready:
        return

    os.makedirs(FONT_DIR, exist_ok=True)
    for path, url in FONT_URLS.items():
        if not os.path.exists(path):
            try:
                urllib.request.urlretrieve(url, path)
            except Exception:
                pass

    try:
        if os.path.exists(FONT_REGULAR_PATH):
            pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_REGULAR_PATH))
        if os.path.exists(FONT_BOLD_PATH):
            pdfmetrics.registerFont(TTFont(FONT_NAME_BOLD, FONT_BOLD_PATH))
    except Exception:
        pass

    _fonts_ready = True


def _active_font():
    _ensure_fonts()
    if os.path.exists(FONT_REGULAR_PATH):
        return FONT_NAME
    return "Helvetica"


def _active_font_bold():
    _ensure_fonts()
    if os.path.exists(FONT_BOLD_PATH):
        return FONT_NAME_BOLD
    return "Helvetica-Bold"


def fa(text):
    """متن فارسی را برای نمایش درست راست‌به‌چپ در PDF آماده می‌کند."""
    if text is None:
        return ""
    text = str(text)
    try:
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except Exception:
        return text


def build_plan_pdf(plan: dict) -> bytes:
    _ensure_fonts()
    font_name = _active_font()
    font_bold = _active_font_bold()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=18 * mm, leftMargin=18 * mm, topMargin=16 * mm, bottomMargin=16 * mm,
    )

    title_style = ParagraphStyle(
        "TitleFa", fontName=font_bold, fontSize=18, alignment=TA_CENTER,
        textColor=colors.HexColor("#7c3aed"), spaceAfter=10,
    )
    heading_style = ParagraphStyle(
        "HeadingFa", fontName=font_bold, fontSize=13, alignment=TA_RIGHT,
        textColor=colors.HexColor("#201a3a"), spaceBefore=14, spaceAfter=6,
    )
    normal_style = ParagraphStyle(
        "NormalFa", fontName=font_name, fontSize=10.5, alignment=TA_RIGHT,
        textColor=colors.HexColor("#201a3a"), leading=16,
    )
    cell_style = ParagraphStyle(
        "CellFa", fontName=font_name, fontSize=9.5, alignment=TA_RIGHT, leading=14,
    )
    cell_style_bold = ParagraphStyle(
        "CellFaBold", fontName=font_bold, fontSize=9.5, alignment=TA_CENTER,
        textColor=colors.white, leading=14,
    )

    story = []
    story.append(Paragraph(fa("برنامه مطالعاتی نورتیکا"), title_style))
    story.append(Paragraph(
        fa(f"پایه: {plan.get('grade', '')} — رشته: {plan.get('field', '')} — بازه: {plan.get('start_date', '')} تا {plan.get('end_date', '')}"),
        normal_style,
    ))
    story.append(Spacer(1, 8))

    if plan.get("analysis"):
        story.append(Paragraph(fa("تحلیل و توصیه هوش مصنوعی نورتیکا"), heading_style))
        story.append(Paragraph(fa(plan["analysis"]), normal_style))

    dist = plan.get("subject_distribution") or []
    if dist:
        story.append(Paragraph(fa("توزیع دروس در برنامه"), heading_style))
        data = [[Paragraph(fa("درصد"), cell_style_bold), Paragraph(fa("درس"), cell_style_bold)]]
        for d in dist:
            data.append([
                Paragraph(fa(f"{d.get('percent', 0)}٪"), cell_style),
                Paragraph(fa(d.get("subject", "")), cell_style),
            ])
        t = Table(data, colWidths=[40 * mm, 110 * mm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7c3aed")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d8d0f0")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f6f5ff")]),
        ]))
        story.append(t)

    growth = plan.get("growth_table") or []
    if growth:
        story.append(Paragraph(fa("جدول رشد پیش‌بینی‌شده"), heading_style))
        data = [[
            Paragraph(fa("توضیح"), cell_style_bold),
            Paragraph(fa("درصد تسلط"), cell_style_bold),
            Paragraph(fa("هفته"), cell_style_bold),
        ]]
        for g in growth:
            data.append([
                Paragraph(fa(g.get("note", "")), cell_style),
                Paragraph(fa(f"{g.get('expected_mastery_percent', 0)}٪"), cell_style),
                Paragraph(fa(str(g.get("week", ""))), cell_style),
            ])
        t = Table(data, colWidths=[80 * mm, 35 * mm, 35 * mm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ec4899")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#f4d6e6")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fff5fa")]),
        ]))
        story.append(t)

    schedule = plan.get("schedule") or []
    if schedule:
        story.append(Paragraph(fa("برنامه روز‌به‌روز"), heading_style))
        data = [[
            Paragraph(fa("زمان (دقیقه)"), cell_style_bold),
            Paragraph(fa("مبحث"), cell_style_bold),
            Paragraph(fa("درس"), cell_style_bold),
            Paragraph(fa("تاریخ / روز"), cell_style_bold),
        ]]
        for day in schedule:
            items = day.get("items") or []
            if not items:
                continue
            first = True
            for it in items:
                date_cell = f"{day.get('date','')} ({day.get('day_name','')})" if first else ""
                data.append([
                    Paragraph(fa(str(it.get("minutes", ""))), cell_style),
                    Paragraph(fa(it.get("focus", "")), cell_style),
                    Paragraph(fa(it.get("subject", "")), cell_style),
                    Paragraph(fa(date_cell), cell_style),
                ])
                first = False
        t = Table(data, colWidths=[25 * mm, 50 * mm, 40 * mm, 35 * mm], repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7c3aed")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d8d0f0")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f6f5ff")]),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
        ]))
        story.append(t)

    story.append(Spacer(1, 14))
    story.append(Paragraph(fa("نورتیکا، نوری در مسیر تاریکی تو!"), normal_style))

    doc.build(story)
    return buffer.getvalue()
