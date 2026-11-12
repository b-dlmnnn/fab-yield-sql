import math
import os
import sqlite3
import numpy as np
import pandas as pd
from src.build_db import create_fab_database

DB_FILE = "fab_telemetry.db"
MAX_ROWS = 500


def ensure_db():
    if not os.path.exists(DB_FILE):
        create_fab_database(DB_FILE)


def wilson_ci(k, n, z=1.96):
    if n == 0:
        return 0.0, 0.0
    p = k / float(n)
    denom = 1.0 + (z * z) / n
    center = p + (z * z) / (2.0 * n)
    margin = z * math.sqrt((p * (1.0 - p) + (z * z) / (4.0 * n)) / n)
    low = max(0.0, (center - margin) / denom) * 100.0
    high = min(1.0, (center + margin) / denom) * 100.0
    return round(low, 2), round(high, 2)


def two_prop_ztest(k1, n1, k2, n2):
    p1 = k1 / max(float(n1), 1.0)
    p2 = k2 / max(float(n2), 1.0)
    p_pool = (k1 + k2) / max(float(n1 + n2), 1.0)
    se = math.sqrt(max(p_pool * (1.0 - p_pool) * (1.0 / max(n1, 1) + 1.0 / max(n2, 1)), 1e-12))
    z_stat = (p1 - p2) / se
    p_val = math.erfc(abs(z_stat) / math.sqrt(2.0))
    return round(z_stat, 3), round(p_val, 5)


def enrich_equipment_stats(df_tools):
    tot_n = int(df_tools["n_wafers"].sum())
    tot_pass = int(df_tools["passed_wafers"].sum())
    ci_lows, ci_highs, z_scores, p_vals = list(), list(), list(), list()
    for _, row in df_tools.iterrows():
        k1, n1 = int(row["passed_wafers"]), int(row["n_wafers"])
        lo, hi = wilson_ci(k1, n1)
        z_s, p_v = two_prop_ztest(k1, n1, tot_pass - k1, tot_n - n1)
        ci_lows.append(lo)
        ci_highs.append(hi)
        z_scores.append(z_s)
        p_vals.append(p_v)
    out = df_tools.copy()
    out["ci_95_low"] = ci_lows
    out["ci_95_high"] = ci_highs
    out["z_vs_rest"] = z_scores
    out["p_value"] = p_vals
    return out


def add_spc_control_limits(df_lots):
    out = df_lots.copy()
    p_bar = float(out["n_passed"].sum()) / max(float(out["n_inspected"].sum()), 1.0)
    n_bar = float(out["n_inspected"].mean())
    sigma = math.sqrt(max(p_bar * (1.0 - p_bar) / max(n_bar, 1.0), 1e-9))
    out["spc_center_pct"] = round(p_bar * 100.0, 2)
    out["spc_ucl_pct"] = round(min(1.0, p_bar + 3.0 * sigma) * 100.0, 2)
    out["spc_lcl_pct"] = round(max(0.0, p_bar - 3.0 * sigma) * 100.0, 2)
    out["out_of_control"] = (out["lot_yield_pct"] < out["spc_lcl_pct"]) | (out["lot_yield_pct"] > out["spc_ucl_pct"])
    return out


def run_select_query(sql_text):
    ensure_db()
    lines = [l for l in sql_text.strip().splitlines() if not l.strip().startswith("--")]
    cleaned = "\n".join(lines).strip()
    if cleaned.endswith(";"):
        cleaned = cleaned.rstrip(";").strip()
    if ";" in cleaned:
        raise ValueError("Security Policy: Multi-statement SQL execution is blocked.")
    lowered = cleaned.lower()
    if not (lowered.startswith("select") or lowered.startswith("with")):
        raise ValueError("Security Policy: Only read-only SELECT or WITH queries are allowed.")
    forbidden = ("drop ", "delete ", "update ", "insert ", "alter ", "attach ", "pragma ", "replace ", "create ")
    if any(word in lowered for word in forbidden):
        raise ValueError("Security Policy: Write or schema-modifying keywords are blocked.")

    conn = sqlite3.connect(f"file:{DB_FILE}?mode=ro", uri=True, timeout=2.0)
    try:
        df = pd.read_sql_query(cleaned, conn)
        return df.head(MAX_ROWS)
    finally:
        conn.close()


def load_sql_templates():
    mapping = {
        "1. Equipment Yield, Wilson CI & Bottleneck Rank": "sql/01_equipment_yield.sql",
        "2. SPC Lot Yield Control Chart (LAG & Rolling)": "sql/02_spc_lot_trend.sql",
        "3. Shift x Tool Pareto Cost Attribution": "sql/03_shift_pareto.sql",
        "4. SiliconGuard Risk Decile Calibration Bridge": "sql/04_risk_calibration.sql",
    }
    out = {}
    for label, path in mapping.items():
        with open(path, "r") as f:
            out[label] = f.read()
    return out
