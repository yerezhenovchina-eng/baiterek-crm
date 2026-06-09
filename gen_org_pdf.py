# gen_org_pdf.py — Корпоративный профиль организации v4
import io, os
from datetime import datetime
from collections import OrderedDict
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image as RLImage, KeepTogether
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ── Цвета ──────────────────────────────────────────────────
C_EMERALD  = colors.HexColor("#004D40")   # глубокий изумрудный (основной)
C_EMERALD2 = colors.HexColor("#00695C")   # чуть светлее
C_GOLD     = colors.HexColor("#C8A84B")   # золото
C_GOLD_L   = colors.HexColor("#FFF8E1")   # светлое золото (фон дашборда)
C_GRAPH    = colors.HexColor("#1E293B")   # графитовый (основной текст)
C_BG       = colors.HexColor("#F8FAFC")   # светло-серый фон
C_WHITE    = colors.white
C_LGREEN   = colors.HexColor("#E8F5E9")   # светло-зелёный (шапка таблиц)
C_ROW      = colors.HexColor("#F1F5F1")   # чётная строка
C_LINE     = colors.HexColor("#D4C8A0")   # линии таблиц
C_LINE2    = colors.HexColor("#E2E8F0")   # тонкие разделители
C_BADGE_T  = colors.HexColor("#1B5E20")   # текст бэджа "Действующий"
C_BADGE_B  = colors.HexColor("#E8F5E9")   # фон бэджа
C_BADGE_BD = colors.HexColor("#66BB6A")   # граница бэджа
C_RED      = colors.HexColor("#B71C1C")
C_RED_B    = colors.HexColor("#FFEBEE")
C_GRAY     = colors.HexColor("#64748B")
C_MGRAY    = colors.HexColor("#94A3B8")
C_SECBG    = colors.HexColor("#F0F7F4")   # фон заголовка раздела

W, H = A4
USABLE = 165*mm

# ── Шрифты ─────────────────────────────────────────────────
def _register_fonts():
    base = os.path.dirname(__file__)
    FONTS_DIR = os.path.join(base, "static", "fonts")
    # Приоритет: Carlito > Liberation Sans > DejaVu
    candidates = [
        ("Carlito-Regular.ttf",      "Carlito-Bold.ttf"),
        ("LiberationSans-Regular.ttf","LiberationSans-Bold.ttf"),
        ("DejaVuSans.ttf",            "DejaVuSans-Bold.ttf"),
    ]
    system = "/usr/share/fonts/truetype"
    sys_candidates = [
        (f"{system}/crosextra/Carlito-Regular.ttf",       f"{system}/crosextra/Carlito-Bold.ttf"),
        (f"{system}/liberation/LiberationSans-Regular.ttf",f"{system}/liberation/LiberationSans-Bold.ttf"),
        (f"{system}/dejavu/DejaVuSans.ttf",                f"{system}/dejavu/DejaVuSans-Bold.ttf"),
    ]
    all_candidates = [(os.path.join(FONTS_DIR,r), os.path.join(FONTS_DIR,b)) for r,b in candidates]
    all_candidates += sys_candidates
    for r, b in all_candidates:
        if os.path.exists(r) and os.path.exists(b):
            try:
                pdfmetrics.registerFont(TTFont("CF", r))
                pdfmetrics.registerFont(TTFont("CF-Bold", b))
                return "CF", "CF-Bold"
            except: continue
    return "Helvetica", "Helvetica-Bold"

FONT, FONT_BOLD = _register_fonts()

# ── Стили ──────────────────────────────────────────────────
def _S(name, **kw):
    d = dict(fontName=FONT, fontSize=9, textColor=C_GRAPH, leading=13)
    d.update(kw)
    return ParagraphStyle(name, **d)

