-- Soru 2: Parti (Lot) bazli verim trendi, bir onceki partiye gore degisim (LAG) ve hareketli ortalama nedir?
WITH lot_agg AS (
    SELECT
        lot_id,
        MAX(lot_size) AS lot_size,
        MIN(inspected_at) AS lot_start,
        COUNT(wafer_id) AS n_inspected,
        SUM(is_passed) AS n_passed,
        ROUND(100.0 * SUM(is_passed) / COUNT(wafer_id), 2) AS lot_yield_pct,
        ROUND(SUM(estimated_cost_usd), 2) AS lot_cost_usd
    FROM fact_wafer_inspection
    GROUP BY lot_id
)
SELECT
    lot_id,
    lot_size,
    n_inspected,
    n_passed,
    lot_start,
    lot_yield_pct,
    ROUND(lot_yield_pct - LAG(lot_yield_pct) OVER (ORDER BY lot_id), 2) AS delta_prev_lot_pct,
    ROUND(AVG(lot_yield_pct) OVER (ORDER BY lot_id ROWS BETWEEN 4 PRECEDING AND CURRENT ROW), 2) AS rolling_5_lot_pct,
    lot_cost_usd
FROM lot_agg
ORDER BY lot_id ASC;
