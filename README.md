# 🗄️ Fab Yield SQL Analytics — Semiconductor Telemetry & Quality Warehouse

An end-to-end relational **SQL Analytics & Business Intelligence** dashboard uniting upstream sensor telemetry ([SiliconGuard AI](https://github.com)) and downstream optical inspection logs ([Vision Inspector](https://github.com)) across 1,200 simulated semiconductor wafers.

## Key Capabilities
- **Normalized Relational Schema (`SQLite`):** Models 4 interconnected tables (`tools`, `wafers`, `sensor_telemetry`, `optical_inspections`) with primary/foreign key constraints.
- **Advanced Analytical SQL (`sql/analytics_queries.sql`):** Implements Common Table Expressions (**CTEs**), **Window Functions** (`AVG() OVER` 5-lot rolling yield), and multi-table `JOIN` root-cause aggregations.
- **Interactive Read-Only SQL Sandbox:** Allows engineers to execute custom `SELECT` / `WITH` queries directly against a URI read-only connection (`mode=ro`) with SQL write-injection protection.

## Run Locally
```bash
pip install -r requirements.txt
python -m src.build_db
python -m pytest -v
streamlit run app.py
```
