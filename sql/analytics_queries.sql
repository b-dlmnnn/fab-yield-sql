-- 1. Makine (Tool) Bazli Verim, Hedef Sapmasi ve Toplam Fire Maliyeti
WITH tool_summary AS (
    SELECT
        t.tool_id,
        t.process_step,
        t.chamber_model,
        t.target_yield_pct,
        COUNT(w.wafer_id) AS total_wafers,
        SUM(CASE WHEN o.routing_decision = 'RELEASE' THEN 1 ELSE 0 END) AS passed_wafers,
        ROUND(AVG(s.chamber_temp_c), 2) AS avg_temp_c,
        ROUND(SUM(o.estimated_cost_usd), 2) AS total_loss_usd
    FROM tools t
    JOIN wafers w ON t.tool_id = w.tool_id
    JOIN sensor_telemetry s ON w.wafer_id = s.wafer_id
    JOIN optical_inspections o ON w.wafer_id = o.wafer_id
    GROUP BY t.tool_id, t.process_step, t.chamber_model, t.target_yield_pct
)
SELECT
    tool_id,
    process_step,
    total_wafers,
    ROUND(100.0 * passed_wafers / total_wafers, 2) AS actual_yield_pct,
    ROUND((100.0 * passed_wafers / total_wafers) - target_yield_pct, 2) AS yield_gap_pct,
    avg_temp_c,
    total_loss_usd
FROM tool_summary
ORDER BY actual_yield_pct ASC;

-- 2. Parti (Lot) Bazli Hareketli Ortalama Verim Takibi (Window Function)
WITH lot_yield AS (
    SELECT
        w.lot_id,
        MIN(w.inspected_at) AS lot_start_time,
        COUNT(w.wafer_id) AS wafers_in_lot,
        ROUND(100.0 * SUM(CASE WHEN o.routing_decision = 'RELEASE' THEN 1 ELSE 0 END) / COUNT(w.wafer_id), 2) AS lot_yield_pct,
        ROUND(SUM(o.estimated_cost_usd), 2) AS lot_cost_usd
    FROM wafers w
    JOIN optical_inspections o ON w.wafer_id = o.wafer_id
    GROUP BY w.lot_id
)
SELECT
    lot_id,
    lot_start_time,
    wafers_in_lot,
    lot_yield_pct,
    ROUND(AVG(lot_yield_pct) OVER (ORDER BY lot_id ROWS BETWEEN 4 PRECEDING AND CURRENT ROW), 2) AS rolling_5_lot_yield_pct,
    lot_cost_usd
FROM lot_yield
ORDER BY lot_id ASC;

-- 3. Vardiya (Shift) ve Kusur Turu Kok Neden Dagilimi
SELECT
    w.shift,
    o.primary_defect_type,
    COUNT(*) AS incident_count,
    ROUND(AVG(s.sensor_risk_prob) * 100, 2) AS avg_sensor_risk_pct,
    ROUND(SUM(o.estimated_cost_usd), 2) AS total_cost_usd
FROM wafers w
JOIN sensor_telemetry s ON w.wafer_id = s.wafer_id
JOIN optical_inspections o ON w.wafer_id = o.wafer_id
WHERE o.routing_decision != 'RELEASE'
GROUP BY w.shift, o.primary_defect_type
ORDER BY total_cost_usd DESC;
