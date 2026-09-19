# -*- coding: utf-8 -*-
"""
STAGE IMMERSION L2 DSTAAN — LABORATOIRE DE PÉDOLOGIE
ISRA / CRA SAINT-LOUIS

VERSION XXL
- Navigation horizontale en haut (pas de barre latérale)
- Accès privé
- Tableau de bord
- Profil et objectifs
- Journal quotidien exhaustif
- Photos liées aux journées
- Registre des échantillons
- Analyses de sols
- Matériel / équipements
- Compétences
- Encadrement
- Documents et notes
- Rapport journalier PDF avec introduction, photos et conclusion
- Rapport mensuel PDF avec introduction, synthèse, tableaux, photos et conclusion
- Export CSV
- Base PostgreSQL / Supabase
- Journal d'audit
- Interface responsive et professionnelle

Installation:
    pip install -r requirements.txt

Lancement:
    streamlit run stage.py

Migration unique de l'ancien SQLite:
    python stage.py --migrate-sqlite chemin/ancien.db

IMPORTANT:
Pour Streamlit Cloud, utilise st.secrets pour les identifiants et une base
persistante si les données doivent survivre aux redéploiements.
"""

from __future__ import annotations

import io
import secrets
from datetime import date, datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

import pandas as pd
import streamlit as st

from PIL import Image

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image as RLImage, KeepTogether
)

# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Stage L2 DSTAAN — Pédologie ISRA Saint-Louis",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="collapsed",
)

APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "stage_data"
PHOTO_DIR = DATA_DIR / "photos"
REPORT_DIR = DATA_DIR / "rapports"

for folder in (DATA_DIR, PHOTO_DIR, REPORT_DIR):
    folder.mkdir(parents=True, exist_ok=True)

DEFAULT_LOGIN = "iy@2012"
DEFAULT_PASSWORD = "issayoume2026"

# PostgreSQL/Supabase : configure [postgres] dans .streamlit/secrets.toml
# Le mot de passe n'est volontairement jamais écrit en clair dans ce fichier.

# ============================================================
# STYLE XXL — NAVIGATION EN HAUT
# ============================================================

