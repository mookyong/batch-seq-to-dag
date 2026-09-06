# Auto-generated from dag_generation_input.xlsx
# seq_name: SEQ_MONTHLY_SETTLEMENT
# review_status: needs_review
# NOTE: sensor_type is missing; using start_mode/manual scaffold
# NOTE: notify_channel is missing; notify tasks are placeholders
# NOTE: model_mapping is missing; dbt graph dependency is used

from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import BranchPythonOperator
from cosmos import DbtTaskGroup, ExecutionConfig, ProfileConfig, ProjectConfig, RenderConfig
from cosmos.profiles import PostgresUserPasswordProfileMapping

DAG_ID = 'seq_monthly_settlement'
DAG_NAME = 'SEQ_MONTHLY_SETTLEMENT - 월 정산 마감'
DESCRIPTION = '월 정산 마감' + ' 업무를 Airflow + dbt(Cosmos)로 오케스트레이션한다.'
START_DATE = datetime(2026, 9, 5)
REVIEW_STATUS = 'needs_review'
REVIEW_COMMENT = '확인 필요: model_mapping, notify_channel, notify_recipients, schedule_interval, sensor_target, sensor_type'

DEFAULT_ARGS = {
    'owner': '정산운영팀 / 박정산',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'email_on_failure': False,
    'email_on_retry': False,
}


def choose_route() -> str:
    return 'manual_start'


with DAG(
    dag_id=DAG_ID,
    dag_display_name=DAG_NAME,
    description=DESCRIPTION,
    start_date=START_DATE,
    schedule='0 1 1 * *',
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=['monthly', 'monthly_settlement', 'dbt', 'airflow'],
    max_active_runs=1,
) as dag:
    start = EmptyOperator(task_id='start')

    route = BranchPythonOperator(
        task_id='route',
        python_callable=choose_route,
    )

    manual_start = EmptyOperator(task_id='manual_start')

    dbt_build = DbtTaskGroup(
        group_id='dbt_monthly_settlement',
        project_config=ProjectConfig('/opt/airflow/dbt/monthly_settlement'),
        profile_config=ProfileConfig(
            profile_name='monthly_settlement',
            target_name='prod',
            profile_mapping=PostgresUserPasswordProfileMapping(
                conn_id='TODO_WAREHOUSE_CONN_ID',
                profile_args={
                    'schema': 'TODO_SCHEMA',
                    'database': 'TODO_DATABASE',
                },
            ),
        ),
        execution_config=ExecutionConfig(
            dbt_executable_path='/usr/local/bin/dbt',
        ),
        render_config=RenderConfig(select=['tag:monthly_settlement']),
    )

    validate = BashOperator(
        task_id='validate',
        bash_command='cd /opt/airflow/dbt/monthly_settlement && dbt test --select tag:monthly_settlement',
        cwd='/opt/airflow/dbt/monthly_settlement',
    )

    notify_success = EmptyOperator(task_id='notify_success')
    notify_failure = EmptyOperator(task_id='notify_failure')

    end = EmptyOperator(task_id='end', trigger_rule='none_failed_min_one_success')

    start >> route
    route >> manual_start >> dbt_build >> validate >> notify_success >> end
    validate >> notify_failure >> end

    # review / note
    # TODO: connect notify_channel / notify_recipients if available
    # TODO: refine model_mapping when populated
