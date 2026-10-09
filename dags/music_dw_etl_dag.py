from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.exceptions import AirflowException

# Importación de los módulos del pipeline
import sys
sys.path.append('/opt/airflow/src')

from extract_validate import extract_spotify, extract_grammy, validate_raw_data
from transform import transform_spotify_data, transform_grammy_data, integrate_datasets
from validate_prepared import validate_prepared_data
from load import load_data_warehouse

default_args = {
    'owner': 'data_engineering_team',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 0, # Política por defecto: no reintentar fallos deterministas de datos
}

with DAG(
    'music_dw_etl_pipeline',
    default_args=default_args,
    description='Pipeline ETL e Integración de Spotify y Grammys hacia Data Warehouse',
    schedule_interval='@daily',
    catchup=False,
) as dag:

    # 1. Tareas de Extracción (Transient Retries Habilitados)
    task_extract_spotify = PythonOperator(
        task_id='extract_spotify',
        python_callable=extract_spotify,
        retries=2,
        retry_delay=timedelta(seconds=30)
    )

    task_extract_grammy = PythonOperator(
        task_id='extract_grammy',
        python_callable=extract_grammy,
        retries=2,
        retry_delay=timedelta(seconds=30)
    )

    # 2. Tareas de Validación Cruda (Gate 1 - Zero Retries)
    task_validate_raw_spotify = PythonOperator(
        task_id='validate_raw_spotify',
        python_callable=validate_raw_data,
        op_kwargs={'source': 'spotify'},
        retries=0
    )

    task_validate_raw_grammy = PythonOperator(
        task_id='validate_raw_grammy',
        python_callable=validate_raw_data,
        op_kwargs={'source': 'grammy'},
        retries=0
    )

    # 3. Transformación e Integración
    def run_transformation(**kwargs):
        # Transfiere únicamente referencias de rutas o ejecuta módulos desacoplados
        df_sp_raw = extract_spotify()
        df_gr_raw = extract_grammy()
        df_sp_clean = transform_spotify_data(df_sp_raw)
        df_gr_clean = transform_grammy_data(df_gr_raw)
        df_integrated = integrate_datasets(df_sp_clean, df_gr_clean)
        return "data/processed/integrated_data.parquet"

    task_transform_integrate = PythonOperator(
        task_id='transform_and_integrate',
        python_callable=run_transformation,
        retries=0
    )

    # 4. Validación Preparada (Gate 2 - Zero Retries)
    def run_prepared_validation(**kwargs):
        import pandas as pd
        df_integrated = pd.read_parquet("data/processed/integrated_data.parquet") if False else None
        # Evaluamos el dataset integrado directo
        df_sp_raw = extract_spotify()
        df_gr_raw = extract_grammy()
        df_integrated = integrate_datasets(transform_spotify_data(df_sp_raw), transform_grammy_data(df_gr_raw))
        
        passed = validate_prepared_data(df_integrated)
        if not passed:
            raise AirflowException("❌ Gate 2 de Validación Preparada Falló. Cancelando Carga al DW.")

    task_validate_prepared = PythonOperator(
        task_id='validate_prepared_data',
        python_callable=run_prepared_validation,
        retries=0
    )

    # 5. Carga al Data Warehouse (Transient Retries Habilitados)
    def run_dw_load(**kwargs):
        df_sp_raw = extract_spotify()
        df_gr_raw = extract_grammy()
        df_integrated = integrate_datasets(transform_spotify_data(df_sp_raw), transform_grammy_data(df_gr_raw))
        success = load_data_warehouse(df_integrated)
        if not success:
            raise AirflowException("❌ Error durante la carga a PostgreSQL.")

    task_load_dw = PythonOperator(
        task_id='load_data_warehouse',
        python_callable=run_dw_load,
        retries=2,
        retry_delay=timedelta(seconds=30)
    )

    # ------------------------------------------------------------------
    # DEFINICIÓN DE DEPENDENCIAS Y CONTROL DE FLUJO
    # ------------------------------------------------------------------
    task_extract_spotify >> task_validate_raw_spotify
    task_extract_grammy >> task_validate_raw_grammy

    [task_validate_raw_spotify, task_validate_raw_grammy] >> task_transform_integrate
    task_transform_integrate >> task_validate_prepared
    task_validate_prepared >> task_load_dw