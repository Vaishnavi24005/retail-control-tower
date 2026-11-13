"""Airflow 3 DAG. Deploy with tower.py and its requirements on every worker."""
import os
from datetime import timedelta

import pendulum
from airflow.sdk import dag, get_current_context, task


@dag(dag_id='retail_control_tower', schedule='0 * * * *',
     start_date=pendulum.datetime(2026, 1, 1, tz='UTC'),
     catchup=False, max_active_runs=1,
     default_args={'retries': 2, 'retry_delay': timedelta(minutes=5)})
def control_tower():
    @task
    def refresh_warehouse():
        from tower import refresh

        hour = get_current_context()['data_interval_end']
        refresh(hour, deliver_alerts=os.getenv('TOWER_NOTIFY') == '1')

    refresh_warehouse()


control_tower()
