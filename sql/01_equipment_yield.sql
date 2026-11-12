-- Query 1: What are the actual First-Pass Yield (FPY), target variance, rank (RANK), and total cost per equipment?
-- Performance Note: Uses INDEX SCAN via idx_fact_tool instead of a full table scan on EXPLAIN QUERY PLAN.
WITH equip_stats AS (
    SELECT
        e.tool_id,
        e.process_step,
        e.chamber_model,
        e.target_yield_pct,
        e.target_rationale,
        COUNT(f.wafer_id) AS n_wafers,
        SUM(f.is_passed) AS passed_wafers,
        ROUND(AVG(f.chamber_temp_c), 2) AS avg_temp_c,
        ROUND(SUM(f.estimated_cost_usd), 2) AS total_cost_usd
    FROM dim_equipment e
    JOIN fact_wafer_inspection f ON e.tool_id = f.tool_id
    GROUP BY e.tool_id, e.process_step, e.chamber_model, e.target_yield_pct, e.target_rationale
    HAVING COUNT(f.wafer_id) > 0
)
SELECT
    RANK() OVER (ORDER BY (1.0 * passed_wafers / n_wafers) ASC) AS bottleneck_rank,
    tool_id,
    process_step,
    n_wafers,
    passed_wafers,
    ROUND(100.0 * passed_wafers / n_wafers, 2) AS actual_yield_pct,
    target_yield_pct,
    ROUND((100.0 * passed_wafers / n_wafers) - target_yield_pct, 2) AS yield_gap_pct,
    avg_temp_c,
    total_cost_usd,
    target_rationale
FROM equip_stats
ORDER BY actual_yield_pct ASC;
