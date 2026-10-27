import pandas as pd


def limpiar_torniquetes(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Limpia datos de torniquetes:
      - Elimina duplicados de ingresos en el mismo segundo para el mismo socio (DoD HU-01).
      - Estandariza fechas mixtas (YYYY-MM-DD vs DD/MM/YYYY) resolviendo el incidente de Sprint 1.
      - Ordena cronológicamente.
    """
    df = df_raw.copy()
    total_inicial = len(df)

    # 1. Parseo flexible de fechas para homogeneizar formatos
    df["fecha_hora_ingreso"] = pd.to_datetime(df["fecha_hora_ingreso"], format="mixed", errors="coerce")
    df["fecha_vinculacion"] = pd.to_datetime(df["fecha_vinculacion"], format="mixed", errors="coerce")

    # 2. Descartar nulos en fechas clave si existieran
    df = df.dropna(subset=["fecha_hora_ingreso", "id_socio"])

    # 3. Eliminar duplicados exactos de marcación (DoD: 0% duplicados)
    df = df.drop_duplicates(subset=["id_socio", "fecha_hora_ingreso"])
    duplicados_eliminados = total_inicial - len(df)

    df = df.sort_values(by=["id_socio", "fecha_hora_ingreso"]).reset_index(drop=True)

    print(f"[CLEANING] Torniquetes: {len(df):,} válidos ({duplicados_eliminados} duplicados removidos)")
    return df


def limpiar_pagos(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Valida tipos y coherencia en la pasarela ERP."""
    df = df_raw.copy()
    df["fecha_vencimiento"] = pd.to_datetime(df["fecha_vencimiento"], errors="coerce")
    df["antiguedad_meses"] = df["antiguedad_meses"].fillna(1).astype(int)
    df["cobro_fallido_reciente"] = df["cobro_fallido_reciente"].fillna(0).astype(int)
    df["costo_mensual_cop"] = df["costo_mensual_cop"].astype(float)
    df = df.drop_duplicates(subset=["id_socio"]).reset_index(drop=True)

    print(f"[CLEANING] Pagos ERP: {len(df):,} socios validados")
    return df


def limpiar_app(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Valida métricas del mock de Aura App."""
    df = df_raw.copy()
    columnas_numericas = [
        "dias_sin_abrir_app",
        "cancelaciones_app_30d",
        "clases_grupales_reservadas",
        "interacciones_soporte"
    ]
    for col in columnas_numericas:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    df = df.drop_duplicates(subset=["id_socio"]).reset_index(drop=True)

    print(f"[CLEANING] Aura App: {len(df):,} socios validados")
    return df


def procesar_limpieza_completa(df_torniquetes_raw, df_pagos_raw, df_app_raw):
    """Pipeline unificado de limpieza para las 3 fuentes."""
    df_torniquetes = limpiar_torniquetes(df_torniquetes_raw)
    df_pagos = limpiar_pagos(df_pagos_raw)
    df_app = limpiar_app(df_app_raw)
    return df_torniquetes, df_pagos, df_app


if __name__ == "__main__":
    from extraction import extraer_datos_crudos
    t_raw, p_raw, a_raw = extraer_datos_crudos()
    t_clean, p_clean, a_clean = procesar_limpieza_completa(t_raw, p_raw, a_raw)