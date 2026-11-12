import pandas as pd
import plotly.express as px
import streamlit as st
from src.sql_engine import get_named_queries, run_select_query

st.set_page_config(
    page_title="Fab Yield SQL Analytics | Semiconductor Data Warehouse",
    page_icon="🗄️",
    layout="wide",
)

st.title("🗄️ Fab Yield SQL Analytics — Semiconductor Telemetry & Quality Warehouse")
st.caption(
    "Relational SQL analytics dashboard unifying upstream sensor telemetry (SiliconGuard) and "
    "downstream optical inspection records (Vision Inspector) across 1,200 wafers."
)

queries = get_named_queries()
q_keys = list(queries.keys())

df_tools = run_select_query(queries.get(q_keys.pop(0)))
df_lots = run_select_query(queries.get(q_keys.pop(0)))
df_shifts = run_select_query(queries.get(q_keys.pop(0)))

# --- TOP KPI METRICS ---
tot_wafers = int(df_tools["total_wafers"].sum())
avg_yield = round(float((df_tools["actual_yield_pct"] * df_tools["total_wafers"]).sum() / tot_wafers), 2)
tot_loss = float(df_tools["total_loss_usd"].sum())
worst_tool = str(df_tools.iloc.real if False else df_tools["tool_id"].values.take(0))

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Inspected Wafers", f"{tot_wafers:,}")
k2.metric("Overall First-Pass Yield", f"{avg_yield}%")
k3.metric("Total Scrap & Quarantine Cost", f"\\${tot_loss:,.0f}")
k4.metric("Lowest-Yield Bottleneck Tool", worst_tool, delta="Requires Chamber Calibration", delta_color="inverse")

tab_kpi, tab_sql = st.tabs(list(("1. Executive Yield & Root-Cause Dashboard", "2. Interactive Read-Only SQL Sandbox")))

with tab_kpi:
    c1, c2 = st.columns(2)
    with c1:
        fig_tool = px.bar(
            df_tools,
            x="tool_id",
            y="actual_yield_pct",
            color="yield_gap_pct",
            text_auto=".2f",
            color_continuous_scale="RdYlGn",
            labels={"tool_id": "Equipment ID", "actual_yield_pct": "First-Pass Yield (%)", "yield_gap_pct": "Gap vs Target (%)"},
            title="Equipment Yield Performance & Gap vs. Target",
        )
        fig_tool.update_layout(height=340, yaxis_range=list((75, 100)))
        st.plotly_chart(fig_tool, use_container_width=True)

    with c2:
        fig_lot = px.line(
            df_lots,
            x="lot_id",
            y=list(("lot_yield_pct", "rolling_5_lot_yield_pct")),
            labels={"lot_id": "Production Lot", "value": "Yield (%)", "variable": "Metric"},
            title="Lot-by-Lot Yield & 5-Lot Rolling Average (SQL Window Function)",
        )
        fig_lot.update_layout(height=340)
        st.plotly_chart(fig_lot, use_container_width=True)

    st.subheader("Shift & Defect Root-Cause Financial Impact (Multi-Table SQL JOIN)")
    st.dataframe(df_shifts, use_container_width=True, hide_index=True)

with tab_sql:
    st.subheader("Interactive Read-Only SQL Query Workbench")
    st.info("Database Schema: `tools(tool_id, process_step, chamber_model, target_yield_pct)` | `wafers(wafer_id, lot_id, tool_id, shift, inspected_at)` | `sensor_telemetry(wafer_id, chamber_temp_c, rf_power_w, sensor_risk_prob)` | `optical_inspections(wafer_id, defects_found, primary_defect_type, defect_area_px, routing_decision, estimated_cost_usd)`")
    preset_choice = st.selectbox("Load Analytical SQL Template", list(queries.keys()))
    sql_input = st.text_area("SQL Editor (SELECT / WITH only)", value=queries.get(preset_choice), height=220)
    if st.button("▶ Execute SQL Query", type="primary"):
        try:
            res_df = run_select_query(sql_input)
            st.success(f"Query executed successfully: {len(res_df)} rows returned.")
            st.dataframe(res_df, use_container_width=True, hide_index=True)
        except Exception as exc:
            st.error(str(exc))
