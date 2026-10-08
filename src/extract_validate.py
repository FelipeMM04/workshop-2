import os
import json
import pandas as pd
import psycopg2
import great_expectations as gx

# Ruta para preservar metadatos de validación (Required Evidence)
META_DIR = "data/metadata"
os.makedirs(META_DIR, exist_ok=True)

# ----------------------------------------------------------------------
# RAMA 1: SPOTIFY BRANCH
# ----------------------------------------------------------------------
def extract_spotify():
    """Extract: Carga directa del CSV sin limpiezas prematuras."""
    file_path = "data/raw/spotify_dataset.csv"
    df = pd.read_csv(file_path)
    print(f"[EXTRACT SPOTIFY] Extraídos {len(df):,} registros crudos.")
    return df

def validate_spotify_raw(df, force_critical_fail=False):
    """Validate: Aplica Expectativas de reglas crudas (QR-01, QR-02, QR-03)."""
    print("\n" + "="*70)
    print(" [SPOTIFY BRANCH] EJECUTANDO VALIDATE_SPOTIFY_RAW")
    print("="*70)
    
    gx_df = gx.from_pandas(df)
    
    # Inyección opcional para simular fallo controlado (Required Evidence)
    if force_critical_fail:
        # Simulamos un error crítico violando QR-01 (introduciendo un nulo en track_id)
        gx_df.iloc[0, gx_df.columns.get_loc('track_id')] = None
    
    # QR-01 (Critical): track_id NOT NULL
    res_qr01 = gx_df.expect_column_values_to_not_be_null('track_id')
    # QR-02 (Critical): popularity BETWEEN 0 AND 100
    res_qr02 = gx_df.expect_column_values_to_be_between('popularity', min_value=0, max_value=100)
    # QR-03 (Warning): duration_ms >= 0
    res_qr03 = gx_df.expect_column_values_to_be_between('duration_ms', min_value=0)
    
    results = {
        "QR-01": {"success": res_qr01['success'], "unexpected": res_qr01['result']['unexpected_count'], "severity": "Critical"},
        "QR-02": {"success": res_qr02['success'], "unexpected": res_qr02['result']['unexpected_count'], "severity": "Critical"},
        "QR-03": {"success": res_qr03['success'], "unexpected": res_qr03['result']['unexpected_count'], "severity": "Warning"}
    }
    
    # Preservar metadatos de ejecución
    with open(f"{META_DIR}/spotify_raw_validation.json", "w") as f:
        json.dump(results, f, indent=4)
        
    print(f" -> QR-01 (track_id NOT NULL)      : Success={results['QR-01']['success']} | Unexpected={results['QR-01']['unexpected']}")
    print(f" -> QR-02 (popularity 0-100)      : Success={results['QR-02']['success']} | Unexpected={results['QR-02']['unexpected']}")
    print(f" -> QR-03 (duration_ms >= 0)      : Success={results['QR-03']['success']} | Unexpected={results['QR-03']['unexpected']}")
    
    # Evaluar política de detención
    critical_failed = not (results['QR-01']['success'] and results['QR-02']['success'])
    if critical_failed:
        print("\n❌ [GATE SPOTIFY] BLOQUEO CRÍTICO: Se detiene el procesamiento de la rama Spotify.")
        return False, df
    
    print("\n✅ [GATE SPOTIFY] PASO APROBADO: Datos crudos seguros para continuar.")
    return True, df

# ----------------------------------------------------------------------
# RAMA 2: GRAMMY BRANCH
# ----------------------------------------------------------------------
def extract_grammys():
    """Extract: Consulta directa a la base de datos PostgreSQL raw_grammys."""
    conn = psycopg2.connect(
        dbname="music_dw", user="postgres", password="postgres", host="localhost", port="5432"
    )
    df = pd.read_sql_query("SELECT * FROM raw_grammys;", conn)
    conn.close()
    print(f"[EXTRACT GRAMMYS] Extraídos {len(df):,} registros crudos de PostgreSQL.")
    return df

def validate_grammys_raw(df):
    """Validate: Aplica Expectativas para reglas crudas (QR-05a, QR-05b, QR-06)."""
    print("\n" + "="*70)
    print(" [GRAMMY BRANCH] EJECUTANDO VALIDATE_GRAMMYS_RAW")
    print("="*70)
    
    gx_df = gx.from_pandas(df)
    
    # QR-05a (Critical): year NOT NULL
    res_qr05a = gx_df.expect_column_values_to_not_be_null('year')
    # QR-05b (Critical): year BETWEEN 1950 AND 2030
    res_qr05b = gx_df.expect_column_values_to_be_between('year', min_value=1950, max_value=2030)
    # QR-06 (Critical): winner NOT NULL
    res_qr06 = gx_df.expect_column_values_to_not_be_null('winner')
    
    results = {
        "QR-05a": {"success": res_qr05a['success'], "unexpected": res_qr05a['result']['unexpected_count'], "severity": "Critical"},
        "QR-05b": {"success": res_qr05b['success'], "unexpected": res_qr05b['result']['unexpected_count'], "severity": "Critical"},
        "QR-06":  {"success": res_qr06['success'],  "unexpected": res_qr06['result']['unexpected_count'],  "severity": "Critical"}
    }
    
    with open(f"{META_DIR}/grammy_raw_validation.json", "w") as f:
        json.dump(results, f, indent=4)
        
    print(f" -> QR-05a (year NOT NULL)        : Success={results['QR-05a']['success']} | Unexpected={results['QR-05a']['unexpected']}")
    print(f" -> QR-05b (year 1950-2030)       : Success={results['QR-05b']['success']} | Unexpected={results['QR-05b']['unexpected']}")
    print(f" -> QR-06  (winner NOT NULL)      : Success={results['QR-06']['success']}  | Unexpected={results['QR-06']['unexpected']}")
    
    critical_failed = not (results['QR-05a']['success'] and results['QR-05b']['success'] and results['QR-06']['success'])
    if critical_failed:
        print("\n❌ [GATE GRAMMY] BLOQUEO CRÍTICO: Se detiene el procesamiento de la rama Grammy.")
        return False, df
        
    print("\n✅ [GATE GRAMMY] PASO APROBADO: Datos crudos seguros para continuar.")
    return True, df

# ----------------------------------------------------------------------
# ORQUESTACIÓN Y PRUEBA DE EVIDENCIAS (REQUIRED EVIDENCE)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    print("======================================================================")
    print(" EJECUCIÓN 1: PRUEBA DE EXTRACCIÓN Y VALIDACIÓN CRUDA EXITOSA")
    print("======================================================================")
    df_sp = extract_spotify()
    sp_ok, _ = validate_spotify_raw(df_sp, force_critical_fail=False)
    
    df_gr = extract_grammys()
    gr_ok, _ = validate_grammys_raw(df_gr)
    
    print("\n" + "="*70)
    print(" EJECUCIÓN 2: SIMULACIÓN DE FALLO CRÍTICO CONTROLADO (RULE QR-01)")
    print("="*70)
    validate_spotify_raw(df_sp, force_critical_fail=True)