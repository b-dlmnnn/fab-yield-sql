import os
import sqlite3
import pandas as pd
from src.build_db import create_fab_database

DB_FILE = "fab_telemetry.db"


def ensure_db():
    if not os.path.exists(DB_FILE):
        create_fab_database(DB_FILE)


def run_select_query(sql_text):
    ensure_db()
    lines = [l for l in sql_text.strip().splitlines() if not l.strip().startswith("--")]
    cleaned = "\n".join(lines).strip()
    lowered = cleaned.lower()
    if not (lowered.startswith("select") or lowered.startswith("with")):
        raise ValueError("Security Policy: Only read-only SELECT or WITH (CTE) queries are permitted.")
    forbidden = ("drop ", "delete ", "update ", "insert ", "alter ", "attach ", "pragma ")
    if any(word in lowered for word in forbidden):
        raise ValueError("Security Policy: Write or schema-modifying SQL keywords are blocked.")

    conn = sqlite3.connect(f"file:{DB_FILE}?mode=ro", uri=True)
    try:
        return pd.read_sql_query(cleaned, conn)
    finally:
        conn.close()


def get_named_queries():
    with open("sql/analytics_queries.sql", "r") as f:
        raw = f.read()
    parts = [p.strip() for p in raw.split(";") if p.strip()]
    return {
        "1. Tool Yield vs. Target & Scrap Cost (CTE + Multi-JOIN)": parts.pop(0) + ";",
        "2. Lot-by-Lot Rolling Yield Trend (Window Function)": parts.pop(0) + ";",
        "3. Shift & Defect Root-Cause Breakdown (GROUP BY)": parts.pop(0) + ";",
    }
