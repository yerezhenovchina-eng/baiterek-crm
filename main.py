# main.py — НИХ Байтерек corporate dashboard
import io, bcrypt, os
from datetime import datetime
from fastapi import Query, FastAPI, Request, Form, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from itsdangerous import URLSafeTimedSerializer, BadSignature
import uvicorn

from database import init_db, get_db, ORGANIZATIONS, ORG_MAP, ORG_BY_USERNAME, now

app = FastAPI(title="НИХ Байтерек — Корпоративная карточка")
templates = Jinja2Templates(directory="templates")

# Static files (logos etc.)
if os.path.isdir("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")
SECRET_KEY = "baiterek-secret-2024"
SESSION_MAX_AGE = 8 * 3600
serializer = URLSafeTimedSerializer(SECRET_KEY)

def fmt(d):
    if not d: return "—"
    try: return datetime.fromisoformat(d).strftime("%d.%m.%Y")
    except: return d

templates.env.globals["fmt"] = fmt
templates.env.globals["ORGANIZATIONS"] = ORGANIZATIONS
templates.env.globals["ORG_MAP"] = ORG_MAP

# ── Auth helpers ───────────────────────────────────────────
def get_session(request: Request):
    token = request.cookies.get("session")
    if not token: return None
    try: return serializer.loads(token, max_age=SESSION_MAX_AGE)
    except BadSignature: return None

def can_edit(session: dict, org_id: int) -> bool:
    """User can edit if admin or curator of this org."""
    if not session: return False
    if session.get("role") == "admin": return True
    allowed = ORG_BY_USERNAME.get(session.get("username"), [])
    return org_id in allowed

def can_edit_kpd(session: dict, employee: str) -> bool:
    """Admin can edit all KPD. Users can edit only their own and ДКВ."""
    if not session: return False
    if session.get("role") == "admin": return True
    if employee == "ДКВ": return True
    username = session.get("username", "")
    _kpd_name = {"akbota": "Акбота", "dinara": "Динара", "ilmira": "Ильмира",
                 "zhanna": "Жанна", "ardak": "Ардак", "chingiz": "Чингиз"}
    my_kpd_name = _kpd_name.get(username.lower(), username)
    return employee == my_kpd_name

templates.env.globals["can_edit"] = can_edit
templates.env.globals["can_edit_kpd"] = can_edit_kpd

def require_session(request: Request):
    s = get_session(request)
    if not s: raise HTTPException(302, headers={"Location": "/login"})
    return s

def redir(url): return RedirectResponse(url, status_code=302)

# ── Login / Logout ─────────────────────────────────────────
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: str = ""):
    return templates.TemplateResponse("login.html", {"request": request, "error": error})

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    db = get_db()
    row = db.execute("SELECT * FROM users WHERE username=? AND is_active=1", (username,)).fetchone()
    db.close()
    if not row or not bcrypt.checkpw(password.encode(), row["password_hash"].encode()):
        return redir("/login?error=Неверный+логин+или+пароль")
    token = serializer.dumps({"uid": row["id"], "username": row["username"],
                               "role": row["role"], "full_name": row["full_name"]})
    resp = redir("/")
    resp.set_cookie("session", token, httponly=True, max_age=SESSION_MAX_AGE)
    return resp

@app.get("/logout")
async def logout():
    resp = redir("/login")
    resp.delete_cookie("session")
    return resp

# ── Смена пароля пользователем ─────────────────────────────
@app.get("/change-password", response_class=HTMLResponse)
async def change_password_page(request: Request, error: str = "", success: str = ""):
    s = get_session(request)
    if not s: return redir("/login")
    return templates.TemplateResponse("change_password.html", {
        "request": request, "session": s, "error": error, "success": success
    })