def _styles():
    return {
        "org_name":   _S("on", fontName=FONT_BOLD, fontSize=20, textColor=C_EMERALD, leading=26),
        "org_sub":    _S("os", fontSize=10, textColor=C_GOLD, leading=14),
        "hdr_dept":   _S("hd", fontSize=8, textColor=C_GRAY, leading=11),
        "hdr_dl":     _S("hdl", fontSize=7.5, textColor=C_MGRAY, alignment=TA_RIGHT, leading=10),
        "hdr_dv":     _S("hdv", fontName=FONT_BOLD, fontSize=11, textColor=C_EMERALD, alignment=TA_RIGHT, leading=14),
        "dash_num":   _S("dn", fontName=FONT_BOLD, fontSize=22, textColor=C_EMERALD, alignment=TA_CENTER, leading=26),
        "dash_gold":  _S("dg", fontName=FONT_BOLD, fontSize=22, textColor=C_GOLD, alignment=TA_CENTER, leading=26),
        "dash_lbl":   _S("dl", fontSize=7.5, textColor=C_GRAY, alignment=TA_CENTER, leading=10),
        "sec_num":    _S("sn", fontName=FONT_BOLD, fontSize=10, textColor=C_EMERALD, leading=14),
        "sec_title":  _S("st", fontName=FONT_BOLD, fontSize=10, textColor=C_GRAPH, leading=14),
        "th":         _S("th", fontName=FONT_BOLD, fontSize=8, textColor=C_GRAPH, alignment=TA_CENTER, leading=11),
        "th_l":       _S("thl", fontName=FONT_BOLD, fontSize=8, textColor=C_GRAPH, leading=11),
        "td":         _S("td", fontSize=8.5, textColor=C_GRAPH, leading=11),
        "td_b":       _S("tdb", fontName=FONT_BOLD, fontSize=8.5, textColor=C_GRAPH, leading=11),
        "td_c":       _S("tdc", fontSize=8.5, textColor=C_GRAPH, alignment=TA_CENTER, leading=11),
        "badge_ok":   _S("bok", fontName=FONT_BOLD, fontSize=7.5, textColor=C_BADGE_T, alignment=TA_CENTER, leading=10),
        "badge_no":   _S("bno", fontName=FONT_BOLD, fontSize=7.5, textColor=C_RED, alignment=TA_CENTER, leading=10),
        "empty":      _S("emp", fontSize=8.5, textColor=C_MGRAY, alignment=TA_CENTER),
        "mini_num":   _S("mn", fontName=FONT_BOLD, fontSize=26, textColor=C_EMERALD, alignment=TA_CENTER, leading=30),
        "mini_gold":  _S("mg", fontName=FONT_BOLD, fontSize=26, textColor=C_GOLD, alignment=TA_CENTER, leading=30),
        "mini_lbl":   _S("ml", fontSize=8, textColor=C_GRAY, alignment=TA_CENTER, leading=11),
        "grp_hdr":    _S("gh", fontName=FONT_BOLD, fontSize=8.5, textColor=C_WHITE, leading=11),
        "footer_b":   _S("fb", fontName=FONT_BOLD, fontSize=8, textColor=C_EMERALD, leading=11),
        "footer_s":   _S("fs", fontSize=7.5, textColor=C_GRAY, leading=11),
        "footer_r":   _S("fr", fontName=FONT_BOLD, fontSize=8, textColor=C_GRAPH, alignment=TA_RIGHT, leading=11),
    }

def generate_org_pdf(org: dict, db) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
        leftMargin=15*mm, rightMargin=15*mm,
        topMargin=10*mm, bottomMargin=12*mm,
        title=f"Корпоративный профиль — {org['short']}")

    st = _styles()
    story = []
    org_id = org["id"]
    today  = datetime.now().strftime("%d.%m.%Y")
    BASE   = os.path.dirname(__file__)

    # ── Данные ────────────────────────────────────────
    sd_rows = db.execute(
        "SELECT full_name, role, is_independent, date_from, date_to "
        "FROM sd_members WHERE org_id=? ORDER BY date_to IS NULL DESC, date_from",
        (org_id,)).fetchall()
    board_rows = db.execute(
        "SELECT full_name, position, date_from, date_to "
        "FROM board_members WHERE org_id=? ORDER BY date_to IS NULL DESC, date_from",
        (org_id,)).fetchall()
    sess_rows = db.execute(
        "SELECT id, session_date, format, order_type FROM sd_sessions "
        "WHERE org_id=? ORDER BY session_date DESC", (org_id,)).fetchall()
    acc_rows = db.execute(
        "SELECT full_name, position, org_name, date_from, date_to FROM accountable "
        "WHERE org_id=? ORDER BY org_name, "
        "CASE position WHEN 'head' THEN 0 WHEN 'chair' THEN 0 WHEN 'deputy' THEN 1 ELSE 2 END, full_name",
        (org_id,)).fetchall()

    total_q   = sum(db.execute("SELECT COUNT(*) FROM sd_agenda_items WHERE session_id=?",
                               (r["id"],)).fetchone()[0] for r in sess_rows)
    ind_count = sum(1 for r in sd_rows if r["is_independent"] or r["role"] == "ind")
    acc_groups = OrderedDict()
    for r in acc_rows:
        acc_groups.setdefault(r["org_name"] or "Без службы", []).append(r)

    story.append(Paragraph(org["name"], st["org_name"]))
    story.append(Paragraph("Корпоративный профиль организации", st["org_sub"]))
    story.append(Spacer(1, 5*mm))

    doc.build(story)
    return buf.getvalue()