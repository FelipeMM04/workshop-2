import pandas as pd
import psycopg2
import great_expectations as gx

def validate_spotify_data(file_path):
    print("\n" + "="*70)
    print(" [GX EXECUTION] EVALUANDO EXPECTATION SUITE: spotify_raw_suite (SUCCESS CASE)")
    print("="*70)
    
    df = pd.read_csv(file_path)
    gx_df = gx.from_pandas(df)
    
    # QR-01: Integridad en track_id
    res_id = gx_df.expect_column_values_to_not_be_null('track_id')
    # QR-02: Rango de Popularidad
    res_pop = gx_df.expect_column_values_to_be_between('popularity', min_value=0, max_value=100)
    # QR-03: Rango de Duración
    res_dur = gx_df.expect_column_values_to_be_between('duration_ms', min_value=0)
    
    print(f"\n[Rule QR-01] track_id NOT NULL:")
    print(f"  - Success: {res_id['success']}")
    print(f"  - Element Count: {res_id['result']['element_count']:,}")
    print(f"  - Unexpected Count: {res_id['result']['unexpected_count']}")
    
    print(f"\n[Rule QR-02] popularity BETWEEN 0 AND 100:")
    print(f"  - Success: {res_pop['success']}")
    print(f"  - Unexpected Count: {res_pop['result']['unexpected_count']}")
    
    print(f"\n[Rule QR-03] duration_ms >= 0:")
    print(f"  - Success: {res_dur['success']}")
    print(f"  - Unexpected Count: {res_dur['result']['unexpected_count']}")
    
    return res_id['success'] and res_pop['success'] and res_dur['success']

def test_failed_execution(file_path):
    print("\n" + "="*70)
    print(" [GX EXECUTION] EVALUANDO EXPECTATION SUITE: spotify_raw_suite (FAILURE CASE SIMULATION)")
    print("="*70)
    
    df = pd.read_csv(file_path)
    # Introducimos artificialmente un fallo para probar el Checkpoint (ej. exigiéndole popularidad min 50)
    gx_df = gx.from_pandas(df)
    
    res_fail = gx_df.expect_column_values_to_be_between('popularity', min_value=50, max_value=100)
    
    print(f"\n[Rule SIMULATION-FAIL] popularity BETWEEN 50 AND 100:")
    print(f"  - Success: {res_fail['success']}")
    print(f"  - Element Count: {res_fail['result']['element_count']:,}")
    print(f"  - Unexpected Count: {res_fail['result']['unexpected_count']:,}")
    print(f"  - Unexpected Percent: {res_fail['result']['unexpected_percent']:.2f}%")
    
    return res_fail['success']

if __name__ == "__main__":
    s_ok = validate_spotify_data('data/raw/spotify_dataset.csv')
    
    # Ejecutamos la simulación de fallo para capturar evidencia
    f_ok = test_failed_execution('data/raw/spotify_dataset.csv')
    
    print("\n" + "="*70)
    if not f_ok:
        print("❌ RESULTADO GLOBAL CHECKPOINT (PRUEBA DE FALLO): BLOQUEO DE ETL POR REGLA CRÍTICA")
    print("="*70)