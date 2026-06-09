# database.py — SQLite schema for НИХ Байтерек corporate dashboard
import sqlite3
import bcrypt
from datetime import datetime

DB_PATH = "baiterek.db"

# All subsidiary organizations and their curators
ORGANIZATIONS = [
    {"id": 1, "short": "АКК",    "name": 'АО «Аграрная кредитная корпорация»',               "curator": "Admin",  "logo": "akk.png"},
    {"id": 2, "short": "БРК",    "name": 'АО «Банк Развития Казахстана»',                    "curator": "Akbota", "logo": "brk.png"},
    {"id": 3, "short": "ФРП",    "name": 'АО «Фонд развития промышленности»',                "curator": "Akbota", "logo": "frp.png"},
    {"id": 4, "short": "ЭКА",    "name": 'АО «Экспортно-кредитное агентство»',               "curator": "Dinara", "logo": "eka.png"},
    {"id": 5, "short": "QIC",    "name": 'АО «Qazaqstan Investment Corporation»',             "curator": "Dinara", "logo": "qic.png"},
    {"id": 6, "short": "Даму",   "name": 'АО «Фонд развития предпринимательства «Даму»',     "curator": "Ilmira", "logo": "damu.png"},
    {"id": 7, "short": "Отбасы", "name": 'АО «ЖССБ «Отбасы банк»',                          "curator": "Ilmira", "logo": "otbasy.png"},
    {"id": 8, "short": "КЖК",    "name": 'АО «Казахстанская жилищная компания»',             "curator": "Ilmira", "logo": "kjk.png"},
    {"id": 9, "short": "КАФ",    "name": 'АО «КазАгроФинанс»',                              "curator": "Zhanna", "logo": "kaf.png"},
    {"id":10, "short": "KTD",    "name": 'ЧК «Kazakh Tourism Development Ltd.»',             "curator": "Zhanna", "logo": "ktd.png"},
]

ORG_MAP = {o["id"]: o for o in ORGANIZATIONS}
ORG_BY_USERNAME = {}
for o in ORGANIZATIONS:
    ORG_BY_USERNAME.setdefault(o["curator"], []).append(o["id"])

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def now():
    return datetime.utcnow().isoformat(timespec='seconds')

