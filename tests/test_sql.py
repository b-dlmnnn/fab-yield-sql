import pytest
from src.sql_engine import add_spc_control_limits, enrich_equipment_stats, load_sql_templates, run_select_query


def test_all_sql_templates_run():
    templates = load_sql_templates()
    assert len(templates) == 4
    for q in templates.values():
        df = run_select_query(q)
        assert len(df) > 0


def test_data_quality_constraints():
    df = run_select_query("SELECT * FROM fact_wafer_inspection")
    assert df["wafer_id"].nunique() == len(df)
    assert df["is_passed"].isin(list((0, 1))).all()
    assert df.isna().sum().sum() == 0


def test_statistical_enrichment_and_spc():
    templates = load_sql_templates()
    df_eq = enrich_equipment_stats(run_select_query(templates["1. Equipment Yield, Wilson CI & Bottleneck Rank"]))
    assert "ci_95_low" in df_eq.columns and "p_value" in df_eq.columns
    df_lot = add_spc_control_limits(run_select_query(templates["2. SPC Lot Yield Control Chart (LAG & Rolling)"]))
    assert "spc_lcl_pct" in df_lot.columns


def test_sandbox_security_blocks_writes_and_multistatement():
    with pytest.raises(ValueError):
        run_select_query("DROP TABLE fact_wafer_inspection;")
    with pytest.raises(ValueError):
        run_select_query("SELECT 1; SELECT 2;")
