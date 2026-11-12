-- Query 4: Predictive risk score calibration comparing predicted risk deciles against actual defect rates.
-- Performance Note: Evaluates model calibration by grouping inspections into risk deciles and computing actual failure rates.
SELECT
    risk_decile,
    COUNT(wafer_id) AS n_wafers,
    ROUND(AVG(predicted_sensor_risk) * 100, 2) AS avg_predicted_risk_pct,
    ROUND(100.0 * (1.0 - AVG(is_passed)), 2) AS observed_defect_rate_pct,
    ROUND(100.0 * AVG(is_passed), 2) AS observed_yield_pct,
    ROUND(SUM(estimated_cost_usd), 2) AS total_cost_usd
FROM fact_wafer_inspection
GROUP BY risk_decile
ORDER BY risk_decile ASC;
