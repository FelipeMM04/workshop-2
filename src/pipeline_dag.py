import sys
import os
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Forzar UTF-8 en el proceso actual y subprocesos
env = os.environ.copy()
env["PYTHONIOENCODING"] = "utf-8"

def task_extract_and_validate_raw():
    logging.info("Task [extract_validate]: Ejecutando extracción y Gate 1 de Calidad...")
    res = subprocess.run([sys.executable, "src/extract_validate.py"], capture_output=True, text=True, env=env, encoding="utf-8")
    if res.returncode != 0:
        raise Exception(f"Gate 1 / Extracción Falló:\n{res.stderr or res.stdout}")
    logging.info("Task [extract_validate]: SUCCESS")

def task_transform():
    logging.info("Task [transform]: Ejecutando transformación, limpieza y deduplicación...")
    res = subprocess.run([sys.executable, "src/transform.py"], capture_output=True, text=True, env=env, encoding="utf-8")
    if res.returncode != 0:
        raise Exception(f"Transformación Falló:\n{res.stderr or res.stdout}")
    logging.info("Task [transform]: SUCCESS")

def task_validate_prepared():
    logging.info("Task [validate_prepared]: Ejecutando Gate 2 de Calidad en capa preparada...")
    res = subprocess.run([sys.executable, "src/validate_prepared.py"], capture_output=True, text=True, env=env, encoding="utf-8")
    if res.returncode != 0:
        raise Exception(f"Gate 2 / Validación Falló:\n{res.stderr or res.stdout}")
    logging.info("Task [validate_prepared]: SUCCESS")

def task_load_to_dw():
    logging.info("Task [load_to_dw]: Carga de datos en PostgreSQL (music_dw)...")
    res = subprocess.run([sys.executable, "src/load.py"], capture_output=True, text=True, env=env, encoding="utf-8")
    if res.returncode != 0:
        raise Exception(f"Carga a DW Falló:\n{res.stderr or res.stdout}")
    logging.info("Task [load_to_dw]: SUCCESS")

def run_dag():
    print("\n" + "="*70)
    print(" INICIANDO EJECUCIÓN DEL DAG: music_etl_pipeline")
    print("="*70)
    try:
        task_extract_and_validate_raw()
        task_transform()
        task_validate_prepared()
        task_load_to_dw()
        print("\n [DAG SUCCESS] Todas las tareas del DAG completadas exitosamente.")
    except Exception as e:
        print(f"\n [DAG FAILED] El flujo se detuvo por error:\n{e}")

if __name__ == "__main__":
    run_dag()