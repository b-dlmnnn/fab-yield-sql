-- Query 3: Shift-level Pareto analysis of defect types and associated financial loss attribution.
-- Performance Note: Aggregates defect counts and cost impact across shifts using CTEs and cumulative percentage ranking.
WITH defect_costs AS (
    SELECT
        s.shift_label,
        f.tool_id,
        f.primary_defect_type,
        COUNT(*) AS incident_count,
        ROUND(SUM(f.estimated_cost_usd), 2) AS group_cost_usd
    FROM fact_wafer_inspection f
    JOIN dim_shift s ON f.shift_id = s.shift_id
    WHERE f.is_passed = 0
    GROUP BY s.shift_label, f.tool_id, f.primary_defect_type
)
SELECT
    shift_label,
    tool_id,
    primary_defect_type,
    incident_count,
    group_cost_usd,
    ROUND(100.0 * group_cost_usd / SUM(group_cost_usd) OVER (), 2) AS cost_share_pct
FROM defect_costs
ORDER BY group_cost_usd DESC;
