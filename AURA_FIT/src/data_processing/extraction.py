import os
import sqlite3
import pandas as pd

# Rutas dinámicas
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")


def ejecutar_script_sql(cursor: sqlite3.Cursor, ruta_archivo: str):
    """Lee y ejecuta un script .sql en la sesión SQLite activa."""
    if not os.path.exists(ruta_archivo):
        raise FileNotFoundError(f"No se encontró el archivo: {ruta_archivo}")
    
    with open(ruta_archivo, "r", encoding="utf-8") as f:
        script = f.read()
    cursor.executescript(script)


def extraer_datos_crudos():
    """
    Ejecuta los scripts .sql en memoria y retorna 3 DataFrames crudos:
      - df_torniquetes: marcas de acceso físico
      - df_pagos: pasarela ERP y contratos
      - df_app: métricas y uso digital de Aura App
    """
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    archivos = [
        "01_torniquetes_iot.sql",
        "02_pasarela_erp.sql",
        "03_aura_app_logs.sql"
    ]

    for archivo in archivos:
        ruta = os.path.join(DATA_DIR, archivo)
        ejecutar_script_sql(cursor, ruta)

    # Extracción a DataFrames
    df_torniquetes = pd.read_sql_query("SELECT * FROM raw_torniquetes;", conn)
    df_pagos = pd.read_sql_query("SELECT * FROM raw_pagos_erp;", conn)
    df_app = pd.read_sql_query("SELECT * FROM raw_aura_app;", conn)

    conn.close()

    print("[EXTRACTION] Extracción completada con éxito:")
    print(f"  • Torniquetes crudos: {len(df_torniquetes):,} registros")
    print(f"  • Pasarela Pagos:     {len(df_pagos):,} socios")
    print(f"  • Aura App Logs:      {len(df_app):,} registros")

    return df_torniquetes, df_pagos, df_app


if __name__ == "__main__":
    extraer_datos_crudos()