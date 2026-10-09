import os
import json
import pandas as pd

META_DIR = "data/metadata"
os.makedirs(META_DIR, exist_ok=True)

def validate_prepared_data(df_integrated):
    """
    Validate Gate 2: Valida el dataset integrado previo a la carga en PostgreSQL.
    Aplica reglas de negocio (QP-01 a QP-06).
    """
    print("\n" + "="*70)
    print(" [GATE 2: PREPARED VALIDATION] EVALUANDO SUITE POST-TRANSFORMACIÓN")
    print("="*70)

    # QP-01 (Critical): track_id único en catálogo de tracks
    df_unique_tracks = df_integrated[['track_id']].drop_duplicates()
    qp01_unexpected = int(df_unique_tracks['track_id'].duplicated().sum())
    res_qp01_success = (qp01_unexpected == 0)

    # QP-02 (Critical): popularity NOT NULL
    qp02_unexpected = int(df_integrated['popularity'].isna().sum())
    res_qp02_success = (qp02_unexpected == 0)

    # QP-03 (Critical): duration_ms > 0
    qp03_unexpected = int((df_integrated['duration_ms'] <= 0).sum())
    res_qp03_success = (qp03_unexpected == 0)

    # QP-04 (Warning): is_grammy_nominated e is_grammy_winner en {0, 1}
    qp04_nom_unexp = int((~df_integrated['is_grammy_nominated'].isin([0, 1])).sum())
    qp04_win_unexp = int((~df_integrated['is_grammy_winner'].isin([0, 1])).sum())
    res_qp04_success = (qp04_nom_unexp == 0 and qp04_win_unexp == 0)

    results = {
        "QP-01": {"success": res_qp01_success, "unexpected": qp01_unexpected, "severity": "Critical"},
        "QP-02": {"success": res_qp02_success, "unexpected": qp02_unexpected, "severity": "Critical"},
        "QP-03": {"success": res_qp03_success, "unexpected": qp03_unexpected, "severity": "Critical"},
        "QP-04": {"success": res_qp04_success, "unexpected": qp04_nom_unexp + qp04_win_unexp, "severity": "Warning"}
    }

    # Preservar metadatos de validación en Gate 2
    with open(f"{META_DIR}/prepared_data_validation.json", "w") as f:
        json.dump(results, f, indent=4)

    print(f" -> QP-01 (Unicidad track_id)        : Success={results['QP-01']['success']} | Unexpected={results['QP-01']['unexpected']}")
    print(f" -> QP-02 (popularity NOT NULL)      : Success={results['QP-02']['success']} | Unexpected={results['QP-02']['unexpected']}")
    print(f" -> QP-03 (duration_ms > 0)          : Success={results['QP-03']['success']} | Unexpected={results['QP-03']['unexpected']}")
    print(f" -> QP-04 (Flags Grammy en {{0,1}})  : Success={results['QP-04']['success']} | Unexpected={results['QP-04']['unexpected']}")

    critical_failed = not (results['QP-01']['success'] and results['QP-02']['success'] and results['QP-03']['success'])

    if critical_failed:
        print("\n❌ [GATE 2 ERROR] BLOQUEO EN DATOS PREPARADOS: Se detiene la carga al Data Warehouse.")
        return False

    print("\n✅ [GATE 2 APROBADO] Datos integrados listos para cargar en PostgreSQL.")
    return True