@app.post("/change-password")
async def change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
):
    s = get_session(request)
    if not s: return redir("/login")
    uid = s.get("uid")
    db = get_db()
    row = db.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    if not row:
        return redir("/change-password?error=Пользователь+не+найден")
    if not bcrypt.checkpw(current_password.encode(), row["password_hash"].encode()):
        return redir("/change-password?error=Неверный+текущий+пароль")
    if len(new_password) < 6:
        return redir("/change-password?error=Новый+пароль+должен+быть+не+менее+6+символов")
    if new_password != confirm_password:
        return redir("/change-password?error=Пароли+не+совпадают")
    pw_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    db.execute("UPDATE users SET password_hash=? WHERE id=?", (pw_hash, uid))
    db.commit()
    return redir("/change-password?success=Пароль+успешно+изменён")

# ── Dashboard ──────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    s = get_session(request)
    if not s: return redir("/login")
    db = get_db()
    stats = []
    for org in ORGANIZATIONS:
        oid = org["id"]
        sessions_count = db.execute("SELECT COUNT(*) FROM sd_sessions WHERE org_id=?", (oid,)).fetchone()[0]
        agenda_count = db.execute("SELECT COUNT(*) FROM sd_agenda_items WHERE session_id IN (SELECT id FROM sd_sessions WHERE org_id=?)", (oid,)).fetchone()[0]
        stats.append({
            "org": org,
            "members":  db.execute("SELECT COUNT(*) FROM sd_members WHERE org_id=?", (oid,)).fetchone()[0],
            "independent": db.execute("SELECT COUNT(*) FROM sd_members WHERE org_id=? AND is_independent=1", (oid,)).fetchone()[0],
            "sessions": sessions_count,
            "agenda":   agenda_count,
            "cmts":     db.execute("SELECT COUNT(*) FROM committees WHERE org_id=?", (oid,)).fetchone()[0],
            "docs":     db.execute("SELECT COUNT(*) FROM documents WHERE org_id=?", (oid,)).fetchone()[0],
        })
    # Ближайшие заседания СД — следующие 30 дней
    from datetime import timedelta
    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    future_str = (datetime.utcnow() + timedelta(days=30)).strftime("%Y-%m-%d")
    upcoming_rows = db.execute(
        "SELECT * FROM sd_sessions WHERE session_date >= ? AND session_date <= ? ORDER BY session_date ASC LIMIT 20",
        (today_str, future_str)
    ).fetchall()
    upcoming = []
    for r in upcoming_rows:
        org = ORG_MAP.get(r["org_id"])
        if org:
            try:
                d = datetime.fromisoformat(r["session_date"])
                delta = (d - datetime.utcnow()).days
                tag = "today" if delta == 0 else ("soon" if 1 <= delta <= 7 else "")
            except Exception:
                delta, tag = 99, ""
            upcoming.append({"org": org, "date": r["session_date"], "format": r["format"], "order_type": r["order_type"], "tag": tag})
    db.close()
    logo_map = {"АКК":"akk","БРК":"brk","ФРП":"frp","ЭКА":"eka","QIC":"qic",
                "Даму":"damu","Отбасы":"otbasy","КЖК":"kjk","КАФ":"kaf","KTD":"ktd"}
    db2 = get_db()
    try:
        agent_unread = db2.execute("SELECT COUNT(*) FROM agent_alerts WHERE is_read=0").fetchone()[0]
    except Exception:
        agent_unread = 0
    db2.close()
    return templates.TemplateResponse("dashboard.html", {"request": request, "session": s, "stats": stats, "logo_map": logo_map, "upcoming": upcoming, "today_str": today_str, "agent_unread": agent_unread})

if __name__ == "__main__":
    init_db()
    from database import migrate_db
    migrate_db()
    print("\n" + "="*60)
    print("  АО «НИХ» Байтерек — Корпоративная карточка ДО/ДЗО")
    print("  Браузер: http://localhost:8000")
    print("  Логины: admin/admin123, chingiz/pass123,")
    print("          akbota/pass123, dinara/pass123,")
    print("          ilmira/pass123, zhanna/pass123")
    print("="*60 + "\n")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)