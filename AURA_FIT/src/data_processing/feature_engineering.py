import os
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")


def calcular_features_torniquetes(df_torniquetes: pd.DataFrame, fecha_corte: datetime) -> pd.DataFrame:
    """
    Calcula métricas de asistencia física y recencia a partir de los accesos por torniquete.
    """
    # 1. Asegurar formato de fecha en ingresos
    df_torniquetes["fecha_hora_ingreso"] = pd.to_datetime(df_torniquetes["fecha_hora_ingreso"])
    df_torniquetes["fecha_ingreso"] = df_torniquetes["fecha_hora_ingreso"].dt.date
    df_torniquetes["hora_ingreso"] = df_torniquetes["fecha_hora_ingreso"].dt.hour

    # Ventanas de análisis de 15 días
    fecha_limite_15d = (fecha_corte - timedelta(days=15)).date()
    fecha_limite_30d = (fecha_corte - timedelta(days=30)).date()
    corte_date = fecha_corte.date()

    metricas_socios = []

    for id_socio, grupo in df_torniquetes.groupby("id_socio"):
        nombre = grupo["nombre_socio"].iloc[0]
        sede = grupo["sede_frecuente"].iloc[0]

        # Fechas extremas
        primer_ingreso = grupo["fecha_hora_ingreso"].min().date()
        ultimo_ingreso = grupo["fecha_hora_ingreso"].max().date()

        # Días sin asistencia y días de vinculación (SUP-06)
        dias_sin_asistencia = (corte_date - ultimo_ingreso).days
        dias_vinculado = max(1, (corte_date - primer_ingreso).days)

        # Visitas únicas por día en cada ventana
        visitas_unicas = grupo.drop_duplicates(subset=["fecha_ingreso"])
        visitas_ultimos_15d = len(visitas_unicas[visitas_unicas["fecha_ingreso"] >= fecha_limite_15d])
        visitas_previas_15d = len(
            visitas_unicas[
                (visitas_unicas["fecha_ingreso"] >= fecha_limite_30d) &
                (visitas_unicas["fecha_ingreso"] < fecha_limite_15d)
            ]
        )

        # Variación porcentual en 15 días
        if visitas_previas_15d == 0:
            var_asistencia_15d = 0.0 if visitas_ultimos_15d == 0 else 1.0
        else:
            var_asistencia_15d = (visitas_ultimos_15d - visitas_previas_15d) / visitas_previas_15d

        # Frecuencia mensual normalizada
        total_visitas = len(visitas_unicas)
        promedio_visitas_mensuales = round((total_visitas / dias_vinculado) * 30.0, 1)

        # Última hora habitual de ingreso
        ultima_hora_ingreso = int(grupo.sort_values("fecha_hora_ingreso").iloc[-1]["hora_ingreso"])

        # Target de Abandono (SUP-01: Churn marcado a los 21 días sin asistencia)
        target_churn_90d = 1 if dias_sin_asistencia >= 21 else 0

        metricas_socios.append({
            "id_socio": id_socio,
            "nombre_socio": nombre,
            "sede_frecuente": sede,
            "dias_vinculado": dias_vinculado,
            "dias_sin_asistencia": dias_sin_asistencia,
            "var_asistencia_15d": round(float(var_asistencia_15d), 3),
            "promedio_visitas_mensuales": promedio_visitas_mensuales,
            "ultima_hora_ingreso": ultima_hora_ingreso,
            "target_churn_90d": target_churn_90d
        })

    return pd.DataFrame(metricas_socios)


