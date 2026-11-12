# 🗄️ Fab Yield SQL Analytics — Semiconductor Telemetry & Quality Warehouse

An end-to-end relational **SQL Analytics & Statistical Process Control (SPC)** warehouse uniting upstream sensor telemetry ([SiliconGuard AI](https://github.com)) and downstream optical inspection logs ([Vision Inspector](https://github.com)) across 1,200 simulated semiconductor wafers.

## Key Capabilities (V2)
- **Star-Schema Data Warehouse (`SQLite`):** Models `dim_equipment`, `dim_shift`, and indexed `fact_wafer_inspection` tables with foreign-key constraints and data-quality checks.
- **Statistical Rigor & SPC:** Computes **95% Wilson confidence intervals**, two-proportion **Z-tests** (`p-values`), and **SPC p-charts** (`±3σ` control limits) alongside Pareto cost attribution and Shift × Equipment heatmaps.
- **Modular Analytical SQL (`sql/01_*.sql` – `sql/04_*.sql`):** Uses CTEs, `RANK()`, `LAG()`, `HAVING`, and window aggregations.
- **Hardened Read-Only SQL Sandbox:** Enforces URI `mode=ro`, single-statement execution, write-keyword blocklists, query timeouts, and row caps.
