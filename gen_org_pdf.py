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

# ── Цвета ──────────────────────────────────────────────
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

# ── Шрифты ─────────────────────────────────────────────
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

# ── Стили ──────────────────────────────────────────────
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

# ── Вспомогательные ────────────────────────────────────
def _fmt(d):
    if not d: return "—"
    try: return datetime.strptime(d[:10],"%Y-%m-%d").strftime("%d.%m.%Y")
    except: return str(d)

def _role(r):
    return {"chair":"Председатель СД","mem":"Член СД","ind":"Независимый директор",
            "rep":"Представитель акционера","psd":"Председатель СД"}.get(r, r or "—")

def _bpos(p):
    return {"chair":"Председатель Правления","deputy":"Заместитель Председателя Правления",
            "mem":"Член Правления","emp":"Сотрудник"}.get(p, p or "—")

def _apos(p):
    return {"head":"Руководитель","emp":"Сотрудник","chair":"Председатель",
            "deputy":"Заместитель руководителя"}.get(p, p or "—")

def _status(dt):
    if not dt: return "Действующий", True
    return "Выбыл", False

def _badge(txt, ok, st):
    sty = st["badge_ok"] if ok else st["badge_no"]
    bg  = C_BADGE_B if ok else C_RED_B
    brd = C_BADGE_BD if ok else C_RED
    t = Table([[Paragraph(txt, sty)]], colWidths=[21*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1), bg),
        ("BOX",(0,0),(-1,-1),0.6, brd),
        ("TOPPADDING",(0,0),(-1,-1),2),
        ("BOTTOMPADDING",(0,0),(-1,-1),2),
        ("LEFTPADDING",(0,0),(-1,-1),3),
        ("RIGHTPADDING",(0,0),(-1,-1),3),
    ]))
    return t

# ── Заголовок раздела ───────────────────────────────────
def _sec(num, title, st, width=USABLE):
    row = [[
        Paragraph(f"{num}.", st["sec_num"]),
        Paragraph(title.upper(), st["sec_title"]),
    ]]
    t = Table(row, colWidths=[10*mm, width-10*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1), C_SECBG),
        ("LEFTPADDING",(0,0),(0,0), 10),
        ("LEFTPADDING",(1,0),(1,0), 2),
        ("RIGHTPADDING",(0,0),(-1,-1), 6),
        ("TOPPADDING",(0,0),(-1,-1),6),
        ("BOTTOMPADDING",(0,0),(-1,-1),6),
        ("LINEBELOW",(0,0),(-1,-1),2.5, C_EMERALD),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ]))
    return [Spacer(1, 5*mm), t, Spacer(1, 3*mm)]

# ── Стиль основной таблицы ─────────────────────────────
def _tbl_base_style(hdr_rows=1):
    return [
        ("BACKGROUND",    (0,0),(-1,hdr_rows-1), C_LGREEN),
        ("TEXTCOLOR",     (0,0),(-1,hdr_rows-1), C_GRAPH),
        ("FONTNAME",      (0,0),(-1,hdr_rows-1), FONT_BOLD),
        ("FONTSIZE",      (0,0),(-1,hdr_rows-1), 8),
        ("ALIGN",         (0,0),(-1,hdr_rows-1), "CENTER"),
        ("TOPPADDING",    (0,0),(-1,hdr_rows-1), 5),
        ("BOTTOMPADDING", (0,0),(-1,hdr_rows-1), 5),
        ("ROWBACKGROUNDS",(0,hdr_rows),(-1,-1), [C_WHITE, C_ROW]),
        ("FONTNAME",      (0,hdr_rows),(-1,-1), FONT),
        ("FONTSIZE",      (0,hdr_rows),(-1,-1), 8.5),
        ("TOPPADDING",    (0,hdr_rows),(-1,-1), 4),
        ("BOTTOMPADDING", (0,hdr_rows),(-1,-1), 4),
        ("LEFTPADDING",   (0,0),(-1,-1), 6),
        ("RIGHTPADDING",  (0,0),(-1,-1), 6),
        ("GRID",          (0,0),(-1,-1), 0.4, C_LINE2),
        ("LINEBELOW",     (0,hdr_rows-1),(-1,hdr_rows-1), 1, C_LINE),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
    ]