def aplicar_motor_reglas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica el sistema de alerta temprana basado en reglas e interpretabilidad:
      - Riesgo Alto: >= 14 días sin ingreso O caída de visitas >= 50%
      - Riesgo Medio: 7 a 13 días sin ingreso O caída entre 25% y 49%
      - Riesgo Bajo: resto de socios
    """
    niveles = []
    causas = []
    prescripciones = []

    for _, row in df.iterrows():
        dias = row["dias_sin_asistencia"]
        caida = row["var_asistencia_15d"]
        cobro_fallido = row.get("cobro_fallido_reciente", 0)

        # 1. Evaluación de Riesgo Alto
        if dias >= 14 or caida <= -0.50:
            niveles.append("Alto")
            if dias >= 14:
                causas.append(f"Inasistencia prolongada ({int(dias)} días sin asistir)")
                prescripciones.append("Llamada personalizada de bienvenida / reactivación")
            else:
                causas.append(f"Caída drástica de visitas ({abs(round(caida * 100))}% en 15d)")
                prescripciones.append("Sesión VIP de cortesía / Rutina con entrenador")

        # 2. Evaluación de Riesgo Medio
        elif (7 <= dias <= 13) or (-0.49 <= caida <= -0.25):
            niveles.append("Medio")
            if dias >= 7:
                causas.append(f"Alerta temprana ({int(dias)} días sin asistir)")
                prescripciones.append("Mensaje motivacional + Invitación a clase grupal")
            else:
                causas.append(f"Descenso moderado de ritmo ({abs(round(caida * 100))}%)")
                prescripciones.append("Pase de cortesía para un acompañante")

        # 3. Riesgo Bajo
        else:
            if cobro_fallido == 1:
                niveles.append("Medio")
                causas.append("Fricción en cobro de pasarela ERP")
                prescripciones.append("Notificación de actualización de método de pago")
            else:
                niveles.append("Bajo")
                causas.append("Comportamiento habitual y constante")
                prescripciones.append("Fidelización estándar / Felicitación por constancia")

    df["nivel_riesgo_reglas"] = niveles
    df["causa_raiz"] = causas
    df["prescripcion_sugerida"] = prescripciones

    # Flag de intervención operativa (SUP-03: Día 45 a 70)
    df["en_ventana_intervencion"] = df["dias_vinculado"].between(45, 70)

    return df


def construir_master_features(fecha_corte_str: str = "2026-10-25") -> pd.DataFrame:
    """
    Orquesta la unificación de las 3 fuentes limpias, calcula variables analíticas
    y exporta el archivo df_master_features.parquet en data/.
    """
    from extraction import extraer_datos_crudos
    from cleaning import procesar_limpieza_completa

    fecha_corte = datetime.strptime(fecha_corte_str, "%Y-%m-%d")

    # 1. Extracción y Limpieza
    t_raw, p_raw, a_raw = extraer_datos_crudos()
    t_clean, p_clean, a_clean = procesar_limpieza_completa(t_raw, p_raw, a_raw)

    # 2. Features de Torniquetes (Predictor Primario)
    df_torniquetes_feat = calcular_features_torniquetes(t_clean, fecha_corte)

    # 3. Merge con ERP (Pagos) y Mock (App)
    df_master = df_torniquetes_feat.merge(p_clean, on="id_socio", how="left")
    df_master = df_master.merge(a_clean, on="id_socio", how="left")

    # 4. Asignación del motor de reglas analítico
    df_master = aplicar_motor_reglas(df_master)

    # 5. Persistencia en formato Parquet
    ruta_salida = os.path.join(DATA_DIR, "df_master_features.parquet")
    df_master.to_parquet(ruta_salida, index=False)

    print(f"\n[FEATURE ENGINEERING] Master Table generada con éxito:")
    print(f"  • Ubicación: {ruta_salida}")
    print(f"  • Dimensiones: {df_master.shape[0]} socios x {df_master.shape[1]} columnas")
    print(f"  • Tasa de Churn histórica (>=21 días): {df_master['target_churn_90d'].mean() * 100:.1f}%")
    print(f"  • Socios en ventana de intervención (45-70d): {df_master['en_ventana_intervencion'].sum()}")

    return df_master


if __name__ == "__main__":
    construir_master_features()