# IngestIQ

**Intelligent Data Ingestion & Analytics Platform**

IngestIQ is a modern ETL platform designed for SaaS businesses that need to ingest, transform, and analyze user behavior, transactions, and events — all in one unified pipeline.

---

## Features

### Data Ingestion
- **Synthetic data generation** for users, transactions, and events
- **Stateful ingestion** with cursor-based incremental loads
- **NDJSON output** partitioned by source, dataset, and date
- **Resilient HTTP client** with exponential backoff retries

### Data Transformation
- **Staging layer** in PostgreSQL for raw data landing
- **Analytical marts** with upsert logic (mart_users, mart_transactions, mart_events)
- **dbt integration** for SQL-based transformations
- **DuckDB support** for lightweight analytical queries

### Analytics Dashboard
- **Real-time KPI monitoring** — total users, revenue, ARPU, conversion rate
- **Interactive visualizations** — revenue trends, cohort retention, funnel analysis
- **Data quality checks** — missing data detection, failed transaction tracking
- **Auto-refresh** every 30 seconds via WebSocket

### Workflow Orchestration
- **Apache Airflow DAG** for scheduled pipeline execution
- **CLI tool** for local development and manual runs
- **Full pipeline** or granular step-by-step execution

---

## Tech Stack

| Layer | Technologies |
|-------|---------------|
| **Orchestration** | Apache Airflow 3.1.8 |
| **Transformation** | dbt-core, dbt-duckdb |
| **Storage** | PostgreSQL 16, DuckDB |
| **Dashboard** | Streamlit, Plotly |
| **API** | FastAPI, WebSockets |
| **Language** | Python 3.12+ |

---

## Quick Start

### Prerequisites

- Python 3.10+
- Docker & Docker Compose
- PostgreSQL 16 (or Docker)

### 1. Clone & Install

```bash
git clone https://github.com/your-org/ingestiq.git
cd ingestiq
pip install -e .
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings:
# - DATABASE_URL
# - OPENAI_API_KEY (optional, for LLM features)
```

### 3. Run the Pipeline

```bash
# Full pipeline: ingest → transform → analytics
ingestiq all

# Or run step by step
ingestiq ingest
ingestiq transform
ingestiq analytics
```

### 4. Launch Dashboard

```bash
ingestiq dashboard
```

Dashboard will be available at `http://<server-ip>:8501`

---

## CLI Reference

| Command | Description |
|---------|-------------|
| `ingestiq ingest` | Extract and load raw data |
| `ingestiq transform` | Process data into analytical marts |
| `ingestiq preview` | Preview data from marts |
| `ingestiq analytics` | Generate warehouse summaries |
| `ingestiq dashboard` | Launch Streamlit dashboard |
| `ingestiq all` | Run complete pipeline |

---

## Docker Deployment

Start all services with Docker Compose:

```bash
docker-compose up -d
```

| Service | Port | Description |
|---------|------|-------------|
| Airflow UI | 8080 | Workflow orchestration |
| Dashboard | 8501 | Analytics dashboard |
| FastAPI | 8000 | REST API & WebSocket |

Stop services:

```bash
docker-compose down
```

---

## Project Structure

```
ingestiq/
├── dags/                        # Airflow DAG definitions
│   └── ingestiq_pipeline.py
├── src/
│   ├── analytics/               # Analytics & reporting
│   ├── cli/                     # CLI entry point
│   ├── config/                  # Settings & environment
│   ├── dashboard/               # Streamlit dashboard
│   ├── ingest/                  # Data ingestion
│   │   └── sources/             # Source connectors
│   ├── orchestration/           # Pipeline orchestration
│   ├── storage/                 # Database clients
│   └── transform/               # Data transformation
│       └── my_transform_project/# dbt project
├── data_storage/                # Raw data & state
├── test/                        # Test suite
└── docker-compose.yml           # Multi-service setup
```

---

## Configuration

Environment variables (see `.env.example`):

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://...` |
| `DUCKDB_PATH` | Path to DuckDB database | `./data_storage/analytics.duckdb` |
| `OPENAI_API_KEY` | OpenAI API key for LLM features | - |
| `LOG_LEVEL` | Logging verbosity | `INFO` |

---

## License

MIT License — see [LICENSE](LICENSE) for details.
# test deploy