def init_db():
    conn = get_db()
    c = conn.cursor()

    # Users
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        full_name TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'staff',
        is_active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL
    )""")

    # SD Members (per org)
    c.execute("""CREATE TABLE IF NOT EXISTS sd_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        org_id INTEGER NOT NULL,
        full_name TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'mem',
        is_independent INTEGER DEFAULT 0,
        position TEXT,
        date_from TEXT,
        date_to TEXT,
        decision TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )""")

    # SD Sessions (per org)
    c.execute("""CREATE TABLE IF NOT EXISTS sd_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        org_id INTEGER NOT NULL,
        session_date TEXT NOT NULL,
        format TEXT NOT NULL DEFAULT 'Очное',
        order_type TEXT NOT NULL DEFAULT 'Очередное',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )""")

    # SD Agenda items
    c.execute("""CREATE TABLE IF NOT EXISTS sd_agenda_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL REFERENCES sd_sessions(id) ON DELETE CASCADE,
        item_order INTEGER NOT NULL DEFAULT 0,
        text TEXT NOT NULL DEFAULT '',
        status TEXT NOT NULL DEFAULT 'done',
        note TEXT DEFAULT ''
    )""")

    # Committees (per org)
    c.execute("""CREATE TABLE IF NOT EXISTS committees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        org_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        color TEXT NOT NULL DEFAULT '#1a6b3c',
        created_at TEXT NOT NULL
    )""")

    # Committee permanent members
    c.execute("""CREATE TABLE IF NOT EXISTS committee_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        committee_id INTEGER NOT NULL REFERENCES committees(id) ON DELETE CASCADE,
        full_name TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'Член комитета'
    )""")

    # Committee sessions (per org)
    c.execute("""CREATE TABLE IF NOT EXISTS committee_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        org_id INTEGER NOT NULL,
        session_date TEXT NOT NULL,
        protocol_num TEXT,
        created_at TEXT NOT NULL
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS committee_session_participants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        committee_session_id INTEGER NOT NULL REFERENCES committee_sessions(id) ON DELETE CASCADE,
        committee_id INTEGER NOT NULL REFERENCES committees(id) ON DELETE CASCADE
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS committee_session_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        committee_session_id INTEGER NOT NULL REFERENCES committee_sessions(id) ON DELETE CASCADE,
        committee_id INTEGER NOT NULL REFERENCES committees(id) ON DELETE CASCADE,
        full_name TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'Член комитета'
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS committee_agenda_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        committee_session_id INTEGER NOT NULL REFERENCES committee_sessions(id) ON DELETE CASCADE,
        committee_id INTEGER NOT NULL REFERENCES committees(id) ON DELETE CASCADE,
        item_order INTEGER NOT NULL DEFAULT 0,
        text TEXT NOT NULL DEFAULT '',
        status TEXT NOT NULL DEFAULT 'done',
        note TEXT DEFAULT ''
    )""")

    # Accountable (per org)
    c.execute("""CREATE TABLE IF NOT EXISTS accountable (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        org_id INTEGER NOT NULL,
        full_name TEXT NOT NULL,
        position TEXT NOT NULL DEFAULT 'emp',
        org_name TEXT,
        phone TEXT,
        email TEXT,
        date_from TEXT,
        date_to TEXT,
        decision TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )""")

    # Board members (per org)
    c.execute("""CREATE TABLE IF NOT EXISTS board_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        org_id INTEGER NOT NULL,
        full_name TEXT NOT NULL,
        position TEXT,
        date_from TEXT,
        date_to TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )""")

    # Documents (per org)
    c.execute("""CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        org_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        doc_type TEXT NOT NULL DEFAULT 'Положение',
        date_approved TEXT,
        decision TEXT,
        file_name TEXT,
        file_data BLOB,
        file_mime TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )""")

    conn.commit()

    conn.commit()
    conn.close()

def migrate_db():
    """Add new tables for v3 features"""
    conn = get_db()
    c = conn.cursor()

    # Логотипы организаций (ключ short → logo_key)
    LOGO_MAP = {
        'АКК':'akk','БРК':'brk','ФРП':'frp','ЭКА':'eka',
        'QIC':'qic','Даму':'damu','Отбасы':'otbasy',
        'КЖК':'kjk','КАФ':'kaf','KTD':'ktd'
    }

    # План работы СД (per org, один файл)
    c.execute("""CREATE TABLE IF NOT EXISTS sd_work_plan (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        org_id INTEGER NOT NULL UNIQUE,
        file_name TEXT,
        file_data BLOB,
        file_mime TEXT,
        uploaded_at TEXT,
        updated_at TEXT
    )""")

    # Решения ЕА (per org, несколько записей)
    c.execute("""CREATE TABLE IF NOT EXISTS ea_decisions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        org_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        decision_date TEXT,
        file_name TEXT,
        file_data BLOB,
        file_mime TEXT,
        sent_letter INTEGER DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )""")

    # Файлы к заседаниям СД
    c.execute("""CREATE TABLE IF NOT EXISTS sd_session_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL REFERENCES sd_sessions(id) ON DELETE CASCADE,
        file_name TEXT,
        file_data BLOB,
        file_mime TEXT,
        uploaded_at TEXT
    )""")

    # Файлы к заседаниям комитетов
    c.execute("""CREATE TABLE IF NOT EXISTS cmt_session_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        committee_session_id INTEGER NOT NULL REFERENCES committee_sessions(id) ON DELETE CASCADE,
        file_name TEXT,
        file_data BLOB,
        file_mime TEXT,
        uploaded_at TEXT
    )""")

    # Лог активности пользователей
    c.execute("""CREATE TABLE IF NOT EXISTS activity_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        username TEXT NOT NULL,
        full_name TEXT NOT NULL,
        action TEXT NOT NULL,
        org_id INTEGER,
        details TEXT,
        ip_address TEXT,
        created_at TEXT NOT NULL
    )""")

    # Сессии пользователей (онлайн статус)
    c.execute("""CREATE TABLE IF NOT EXISTS user_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        username TEXT NOT NULL,
        full_name TEXT NOT NULL,
        last_seen TEXT NOT NULL,
        ip_address TEXT
    )""")

    conn.commit()
    conn.close()
    print("Migration complete")