st.markdown("""
<style>
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}

.block-container {
    padding-top: 1rem;
    padding-bottom: 3rem;
    max-width: 1500px;
}

.top-brand {
    padding: 1rem 1.2rem;
    border: 1px solid #d9e2d0;
    border-radius: 18px;
    background: linear-gradient(135deg, #f7fbf3, #ffffff);
    margin-bottom: 12px;
}

.top-brand h1 {
    margin: 0;
    font-size: 2rem;
    font-weight: 800;
}

.top-brand p {
    margin: .25rem 0 0;
    color: #667085;
}

.nav-title {
    font-weight: 700;
    font-size: .82rem;
    color: #667085;
    margin-bottom: .25rem;
}

div.stButton > button {
    border-radius: 10px;
    min-height: 42px;
    font-weight: 600;
}

.card {
    border: 1px solid #e4e7ec;
    border-radius: 16px;
    padding: 18px;
    background: #ffffff;
    box-shadow: 0 1px 2px rgba(16,24,40,.04);
    margin-bottom: 12px;
}

.section-title {
    font-size: 1.45rem;
    font-weight: 800;
    margin-top: .4rem;
    margin-bottom: .2rem;
}

.section-subtitle {
    color: #667085;
    margin-bottom: 1rem;
}

.kpi {
    border: 1px solid #e4e7ec;
    border-radius: 15px;
    padding: 15px;
    background: #fff;
}

.photo-card {
    border: 1px solid #e4e7ec;
    border-radius: 14px;
    padding: 8px;
    background: white;
}

.small {
    font-size: .82rem;
    color: #667085;
}

.danger {
    color: #b42318;
}

.success-box {
    padding: 10px 14px;
    border-radius: 10px;
    background: #ecfdf3;
    color: #027a48;
}

@media (max-width: 900px) {
    .top-brand h1 {font-size: 1.5rem;}
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# DESIGN PREMIUM VERT & BLANC
# ============================================================
st.markdown("""
<style>
:root {
    --green-900: #14532d;
    --green-800: #166534;
    --green-700: #15803d;
    --green-600: #16a34a;
    --green-100: #dcfce7;
    --green-50: #f0fdf4;
    --ink: #17321f;
    --muted: #667085;
    --border: #dce8df;
    --surface: #ffffff;
    --surface-2: #f7fbf8;
}

.stApp {
    background:
        radial-gradient(circle at 10% 0%, rgba(22,163,74,.08), transparent 28%),
        radial-gradient(circle at 100% 10%, rgba(20,83,45,.06), transparent 30%),
        #f7faf8;
    color: var(--ink);
}

.block-container {
    max-width: 1550px;
    padding-top: 1rem;
    padding-bottom: 4rem;
}

.top-brand {
    position: relative;
    overflow: hidden;
    padding: 24px 28px;
    border: 1px solid #cfe1d4;
    border-radius: 24px;
    background: linear-gradient(135deg, #ffffff 0%, #f2fbf4 52%, #e6f7ea 100%);
    box-shadow: 0 12px 35px rgba(20,83,45,.08);
    margin-bottom: 14px;
}
.top-brand:after {
    content: "";
    position: absolute;
    width: 190px;
    height: 190px;
    border-radius: 50%;
    right: -55px;
    top: -85px;
    background: rgba(22,163,74,.08);
}
.top-brand h1 {
    margin: 0;
    font-size: 2.15rem;
    font-weight: 850;
    color: var(--green-900);
    letter-spacing: -.5px;
}
.top-brand p {
    margin: .35rem 0 0;
    color: #587060;
    font-size: .98rem;
}

div.stButton > button {
    border-radius: 12px;
    min-height: 44px;
    font-weight: 700;
    border: 1px solid #d4e3d8;
    background: white;
    transition: all .18s ease;
}
div.stButton > button:hover {
    border-color: #86c89a;
    box-shadow: 0 6px 18px rgba(20,83,45,.10);
    transform: translateY(-1px);
}

.section-title {
    margin-top: .7rem;
    padding: 14px 18px;
    border-left: 6px solid var(--green-600);
    border-radius: 12px;
    background: linear-gradient(90deg,#eefaf1,#ffffff);
    color: var(--green-900);
    font-size: 1.55rem;
    font-weight: 850;
}
.section-subtitle {
    color: var(--muted);
    margin: 8px 0 18px;
}

.kpi {
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 18px;
    background: rgba(255,255,255,.92);
    box-shadow: 0 7px 24px rgba(20,83,45,.055);
}

div[data-testid="stMetric"] {
    background: white;
    border: 1px solid var(--border);
    padding: 14px 16px;
    border-radius: 17px;
    box-shadow: 0 5px 18px rgba(20,83,45,.05);
}
div[data-testid="stMetricLabel"] {
    color: #52715c;
}
div[data-testid="stMetricValue"] {
    color: var(--green-900);
    font-weight: 850;
}

div[data-baseweb="tab-list"] {
    gap: 6px;
    padding: 6px;
    border-radius: 15px;
    background: #edf7ef;
}
button[data-baseweb="tab"] {
    border-radius: 10px;
    font-weight: 700;
}
button[data-baseweb="tab"][aria-selected="true"] {
    background: white;
    color: var(--green-800);
    box-shadow: 0 3px 10px rgba(20,83,45,.08);
}

div[data-testid="stDataFrame"] {
    border: 1px solid var(--border);
    border-radius: 15px;
    overflow: hidden;
    box-shadow: 0 5px 20px rgba(20,83,45,.04);
}

div[data-testid="stFileUploader"] {
    border: 2px dashed #9dccaa;
    border-radius: 17px;
    background: #f5fbf6;
    padding: 8px;
}

.photo-card {
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 10px;
    background: white;
    box-shadow: 0 7px 22px rgba(20,83,45,.07);
}

.success-box {
    padding: 12px 16px;
    border-radius: 12px;
    background: #ecfdf3;
    color: #027a48;
    border: 1px solid #abefc6;
}

.stAlert {
    border-radius: 13px;
}

[data-testid="stExpander"] {
    border: 1px solid var(--border);
    border-radius: 15px;
    background: white;
}

hr {
    border-color: #dce8df;
}

.small {
    font-size: .82rem;
    color: var(--muted);
}

@media (max-width: 900px) {
    .top-brand h1 {font-size: 1.55rem;}
    .section-title {font-size: 1.3rem;}
}
</style>
""", unsafe_allow_html=True)

st.markdown(r"""
<style>
/* RESPONSIVE MULTI-SUPPORT */
html, body { overflow-x:hidden !important; }
.stApp { min-width:0 !important; }
.block-container { width:100% !important; max-width:1550px !important; margin:0 auto !important; box-sizing:border-box !important; }
div[data-testid="stRadio"] > div { display:flex !important; flex-wrap:wrap !important; gap:6px !important; }
div[data-testid="stRadio"] label { border:1px solid #d7e7db !important; border-radius:11px !important; padding:7px 12px !important; background:#fff !important; min-height:36px !important; }
img { max-width:100% !important; height:auto !important; }
div[data-testid="stDataFrame"], div[data-testid="stTable"] { max-width:100% !important; overflow-x:auto !important; }
input, textarea, [data-baseweb="select"] { max-width:100% !important; box-sizing:border-box !important; }
div.stButton > button, div[data-testid="stDownloadButton"] button { min-height:44px !important; touch-action:manipulation !important; }
@media (max-width:1100px) { .block-container{padding-left:1rem !important;padding-right:1rem !important;} .top-brand{padding:20px !important;} .top-brand h1{font-size:1.75rem !important;} .section-title{font-size:1.35rem !important;} div[data-testid="stRadio"] label{padding:7px 10px !important;font-size:.90rem !important;} }
@media (max-width:800px) { .block-container{padding:.7rem .75rem 3rem !important;} .top-brand{border-radius:18px !important;padding:17px !important;} .top-brand h1{font-size:1.45rem !important;line-height:1.2 !important;} .top-brand p{font-size:.88rem !important;} .section-title{font-size:1.22rem !important;padding:11px 14px !important;} .card{padding:13px !important;border-radius:14px !important;} div[data-testid="stHorizontalBlock"]{flex-wrap:wrap !important;} div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]{min-width:min(100%,320px) !important;flex:1 1 100% !important;} div[data-testid="stRadio"] > div{flex-direction:row !important;flex-wrap:wrap !important;} div[data-testid="stRadio"] label{flex:0 1 auto !important;} }
@media (max-width:600px) { .block-container{padding-left:.55rem !important;padding-right:.55rem !important;} .top-brand{padding:15px 14px !important;border-radius:15px !important;} .top-brand h1{font-size:1.25rem !important;} .top-brand p{font-size:.78rem !important;line-height:1.35 !important;} div[data-testid="stRadio"] > div{gap:4px !important;} div[data-testid="stRadio"] label{font-size:.74rem !important;padding:6px 8px !important;min-height:34px !important;border-radius:9px !important;flex:0 1 auto !important;} .section-title{font-size:1.08rem !important;line-height:1.25 !important;padding:9px 11px !important;} .section-subtitle{font-size:.82rem !important;line-height:1.35 !important;} .card{padding:11px !important;margin-bottom:9px !important;} .small{font-size:.75rem !important;} div.stButton > button, div[data-testid="stDownloadButton"] button{width:100% !important;min-height:46px !important;} div[data-testid="stFileUploader"]{width:100% !important;box-sizing:border-box !important;} textarea{min-height:110px !important;} }
@media (max-width:380px) { .top-brand h1{font-size:1.12rem !important;} div[data-testid="stRadio"] label{font-size:.68rem !important;padding:5px 6px !important;} .section-title{font-size:1rem !important;} }
p, div, span, label, td, th { overflow-wrap:anywhere; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# MIGRATION UNIQUE : ANCIEN SQLITE -> SUPABASE POSTGRESQL
# ============================================================
# Normalement, l'application n'utilise PAS SQLite.
# Ce bloc n'est activé que si le fichier est lancé ainsi :
#     python stage.py --migrate-sqlite ancien.db
#
# Après migration, l'application fonctionne exclusivement avec PostgreSQL.
MIGRATION_TABLES = [
    "profile", "daily_logs", "monthly_logs", "photos", "samples", "analyses",
    "equipment", "skills", "contacts", "documents", "planning", "incidents",
    "protocols", "audit"
]

def _migration_pg_conn():
    """Connexion PostgreSQL utilisée uniquement par le mode de migration."""
    return psycopg.connect(
        host=st.secrets["postgres"]["host"],
        port=int(st.secrets["postgres"].get("port", 5432)),
        dbname=st.secrets["postgres"].get("database", "postgres"),
        user=st.secrets["postgres"]["user"],
        password=st.secrets["postgres"]["password"],
        sslmode=st.secrets["postgres"].get("sslmode", "require"),
        connect_timeout=int(st.secrets["postgres"].get("connect_timeout", 10)),
        prepare_threshold=None,
        row_factory=dict_row,
    )

def migrate_old_sqlite_to_postgres(sqlite_path: str):
    """
    Transfère les données de l'ancien SQLite vers les tables PostgreSQL
    déjà créées par init_db().

    Cette fonction ne supprime jamais le fichier SQLite source.
    Les conflits sont ignorés pour éviter de dupliquer les données.
    """
    import sqlite3

    src_conn = sqlite3.connect(sqlite_path)
    src_conn.row_factory = sqlite3.Row
    dst_conn = _migration_pg_conn()
    report = []

    try:
        with dst_conn.cursor() as cur:
            for table in MIGRATION_TABLES:
                try:
                    src_cols = [
                        row[1] for row in
                        src_conn.execute(f'PRAGMA table_info("{table}")').fetchall()
                    ]
                except Exception:
                    src_cols = []

                if not src_cols:
                    report.append(f"{table}: absente dans SQLite")
                    continue

                # Vérifie les colonnes réellement présentes dans PostgreSQL.
                cur.execute("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema='public' AND table_name=%s
                """, (table,))
                pg_cols = {r["column_name"] for r in cur.fetchall()}

                cols = [c for c in src_cols if c in pg_cols]
                if not cols:
                    report.append(f"{table}: aucune colonne compatible")
                    continue

                rows = src_conn.execute(
                    f'SELECT * FROM "{table}"'
                ).fetchall()

                if not rows:
                    report.append(f"{table}: 0 ligne")
                    continue

                quoted_cols = ", ".join(f'"{c}"' for c in cols)
                placeholders = ", ".join(["%s"] * len(cols))

                sql = (
                    f'INSERT INTO "{table}" ({quoted_cols}) '
                    f'VALUES ({placeholders}) ON CONFLICT DO NOTHING'
                )

                inserted = 0
                for row in rows:
                    values = []
                    for col in cols:
                        value = row[col]

                        # Conversion BLOB SQLite -> BYTEA PostgreSQL.
                        if table == "photos" and col == "data" and value is not None:
                            value = psycopg.Binary(bytes(value))

                        values.append(value)

                    cur.execute(sql, values)
                    inserted += cur.rowcount

                report.append(
                    f"{table}: {len(rows)} source(s), {inserted} insérée(s)"
                )

        dst_conn.commit()
        return report

    except Exception:
        dst_conn.rollback()
        raise
    finally:
        dst_conn.close()
        src_conn.close()


def run_integrated_migration_cli():
    """
    Mode ligne de commande intégré au même fichier.
    Il est appelé avant le lancement de Streamlit.
    """
    import sys

    if "--migrate-sqlite" not in sys.argv:
        return False

    try:
        index = sys.argv.index("--migrate-sqlite")
        sqlite_path = sys.argv[index + 1]
    except (ValueError, IndexError):
        print("Usage : python stage.py --migrate-sqlite chemin/ancien.db")
        raise SystemExit(2)

    print("=" * 70)
    print("MIGRATION SQLITE -> SUPABASE POSTGRESQL")
    print("=" * 70)
    print(f"Source : {sqlite_path}")

    if not Path(sqlite_path).exists():
        print(f"ERREUR : fichier SQLite introuvable : {sqlite_path}")
        raise SystemExit(1)

    # Crée les tables PostgreSQL avant le transfert.
    init_db()

    results = migrate_old_sqlite_to_postgres(sqlite_path)
    for line in results:
        print(" -", line)

    print("\nMigration terminée.")
    print("Le fichier SQLite source n'a pas été supprimé.")
    print("L'application utilise désormais PostgreSQL/Supabase.")
    raise SystemExit(0)


# ============================================================
# AUTHENTIFICATION
# ============================================================

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_login" not in st.session_state:
    st.session_state.user_login = None
if "page" not in st.session_state:
    st.session_state.page = "Tableau de bord"


def get_credentials():
    try:
        auth = st.secrets.get("auth", {})
        return str(auth.get("login", DEFAULT_LOGIN)), str(auth.get("password", DEFAULT_PASSWORD))
    except Exception:
        return DEFAULT_LOGIN, DEFAULT_PASSWORD


def login_screen():
    st.markdown("""
    <div class="top-brand">
        <h1>🌱 Carnet de stage L2 DSTAAN</h1>
        <p>Laboratoire de pédologie — ISRA / CRA Saint-Louis</p>
    </div>
    """, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("## 🔐 Accès privé")
        st.info("Cette application est réservée à l'utilisateur autorisé.")
        login = st.text_input("Identifiant")
        password = st.text_input("Mot de passe", type="password")

        if st.button("Se connecter", type="primary", use_container_width=True):
            expected_login, expected_password = get_credentials()
            if secrets.compare_digest(login, expected_login) and secrets.compare_digest(password, expected_password):
                st.session_state.authenticated = True
                st.session_state.user_login = login
                st.rerun()
            else:
                st.error("Identifiant ou mot de passe incorrect.")


if not st.session_state.authenticated:
    login_screen()
    st.stop()

# ============================================================
# BASE POSTGRESQL / SUPABASE
# ============================================================

def _pg_settings():
    """Lit la connexion Supabase depuis st.secrets, sans mot de passe dans le code."""
    cfg = st.secrets.get("postgres", {})
    return {
        "host": cfg.get("host", "aws-1-eu-west-1.pooler.supabase.com"),
        "port": int(cfg.get("port", 5432)),
        "dbname": cfg.get("database", "postgres"),
        "user": cfg.get("user", "postgres.ctywepszhxkurvdmoyiy"),
        "password": cfg.get("password", ""),
        "sslmode": cfg.get("sslmode", "require"),
        "connect_timeout": int(cfg.get("connect_timeout", 5)),
        "prepare_threshold": None,
    }


@st.cache_resource(show_spinner=False)
def get_pool():
    """Pool PostgreSQL partagé afin d'éviter une connexion réseau à chaque requête."""
    cfg = _pg_settings()
    if not cfg["password"]:
        raise RuntimeError(
            "Mot de passe PostgreSQL absent. Ajoute [postgres].password dans les secrets Streamlit."
        )
    return ConnectionPool(
        conninfo=None,
        kwargs={
            **cfg,
            "row_factory": dict_row,
        },
        min_size=1,
        max_size=4,
        timeout=10,
        open=True,
    )


def get_conn():
    return get_pool().getconn()


def _pg_sql(sql: str) -> str:
    return sql.replace("?", "%s")


def db_exec(sql: str, params=(), fetch=False, many=False):
    """Requête PostgreSQL via le pool de connexions réutilisables."""
    with get_pool().connection() as conn:
        with conn.cursor() as cur:
            sql = _pg_sql(sql)
            if many:
                cur.executemany(sql, params)
            else:
                cur.execute(sql, params)
            rows = cur.fetchall() if fetch else None
        conn.commit()
        return rows


@st.cache_resource(show_spinner=False)
def init_db():
    statements = [
        """CREATE TABLE IF NOT EXISTS profile (
            id INTEGER PRIMARY KEY CHECK(id=1), student_name TEXT, formation TEXT, level TEXT, institution TEXT,
            host_structure TEXT, service TEXT, supervisor TEXT, start_date TEXT, end_date TEXT, academic_year TEXT,
            objectives TEXT, presentation TEXT, updated_at TEXT)""",
        """CREATE TABLE IF NOT EXISTS daily_logs (
            id BIGSERIAL PRIMARY KEY, log_date TEXT NOT NULL, title TEXT, location TEXT, supervisor TEXT,
            activities TEXT, observations TEXT, techniques TEXT, equipment TEXT, samples TEXT, results TEXT,
            difficulties TEXT, solutions TEXT, lessons TEXT, questions TEXT, next_actions TEXT, introduction TEXT,
            conclusion TEXT, critical_analysis TEXT, professional_behavior TEXT, hours DOUBLE PRECISION DEFAULT 0,
            created_at TEXT, updated_at TEXT)""",
        """CREATE TABLE IF NOT EXISTS monthly_logs (
            id BIGSERIAL PRIMARY KEY, month TEXT NOT NULL UNIQUE, introduction TEXT, summary TEXT, activities TEXT,
            analyses TEXT, fieldwork TEXT, planning_review TEXT, skills TEXT, professional_behavior TEXT, results TEXT,
            difficulties TEXT, solutions TEXT, lessons TEXT, critical_analysis TEXT, objectives_next TEXT, conclusion TEXT,
            supervisor_comment TEXT, created_at TEXT, updated_at TEXT)""",
        """CREATE TABLE IF NOT EXISTS photos (
            id BIGSERIAL PRIMARY KEY, log_id BIGINT REFERENCES daily_logs(id) ON DELETE CASCADE, photo_date TEXT,
            title TEXT, caption TEXT, category TEXT, filename TEXT, mime_type TEXT, data BYTEA NOT NULL, created_at TEXT)""",
        """CREATE TABLE IF NOT EXISTS samples (
            id BIGSERIAL PRIMARY KEY, sample_code TEXT UNIQUE, sample_date TEXT, parcel TEXT, locality TEXT, gps TEXT,
            depth TEXT, crop TEXT, sample_type TEXT, appearance TEXT, preparation TEXT, analyses TEXT, result_summary TEXT,
            interpretation TEXT, remarks TEXT, created_at TEXT)""",
        """CREATE TABLE IF NOT EXISTS analyses (
            id BIGSERIAL PRIMARY KEY, analysis_date TEXT, sample_code TEXT, analysis_name TEXT, objective TEXT, method TEXT,
            equipment TEXT, unit TEXT, result TEXT, interpretation TEXT, agronomic_use TEXT, quality_control TEXT,
            observations TEXT, created_at TEXT)""",
        """CREATE TABLE IF NOT EXISTS equipment (
            id BIGSERIAL PRIMARY KEY, name TEXT, category TEXT, function TEXT, principle TEXT, safety TEXT, observations TEXT,
            learned INTEGER DEFAULT 0, created_at TEXT)""",
        """CREATE TABLE IF NOT EXISTS skills (
            id BIGSERIAL PRIMARY KEY, skill TEXT UNIQUE, category TEXT, level TEXT, evidence TEXT, notes TEXT, updated_at TEXT)""",
        """CREATE TABLE IF NOT EXISTS contacts (
            id BIGSERIAL PRIMARY KEY, name TEXT, role TEXT, service TEXT, phone TEXT, email TEXT, notes TEXT, created_at TEXT)""",
        """CREATE TABLE IF NOT EXISTS documents (
            id BIGSERIAL PRIMARY KEY, doc_date TEXT, title TEXT, doc_type TEXT, reference TEXT, notes TEXT, created_at TEXT)""",
        """CREATE TABLE IF NOT EXISTS planning (
            id BIGSERIAL PRIMARY KEY, task_date TEXT NOT NULL, title TEXT NOT NULL, category TEXT, priority TEXT DEFAULT 'Normale',
            status TEXT DEFAULT 'À faire', location TEXT, supervisor TEXT, notes TEXT, completed_at TEXT, created_at TEXT, updated_at TEXT)""",
        """CREATE TABLE IF NOT EXISTS incidents (
            id BIGSERIAL PRIMARY KEY, incident_date TEXT NOT NULL, title TEXT NOT NULL, type TEXT, severity TEXT, location TEXT,
            description TEXT, immediate_actions TEXT, prevention TEXT, declared_to TEXT, closed INTEGER DEFAULT 0, created_at TEXT, updated_at TEXT)""",
        """CREATE TABLE IF NOT EXISTS protocols (
            id BIGSERIAL PRIMARY KEY, title TEXT NOT NULL UNIQUE, category TEXT, objective TEXT, principle TEXT, materials TEXT,
            steps TEXT, precautions TEXT, quality_control TEXT, "references" TEXT, notes TEXT, created_at TEXT, updated_at TEXT)""",
        """CREATE TABLE IF NOT EXISTS audit (
            id BIGSERIAL PRIMARY KEY, event_time TEXT, user_login TEXT, action TEXT, details TEXT)"""
    ]
    for sql in statements:
        db_exec(sql)

    # Colonnes ajoutées progressivement dans les versions récentes.
    migrations = {
        "profile": {"presentation": "TEXT"},
        "daily_logs": {"introduction": "TEXT", "conclusion": "TEXT", "critical_analysis": "TEXT", "professional_behavior": "TEXT"},
        "monthly_logs": {"introduction": "TEXT", "conclusion": "TEXT", "planning_review": "TEXT", "professional_behavior": "TEXT", "critical_analysis": "TEXT"},
    }
    for table, cols in migrations.items():
        rows = db_exec(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = %s
            """,
            (table,),
            fetch=True,
        )

        existing = {
            row["column_name"] if isinstance(row, dict) else row[0]
            for row in rows
        }
        for col, typ in cols.items():
            if col not in existing:
                db_exec(f'ALTER TABLE "{table}" ADD COLUMN "{col}" {typ}')

    if not db_exec("SELECT id FROM profile WHERE id=1", fetch=True):
        db_exec("""INSERT INTO profile
            (id, student_name, formation, level, institution, host_structure, service, supervisor, start_date, end_date, academic_year, objectives, presentation, updated_at)
            VALUES (1, '', 'DSTAAN', 'L2', '', 'ISRA / CRA Saint-Louis', 'Laboratoire de pédologie', '', '', '', '', '', '', %s)""",
            (datetime.now().isoformat(timespec="seconds"),))

    default_skills = [
        ("Comprendre le rôle d'un laboratoire de pédologie", "Scientifique"),
        ("Identifier les grandes propriétés du sol", "Scientifique"),
        ("Comprendre le prélèvement d'un échantillon", "Terrain"),
        ("Comprendre la préparation d'un échantillon", "Laboratoire"),
        ("Observer une mesure de pH", "Laboratoire"),
        ("Observer une mesure de conductivité électrique", "Laboratoire"),
        ("Comprendre la granulométrie", "Laboratoire"),
        ("Comprendre la matière organique", "Laboratoire"),
        ("Comprendre N-P-K et la fertilité", "Agronomie"),
        ("Relier résultat analytique et décision agronomique", "Agronomie"),
        ("Appliquer les règles de sécurité", "Professionnel"),
        ("Tenir la traçabilité des échantillons", "Professionnel"),
        ("Rédiger une observation scientifique", "Professionnel"),
        ("Présenter clairement un résultat", "Communication"),
    ]
    now = datetime.now().isoformat(timespec="seconds")
    for skill, category in default_skills:
        db_exec("""INSERT INTO skills(skill, category, level, evidence, notes, updated_at)
                   VALUES (%s, %s, 'À découvrir', '', '', %s)
                   ON CONFLICT (skill) DO NOTHING""", (skill, category, now))

    default_protocols = [
        ("Prélèvement d'un échantillon de sol", "Terrain", "Obtenir un échantillon représentatif d'une zone homogène.",
         "La représentativité dépend de l'homogénéité de la zone, de la profondeur et du plan d'échantillonnage.",
         "Tarière ou pelle; sachet propre; étiquette; marqueur; gants; fiche de prélèvement.",
         "Définir la zone; choisir les points; prélever à la profondeur prévue; homogénéiser si nécessaire; conditionner; étiqueter; enregistrer la traçabilité.",
         "Éviter les zones atypiques non représentatives; utiliser du matériel propre; noter toute anomalie.",
         "Vérifier code, date, profondeur, localisation et cohérence de l'étiquette.",
         "Protocole interne du laboratoire à compléter avec les consignes de l'encadreur.",
         "Ne pas exécuter une méthode analytique sans validation ou supervision."),
        ("Préparation d'un échantillon au laboratoire", "Laboratoire", "Préparer l'échantillon avant analyse selon le protocole du laboratoire.",
         "La préparation vise à obtenir un matériau adapté et homogène tout en évitant les contaminations.",
         "Plateau; outils propres; tamis selon protocole; sachets; étiquettes; EPI.",
         "Réceptionner; vérifier l'identification; préparer; homogénéiser; tamiser ou sécher si prévu; conditionner; tracer chaque étape.",
         "Respecter les EPI, éviter les mélanges d'échantillons et suivre strictement le protocole local.",
         "Contrôler l'identification et l'état de l'échantillon avant analyse.",
         "À compléter avec la procédure officielle du laboratoire.",
         "Les paramètres de température, séchage et tamisage doivent venir du protocole validé."),
        ("Observation du pH du sol", "Analyse", "Comprendre le principe et l'interprétation d'une mesure de pH.",
         "Le pH renseigne sur l'acidité ou l'alcalinité du milieu selon le rapport sol/solution utilisé.",
         "pH-mètre; solutions étalons; électrode; béchers; eau ou solution prévue par le protocole.",
         "Observer l'étalonnage; préparer l'échantillon; mesurer selon le rapport prévu; rincer l'électrode; noter le résultat.",
         "Éviter la contamination des solutions; respecter les consignes d'utilisation de l'électrode.",
         "Contrôler l'étalonnage et noter toute anomalie ou dérive.",
         "Protocole officiel du laboratoire à privilégier.",
         "Les valeurs ne doivent pas être interprétées sans connaître la méthode et le contexte agronomique."),
    ]
    for pr in default_protocols:
        db_exec("""INSERT INTO protocols
            (title,category,objective,principle,materials,steps,precautions,quality_control,"references",notes,created_at,updated_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (title) DO NOTHING""", pr + (now, now))



# Mode optionnel : migration intégrée dans ce même fichier.
run_integrated_migration_cli()
init_db()


def audit(action: str, details: str = ""):
    db_exec(
        "INSERT INTO audit(event_time,user_login,action,details) VALUES (?,?,?,?)",
        (datetime.now().isoformat(timespec="seconds"),
         st.session_state.user_login or "", action, details[:3000])
    )


def rows_to_df(rows):
    return pd.DataFrame([dict(r) for r in rows]) if rows else pd.DataFrame()


@st.cache_data(ttl=30, show_spinner=False)
def profile():
    rows = db_exec("SELECT * FROM profile WHERE id=1", fetch=True)
    return dict(rows[0]) if rows else {}


def fmt_date(value):
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").strftime("%d/%m/%Y")
    except Exception:
        return str(value or "")


def month_label(month):
    try:
        return datetime.strptime(month, "%Y-%m").strftime("%B %Y").capitalize()
    except Exception:
        return month


def clean_html(text):
    return (str(text or "")
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br/>"))


# ============================================================
# NAVIGATION HORIZONTALE
# ============================================================

st.markdown("""
<div class="top-brand">
    <h1>🌱 Carnet de stage — L2 DSTAAN</h1>
    <p>Laboratoire de pédologie · ISRA / CRA Saint-Louis · Suivi scientifique et professionnel</p>
</div>
""", unsafe_allow_html=True)

nav_items = [
    "Tableau de bord",
    "Profil",
    "Journal quotidien",
    "Photos",
    "Rapport PDF",
    "Analyses",
    "Échantillons",
    "Matériel",
    "Compétences",
    "Encadrement",
    "Documents",
    "Suivi & outils",
    "Exports",
    "Audit",
]

# Navigation supérieure responsive.
if "page" not in st.session_state:
    st.session_state.page = nav_items[0]
try:
    current_index = nav_items.index(st.session_state.page)
except ValueError:
    current_index = 0
selected_page = st.radio(
    "Navigation principale", nav_items, index=current_index,
    horizontal=True, key="top_navigation", label_visibility="collapsed"
)
st.session_state.page = selected_page
page = selected_page

@st.cache_data(ttl=60, show_spinner=False)
def get_protocols():
    return db_exec("SELECT * FROM protocols ORDER BY category,title", fetch=True)

# ============================================================
# TABLEAU DE BORD
# ============================================================

if page == "Tableau de bord":
    st.markdown('<div class="section-title">🏠 Tableau de bord</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Vue globale de ton immersion et de ta progression.</div>', unsafe_allow_html=True)

    logs = db_exec("SELECT * FROM daily_logs ORDER BY log_date DESC, id DESC", fetch=True)
    analyses = db_exec("SELECT * FROM analyses", fetch=True)
    samples = db_exec("SELECT * FROM samples", fetch=True)
    photo_count_row = db_exec("SELECT COUNT(*) AS n FROM photos", fetch=True)
    photo_count = int(photo_count_row[0]["n"]) if photo_count_row else 0
    skills = db_exec("SELECT * FROM skills", fetch=True)

    hours = sum(float(r["hours"] or 0) for r in logs)
    acquired = sum(1 for r in skills if r["level"] == "Acquis")
    in_progress = sum(1 for r in skills if r["level"] == "En cours")

    planning = db_exec("SELECT * FROM planning ORDER BY task_date ASC, id ASC", fetch=True)
    incidents = db_exec("SELECT * FROM incidents ORDER BY incident_date DESC, id DESC", fetch=True)
    open_tasks = sum(1 for r in planning if r["status"] != "Terminé")
    open_incidents = sum(1 for r in incidents if not r["closed"])

    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("📔 Journées", len(logs))
    c2.metric("⏱️ Heures", f"{hours:.1f}")
    c3.metric("🧪 Analyses", len(analyses))
    c4.metric("🧫 Échantillons", len(samples))
    c5.metric("📷 Photos", photo_count)

    c6,c7,c8 = st.columns(3)
    c6.metric("📋 Tâches ouvertes", open_tasks)
    c7.metric("⚠️ Incidents ouverts", open_incidents)
    c8.metric("🎓 Compétences acquises", acquired)

    if planning:
        st.markdown("### 📅 Prochaines activités")
        upcoming = [r for r in planning if r["status"] != "Terminé"][:6]
        if upcoming:
            st.dataframe(
                rows_to_df(upcoming)[["task_date","title","category","priority","status"]],
                use_container_width=True, hide_index=True
            )

    if incidents:
        st.markdown("### ⚠️ Suivi sécurité")
        st.info(f"{open_incidents} incident(s) restent ouvert(s). Consulte la rubrique **Suivi & outils** pour documenter les mesures prises et la prévention.")

    if profile().get("student_name"):
        st.success(f"Étudiant : **{profile()['student_name']}** · {profile().get('formation','')} {profile().get('level','')}")
    else:
        st.warning("Complète ton profil avant de commencer le carnet.")

    st.markdown("### 🎯 Objectifs")
    st.write(profile().get("objectives") or "Aucun objectif renseigné.")

    st.markdown("### 📈 Progression des compétences")
    cc1, cc2, cc3 = st.columns(3)
    cc1.metric("Acquises", acquired)
    cc2.metric("En cours", in_progress)
    cc3.metric("À découvrir", max(0, len(skills)-acquired-in_progress))

    if skills:
        df = rows_to_df(skills)
        st.bar_chart(df["level"].value_counts())

    st.markdown("### 📅 Dernières journées")
    if logs:
        df = rows_to_df(logs[:8])
        st.dataframe(
            df[["log_date","title","location","hours","lessons"]],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Aucune journée enregistrée.")

# ============================================================
# PROFIL
# ============================================================

elif page == "Profil":
    st.markdown('<div class="section-title">👤 Profil et objectifs</div>', unsafe_allow_html=True)
    p = profile()

    with st.form("profile_form"):
        c1,c2 = st.columns(2)
        with c1:
            student_name = st.text_input("Nom et prénom", p.get("student_name",""))
            formation = st.text_input("Formation", p.get("formation","DSTAAN"))
            level = st.text_input("Niveau", p.get("level","L2"))
            institution = st.text_input("Établissement", p.get("institution",""))
            host_structure = st.text_input("Structure d'accueil", p.get("host_structure","ISRA / CRA Saint-Louis"))
        with c2:
            service = st.text_input("Service / laboratoire", p.get("service","Laboratoire de pédologie"))
            supervisor = st.text_input("Encadreur", p.get("supervisor",""))
            start_date = st.text_input("Date de début", p.get("start_date",""))
            end_date = st.text_input("Date de fin", p.get("end_date",""))
            academic_year = st.text_input("Année académique", p.get("academic_year",""))

        presentation = st.text_area(
            "Présentation du stage",
            p.get("presentation",""),
            height=120,
            placeholder="Présente brièvement la structure d'accueil, le contexte et la raison de ton immersion."
        )
        objectives = st.text_area(
            "Objectifs du stage",
            p.get("objectives",""),
            height=180,
            placeholder="Ex. comprendre les étapes de prélèvement, préparation et analyse des sols..."
        )

        if st.form_submit_button("💾 Enregistrer", type="primary"):
            db_exec("""
                UPDATE profile SET student_name=?, formation=?, level=?, institution=?,
                host_structure=?, service=?, supervisor=?, start_date=?, end_date=?,
                academic_year=?, objectives=?, presentation=?, updated_at=? WHERE id=1
            """, (
                student_name, formation, level, institution, host_structure, service,
                supervisor, start_date, end_date, academic_year, objectives,
                presentation, datetime.now().isoformat(timespec="seconds")
            ))
            audit("Mise à jour profil")
            st.success("Profil enregistré.")
            st.rerun()

# ============================================================
# JOURNAL QUOTIDIEN
# ============================================================

elif page == "Journal quotidien":
    st.markdown('<div class="section-title">📔 Journal quotidien</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Chaque journée devient automatiquement une source pour tes rapports PDF.</div>', unsafe_allow_html=True)

    logs = db_exec("SELECT * FROM daily_logs ORDER BY log_date DESC, id DESC", fetch=True)
    mode = st.radio("Action", ["Nouvelle journée","Modifier","Supprimer"], horizontal=True)

    selected = None
    if mode != "Nouvelle journée" and logs:
        labels = {
            f"{fmt_date(r['log_date'])} — {r['title'] or 'Sans titre'} — ID {r['id']}": r["id"]
            for r in logs
        }
        chosen = st.selectbox("Journée", list(labels))
        sid = labels[chosen]
        selected = dict(next(r for r in logs if r["id"] == sid))

    if mode == "Supprimer":
        if selected:
            st.warning("La journée et les photos qui lui sont associées seront supprimées.")
            if st.button("🗑️ Confirmer", type="primary"):
                db_exec("DELETE FROM photos WHERE log_id=?", (selected["id"],))
                db_exec("DELETE FROM daily_logs WHERE id=?", (selected["id"],))
                audit("Suppression journée", str(selected["id"]))
                st.success("Journée supprimée.")
                st.rerun()
    else:
        default_date = date.today()
        if selected:
            try:
                default_date = datetime.strptime(selected["log_date"], "%Y-%m-%d").date()
            except Exception:
                pass

        with st.form("daily_form"):
            c1,c2,c3 = st.columns(3)
            with c1:
                log_date = st.date_input("Date", default_date)
                title = st.text_input("Titre / objectif", selected.get("title","") if selected else "")
            with c2:
                location = st.text_input("Lieu / activité", selected.get("location","Laboratoire de pédologie") if selected else "Laboratoire de pédologie")
                supervisor = st.text_input("Encadreur", selected.get("supervisor","") if selected else "")
            with c3:
                hours = st.number_input("Durée (heures)", 0.0, 24.0, float(selected.get("hours",0) if selected else 0), .5)

            introduction = st.text_area("Introduction de la journée", selected.get("introduction","") if selected else "", height=100)
            activities = st.text_area("Activités réalisées", selected.get("activities","") if selected else "", height=140)
            observations = st.text_area("Observations scientifiques et techniques", selected.get("observations","") if selected else "", height=120)
            techniques = st.text_area("Techniques / méthodes observées", selected.get("techniques","") if selected else "", height=110)
            equipment = st.text_area("Matériel / équipements", selected.get("equipment","") if selected else "", height=100)
            samples = st.text_area("Échantillons / parcelles / GPS", selected.get("samples","") if selected else "", height=100)
            results = st.text_area("Résultats / mesures / données", selected.get("results","") if selected else "", height=120)
            difficulties = st.text_area("Difficultés rencontrées", selected.get("difficulties","") if selected else "", height=90)
            solutions = st.text_area("Solutions / explications reçues", selected.get("solutions","") if selected else "", height=90)
            lessons = st.text_area("Ce que j'ai appris", selected.get("lessons","") if selected else "", height=120)
            questions = st.text_area("Questions à approfondir", selected.get("questions","") if selected else "", height=90)
            next_actions = st.text_area("Actions prévues", selected.get("next_actions","") if selected else "", height=90)
            conclusion = st.text_area("Conclusion de la journée", selected.get("conclusion","") if selected else "", height=110)

            if st.form_submit_button("💾 Enregistrer la journée", type="primary"):
                now = datetime.now().isoformat(timespec="seconds")
                vals = (
                    log_date.isoformat(), title, location, supervisor, activities,
                    observations, techniques, equipment, samples, results,
                    difficulties, solutions, lessons, questions, next_actions,
                    introduction, conclusion, hours, now, now
                )
                if selected:
                    db_exec("""
                        UPDATE daily_logs SET
                        log_date=?, title=?, location=?, supervisor=?, activities=?,
                        observations=?, techniques=?, equipment=?, samples=?, results=?,
                        difficulties=?, solutions=?, lessons=?, questions=?, next_actions=?,
                        introduction=?, conclusion=?, hours=?, updated_at=?
                        WHERE id=?
                    """, vals[:-1] + (selected["id"],))
                    audit("Modification journée", str(selected["id"]))
                else:
                    db_exec("""
                        INSERT INTO daily_logs
                        (log_date,title,location,supervisor,activities,observations,techniques,
                         equipment,samples,results,difficulties,solutions,lessons,questions,
                         next_actions,introduction,conclusion,hours,created_at,updated_at)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """, vals)
                    audit("Création journée", log_date.isoformat())
                st.success("Journée enregistrée.")
                st.rerun()

    if logs:
        st.markdown("### Historique")
        df = rows_to_df(logs)
        st.dataframe(
            df[["id","log_date","title","location","hours","lessons"]],
            use_container_width=True,
            hide_index=True
        )

# ============================================================
# PHOTOS
# ============================================================

elif page == "Photos":
    st.markdown('<div class="section-title">📷 Photos du stage</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Les photos sont enregistrées dans PostgreSQL / Supabase et peuvent être intégrées aux rapports PDF.</div>', unsafe_allow_html=True)

    logs = db_exec("SELECT * FROM daily_logs ORDER BY log_date DESC", fetch=True)
    if not logs:
        st.warning("Crée d'abord une journée dans le journal quotidien.")
    else:
        options = {
            f"{fmt_date(r['log_date'])} — {r['title'] or 'Sans titre'} — ID {r['id']}": r["id"]
            for r in logs
        }
        chosen = st.selectbox("Associer les photos à la journée", list(options))
        log_id = options[chosen]

        uploads = st.file_uploader(
            "Prendre / importer des photos",
            type=["jpg","jpeg","png","webp"],
            accept_multiple_files=True,
            help="Sur smartphone, cette zone peut permettre de sélectionner directement les photos prises avec l'appareil."
        )

        if uploads:
            st.markdown("### Aperçu")
            cols = st.columns(min(4, len(uploads)))
            for i, upload in enumerate(uploads):
                with cols[i % len(cols)]:
                    st.image(upload, use_container_width=True)
                    st.caption(upload.name)

            if st.button("📥 Enregistrer toutes les photos", type="primary"):
                saved = 0
                for upload in uploads:
                    raw = upload.getvalue()
                    try:
                        img = Image.open(io.BytesIO(raw))
                        if img.mode not in ("RGB", "L"):
                            img = img.convert("RGB")
                        # JPEG pour réduire fortement le volume de la base.
                        out = io.BytesIO()
                        img.save(out, format="JPEG", quality=88, optimize=True)
                        raw = out.getvalue()
                        mime = "image/jpeg"
                    except Exception:
                        mime = upload.type or "application/octet-stream"

                    db_exec("""
                        INSERT INTO photos
                        (log_id,photo_date,title,caption,category,filename,mime_type,data,created_at)
                        VALUES (?,?,?,?,?,?,?,?,?)
                    """, (
                        log_id, date.today().isoformat(), upload.name,
                        "", "Stage", upload.name, mime, memoryview(raw),
                        datetime.now().isoformat(timespec="seconds")
                    ))
                    saved += 1

                audit("Ajout photos", f"{saved} photo(s), journée {log_id}")
                st.success(f"{saved} photo(s) enregistrée(s).")
                st.rerun()

    photos = db_exec("SELECT * FROM photos ORDER BY photo_date DESC, id DESC", fetch=True)
    if photos:
        st.markdown("### 📚 Galerie")
        for start in range(0, len(photos), 2):
            group = photos[start:start+2]
            cols = st.columns(2)
            for col, r in zip(cols, group):
                with col:
                    st.markdown('<div class="photo-card">', unsafe_allow_html=True)
                    st.image(io.BytesIO(r["data"]), use_container_width=True)
                    st.caption(f"📅 {fmt_date(r['photo_date'])} · 📷 {r['filename']}")
                    st.markdown('</div>', unsafe_allow_html=True)
                    caption = st.text_input(
                        "Légende",
                        value=r["caption"] or "",
                        key=f"caption_{r['id']}"
                    )
                    if st.button("💾", key=f"save_photo_{r['id']}"):
                        db_exec("UPDATE photos SET caption=? WHERE id=?", (caption, r["id"]))
                        audit("Modification légende photo", str(r["id"]))
                        st.rerun()
                    if st.button("🗑️", key=f"delete_photo_{r['id']}"):
                        db_exec("DELETE FROM photos WHERE id=?", (r["id"],))
                        audit("Suppression photo", str(r["id"]))
                        st.rerun()

# ============================================================
# RAPPORT PDF
# ============================================================

elif page == "Rapport PDF":
    st.markdown('<div class="section-title">📄 Rapports PDF</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Rapports structurés avec introduction, développement, photos, bilan et conclusion.</div>', unsafe_allow_html=True)

    p = profile()

    st.markdown("""
    <div class="card" style="background:linear-gradient(135deg,#ffffff,#effaf2);border-left:6px solid #16a34a;">
        <div style="font-size:1.15rem;font-weight:800;color:#14532d;">📘 Centre de production des rapports</div>
        <div style="color:#667085;margin-top:5px;">
            Génère des rapports journaliers et mensuels avec une mise en page vert/blanc,
            des tableaux structurés, des introductions et conclusions, ainsi que des photographies
            en grand format.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Styles PDF
    styles = getSampleStyleSheet()
    # Palette PDF : vert / blanc, avec une hiérarchie visuelle forte.
    GREEN_900 = colors.HexColor("#14532d")
    GREEN_800 = colors.HexColor("#166534")
    GREEN_700 = colors.HexColor("#15803d")
    GREEN_100 = colors.HexColor("#dcfce7")
    GREEN_50 = colors.HexColor("#f0fdf4")
    GREY_700 = colors.HexColor("#344054")
    GREY_500 = colors.HexColor("#667085")
    BORDER = colors.HexColor("#cfe1d4")

    styles.add(ParagraphStyle(
        name="XTitle", parent=styles["Title"], fontName="Helvetica-Bold",
        fontSize=22, leading=26, alignment=TA_CENTER, textColor=GREEN_900,
        spaceAfter=7
    ))
    styles.add(ParagraphStyle(
        name="XSubtitle", parent=styles["BodyText"], fontName="Helvetica",
        fontSize=10, leading=13, alignment=TA_CENTER, textColor=GREY_500,
        spaceAfter=12
    ))
    styles.add(ParagraphStyle(
        name="XH1", parent=styles["Heading1"], fontName="Helvetica-Bold",
        fontSize=13.5, leading=17, textColor=GREEN_800,
        spaceBefore=11, spaceAfter=7
    ))
    styles.add(ParagraphStyle(
        name="XH2", parent=styles["Heading2"], fontName="Helvetica-Bold",
        fontSize=10.5, leading=14, textColor=GREEN_700,
        spaceBefore=7, spaceAfter=4
    ))
    styles.add(ParagraphStyle(
        name="XBody", parent=styles["BodyText"], fontName="Helvetica",
        fontSize=9.2, leading=13.5, textColor=GREY_700, spaceAfter=6
    ))
    styles.add(ParagraphStyle(
        name="XSmall", parent=styles["BodyText"], fontName="Helvetica",
        fontSize=7.6, leading=9.5, textColor=GREY_700, spaceAfter=2
    ))
    styles.add(ParagraphStyle(
        name="XCaption", parent=styles["BodyText"], fontName="Helvetica-Oblique",
        fontSize=8, leading=10, alignment=TA_CENTER, textColor=GREY_500,
        spaceBefore=3, spaceAfter=3
    ))
    styles.add(ParagraphStyle(
        name="XCover", parent=styles["Title"], fontName="Helvetica-Bold",
        fontSize=25, leading=29, alignment=TA_CENTER, textColor=GREEN_900,
        spaceAfter=12
    ))

    def P(text, style="XBody"):
        # Conserve uniquement les balises <b> explicitement utilisées par le rapport.
        # Le reste du contenu est échappé pour éviter que du HTML utilisateur
        # soit interprété par ReportLab.
        raw = str(text or "")
        raw = raw.replace("<b>", "@@B_OPEN@@").replace("</b>", "@@B_CLOSE@@")
        safe = clean_html(raw) or "—"
        safe = safe.replace("@@B_OPEN@@", "<b>").replace("@@B_CLOSE@@", "</b>")
        return Paragraph(safe, styles[style])

    def pdf_footer(canvas, doc):
        canvas.saveState()
        # Bandeau supérieur discret
        canvas.setFillColor(GREEN_800)
        canvas.rect(0, A4[1]-0.22*cm, A4[0], 0.22*cm, stroke=0, fill=1)
        # Pied de page
        canvas.setStrokeColor(BORDER)
        canvas.line(1.2*cm, 1.08*cm, A4[0]-1.2*cm, 1.08*cm)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(GREY_500)
        canvas.drawString(
            1.3*cm, .72*cm,
            "Carnet de stage · L2 DSTAAN · Laboratoire de pédologie · ISRA / CRA Saint-Louis"
        )
        canvas.setFillColor(GREEN_800)
        canvas.drawRightString(A4[0]-1.3*cm, .72*cm, f"PAGE {doc.page}")
        canvas.restoreState()

    def make_daily_pdf(log_id):
        rlist = db_exec("SELECT * FROM daily_logs WHERE id=?", (log_id,), fetch=True)
        if not rlist:
            return b""
        r = dict(rlist[0])
        photos = db_exec("SELECT * FROM photos WHERE log_id=? ORDER BY id", (log_id,), fetch=True)

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=1.3*cm, leftMargin=1.3*cm, topMargin=1.3*cm, bottomMargin=1.4*cm)
        story = [
            Spacer(1, 0.35*cm),
            P("RAPPORT JOURNALIER DE STAGE", "XCover"),
            P("L2 DSTAAN · Laboratoire de pédologie · ISRA / CRA Saint-Louis", "XSubtitle"),
        ]

        info = [
            [P("<b>Étudiant</b>","XSmall"), P(p.get("student_name"),"XSmall"),
             P("<b>Date</b>","XSmall"), P(fmt_date(r["log_date"]),"XSmall")],
            [P("<b>Structure</b>","XSmall"), P(p.get("host_structure"),"XSmall"),
             P("<b>Service</b>","XSmall"), P(r.get("location") or p.get("service"),"XSmall")],
            [P("<b>Encadreur</b>","XSmall"), P(r.get("supervisor") or p.get("supervisor"),"XSmall"),
             P("<b>Durée</b>","XSmall"), P(f"{r.get('hours',0)} h","XSmall")],
        ]
        t = Table(info, colWidths=[2.7*cm,6.0*cm,2.7*cm,4.8*cm])
        t.setStyle(TableStyle([
            ("GRID",(0,0),(-1,-1),.5,colors.HexColor("#777777")),
            ("BACKGROUND",(0,0),(-1,-1),colors.white),
            ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
            ("LEFTPADDING",(0,0),(-1,-1),6),
            ("RIGHTPADDING",(0,0),(-1,-1),6),
            ("TOPPADDING",(0,0),(-1,-1),6),
            ("BOTTOMPADDING",(0,0),(-1,-1),6),
        ]))
        story = [
            Spacer(1, 0.25*cm),
            P("RAPPORT JOURNALIER DE STAGE", "XCover"),
            P("L2 DSTAAN · Laboratoire de pédologie · ISRA / CRA Saint-Louis", "XSubtitle"),
            t,
            Spacer(1, 10),
        ]

        sections = [
            ("1. Introduction", r.get("introduction")),
            ("2. Objectif de la journée", r.get("title")),
            ("3. Activités réalisées", r.get("activities")),
            ("4. Observations scientifiques et techniques", r.get("observations")),
            ("5. Techniques et méthodes", r.get("techniques")),
            ("6. Matériel et équipements", r.get("equipment")),
            ("7. Échantillons / parcelles / GPS", r.get("samples")),
            ("8. Résultats et données", r.get("results")),
            ("9. Difficultés rencontrées", r.get("difficulties")),
            ("10. Solutions et explications", r.get("solutions")),
            ("11. Acquis de la journée", r.get("lessons")),
            ("12. Questions à approfondir", r.get("questions")),
            ("13. Actions prévues", r.get("next_actions")),
            ("14. Conclusion", r.get("conclusion")),
        ]
        for title, text in sections:
            story += [P(title,"XH1"), P(text or "Non renseigné.")]

        if photos:
            story += [PageBreak(), P("15. Photographies et observations visuelles","XH1")]
            photo_rows = []
            current = []
            for ph in photos:
                # Fichier temporaire réel : ReportLab lit l'image pendant doc.build().
                path = PHOTO_DIR / f"pdf_tmp_{ph['id']}.jpg"
                caption = ph.get("caption") or ph.get("filename") or "Photo"
                try:
                    raw = bytes(ph["data"])
                    source = io.BytesIO(raw)
                    with Image.open(source) as pil_img:
                        pil_img.load()
                        try:
                            from PIL import ImageOps
                            pil_img = ImageOps.exif_transpose(pil_img)
                        except Exception:
                            pass
                        if pil_img.mode in ("RGBA", "LA") or "transparency" in pil_img.info:
                            rgba = pil_img.convert("RGBA")
                            bg = Image.new("RGB", rgba.size, "white")
                            bg.paste(rgba, mask=rgba.getchannel("A"))
                            pil_img = bg
                        elif pil_img.mode != "RGB":
                            pil_img = pil_img.convert("RGB")
                        pil_img.save(path, format="JPEG", quality=90, optimize=True)

                    img = RLImage(
                        str(path),
                        width=7.8*cm,
                        height=6.2*cm,
                        preserveAspectRatio=True,
                        anchor="c",
                        lazy=0,
                    )
                    cell = [img, P(caption, "XCaption")]
                except Exception as exc:
                    cell = [
                        P(f"Image non disponible : {caption}", "XSmall"),
                        P(f"{caption} · {exc}", "XCaption")
                    ]
                current.append(cell)
                if len(current) == 2:
                    photo_rows.append(current)
                    current = []
            if current:
                current.append("")
                photo_rows.append(current)

            pt = Table(photo_rows, colWidths=[8.2*cm,8.2*cm])
            pt.setStyle(TableStyle([
                ("GRID",(0,0),(-1,-1),.45,colors.HexColor("#777777")),
                ("VALIGN",(0,0),(-1,-1),"TOP"),
                ("LEFTPADDING",(0,0),(-1,-1),6),("RIGHTPADDING",(0,0),(-1,-1),6),
                ("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6),
            ]))
            story.append(pt)

        story += [
            Spacer(1, 12),
            P("Signature de l'étudiant : ________________________________", "XBody"),
            P("Visa / observation de l'encadreur : ________________________________", "XBody"),
        ]
        doc.build(story, onFirstPage=pdf_footer, onLaterPages=pdf_footer)

        for ph in photos:
            tmp = PHOTO_DIR / f"pdf_tmp_{ph['id']}.png"
            try:
                tmp.unlink()
            except Exception:
                pass
        return buf.getvalue()

    def make_monthly_pdf(month):
        logs = [dict(r) for r in db_exec(
            "SELECT * FROM daily_logs WHERE substr(log_date,1,7)=? ORDER BY log_date,id", (month,), fetch=True
        )]
        analyses = [dict(r) for r in db_exec(
            "SELECT * FROM analyses WHERE substr(analysis_date,1,7)=? ORDER BY analysis_date,id", (month,), fetch=True
        )]
        samples = [dict(r) for r in db_exec(
            "SELECT * FROM samples WHERE substr(sample_date,1,7)=? ORDER BY sample_date,id", (month,), fetch=True
        )]
        monthly_rows = db_exec("SELECT * FROM monthly_logs WHERE month=?", (month,), fetch=True)
        m = dict(monthly_rows[0]) if monthly_rows else {}
        photos = db_exec("""
            SELECT p.* FROM photos p
            LEFT JOIN daily_logs d ON d.id=p.log_id
            WHERE substr(d.log_date,1,7)=?
               OR substr(p.photo_date,1,7)=?
            ORDER BY p.id
        """, (month, month), fetch=True)

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=1.2*cm, leftMargin=1.2*cm, topMargin=1.2*cm, bottomMargin=1.4*cm)
        story = [
            Spacer(1, 0.35*cm),
            P("RAPPORT MENSUEL DE STAGE", "XCover"),
            P(f"{month_label(month)} · L2 DSTAAN · Laboratoire de pédologie · ISRA / CRA Saint-Louis", "XSubtitle"),
        ]

        info = [
            [P("<b>Étudiant</b>","XSmall"), P(p.get("student_name"),"XSmall"),
             P("<b>Formation</b>","XSmall"), P(f"{p.get('formation','')} {p.get('level','')}","XSmall")],
            [P("<b>Structure</b>","XSmall"), P(p.get("host_structure"),"XSmall"),
             P("<b>Service</b>","XSmall"), P(p.get("service"),"XSmall")],
            [P("<b>Encadreur</b>","XSmall"), P(p.get("supervisor"),"XSmall"),
             P("<b>Période</b>","XSmall"), P(f"{p.get('start_date','')} → {p.get('end_date','')}","XSmall")],
        ]
        it = Table(info, colWidths=[2.7*cm,6.0*cm,2.7*cm,4.8*cm])
        it.setStyle(TableStyle([
            ("GRID",(0,0),(-1,-1),.5,colors.HexColor("#777777")),
            ("BACKGROUND",(0,0),(-1,-1),colors.white),
            ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
            ("LEFTPADDING",(0,0),(-1,-1),6),
            ("RIGHTPADDING",(0,0),(-1,-1),6),
            ("TOPPADDING",(0,0),(-1,-1),6),
            ("BOTTOMPADDING",(0,0),(-1,-1),6),
        ]))
        story = [
            Spacer(1, 0.25*cm),
            P("RAPPORT MENSUEL DE STAGE", "XCover"),
            P(f"{month_label(month)} · L2 DSTAAN · Laboratoire de pédologie · ISRA / CRA Saint-Louis", "XSubtitle"),
            it,
            Spacer(1, 10),
        ]

        total_hours = sum(float(x.get("hours") or 0) for x in logs)
        # Priorité au contenu réellement renseigné par l'étudiant.
        # Introduction mensuelle si renseignée, sinon présentation du profil.
        # Les objectifs généraux du profil sont toujours repris dans le rapport.
        profile_intro = (p.get("presentation") or "").strip()
        profile_objectives = (p.get("objectives") or "").strip()
        monthly_intro = (m.get("introduction") or "").strip()
        monthly_objectives = (m.get("objectives_next") or "").strip()

        report_intro = monthly_intro or profile_intro or "Introduction non renseignée."

        story += [
            P("1. Introduction", "XH1"),
            P(report_intro),
            P("2. Objectifs du stage", "XH1"),
            P(profile_objectives or "Objectifs du stage non renseignés."),
        ]

        if monthly_objectives:
            story += [
                P("3. Objectifs du mois suivant", "XH1"),
                P(monthly_objectives),
            ]

        story += [
            P("4. Synthèse générale", "XH1"),
            P(m.get("summary") or "Synthèse non renseignée."),
            P("5. Activités réalisées", "XH1"),
            P(m.get("activities") or "Activités non renseignées."),
            P("6. Analyses et travaux scientifiques", "XH1"),
            P(m.get("analyses") or "Travaux non renseignés."),
            P("7. Travaux de terrain", "XH1"),
            P(m.get("fieldwork") or "Travaux de terrain non renseignés."),
            P("8. Compétences acquises", "XH1"),
            P(m.get("skills") or "Compétences non renseignées."),
            P("9. Résultats et apports", "XH1"),
            P(m.get("results") or "Résultats non renseignés."),
            P("10. Difficultés et solutions", "XH1"),
            P(m.get("difficulties") or "Difficultés non renseignées."),
            P(m.get("solutions") or "Solutions non renseignées."),
            P("11. Bilan personnel", "XH1"),
            P(m.get("lessons") or "Bilan non renseigné."),
        ]

        story += [P("13. Indicateurs du mois", "XH1")]
        kpi = Table([
            [P("<b>Journées</b>","XSmall"), P("<b>Heures</b>","XSmall"), P("<b>Analyses</b>","XSmall"), P("<b>Échantillons</b>","XSmall"), P("<b>Photos</b>","XSmall")],
            [P(str(len(logs)),"XSmall"), P(f"{total_hours:.1f}","XSmall"), P(str(len(analyses)),"XSmall"), P(str(len(samples)),"XSmall"), P(str(len(photos)),"XSmall")]
        ], colWidths=[3.2*cm]*5)
        kpi.setStyle(TableStyle([("GRID",(0,0),(-1,-1),.45,colors.HexColor("#777777")),("BACKGROUND",(0,0),(-1,0),colors.white),("ALIGN",(0,0),(-1,-1),"CENTER")]))
        story.append(kpi)

        if logs:
            story += [P("14. Chronologie des journées", "XH1")]
            rows = [[P("<b>Date</b>","XSmall"),P("<b>Activité</b>","XSmall"),P("<b>Heures</b>","XSmall")]]
            for x in logs:
                rows.append([P(fmt_date(x["log_date"]),"XSmall"),P(x["title"] or "—","XSmall"),P(str(x["hours"] or 0),"XSmall")])
            tt = Table(rows, colWidths=[3*cm,12*cm,2*cm], repeatRows=1)
            tt.setStyle(TableStyle([("GRID",(0,0),(-1,-1),.45,colors.HexColor("#777777")),("BACKGROUND",(0,0),(-1,0),colors.white),("VALIGN",(0,0),(-1,-1),"TOP")]))
            story.append(tt)

        if analyses:
            story += [P("15. Analyses enregistrées", "XH1")]
            rows = [[P("<b>Date</b>","XSmall"),P("<b>Échantillon</b>","XSmall"),P("<b>Analyse</b>","XSmall"),P("<b>Résultat</b>","XSmall"),P("<b>Unité</b>","XSmall")]]
            for x in analyses:
                rows.append([
                    P(fmt_date(x["analysis_date"]),"XSmall"),
                    P(x.get("sample_code"),"XSmall"),
                    P(x.get("analysis_name"),"XSmall"),
                    P(x.get("result"),"XSmall"),
                    P(x.get("unit"),"XSmall")
                ])
            at = Table(rows, colWidths=[2.3*cm,3*cm,5*cm,3*cm,2*cm], repeatRows=1)
            at.setStyle(TableStyle([("GRID",(0,0),(-1,-1),.45,colors.HexColor("#777777")),("BACKGROUND",(0,0),(-1,0),colors.white),("VALIGN",(0,0),(-1,-1),"TOP")]))
            story.append(at)

        if photos:
            story += [PageBreak(), P("16. Photographies du mois", "XH1")]
            photo_rows = []
            current = []
            for ph in photos:
                # Fichier temporaire réel : ReportLab lit l'image pendant doc.build().
                path = PHOTO_DIR / f"pdf_month_tmp_{ph['id']}.jpg"
                caption = ph.get("caption") or ph.get("filename") or "Photo"
                try:
                    raw = bytes(ph["data"])
                    source = io.BytesIO(raw)
                    with Image.open(source) as pil_img:
                        pil_img.load()
                        try:
                            from PIL import ImageOps
                            pil_img = ImageOps.exif_transpose(pil_img)
                        except Exception:
                            pass
                        if pil_img.mode in ("RGBA", "LA") or "transparency" in pil_img.info:
                            rgba = pil_img.convert("RGBA")
                            bg = Image.new("RGB", rgba.size, "white")
                            bg.paste(rgba, mask=rgba.getchannel("A"))
                            pil_img = bg
                        elif pil_img.mode != "RGB":
                            pil_img = pil_img.convert("RGB")
                        pil_img.save(path, format="JPEG", quality=90, optimize=True)

                    img = RLImage(
                        str(path),
                        width=7.8*cm,
                        height=6.2*cm,
                        preserveAspectRatio=True,
                        anchor="c",
                        lazy=0,
                    )
                    current.append([img, P(caption, "XCaption")])
                except Exception as exc:
                    current.append([
                        P(f"Image non disponible : {caption}", "XSmall"),
                        P(f"{caption} · {exc}", "XCaption")
                    ])
                if len(current)==2:
                    photo_rows.append(current); current=[]
            if current:
                current.append(""); photo_rows.append(current)
            pt = Table(photo_rows, colWidths=[8.2*cm,8.2*cm])
            pt.setStyle(TableStyle([("GRID",(0,0),(-1,-1),.45,colors.HexColor("#777777")),("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),5),("TOPPADDING",(0,0),(-1,-1),5)]))
            story.append(pt)

        story += [
            P("17. Conclusion générale", "XH1"),
            P(m.get("conclusion") or
              "Ce mois d'immersion a permis de consolider les observations et les apprentissages réalisés au laboratoire. "
              "Les activités doivent être replacées dans une démarche de rigueur scientifique, de traçabilité des échantillons, "
              "de respect des procédures et de mise en relation des résultats avec les problématiques agronomiques."),
            P("18. Observation de l'encadreur", "XH1"),
            P(m.get("supervisor_comment") or "Observation / visa de l'encadreur :"),
            Spacer(1, 10),
            P("Signature de l'étudiant : ________________________________", "XBody"),
            P("Signature / visa de l'encadreur : ________________________________", "XBody"),
        ]

        doc.build(story, onFirstPage=pdf_footer, onLaterPages=pdf_footer)

        for ph in photos:
            tmp = PHOTO_DIR / f"pdf_month_tmp_{ph['id']}.jpg"
            try: tmp.unlink()
            except Exception: pass

        return buf.getvalue()

    # -------- Journalier --------
    st.markdown("### 📄 Rapport journalier")
    logs = db_exec("SELECT * FROM daily_logs ORDER BY log_date DESC,id DESC", fetch=True)
    if logs:
        choices = {f"{fmt_date(r['log_date'])} — {r['title'] or 'Sans titre'} — ID {r['id']}": r["id"] for r in logs}
        label = st.selectbox("Journée à exporter", list(choices), key="pdf_daily_choice")
        daily_id = choices[label]
        photo_count = len(db_exec("SELECT id FROM photos WHERE log_id=?", (daily_id,), fetch=True))
        st.info(f"{photo_count} photo(s) seront intégrées au rapport si elles sont associées à cette journée.")
        daily_pdf = make_daily_pdf(daily_id)
        st.download_button(
            "⬇️ Télécharger le rapport journalier PDF",
            data=daily_pdf,
            file_name=f"rapport_journalier_{next(r['log_date'] for r in logs if r['id']==daily_id)}.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )
    else:
        st.info("Aucune journée disponible.")

    # -------- Mensuel --------
    st.markdown("### 📊 Rapport mensuel")
    months = sorted(set(
        [r["log_date"][:7] for r in logs if r["log_date"]] + [date.today().strftime("%Y-%m")]
    ), reverse=True)
    month = st.selectbox("Mois à exporter", months, format_func=month_label, key="pdf_month_choice")

    monthly_exists = bool(db_exec("SELECT id FROM monthly_logs WHERE month=?", (month,), fetch=True))
    if not monthly_exists:
        st.warning("Le texte personnalisé de ce mois n'est pas encore enregistré. Le PDF utilisera des textes par défaut pour les parties manquantes.")

    monthly_photo_count = len(db_exec("""
        SELECT p.id
        FROM photos p
        LEFT JOIN daily_logs d ON d.id=p.log_id
        WHERE substr(d.log_date,1,7)=?
           OR substr(p.photo_date,1,7)=?
    """, (month, month), fetch=True))
    st.info(f"📷 {monthly_photo_count} photo(s) trouvée(s) pour {month_label(month)} et intégrées au PDF.")

    monthly_pdf = make_monthly_pdf(month)
    st.download_button(
        "⬇️ Télécharger le rapport mensuel PDF",
        data=monthly_pdf,
        file_name=f"rapport_mensuel_{month}.pdf",
        mime="application/pdf",
        type="primary",
        use_container_width=True
    )

    # -------- Édition du rapport mensuel --------
    st.markdown("### ✍️ Préparer le contenu du rapport mensuel")
    existing = db_exec("SELECT * FROM monthly_logs WHERE month=?", (month,), fetch=True)
    m = dict(existing[0]) if existing else {}

    with st.form("monthly_edit_form"):
        introduction = st.text_area("Introduction", m.get("introduction",""), height=130)
        summary = st.text_area("Synthèse générale", m.get("summary",""), height=130)
        activities = st.text_area("Activités réalisées", m.get("activities",""), height=130)
        analyses_txt = st.text_area("Analyses et travaux scientifiques", m.get("analyses",""), height=120)
        fieldwork = st.text_area("Travaux de terrain", m.get("fieldwork",""), height=110)
        skills_txt = st.text_area("Compétences acquises", m.get("skills",""), height=110)
        results = st.text_area("Résultats et apports", m.get("results",""), height=110)
        difficulties = st.text_area("Difficultés", m.get("difficulties",""), height=90)
        solutions = st.text_area("Solutions / améliorations", m.get("solutions",""), height=90)
        lessons = st.text_area("Bilan personnel", m.get("lessons",""), height=110)
        objectives_next = st.text_area("Objectifs du mois suivant", m.get("objectives_next",""), height=100)
        conclusion = st.text_area("Conclusion générale", m.get("conclusion",""), height=130)
        supervisor_comment = st.text_area("Observation de l'encadreur", m.get("supervisor_comment",""), height=90)

        if st.form_submit_button("💾 Enregistrer le rapport mensuel", type="primary"):
            now = datetime.now().isoformat(timespec="seconds")
            if m:
                db_exec("""
                    UPDATE monthly_logs SET introduction=?,summary=?,activities=?,analyses=?,
                    fieldwork=?,skills=?,results=?,difficulties=?,solutions=?,lessons=?,
                    objectives_next=?,conclusion=?,supervisor_comment=?,updated_at=?
                    WHERE month=?
                """, (
                    introduction,summary,activities,analyses_txt,fieldwork,skills_txt,results,
                    difficulties,solutions,lessons,objectives_next,conclusion,supervisor_comment,now,month
                ))
            else:
                db_exec("""
                    INSERT INTO monthly_logs
                    (month,introduction,summary,activities,analyses,fieldwork,skills,results,
                     difficulties,solutions,lessons,objectives_next,conclusion,supervisor_comment,
                     created_at,updated_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    month,introduction,summary,activities,analyses_txt,fieldwork,skills_txt,results,
                    difficulties,solutions,lessons,objectives_next,conclusion,supervisor_comment,now,now
                ))
            audit("Enregistrement rapport mensuel", month)
            st.success("Contenu mensuel enregistré.")
            st.rerun()

# ============================================================
# ANALYSES
# ============================================================

elif page == "Analyses":
    st.markdown('<div class="section-title">🧪 Analyses de sols</div>', unsafe_allow_html=True)
    st.caption("Documente ici ce que tu observes. Les méthodes précises doivent être confirmées par le personnel du laboratoire.")

    rows = db_exec("SELECT * FROM analyses ORDER BY analysis_date DESC,id DESC", fetch=True)
    mode = st.radio("Action", ["Ajouter","Modifier","Supprimer"], horizontal=True)
    selected = None

    if mode != "Ajouter" and rows:
        labels = {f"ID {r['id']} — {fmt_date(r['analysis_date'])} — {r['analysis_name']} — {r['sample_code']}":r["id"] for r in rows}
        chosen = st.selectbox("Analyse", list(labels))
        selected = dict(next(r for r in rows if r["id"]==labels[chosen]))

    if mode == "Supprimer":
        if selected and st.button("🗑️ Supprimer", type="primary"):
            db_exec("DELETE FROM analyses WHERE id=?", (selected["id"],))
            audit("Suppression analyse", str(selected["id"]))
            st.rerun()
    else:
        d = date.today()
        if selected:
            try: d = datetime.strptime(selected["analysis_date"], "%Y-%m-%d").date()
            except Exception: pass

        with st.form("analysis_form"):
            c1,c2,c3=st.columns(3)
            with c1:
                analysis_date=st.date_input("Date",d)
                sample_code=st.text_input("Code échantillon",selected.get("sample_code","") if selected else "")
            with c2:
                analysis_name=st.selectbox("Analyse",["pH","Conductivité électrique (CE)","Granulométrie","Matière organique","Carbone organique","Azote","Phosphore","Potassium","Calcaire / carbonates","Autre"])
                unit=st.text_input("Unité",selected.get("unit","") if selected else "")
            with c3:
                equipment=st.text_input("Appareil / matériel",selected.get("equipment","") if selected else "")
                result=st.text_input("Résultat",selected.get("result","") if selected else "")
            objective=st.text_area("Objectif",selected.get("objective","") if selected else "",height=80)
            method=st.text_area("Méthode / protocole observé",selected.get("method","") if selected else "",height=100)
            interpretation=st.text_area("Interprétation",selected.get("interpretation","") if selected else "",height=100)
            agronomic_use=st.text_area("Utilité agronomique",selected.get("agronomic_use","") if selected else "",height=100)
            quality_control=st.text_area("Contrôle qualité",selected.get("quality_control","") if selected else "",height=80)
            observations=st.text_area("Observations",selected.get("observations","") if selected else "",height=90)

            if st.form_submit_button("💾 Enregistrer",type="primary"):
                if selected:
                    db_exec("""
                        UPDATE analyses SET analysis_date=?,sample_code=?,analysis_name=?,objective=?,method=?,
                        equipment=?,unit=?,result=?,interpretation=?,agronomic_use=?,quality_control=?,observations=?
                        WHERE id=?
                    """,(analysis_date.isoformat(),sample_code,analysis_name,objective,method,equipment,unit,result,interpretation,agronomic_use,quality_control,observations,selected["id"]))
                else:
                    db_exec("""
                        INSERT INTO analyses
                        (analysis_date,sample_code,analysis_name,objective,method,equipment,unit,result,
                         interpretation,agronomic_use,quality_control,observations,created_at)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,(analysis_date.isoformat(),sample_code,analysis_name,objective,method,equipment,unit,result,interpretation,agronomic_use,quality_control,observations,datetime.now().isoformat(timespec="seconds")))
                audit("Enregistrement analyse",analysis_name)
                st.success("Analyse enregistrée.")
                st.rerun()

    if rows:
        st.dataframe(rows_to_df(rows),use_container_width=True,hide_index=True)

# ============================================================
# ÉCHANTILLONS
# ============================================================

elif page == "Échantillons":
    st.markdown('<div class="section-title">🧫 Registre des échantillons</div>', unsafe_allow_html=True)
    st.caption("Traçabilité : code → parcelle → localisation → profondeur → analyses → interprétation.")

    rows=db_exec("SELECT * FROM samples ORDER BY sample_date DESC,id DESC",fetch=True)
    mode=st.radio("Action",["Ajouter","Modifier","Supprimer"],horizontal=True)
    selected=None
    if mode!="Ajouter" and rows:
        labels={f"{r['sample_code']} — {fmt_date(r['sample_date'])} — ID {r['id']}":r["id"] for r in rows}
        chosen=st.selectbox("Échantillon",list(labels))
        selected=dict(next(r for r in rows if r["id"]==labels[chosen]))

    if mode=="Supprimer":
        if selected and st.button("🗑️ Supprimer",type="primary"):
            db_exec("DELETE FROM samples WHERE id=?",(selected["id"],))
            audit("Suppression échantillon",selected["sample_code"])
            st.rerun()
    else:
        d=date.today()
        if selected:
            try:d=datetime.strptime(selected["sample_date"],"%Y-%m-%d").date()
            except Exception:pass
        with st.form("sample_form"):
            c1,c2,c3=st.columns(3)
            with c1:
                sample_code=st.text_input("Code *",selected.get("sample_code","") if selected else "")
                sample_date=st.date_input("Date",d)
                parcel=st.text_input("Parcelle / zone",selected.get("parcel","") if selected else "")
                locality=st.text_input("Localité",selected.get("locality","") if selected else "")
            with c2:
                gps=st.text_input("GPS",selected.get("gps","") if selected else "")
                depth=st.text_input("Profondeur",selected.get("depth","") if selected else "")
                crop=st.text_input("Culture",selected.get("crop","") if selected else "")
                sample_type=st.selectbox("Type",["Sol","Profil de sol","Eau","Plante","Autre"])
            with c3:
                appearance=st.text_area("Aspect / description",selected.get("appearance","") if selected else "",height=150)
            preparation=st.text_area("Préparation",selected.get("preparation","") if selected else "",height=90)
            analyses=st.text_area("Analyses demandées / réalisées",selected.get("analyses","") if selected else "",height=90)
            result_summary=st.text_area("Résumé des résultats",selected.get("result_summary","") if selected else "",height=90)
            interpretation=st.text_area("Interprétation",selected.get("interpretation","") if selected else "",height=90)
            remarks=st.text_area("Remarques",selected.get("remarks","") if selected else "",height=80)
            if st.form_submit_button("💾 Enregistrer",type="primary"):
                try:
                    if selected:
                        db_exec("""
                            UPDATE samples SET sample_code=?,sample_date=?,parcel=?,locality=?,gps=?,depth=?,crop=?,
                            sample_type=?,appearance=?,preparation=?,analyses=?,result_summary=?,interpretation=?,remarks=?
                            WHERE id=?
                        """,(sample_code,sample_date.isoformat(),parcel,locality,gps,depth,crop,sample_type,appearance,preparation,analyses,result_summary,interpretation,remarks,selected["id"]))
                    else:
                        db_exec("""
                            INSERT INTO samples
                            (sample_code,sample_date,parcel,locality,gps,depth,crop,sample_type,appearance,preparation,
                             analyses,result_summary,interpretation,remarks,created_at)
                            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                        """,(sample_code,sample_date.isoformat(),parcel,locality,gps,depth,crop,sample_type,appearance,preparation,analyses,result_summary,interpretation,remarks,datetime.now().isoformat(timespec="seconds")))
                    audit("Enregistrement échantillon",sample_code)
                    st.success("Échantillon enregistré.")
                    st.rerun()
                except psycopg.IntegrityError:
                    st.error("Ce code d'échantillon existe déjà.")
    if rows:
        st.dataframe(rows_to_df(rows),use_container_width=True,hide_index=True)

# ============================================================
# MATÉRIEL
# ============================================================

elif page == "Matériel":
    st.markdown('<div class="section-title">🔬 Matériel et équipements</div>',unsafe_allow_html=True)
    st.markdown('<div class="card"><b>🛠️ Carnet technique</b><br><span class="small">Note le rôle, le principe, les précautions de sécurité et ce que tu as réellement appris sur chaque équipement.</span></div>',unsafe_allow_html=True)
    rows=db_exec("SELECT * FROM equipment ORDER BY category,name",fetch=True)
    with st.form("equipment_form"):
        c1,c2=st.columns(2)
        with c1:
            name=st.text_input("Nom")
            category=st.selectbox("Catégorie",["Laboratoire","Terrain","Mesure","Préparation","Sécurité","Autre"])
            function=st.text_area("Fonction",height=80)
        with c2:
            principle=st.text_area("Principe général",height=80)
            safety=st.text_area("Sécurité",height=80)
            observations=st.text_area("Observation / apprentissage",height=80)
        learned=st.checkbox("Je maîtrise maintenant son rôle")
        if st.form_submit_button("💾 Ajouter",type="primary"):
            db_exec("""INSERT INTO equipment(name,category,function,principle,safety,observations,learned,created_at)
                       VALUES (?,?,?,?,?,?,?,?)""",(name,category,function,principle,safety,observations,int(learned),datetime.now().isoformat(timespec="seconds")))
            audit("Ajout matériel",name); st.success("Ajouté."); st.rerun()
    if rows:
        st.dataframe(rows_to_df(rows),use_container_width=True,hide_index=True)

# ============================================================
# COMPÉTENCES
# ============================================================

elif page == "Compétences":
    st.markdown('<div class="section-title">🎓 Compétences</div>',unsafe_allow_html=True)
    st.markdown('<div class="card"><b>📈 Progression personnelle</b><br><span class="small">Mets à jour tes acquis au fur et à mesure du stage et conserve une preuve de chaque compétence.</span></div>',unsafe_allow_html=True)
    rows=db_exec("SELECT * FROM skills ORDER BY category,skill",fetch=True)
    df=rows_to_df(rows)
    if not df.empty:
        for cat in df["category"].dropna().unique():
            st.markdown(f"### {cat}")
            for _,r in df[df["category"]==cat].iterrows():
                c1,c2,c3=st.columns([4,2,4])
                c1.write(r["skill"])
                levels=["À découvrir","En cours","Acquis"]
                level=c2.selectbox("Niveau",levels,index=levels.index(r["level"]) if r["level"] in levels else 0,key=f"lv_{r['id']}")
                evidence=c3.text_input("Preuve",r["evidence"] or "",key=f"ev_{r['id']}")
                if c2.button("Enregistrer",key=f"save_{r['id']}"):
                    db_exec("UPDATE skills SET level=?,evidence=?,updated_at=? WHERE id=?",(level,evidence,datetime.now().isoformat(timespec="seconds"),r["id"]))
                    audit("Mise à jour compétence",r["skill"]); st.rerun()

# ============================================================
# ENCADREMENT
# ============================================================

elif page == "Encadrement":
    st.markdown('<div class="section-title">👥 Encadrement et contacts</div>',unsafe_allow_html=True)
    st.markdown('<div class="card"><b>🤝 Réseau d’encadrement</b><br><span class="small">Centralise les personnes, fonctions, services et notes utiles à ton immersion.</span></div>',unsafe_allow_html=True)
    rows=db_exec("SELECT * FROM contacts ORDER BY name",fetch=True)
    with st.form("contact_form"):
        c1,c2=st.columns(2)
        with c1:
            name=st.text_input("Nom")
            role=st.text_input("Fonction / rôle")
            service=st.text_input("Service")
        with c2:
            phone=st.text_input("Téléphone")
            email=st.text_input("Email")
            notes=st.text_area("Notes",height=100)
        if st.form_submit_button("💾 Ajouter",type="primary"):
            db_exec("""INSERT INTO contacts(name,role,service,phone,email,notes,created_at)
                       VALUES (?,?,?,?,?,?,?)""",(name,role,service,phone,email,notes,datetime.now().isoformat(timespec="seconds")))
            audit("Ajout contact",name); st.success("Contact ajouté."); st.rerun()
    if rows: st.dataframe(rows_to_df(rows),use_container_width=True,hide_index=True)

# ============================================================
# DOCUMENTS
# ============================================================

elif page == "Documents":
    st.markdown('<div class="section-title">📚 Documents et notes</div>',unsafe_allow_html=True)
    st.markdown('<div class="card"><b>📖 Bibliothèque de stage</b><br><span class="small">Références, protocoles, cours, articles et notes personnelles peuvent être recensés ici.</span></div>',unsafe_allow_html=True)
    rows=db_exec("SELECT * FROM documents ORDER BY doc_date DESC,id DESC",fetch=True)
    with st.form("document_form"):
        c1,c2=st.columns(2)
        with c1:
            doc_date=st.date_input("Date",date.today())
            title=st.text_input("Titre")
            doc_type=st.selectbox("Type",["Protocole","Cours","Article","Rapport","Note personnelle","Autre"])
        with c2:
            reference=st.text_input("Référence / source")
            notes=st.text_area("Notes",height=150)
        if st.form_submit_button("💾 Ajouter",type="primary"):
            db_exec("""INSERT INTO documents(doc_date,title,doc_type,reference,notes,created_at)
                       VALUES (?,?,?,?,?,?)""",(doc_date.isoformat(),title,doc_type,reference,notes,datetime.now().isoformat(timespec="seconds")))
            audit("Ajout document",title); st.success("Ajouté."); st.rerun()
    if rows: st.dataframe(rows_to_df(rows),use_container_width=True,hide_index=True)

# ============================================================
# SUIVI & OUTILS
# ============================================================

elif page == "Suivi & outils":
    st.markdown('<div class="section-title">🧰 Suivi & outils du stage</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Planning, sécurité, protocoles et outils pratiques réunis dans un seul espace pour éviter de multiplier les rubriques.</div>', unsafe_allow_html=True)

    tabs = st.tabs(["📅 Planning", "⚠️ Sécurité & incidents", "🧪 Protocoles", "🔎 Recherche rapide"])

    # ---------------- PLANNING ----------------
    with tabs[0]:
        st.markdown("### 📅 Planning et tâches")
        tasks = db_exec("SELECT * FROM planning ORDER BY task_date ASC, id ASC", fetch=True)
        task_options = {f"{fmt_date(r['task_date'])} — {r['title']} — ID {r['id']}": r for r in tasks}
        selected_task = st.selectbox("Modifier une tâche existante (optionnel)", ["➕ Nouvelle tâche"] + list(task_options), key="task_selector")
        existing = task_options.get(selected_task)

        with st.form("planning_form"):
            c1,c2 = st.columns(2)
            task_date = c1.date_input("Date", value=datetime.strptime(existing["task_date"], "%Y-%m-%d").date() if existing else date.today())
            title = c2.text_input("Activité / tâche", value=existing["title"] if existing else "")
            c3,c4,c5 = st.columns(3)
            category = c3.selectbox("Catégorie", ["Laboratoire","Terrain","Formation","Rapport","Réunion","Administratif","Autre"], index=(["Laboratoire","Terrain","Formation","Rapport","Réunion","Administratif","Autre"].index(existing["category"]) if existing and existing["category"] in ["Laboratoire","Terrain","Formation","Rapport","Réunion","Administratif","Autre"] else 0))
            priority = c4.selectbox("Priorité", ["Basse","Normale","Haute","Urgente"], index=(["Basse","Normale","Haute","Urgente"].index(existing["priority"]) if existing and existing["priority"] in ["Basse","Normale","Haute","Urgente"] else 1))
            status = c5.selectbox("État", ["À faire","En cours","Terminé","Reporté"], index=(["À faire","En cours","Terminé","Reporté"].index(existing["status"]) if existing and existing["status"] in ["À faire","En cours","Terminé","Reporté"] else 0))
            c6,c7 = st.columns(2)
            location = c6.text_input("Lieu", value=existing["location"] if existing else "")
            supervisor = c7.text_input("Encadreur", value=existing["supervisor"] if existing else "")
            notes = st.text_area("Notes / consignes", value=existing["notes"] if existing else "", height=100)
            submitted = st.form_submit_button("💾 Enregistrer", type="primary")

        if submitted:
            now = datetime.now().isoformat(timespec="seconds")
            completed_at = now if status == "Terminé" else (existing["completed_at"] if existing else None)
            values = (task_date.isoformat(), title, category, priority, status, location, supervisor, notes, completed_at, now)
            if existing:
                db_exec("""UPDATE planning SET task_date=?,title=?,category=?,priority=?,status=?,location=?,supervisor=?,notes=?,completed_at=?,updated_at=? WHERE id=?""", values + (existing["id"],))
                audit("Modification planning", str(existing["id"]))
            else:
                db_exec("""INSERT INTO planning(task_date,title,category,priority,status,location,supervisor,notes,completed_at,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)""", values[:9] + (now, now))
                audit("Création planning", title)
            st.success("Tâche enregistrée.")
            st.rerun()

        if tasks:
            st.dataframe(rows_to_df(tasks)[["id","task_date","title","category","priority","status","location"]], use_container_width=True, hide_index=True)

    # ---------------- SECURITE ----------------
    with tabs[1]:
        st.markdown("### ⚠️ Registre des incidents, anomalies et mesures de prévention")
        st.info("Documente uniquement les faits observés. Pour tout incident réel, applique d'abord les consignes de sécurité et informe l'encadreur selon les procédures du laboratoire.")
        incidents = db_exec("SELECT * FROM incidents ORDER BY incident_date DESC, id DESC", fetch=True)
        inc_options = {f"{fmt_date(r['incident_date'])} — {r['title']} — ID {r['id']}": r for r in incidents}
        inc_selected = st.selectbox("Modifier un enregistrement (optionnel)", ["➕ Nouvel enregistrement"] + list(inc_options), key="incident_selector")
        inc = inc_options.get(inc_selected)
        with st.form("incident_form"):
            c1,c2,c3 = st.columns(3)
            incident_date = c1.date_input("Date", value=datetime.strptime(inc["incident_date"], "%Y-%m-%d").date() if inc else date.today())
            ititle = c2.text_input("Intitulé", value=inc["title"] if inc else "")
            itype = c3.selectbox("Type", ["Sécurité","Matériel","Échantillon","Qualité","Organisation","Autre"], index=(["Sécurité","Matériel","Échantillon","Qualité","Organisation","Autre"].index(inc["type"]) if inc and inc["type"] in ["Sécurité","Matériel","Échantillon","Qualité","Organisation","Autre"] else 0))
            c4,c5,c6 = st.columns(3)
            severity = c4.selectbox("Niveau", ["Information","Faible","Modéré","Élevé"], index=(["Information","Faible","Modéré","Élevé"].index(inc["severity"]) if inc and inc["severity"] in ["Information","Faible","Modéré","Élevé"] else 0))
            location = c5.text_input("Lieu", value=inc["location"] if inc else "")
            declared_to = c6.text_input("Signalé à", value=inc["declared_to"] if inc else "")
            description = st.text_area("Description factuelle", value=inc["description"] if inc else "", height=100)
            immediate_actions = st.text_area("Mesures prises immédiatement", value=inc["immediate_actions"] if inc else "", height=90)
            prevention = st.text_area("Prévention / action corrective", value=inc["prevention"] if inc else "", height=90)
            closed = st.checkbox("Dossier clôturé", value=bool(inc["closed"]) if inc else False)
            inc_submit = st.form_submit_button("💾 Enregistrer l'incident", type="primary")
        if inc_submit:
            now = datetime.now().isoformat(timespec="seconds")
            vals=(incident_date.isoformat(),ititle,itype,severity,location,description,immediate_actions,prevention,declared_to,int(closed),now,now)
            if inc:
                db_exec("""UPDATE incidents SET incident_date=?,title=?,type=?,severity=?,location=?,description=?,immediate_actions=?,prevention=?,declared_to=?,closed=?,updated_at=? WHERE id=?""", vals[:-1] + (inc["id"],))
                audit("Modification incident", str(inc["id"]))
            else:
                db_exec("""INSERT INTO incidents(incident_date,title,type,severity,location,description,immediate_actions,prevention,declared_to,closed,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""", vals)
                audit("Création incident", ititle)
            st.success("Enregistrement sécurité sauvegardé.")
            st.rerun()
        if incidents:
            st.dataframe(rows_to_df(incidents)[["id","incident_date","title","type","severity","location","closed"]], use_container_width=True, hide_index=True)

    # ---------------- PROTOCOLES ----------------
    with tabs[2]:
        st.markdown("### 🧪 Bibliothèque de protocoles et fiches techniques")
        st.warning("Les fiches intégrées sont pédagogiques. Elles ne remplacent pas les procédures officielles du laboratoire ni les instructions de l'encadreur.")
        protocols = get_protocols()
        for pr in protocols:
            with st.expander(f"🧪 {pr['title']} — {pr['category']}"):
                st.markdown(f"**Objectif**  \n{pr['objective'] or '—'}")
                st.markdown(f"**Principe**  \n{pr['principle'] or '—'}")
                st.markdown(f"**Matériel**  \n{pr['materials'] or '—'}")
                st.markdown(f"**Étapes**  \n{pr['steps'] or '—'}")
                st.markdown(f"**Précautions**  \n{pr['precautions'] or '—'}")
                st.markdown(f"**Contrôle qualité**  \n{pr['quality_control'] or '—'}")
                st.markdown(f"**Références / consignes**  \n{pr['references'] or '—'}")
                st.caption(pr['notes'] or '')

    # ---------------- RECHERCHE ----------------
    with tabs[3]:
        st.markdown("### 🔎 Recherche rapide dans le carnet")
        query = st.text_input("Mot-clé", placeholder="ex. pH, granulométrie, échantillon, sécurité...")
        if query.strip():
            q=f"%{query.strip()}%"
            results=[]
            for table, label, fields in [
                ("daily_logs","Journal",["title","activities","observations","techniques","results","lessons"]),
                ("samples","Échantillons",["sample_code","parcel","locality","crop","analyses","interpretation"]),
                ("analyses","Analyses",["sample_code","analysis_name","method","result","interpretation"]),
                ("documents","Documents",["title","doc_type","reference","notes"]),
                ("planning","Planning",["title","category","notes"]),
            ]:
                condition=" OR ".join([f"{f} LIKE ?" for f in fields])
                found=db_exec(f"SELECT * FROM {table} WHERE {condition} ORDER BY id DESC LIMIT 30", tuple([q]*len(fields)), fetch=True)
                for r in found:
                    d=dict(r)
                    d["source"]=label
                    d["id_source"]=d.get("id")
                    results.append(d)
            if results:
                st.success(f"{len(results)} résultat(s) trouvé(s).")
                st.dataframe(pd.DataFrame(results).fillna(""), use_container_width=True, hide_index=True)
            else:
                st.info("Aucun résultat pour ce mot-clé.")

# ============================================================
# EXPORTS
# ============================================================

elif page == "Exports":
    st.markdown('<div class="section-title">📤 Exports et sauvegardes</div>',unsafe_allow_html=True)
    tables=["daily_logs","analyses","samples","equipment","skills","contacts","documents","planning","incidents","protocols","audit"]
    for table in tables:
        df=rows_to_df(db_exec(f"SELECT * FROM {table}",fetch=True))
        if not df.empty:
            st.download_button(
                f"⬇️ Exporter {table}.csv",
                df.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"{table}.csv",
                mime="text/csv",
                use_container_width=True
            )

    st.markdown("### 🩺 État des données")
    health = []
    for table in ["profile","daily_logs","photos","samples","analyses","equipment","skills","contacts","documents","planning","incidents","protocols","audit"]:
        try:
            count = db_exec(f"SELECT COUNT(*) AS n FROM {table}", fetch=True)[0]["n"]
            health.append({"Table": table, "Enregistrements": count})
        except Exception as exc:
            health.append({"Table": table, "Enregistrements": f"Erreur: {exc}"})
    st.dataframe(pd.DataFrame(health), use_container_width=True, hide_index=True)

    st.info("💡 La base de production est PostgreSQL/Supabase. Les sauvegardes se font côté Supabase.")

# ============================================================
# AUDIT
# ============================================================

elif page == "Audit":
    st.markdown("<div class='section-title'>🔐 Journal d'audit</div>",unsafe_allow_html=True)
    st.info("Cette rubrique est visible uniquement après authentification.")
    rows=db_exec("SELECT * FROM audit ORDER BY id DESC LIMIT 5000",fetch=True)
    if rows:
        st.dataframe(rows_to_df(rows),use_container_width=True,hide_index=True)
        df=rows_to_df(rows)
        st.download_button("⬇️ Exporter audit.csv",df.to_csv(index=False).encode("utf-8-sig"),"audit.csv","text/csv")

# ============================================================
# FOOTER
# ============================================================

st.markdown("---")
st.caption(
    f"🌱 Carnet de stage L2 DSTAAN · ISRA / CRA Saint-Louis · "
    f"Utilisateur : {st.session_state.user_login} · "
    f"{datetime.now().strftime('%d/%m/%Y %H:%M')}"
)

# Déconnexion accessible en bas, sans barre latérale.
if st.button("🚪 Se déconnecter"):
    audit("Déconnexion")
    st.session_state.authenticated=False
    st.session_state.user_login=None
    st.rerun()
