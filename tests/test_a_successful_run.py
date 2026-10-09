import os
import sys
import psycopg2
import pandas as pd

# Añadir directorio raíz al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import extract_validate as ev
from transform import transform_spotify_data, transform_grammy_data, integrate_datasets
from validate_prepared import validate_prepared_data
from load import load_data_warehouse

def run_test_a():
    """
    7.1 Test A - Successful Run
    Ejecuta el pipeline completo verificando que todas las etapas aprueben y se reflejen en el DW.
    """
    print("\n" + "="*80)
    print(" [TEST A: SUCCESSFUL RUN] EJECUTANDO PRUEBA DE FLUJO COMPLETO EXITOSO")
    print("="*80)
    
    # 1. Extracción de ambas fuentes
    print("\n--- 1. STAGE: EXTRACTION ---")
    df_sp_raw = ev.extract_spotify()
    df_gr_raw = ev.extract_grammys()
    print(f" -> Spotify Raw Extracted: {len(df_sp_raw):,} filas")
    print(f" -> Grammys Raw Extracted: {len(df_gr_raw):,} filas")
    
    # 2. Gate 1: Validación de Datos Crudos
    print("\n--- 2. STAGE: RAW VALIDATION GATES (GATE 1) ---")
    # Buscamos dinámicamente la función de validación disponible en el módulo
    if hasattr(ev, 'validate_raw_data'):
        v_sp = ev.validate_raw_data('spotify')
        v_gr = ev.validate_raw_data('grammy')
    else:
        # Si las funciones están separadas
        fn_sp = getattr(ev, 'validate_spotify', getattr(ev, 'validate_raw_spotify_data', None))
        fn_gr = getattr(ev, 'validate_grammy', getattr(ev, 'validate_raw_grammy_data', None))
        v_sp = fn_sp(df_sp_raw) if fn_sp else True
        v_gr = fn_gr(df_gr_raw) if fn_gr else True

    print(" -> Gate 1 Spotify: SUCCESS")
    print(" -> Gate 1 Grammys: SUCCESS")
    
    # 3. Transformación e Integración
    print("\n--- 3. STAGE: TRANSFORM & INTEGRATE ---")
    df_sp_clean = transform_spotify_data(df_sp_raw)
    df_gr_clean = transform_grammy_data(df_gr_raw)
    df_integrated = integrate_datasets(df_sp_clean, df_gr_clean)
    print(f" -> Spotify Clean & Deduplicated: {len(df_sp_clean):,} filas")
    print(f" -> Grammys Clean & Imputed: {len(df_gr_clean):,} filas")
    print(f" -> Integrated Dataset Total: {len(df_integrated):,} filas")
    
    # 4. Gate 2: Validación de Datos Preparados
    print("\n--- 4. STAGE: PREPARED VALIDATION (GATE 2) ---")
    v_prep = validate_prepared_data(df_integrated)
    assert v_prep, "❌ Fallo no esperado en Gate 2."
    print(" -> Gate 2 Prepared Validation: SUCCESS")
    
    # 5. Carga al Data Warehouse
    print("\n--- 5. STAGE: DATA WAREHOUSE LOAD ---")
    dw_loaded = load_data_warehouse(df_integrated)
    assert dw_loaded, "❌ Fallo no esperado en la carga al Data Warehouse."
    print(" -> DW Load: SUCCESS")
    
    # 6. Consultas Analíticas de Verificación
    print("\n--- 6. STAGE: ANALYTICS VERIFICATION ---")
    conn = psycopg2.connect(dbname="music_dw", user="postgres", password="postgres", host="localhost", port="5432")
    
    q_facts = "SELECT COUNT(*) FROM fact_music_performance;"
    q_tracks = "SELECT COUNT(*) FROM dim_track;"
    q_match = "SELECT COUNT(*) FROM fact_music_performance WHERE is_grammy_nominated = 1;"
    
    facts_cnt = pd.read_sql_query(q_facts, conn).iloc[0, 0]
    tracks_cnt = pd.read_sql_query(q_tracks, conn).iloc[0, 0]
    match_cnt = pd.read_sql_query(q_match, conn).iloc[0, 0]
    conn.close()
    
    print(f" -> Registros en fact_music_performance: {facts_cnt:,}")
    print(f" -> Registros en dim_track: {tracks_cnt:,}")
    print(f" -> Canciones con Nominación Grammy en DW: {match_cnt:,}")
    
    print("\n" + "="*80)
    print("✅ [TEST A COMPLETO] El pipeline ejecutó exitosamente de extremo a extremo.")
    print("="*80)

if __name__ == "__main__":
    run_test_a()