"""Airflow DAG for the local Loan & Customer Intelligence Platform pipeline."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.bash import BashOperator


LOCAL_ROOT = Path(__file__).resolve().parents[1]
DOCKER_ROOT = Path("/opt/airflow/project")
ROOT = DOCKER_ROOT if DOCKER_ROOT.exists() else LOCAL_ROOT
PYTHONPATH = str(ROOT / "src")


default_args = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


with DAG(
    dag_id="loan_customer_intelligence_pipeline",
    description="Bronze, silver, gold ETL and streaming fraud simulation",
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["loans", "customer-intelligence", "warehouse"],
) as dag:
    generate_sources = BashOperator(
        task_id="generate_sources",
        bash_command=f'PYTHONPATH="{PYTHONPATH}" python -m loan_intelligence.cli --root "{ROOT}" generate',
    )

    run_etl = BashOperator(
        task_id="run_etl",
        bash_command=f'PYTHONPATH="{PYTHONPATH}" python -m loan_intelligence.cli --root "{ROOT}" run-etl',
    )

    simulate_stream = BashOperator(
        task_id="simulate_stream",
        bash_command=f'PYTHONPATH="{PYTHONPATH}" python -m loan_intelligence.cli --root "{ROOT}" simulate-stream --events 100',
    )

    generate_sources >> run_etl >> simulate_stream
