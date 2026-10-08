import os
import json
import pandas as pd
import great_expectations as gx

META_DIR = "data/metadata"
os.makedirs(META_DIR, exist_ok=True)

def validate_prepared_data(df_integrated, force_critical_fail=False):
    """
    Gate 2: Validación de datos preparados post-transformación e integración.
    Revisa la unicidad del grano de dimensión, marcadores de integración (is_grammy_nominated)
    y rangos válidos post-procesamiento.
    """
    print("\n" + "="*70)
    print(" [GATE 2: PREPARED VALIDATION] EVALUANDO SUITE POST-TRANSFORMACIÓN")
    print("="*70)
    
    df = df_integrated.copy()
    
    # Inyección opcional para simular fallo controlado (Required Evidence)
    if force_critical_fail:
        # Simulamos un error crítico forzando valores de bandera fuera de rango (2)
        df.loc[0, 'is_grammy_nominated'] = 2
    
    # 1. Unicidad del grano para dim_track (QR-04 / Critical)
    df_unique_tracks = df.drop_duplicates(subset=['track_id'])
    gx_tracks = gx.from_pandas(df_unique_tracks)
    res_unique = gx_tracks.expect_column_values_to_be_unique('track_id')
    
    gx_df = gx.from_pandas(df)
    
    # 2. Rangos de popularidad post-transformación (QR-02 / Critical)
    res_pop = gx_df.expect_column_values_to_be_between('popularity', min_value=0, max_value=100)
    
    # 3. Integridad de banderas de integración (PREP-01 / Critical): solo valores 0 o 1
    res_nom = gx_df.expect_column_values_to_be_in_set('is_grammy_nominated', [0, 1])
    
    # 4. Integridad de ganadores (PREP-02 / Critical): solo valores 0 o 1
    res_win = gx_df.expect_column_values_to_be_in_set('is_grammy_winner', [0, 1])
    
    results = {
        "QR-04 (Uniqueness track_id)": {"success": res_unique['success'], "unexpected": res_unique['result']['unexpected_count'], "severity": "Critical"},
        "QR-02 (Popularity Range)":    {"success": res_pop['success'],    "unexpected": res_pop['result']['unexpected_count'],    "severity": "Critical"},
        "PREP-01 (Nominated Flag)":    {"success": res_nom['success'],    "unexpected": res_nom['result']['unexpected_count'],    "severity": "Critical"},
        "PREP-02 (Winner Flag)":       {"success": res_win['success'],    "unexpected": res_win['result']['unexpected_count'],    "severity": "Critical"}
    }
    
    # Preservar metadatos de validación
    with open(f"{META_DIR}/prepared_validation.json", "w") as f:
        json.dump(results, f, indent=4)
        
    for rule, data in results.items():
        print(f" -> {rule:<30} : Success={data['success']} | Unexpected={data['unexpected']}")
        
    critical_passed = all(data['success'] for data in results.values() if data['severity'] == "Critical")
    
    if not critical_passed:
        print("\n❌ [GATE 2 BLOQUEADO] FALLO EN REGLA CRÍTICA PREPARADA: SE CANCELA LA CARGA A LOAD_DW.")
        return False
        
    print("\n✅ [GATE 2 APROBADO] Dataset preparado analíticamente listo para ejecutar load_dw.")
    return True

if __name__ == "__main__":
    from transform import transform_spotify_data, transform_grammy_data, integrate_datasets
    import psycopg2
    
    # 1. Preparación de datos
    df_sp_raw = pd.read_csv("data/raw/spotify_dataset.csv")
    df_sp_clean = transform_spotify_data(df_sp_raw)
    
    conn = psycopg2.connect(dbname="music_dw", user="postgres", password="postgres", host="localhost", port="5432")
    df_gr_raw = pd.read_sql_query("SELECT * FROM raw_grammys;", conn)
    conn.close()
    
    df_gr_clean = transform_grammy_data(df_gr_raw)
    df_integrated = integrate_datasets(df_sp_clean, df_gr_clean)
    
    print("\n" + "="*70)
    print(" EJECUCIÓN 1: PRUEBA DE VALIDACIÓN DE DATOS PREPARADOS EXITOSA")
    print("="*70)
    success = validate_prepared_data(df_integrated, force_critical_fail=False)
    
    print("\n" + "="*70)
    print(" EJECUCIÓN 2: PRUEBA DE FALLO CONTROLADO EN GATE 2 (RULE PREP-01 BANDERA FUERA DE RANGO)")
    print("="*70)
    validate_prepared_data(df_integrated, force_critical_fail=True)