# ── Главная функция ─────────────────────────────────────
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

    def _img(path, w, h):
        if os.path.exists(path):
            try: return RLImage(path, width=w, height=h, kind="proportional")
            except: pass
        return ""

    bait_logo = os.path.join(BASE, "static", "baiterek_logo_nobg.png")
    org_logo  = os.path.join(BASE, "static", "logos_clean", org.get("logo",""))

    # ══ ШАПКА ════════════════════════════════════════
    hdr = Table([[
        _img(bait_logo, 30*mm, 15*mm),
        Paragraph("<font color='#CBD5E1' size='18'>│</font>",
                  ParagraphStyle("sep", alignment=TA_CENTER, leading=20)),
        _img(org_logo, 14*mm, 14*mm),
        [Paragraph("Департамент", st["hdr_dept"]),
         Paragraph("корпоративного взаимодействия", st["hdr_dept"])],
        "",
        [Paragraph("Сформировано:", st["hdr_dl"]),
         Paragraph(today, st["hdr_dv"])],
    ]], colWidths=[32*mm, 6*mm, 16*mm, 65*mm, 8*mm, 38*mm])
    hdr.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("ALIGN",(5,0),(5,0),"RIGHT"),
        ("LEFTPADDING",(0,0),(-1,-1),2),
        ("RIGHTPADDING",(0,0),(-1,-1),2),
        ("TOPPADDING",(0,0),(-1,-1),4),
        ("BOTTOMPADDING",(0,0),(-1,-1),6),
        ("LINEBELOW",(0,0),(-1,0),1.5, C_GOLD),
    ]))
    story.append(hdr)
    story.append(Spacer(1,5*mm))
    story.append(Paragraph(org["name"], st["org_name"]))
    story.append(Paragraph("Корпоративный профиль организации", st["org_sub"]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=C_GOLD, spaceBefore=4, spaceAfter=4))
    story.append(Spacer(1,3*mm))

    # ══ ДАШБОРД (5 карточек) ═════════════════════════
    metrics = [
        (len(sd_rows),    "Членов СД",              False),
        (ind_count,       "Независимых\nдиректора",  True),
        (len(board_rows), "Членов\nПравления",       False),
        (len(sess_rows),  "Заседаний СД\n(2026)",    False),
        (total_q,         "Рассмотрено\nвопросов",   True),
    ]
    CW = USABLE / 5

    def _dash_cell(val, lbl, gold):
        ns = st["dash_gold"] if gold else st["dash_num"]
        return Table([
            [Paragraph(str(val), ns)],
            [Paragraph(lbl, st["dash_lbl"])],
        ], colWidths=[CW], style=[
            ("ALIGN",(0,0),(-1,-1),"CENTER"),
            ("TOPPADDING",(0,0),(-1,-1),6),
            ("BOTTOMPADDING",(0,0),(-1,-1),6),
        ])

    dash = Table([[_dash_cell(v,l,g) for v,l,g in metrics]], colWidths=[CW]*5)
    dash.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1), C_GOLD_L),
        ("BOX",(0,0),(-1,-1),0.8, C_LINE),
        ("INNERGRID",(0,0),(-1,-1),0.4, C_LINE),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("TOPPADDING",(0,0),(-1,-1),2),
        ("BOTTOMPADDING",(0,0),(-1,-1),2),
    ]))
    story.append(dash)

    # ══ 1. СОСТАВ СД ═════════════════════════════════
    story += _sec("1", "Состав совета директоров", st)
    if sd_rows:
        r0 = [Paragraph("№",st["th"]), Paragraph("ФИО",st["th_l"]),
              Paragraph("Роль",st["th_l"]),
              Paragraph("Срок полномочий",st["th"]), "", Paragraph("Статус",st["th"])]
        r1 = ["","","", Paragraph("с",st["th"]), Paragraph("по",st["th"]), ""]
        rows = [r0, r1]
        for i, r in enumerate(sd_rows, 1):
            role_txt = _role(r["role"])
            if r["is_independent"] and r["role"] not in ("chair","psd"):
                role_txt = "Независимый директор"
            txt, ok = _status(r["date_to"])
            rows.append([
                Paragraph(str(i), st["td_c"]),
                Paragraph(r["full_name"], st["td_b"]),
                Paragraph(role_txt, st["td"]),
                Paragraph(_fmt(r["date_from"]), st["td_c"]),
                Paragraph(_fmt(r["date_to"]), st["td_c"]),
                _badge(txt, ok, st),
            ])
        s = _tbl_base_style(hdr_rows=2) + [
            ("SPAN",(3,0),(4,0)), ("SPAN",(0,0),(0,1)),
            ("SPAN",(1,0),(1,1)), ("SPAN",(2,0),(2,1)), ("SPAN",(5,0),(5,1)),
            ("TOPPADDING",(0,1),(-1,1),3), ("BOTTOMPADDING",(0,1),(-1,1),3),
        ]
        t = Table(rows, colWidths=[8*mm,57*mm,48*mm,18*mm,18*mm,22*mm], repeatRows=2)
        t.setStyle(TableStyle(s))
        story.append(t)
    else:
        story.append(Paragraph("Данные не внесены", st["empty"]))

    # ══ 2. ПРАВЛЕНИЕ ═════════════════════════════════
    story += _sec("2", "Состав правления", st)
    if board_rows:
        r0 = [Paragraph("№",st["th"]), Paragraph("ФИО",st["th_l"]),
              Paragraph("Должность",st["th_l"]),
              Paragraph("Срок полномочий",st["th"]), "", Paragraph("Статус",st["th"])]
        r1 = ["","","", Paragraph("с",st["th"]), Paragraph("по",st["th"]), ""]
        rows = [r0, r1]
        for i, r in enumerate(board_rows, 1):
            txt, ok = _status(r["date_to"])
            rows.append([
                Paragraph(str(i), st["td_c"]),
                Paragraph(r["full_name"], st["td_b"]),
                Paragraph(_bpos(r["position"]), st["td"]),
                Paragraph(_fmt(r["date_from"]), st["td_c"]),
                Paragraph(_fmt(r["date_to"]), st["td_c"]),
                _badge(txt, ok, st),
            ])
        s = _tbl_base_style(hdr_rows=2) + [
            ("SPAN",(3,0),(4,0)), ("SPAN",(0,0),(0,1)),
            ("SPAN",(1,0),(1,1)), ("SPAN",(2,0),(2,1)), ("SPAN",(5,0),(5,1)),
            ("TOPPADDING",(0,1),(-1,1),3), ("BOTTOMPADDING",(0,1),(-1,1),3),
        ]
        t = Table(rows, colWidths=[8*mm,57*mm,48*mm,18*mm,18*mm,22*mm], repeatRows=2)
        t.setStyle(TableStyle(s))
        story.append(t)
    else:
        story.append(Paragraph("Данные не внесены", st["empty"]))

    # ══ 3. ПОДОТЧЁТНЫЕ СД ════════════════════════════
    story += _sec("3", "Состав служб, подотчётных СД", st)
    if acc_groups:
        for gname, members in acc_groups.items():
            grp = Table([[Paragraph(gname, st["grp_hdr"])]], colWidths=[USABLE])
            grp.setStyle(TableStyle([
                ("BACKGROUND",(0,0),(-1,-1), C_EMERALD2),
                ("LEFTPADDING",(0,0),(-1,-1),10),
                ("TOPPADDING",(0,0),(-1,-1),4),
                ("BOTTOMPADDING",(0,0),(-1,-1),4),
            ]))
            story.append(grp)
            rows = [[Paragraph("№",st["th"]), Paragraph("ФИО",st["th_l"]),
                     Paragraph("Должность",st["th_l"]),
                     Paragraph("с",st["th"]), Paragraph("по",st["th"])]]
            for j, r in enumerate(members, 1):
                rows.append([
                    Paragraph(str(j), st["td_c"]),
                    Paragraph(r["full_name"], st["td_b"]),
                    Paragraph(_apos(r["position"]), st["td"]),
                    Paragraph(_fmt(r["date_from"]), st["td_c"]),
                    Paragraph(_fmt(r["date_to"]), st["td_c"]),
                ])
            t = Table(rows, colWidths=[10*mm, 75*mm, 55*mm, 13*mm, 13*mm])
            t.setStyle(TableStyle(_tbl_base_style() + [("ALIGN",(3,0),(4,-1),"CENTER")]))
            story.append(t)
            story.append(Spacer(1,1.5*mm))
    else:
        story.append(Paragraph("Данные не внесены", st["empty"]))

    # ══ 4. ЗАСЕДАНИЯ СД ══════════════════════════════
    story += _sec("4", "Заседания совета директоров (2026)", st)

    # Мини-инфографика слева + таблица справа
    LEFT_W  = 38*mm
    RIGHT_W = USABLE - LEFT_W - 4*mm

    mini = Table([
        [Paragraph(str(len(sess_rows)), st["mini_num"])],
        [Paragraph("Всего заседаний", st["mini_lbl"])],
        [Spacer(1,3*mm)],
        [Paragraph(str(total_q), st["mini_gold"])],
        [Paragraph("Всего вопросов", st["mini_lbl"])],
    ], colWidths=[LEFT_W])
    mini.setStyle(TableStyle([
        ("ALIGN",(0,0),(-1,-1),"CENTER"),
        ("BACKGROUND",(0,0),(-1,-1), C_SECBG),
        ("BOX",(0,0),(-1,-1),0.5, C_LINE),
        ("TOPPADDING",(0,0),(-1,-1),4),
        ("BOTTOMPADDING",(0,0),(-1,-1),4),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ]))

    if sess_rows:
        rows = [[Paragraph("№",st["th"]), Paragraph("Дата",st["th"]),
                 Paragraph("Формат",st["th"]), Paragraph("Вид",st["th"]),
                 Paragraph("Кол-во вопросов",st["th"])]]
        for i, r in enumerate(sess_rows, 1):
            aq = db.execute("SELECT COUNT(*) FROM sd_agenda_items WHERE session_id=?",
                            (r["id"],)).fetchone()[0]
            rows.append([
                Paragraph(str(i), st["td_c"]),
                Paragraph(_fmt(r["session_date"]), st["td_c"]),
                Paragraph(r["format"] or "—", st["td_c"]),
                Paragraph(r["order_type"] or "—", st["td_c"]),
                Paragraph(str(aq) if aq else "—", st["td_c"]),
            ])
        sess_tbl = Table(rows, colWidths=[9*mm, 22*mm, 28*mm, 28*mm, RIGHT_W-9*mm-22*mm-28*mm-28*mm])
        sess_tbl.setStyle(TableStyle(_tbl_base_style() + [("ALIGN",(0,0),(-1,-1),"CENTER")]))
    else:
        sess_tbl = Paragraph("Заседания не зафиксированы", st["empty"])

    two = Table([[mini, Spacer(4*mm,1), sess_tbl]], colWidths=[LEFT_W, 4*mm, RIGHT_W])
    two.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("LEFTPADDING",(0,0),(-1,-1),0),
        ("RIGHTPADDING",(0,0),(-1,-1),0),
        ("TOPPADDING",(0,0),(-1,-1),0),
        ("BOTTOMPADDING",(0,0),(-1,-1),0),
    ]))
    story.append(two)

    # ══ ФУТЕР ════════════════════════════════════════
    story.append(Spacer(1,6*mm))
    story.append(HRFlowable(width="100%", thickness=1, color=C_LINE))
    story.append(Spacer(1,2*mm))
    footer = Table([[
        _img(bait_logo, 22*mm, 11*mm),
        [Paragraph("АО «НИХ «Байтерек»", st["footer_b"]),
         Paragraph("Департамент корпоративного взаимодействия", st["footer_s"])],
        Paragraph(f"Сформировано: {today}", st["footer_r"]),
    ]], colWidths=[26*mm, 100*mm, 39*mm])
    footer.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("ALIGN",(2,0),(2,0),"RIGHT"),
        ("LEFTPADDING",(0,0),(-1,-1),2),
        ("RIGHTPADDING",(0,0),(-1,-1),2),
    ]))
    story.append(footer)

    doc.build(story)
    return buf.getvalue()
