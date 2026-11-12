import os
import sqlite3
import numpy as np
import pandas as pd


def create_fab_database(db_path="fab_telemetry.db", n_wafers=1200, seed=42):
    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE tools (
        tool_id TEXT PRIMARY KEY,
        process_step TEXT NOT NULL,
        chamber_model TEXT NOT NULL,
        target_yield_pct REAL NOT NULL
    );

    CREATE TABLE wafers (
        wafer_id TEXT PRIMARY KEY,
        lot_id TEXT NOT NULL,
        tool_id TEXT NOT NULL,
        shift TEXT NOT NULL,
        inspected_at TEXT NOT NULL,
        FOREIGN KEY (tool_id) REFERENCES tools(tool_id)
    );

    CREATE TABLE sensor_telemetry (
        telemetry_id INTEGER PRIMARY KEY AUTOINCREMENT,
        wafer_id TEXT NOT NULL,
        chamber_temp_c REAL NOT NULL,
        rf_power_w REAL NOT NULL,
        sensor_risk_prob REAL NOT NULL,
        FOREIGN KEY (wafer_id) REFERENCES wafers(wafer_id)
    );

    CREATE TABLE optical_inspections (
        inspection_id INTEGER PRIMARY KEY AUTOINCREMENT,
        wafer_id TEXT NOT NULL,
        defects_found INTEGER NOT NULL,
        primary_defect_type TEXT NOT NULL,
        defect_area_px INTEGER NOT NULL,
        routing_decision TEXT NOT NULL,
        estimated_cost_usd REAL NOT NULL,
        FOREIGN KEY (wafer_id) REFERENCES wafers(wafer_id)
    );
    """)

    tools_data = list((
        ("ETCH-01", "Plasma Etching", "Lam-Kiyo-FX", 94.0),
        ("LITHO-02", "DUV Lithography", "ASML-Twinscan", 95.5),
        ("CVD-03", "Thin-Film Deposition", "Applied-Producer", 92.0),
        ("CMP-04", "Chemical Planarization", "Ebara-FREX", 94.5),
    ))
    cur.executemany("INSERT INTO tools VALUES (?, ?, ?, ?)", tools_data)

    rng = np.random.RandomState(seed)
    base_time = pd.Timestamp("2026-10-01 06:00:00")
    tool_ids = list(("ETCH-01", "LITHO-02", "CVD-03", "CMP-04"))
    shifts = list(("Shift-A (Morning)", "Shift-B (Evening)", "Shift-C (Night)"))

    for i in range(n_wafers):
        w_id = f"WFR-{10000 + i}"
        lot_id = f"LOT-{200 + (i // 25)}"
        tool_id = str(rng.choice(tool_ids, p=list((0.28, 0.25, 0.27, 0.20))))
        shift = str(rng.choice(shifts))
        ts = (base_time + pd.Timedelta(minutes=12 * i)).strftime("%Y-%m-%d %H:%M:%S")

        base_fail_rate = 0.06
        if tool_id == "CVD-03":
            base_fail_rate += 0.08
        if "Night" in shift:
            base_fail_rate += 0.04

        is_defective = rng.rand() < base_fail_rate

        if is_defective:
            temp_c = round(float(rng.normal(368.0, 6.5)), 2)
            rf_w = round(float(rng.normal(1245.0, 35.0)), 1)
            s_prob = round(float(np.clip(rng.beta(5, 2), 0.15, 0.99)), 4)
            defects = int(rng.choice(list((1, 2, 3)), p=list((0.35, 0.45, 0.20))))
            d_type = str(rng.choice(list(("Solder Bridge", "Linear Scratch", "Micro-Particle"))))
            area_px = int(defects * rng.randint(110, 310))
            routing = "BLOCK_PACKAGING" if (defects >= 2 or s_prob >= 0.65) else "SECONDARY_LAB_CHECK"
            cost = 4500.0 if routing == "BLOCK_PACKAGING" else 400.0
        else:
            temp_c = round(float(rng.normal(350.0, 2.5)), 2)
            rf_w = round(float(rng.normal(1200.0, 12.0)), 1)
            s_prob = round(float(np.clip(rng.beta(1.5, 8), 0.01, 0.68)), 4)
            false_alarm = rng.rand() < 0.04
            defects = 1 if false_alarm else 0
            d_type = "Micro-Particle" if false_alarm else "None"
            area_px = int(rng.randint(35, 75)) if false_alarm else 0
            routing = "SECONDARY_LAB_CHECK" if false_alarm else "RELEASE"
            cost = 400.0 if false_alarm else 0.0

        cur.execute("INSERT INTO wafers VALUES (?, ?, ?, ?, ?)", (w_id, lot_id, tool_id, shift, ts))
        cur.execute("INSERT INTO sensor_telemetry (wafer_id, chamber_temp_c, rf_power_w, sensor_risk_prob) VALUES (?, ?, ?, ?)", (w_id, temp_c, rf_w, s_prob))
        cur.execute("INSERT INTO optical_inspections (wafer_id, defects_found, primary_defect_type, defect_area_px, routing_decision, estimated_cost_usd) VALUES (?, ?, ?, ?, ?, ?)", (w_id, defects, d_type, area_px, routing, cost))

    conn.commit()
    conn.close()
    print(f"DB_OLUSTURULDU: {db_path} ({n_wafers} wafers)")


if __name__ == "__main__":
    create_fab_database()
