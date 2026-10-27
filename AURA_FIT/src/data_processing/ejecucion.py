import os
import sys
import time
import subprocess

# Configurar el directorio raíz del proyecto para importaciones dinámicas
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
SRC_DIR = os.path.join(PROJECT_DIR, "src")
DATA_DIR = os.path.join(PROJECT_DIR, "data")
MODELS_DIR = os.path.join(PROJECT_DIR, "models")
DASHBOARD_SCRIPT = os.path.join(SRC_DIR, "dashboard", "app.py")

for path in [SCRIPT_DIR, SRC_DIR, PROJECT_DIR]:
    if path not in sys.path:
        sys.path.insert(0, path)

# Importar los módulos creados en los pasos previos
from simulate_data import generar_archivos_sql
from extraction import extraer_datos_crudos
from cleaning import procesar_limpieza_completa
from feature_engineering import (
    calcular_features_torniquetes,
    aplicar_motor_reglas
)
from datetime import datetime


def print_banner(titulo: str):
    """Imprime separadores visuales claros en consola."""
    linea = "=" * 70
    print(f"\n{linea}")
    print(f" {titulo.upper()}")
    print(f"{linea}")


def ejecutar_pipeline_completo():
    """
    Ejecuta el flujo secuencial de punta a punta:
      Paso 0: Simulación de fuentes (.sql) si no existen
      Paso 1: Extracción SQLite en memoria
      Paso 2: Limpieza y deduplicación (QA HU-01)
      Paso 3: Feature Engineering y motor de reglas analítico
      Paso 4: Entrenamiento de modelos LightGBM y semáforo algorítmico
      Paso 5: Lanzamiento automatizado del Dashboard en Streamlit
    """
    inicio_total = time.time()
    print_banner("▲ AURA FIT · INICIO DE PIPELINE ÁGIL AUTOMATIZADO")
    print(f"Directorio del proyecto: {PROJECT_DIR}")

    # --------------------------------------------------------------------------
    # PASO 0: VERIFICACIÓN O SIMULACIÓN DE DATOS CRUDOS (.sql)
    # --------------------------------------------------------------------------
    print_banner("Paso 0: Verificación de fuentes de datos (.sql)")
    archivos_sql = [
        "01_torniquetes_iot.sql",
        "02_pasarela_erp.sql",
        "03_aura_app_logs.sql"
    ]
    faltan_archivos = any(not os.path.exists(os.path.join(DATA_DIR, f)) for f in archivos_sql)

    if faltan_archivos:
        print("[AVISO] No se detectaron las 3 fuentes en /data. Generando simulación controlada...")
        generar_archivos_sql(num_socios=800)
    else:
        print("[OK] Fuentes .sql detectadas correctamente en disco.")

    # --------------------------------------------------------------------------
    # PASO 1: EXTRACCIÓN (SQLite en memoria)
    # --------------------------------------------------------------------------
    print_banner("Paso 1: Extracción de datos crudos (extraction.py)")
    t0 = time.time()
    t_raw, p_raw, a_raw = extraer_datos_crudos()
    print(f"[TIEMPO] Extracción completada en {time.time() - t0:.2f} segundos.")

    # --------------------------------------------------------------------------
    # PASO 2: LIMPIEZA Y CALIDAD DE DATOS (cleaning.py)
    # --------------------------------------------------------------------------
    print_banner("Paso 2: Limpieza, validación de formatos y deduplicación (cleaning.py)")
    t0 = time.time()
    t_clean, p_clean, a_clean = procesar_limpieza_completa(t_raw, p_raw, a_raw)
    print(f"[TIEMPO] Limpieza completada en {time.time() - t0:.2f} segundos.")

    # --------------------------------------------------------------------------
    # PASO 3: FEATURE ENGINEERING Y MOTOR DE REGLAS (feature_engineering.py)
    # --------------------------------------------------------------------------
    print_banner("Paso 3: Construcción de features y motor de reglas (feature_engineering.py)")
    t0 = time.time()
    fecha_corte = datetime.strptime("2026-10-25", "%Y-%m-%d")
    
    # Cálculo de métricas sobre torniquetes
    df_torniquetes_feat = calcular_features_torniquetes(t_clean, fecha_corte)

    # Consolidación de la Visión 360° del socio
    df_master = df_torniquetes_feat.merge(p_clean, on="id_socio", how="left")
    df_master = df_master.merge(a_clean, on="id_socio", how="left")

    # Aplicación del sistema de alerta temprana por reglas
    df_master = aplicar_motor_reglas(df_master)

    # Exportación inicial
    parquet_master_path = os.path.join(DATA_DIR, "df_master_features.parquet")
    df_master.to_parquet(parquet_master_path, index=False)
    print(f"[OK] Master Table preliminar guardada: {parquet_master_path}")
    print(f"[TIEMPO] Feature Engineering completado en {time.time() - t0:.2f} segundos.")

    # --------------------------------------------------------------------------
    # PASO 4: ENTRENAMIENTO Y SEMÁFORO ALGORÍTMICO (train.py)
    # --------------------------------------------------------------------------
    print_banner("Paso 4: Entrenamiento de modelos y semáforo algorítmico (train.py)")
    t0 = time.time()

    # Importar el módulo de modelos
    models_path = os.path.join(SRC_DIR, "models")
    if models_path not in sys.path:
        sys.path.insert(0, models_path)

    import train as model_train
    model_train.ejecutar_entrenamiento()
    print(f"[TIEMPO] Entrenamiento y exportación finalizados en {time.time() - t0:.2f} segundos.")

    tiempo_total = time.time() - inicio_total
    print_banner(f"PIPELINE COMPLETADO CON ÉXITO EN {tiempo_total:.2f} SEGUNDOS")

    # --------------------------------------------------------------------------
    # PASO 5: DESPLIEGUE DEL DASHBOARD STREAMLIT
    # --------------------------------------------------------------------------
    print("\n[DESPLIEGUE] Abriendo Dashboard de Recepción en Streamlit...")
    print(f"Ejecutando: python -m streamlit run \"{DASHBOARD_SCRIPT}\"\n")
    
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", DASHBOARD_SCRIPT], check=True)
    except KeyboardInterrupt:
        print("\n[FIN] Ejecución de Streamlit detenida por el usuario.")


if __name__ == "__main__":
    ejecutar_pipeline_completo()