import os
import sqlite3
import numpy as np
import pandas as pd


def create_fab_database(db_path="fab_telemetry.db", n_wafers=1200, seed=42):
    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")

    cur.executescript("""
    CREATE TABLE dim_equipment (
        tool_id TEXT PRIMARY KEY,
        process_step TEXT NOT NULL,
        chamber_model TEXT NOT NULL,
        target_yield_pct REAL NOT NULL,
        target_rationale TEXT NOT NULL
    );

    CREATE TABLE dim_shift (
        shift_id TEXT PRIMARY KEY,
        shift_label TEXT NOT NULL,
        hours_window TEXT NOT NULL
    );

    CREATE TABLE fact_wafer_inspection (
        wafer_id TEXT PRIMARY KEY,
        lot_id TEXT NOT NULL,
        lot_size INTEGER NOT NULL,
        tool_id TEXT NOT NULL,
        shift_id TEXT NOT NULL,
        inspected_at TEXT NOT NULL,
        chamber_temp_c REAL NOT NULL,
        rf_power_w REAL NOT NULL,
        predicted_sensor_risk REAL NOT NULL,
        risk_decile TEXT NOT NULL,
        defects_found INTEGER NOT NULL,
        primary_defect_type TEXT NOT NULL,
        defect_area_px INTEGER NOT NULL,
        routing_decision TEXT NOT NULL,
        is_passed INTEGER NOT NULL CHECK (is_passed IN (0, 1)),
        estimated_cost_usd REAL NOT NULL,
        FOREIGN KEY (tool_id) REFERENCES dim_equipment(tool_id),
        FOREIGN KEY (shift_id) REFERENCES dim_shift(shift_id)
    );

    CREATE INDEX idx_fact_tool ON fact_wafer_inspection(tool_id);
    CREATE INDEX idx_fact_shift ON fact_wafer_inspection(shift_id);
    CREATE INDEX idx_fact_lot ON fact_wafer_inspection(lot_id);
    """)

    tools_data = list((
        ("ETCH-01", "Plasma Etching", "Lam-Kiyo-FX", 94.0, "Historical Q3 baseline for dry etch uniformity"),
        ("LITHO-02", "DUV Lithography", "ASML-Twinscan", 95.5, "Tightest overlay spec in patterning module"),
        ("CVD-03", "Thin-Film Deposition", "Applied-Producer", 92.0, "Higher thermal stress tolerance in dielectric layer"),
        ("CMP-04", "Chemical Planarization", "Ebara-FREX", 94.5, "Post-planarization surface scratch SLA"),
    ))
    cur.executemany("INSERT INTO dim_equipment VALUES (?, ?, ?, ?, ?)", tools_data)

    shifts_data = list((
        ("SHIFT-A", "Shift-A (Morning)", "06:00 - 14:00"),
        ("SHIFT-B", "Shift-B (Evening)", "14:00 - 22:00"),
        ("SHIFT-C", "Shift-C (Night)", "22:00 - 06:00"),
    ))
    cur.executemany("INSERT INTO dim_shift VALUES (?, ?, ?)", shifts_data)

    rng = np.random.RandomState(seed)
    base_time = pd.Timestamp("2026-10-01 06:00:00")
    tool_ids = list(("ETCH-01", "LITHO-02", "CVD-03", "CMP-04"))
    shift_ids = list(("SHIFT-A", "SHIFT-B", "SHIFT-C"))

    for i in range(n_wafers):
        w_id = f"WFR-{10000 + i}"
        lot_id = f"LOT-{200 + (i // 25)}"
        tool_id = str(rng.choice(tool_ids, p=list((0.28, 0.25, 0.27, 0.20))))
        shift_id = str(rng.choice(shift_ids))
        ts = (base_time + pd.Timedelta(minutes=12 * i)).strftime("%Y-%m-%d %H:%M:%S")

        # Kontrollu sentetik anomali enjeksiyonu (CVD-03 +8%, SHIFT-C +4%)
        fail_rate = 0.06 + (0.08 if tool_id == "CVD-03" else 0.0) + (0.04 if shift_id == "SHIFT-C" else 0.0)
        is_defective = rng.rand() < fail_rate

        if is_defective:
            temp_c = round(float(rng.normal(368.0, 6.5)), 2)
            rf_w = round(float(rng.normal(1245.0, 35.0)), 1)
            s_prob = round(float(np.clip(rng.beta(5, 2), 0.15, 0.99)), 4)
            defects = int(rng.choice(list((1, 2, 3)), p=list((0.35, 0.45, 0.20))))
            d_type = str(rng.choice(list(("Solder Bridge", "Linear Scratch", "Micro-Particle")), p=list((0.48, 0.34, 0.18))))
            area_px = int(defects * rng.randint(110, 310))
            routing = "BLOCK_PACKAGING" if (defects >= 2 or s_prob >= 0.65) else "SECONDARY_LAB_CHECK"
            cost = 4500.0 if routing == "BLOCK_PACKAGING" else 400.0
            passed = 0
        else:
            temp_c = round(float(rng.normal(350.0, 2.5)), 2)
            rf_w = round(float(rng.normal(1200.0, 12.0)), 1)
            s_prob = round(float(np.clip(rng.beta(1.5, 8), 0.01, 0.68)), 4)
            false_alarm = rng.rand() < 0.035
            defects = 1 if false_alarm else 0
            d_type = "Micro-Particle" if false_alarm else "None"
            area_px = int(rng.randint(35, 75)) if false_alarm else 0
            routing = "SECONDARY_LAB_CHECK" if false_alarm else "RELEASE"
            cost = 400.0 if false_alarm else 0.0
            passed = 0 if false_alarm else 1

        if s_prob < 0.20:
            decile = "1. Low (<20%)"
        elif s_prob < 0.45:
            decile = "2. Moderate (20-45%)"
        elif s_prob < 0.70:
            decile = "3. Elevated (45-70%)"
        else:
            decile = "4. Critical (>=70%)"

        cur.execute(
            "INSERT INTO fact_wafer_inspection VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (w_id, lot_id, 25, tool_id, shift_id, ts, temp_c, rf_w, s_prob, decile, defects, d_type, area_px, routing, passed, cost),
        )

    conn.commit()
    conn.close()
    print(f"STAR_SCHEMA_OLUSTURULDU: {db_path} ({n_wafers} wafers)")


if __name__ == "__main__":
    create_fab_database()
