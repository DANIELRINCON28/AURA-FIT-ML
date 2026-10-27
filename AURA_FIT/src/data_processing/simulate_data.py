import os
import random
from datetime import datetime, timedelta
import numpy as np

# Semilla para reproducibilidad total en el equipo
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

# Ruta dinámica hacia AURA_FIT/data/ sin importar desde dónde se ejecute el script
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")


def generar_archivos_sql(num_socios: int = 800, fecha_corte_str: str = "2026-10-25"):
    """
    Genera 3 archivos .sql en la carpeta data/:
      1. 01_torniquetes_iot.sql  (Predictor Primario: accesos físicos e historial)
      2. 02_pasarela_erp.sql     (Detonante Financiero: planes, pagos y cobros declinados)
      3. 03_aura_app_logs.sql    (Enriquecedor Secundario / Mock: uso de app y reservas)
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    fecha_corte = datetime.strptime(fecha_corte_str, "%Y-%m-%d")

    sedes = [
        "Sede Poblado", "Sede Laureles", "Sede Envigado",
        "Sede Sabaneta", "Sede Belén", "Sede Chapinero",
        "Sede Usaquén", "Sede Ciudad Jardín"
    ]
    planes = ["Aura Fit", "Aura Black", "Aura Elite"]
    pesos_planes = [0.55, 0.30, 0.15]
    metodos_pago = ["Tarjeta Crédito", "Débito Automático", "PSE"]
    nombres_base = [
        "Juan", "María", "Carlos", "Laura", "Andrés", "Valentina",
        "Santiago", "Camila", "Daniel", "Sofía", "Sebastián", "Mariana",
        "David", "Paula", "Mateo", "Natalia", "Alejandro", "Juliana"
    ]
    apellidos_base = [
        "Pérez", "Gómez", "Rodríguez", "Martínez", "Rincón", "Ochoa",
        "Suaza", "Ríos", "Valencia", "Restrepo", "Giraldo", "Morales",
        "Castro", "Vargas", "Ramírez", "Londoño", "Cano", "Jiménez"
    ]

    sql_torniquetes = [
        "-- ==========================================",
        "-- FUENTE 1: TORNIQUETES IoT (Accesos Físicos)",
        "-- ==========================================",
        "DROP TABLE IF EXISTS raw_torniquetes;",
        "CREATE TABLE raw_torniquetes (",
        "    id_registro INTEGER PRIMARY KEY AUTOINCREMENT,",
        "    id_socio VARCHAR(20),",
        "    nombre_socio VARCHAR(100),",
        "    sede_frecuente VARCHAR(50),",
        "    fecha_vinculacion VARCHAR(30),",
        "    fecha_hora_ingreso VARCHAR(30)",
        ");\n"
    ]

    sql_pagos = [
        "-- ==========================================",
        "-- FUENTE 2: PASARELA ERP (Facturación y Pagos)",
        "-- ==========================================",
        "DROP TABLE IF EXISTS raw_pagos_erp;",
        "CREATE TABLE raw_pagos_erp (",
        "    id_socio VARCHAR(20) PRIMARY KEY,",
        "    plan_actual VARCHAR(30),",
        "    metodo_pago_registrado VARCHAR(30),",
        "    fecha_vencimiento VARCHAR(20),",
        "    antiguedad_meses INTEGER,",
        "    veces_renovado INTEGER,",
        "    cobro_fallido_reciente INTEGER,",
        "    costo_mensual_cop INTEGER",
        ");\n"
    ]

    sql_app = [
        "-- ==========================================",
        "-- FUENTE 3: AURA APP LOGS (Simulado / Mock)",
        "-- ==========================================",
        "DROP TABLE IF EXISTS raw_aura_app;",
        "CREATE TABLE raw_aura_app (",
        "    id_socio VARCHAR(20) PRIMARY KEY,",
        "    dias_sin_abrir_app INTEGER,",
        "    cancelaciones_app_30d INTEGER,",
        "    clases_grupales_reservadas INTEGER,",
        "    interacciones_soporte INTEGER",
        ");\n"
    ]

    Precios = {"Aura Fit": 89000, "Aura Black": 119000, "Aura Elite": 159000}

    for i in range(1, num_socios + 1):
        id_socio = f"SOC-{i:04d}"
        nombre = f"{random.choice(nombres_base)} {random.choice(apellidos_base)}"
        sede = random.choice(sedes)
        plan = random.choices(planes, weights=pesos_planes, k=1)[0]
        metodo = random.choice(metodos_pago)

        # Forzamos que ~45% de la base esté en la ventana de intervención (Día 45 a 70)
        if random.random() < 0.45:
            dias_vinculado = random.randint(45, 70)
        else:
            dias_vinculado = random.randint(25, 180)

        fecha_vinc = fecha_corte - timedelta(days=dias_vinculado)

        # Asignamos arquetipo de comportamiento para entrenar modelos y reglas coherentes:
        # 1. 'fiel' (50%): asiste constante
        # 2. 'en_riesgo_caida' (25%): asistía bien y cayó drásticamente en los últimos 15 días
        # 3. 'churn_consumado' (25%): dejó de asistir hace >= 21 días (SUP-01)
        arquetipo = random.choices(
            ["fiel", "en_riesgo_caida", "churn_consumado"],
            weights=[0.50, 0.25, 0.25],
            k=1
        )[0]

        # -----------------------------------------------------
        # 1. Generación de Accesos en Torniquetes
        # -----------------------------------------------------
        hora_habitual = random.choice([6, 7, 8, 12, 17, 18, 19, 20])
        fechas_asistencia = []

        for d in range(dias_vinculado + 1):
            dia_actual = fecha_vinc + timedelta(days=d)
            dias_hasta_corte = (fecha_corte - dia_actual).days

            if arquetipo == "fiel":
                prob_asistir = 0.45  # ~3.1 veces por semana
            elif arquetipo == "en_riesgo_caida":
                # Caída fuerte en los últimos 15 días o inasistencia de 8-16 días
                if dias_hasta_corte <= 10:
                    prob_asistir = 0.0
                elif dias_hasta_corte <= 15:
                    prob_asistir = 0.08
                else:
                    prob_asistir = 0.50
            else:  # churn_consumado (SUP-01: >= 21 días sin asistencia)
                dias_abandono = random.randint(21, min(35, max(22, dias_vinculado - 5)))
                if dias_hasta_corte < dias_abandono:
                    prob_asistir = 0.0
                else:
                    prob_asistir = 0.35

            if d == 0 or random.random() < prob_asistir:
                minuto = random.randint(0, 59)
                dt_ingreso = dia_actual.replace(hour=hora_habitual, minute=minuto, second=0)
                fechas_asistencia.append(dt_ingreso)

        for dt_ing in fechas_asistencia:
            # Inyectamos 3% de fechas con formato slash (DD/MM/YYYY) para simular el incidente del Sprint 1
            if random.random() < 0.03:
                str_ingreso = dt_ing.strftime("%d/%m/%Y %H:%M:%S")
            else:
                str_ingreso = dt_ing.strftime("%Y-%m-%d %H:%M:%S")

            str_vinc = fecha_vinc.strftime("%Y-%m-%d")
            insert_stmt = (
                f"INSERT INTO raw_torniquetes (id_socio, nombre_socio, sede_frecuente, fecha_vinculacion, fecha_hora_ingreso) "
                f"VALUES ('{id_socio}', '{nombre}', '{sede}', '{str_vinc}', '{str_ingreso}');"
            )
            sql_torniquetes.append(insert_stmt)

            # Inyectamos 1.5% de registros duplicados para validar HU-01 (0% duplicados en limpieza)
            if random.random() < 0.015:
                sql_torniquetes.append(insert_stmt)

        # -----------------------------------------------------
        # 2. Generación de Pasarela ERP (Pagos)
        # -----------------------------------------------------
        antiguedad_meses = max(1, round(dias_vinculado / 30))
        veces_renovado = max(0, antiguedad_meses - 1)
        fecha_venc = (fecha_corte + timedelta(days=random.randint(-10, 25))).strftime("%Y-%m-%d")

        if arquetipo == "churn_consumado":
            cobro_fallido = 1 if random.random() < 0.65 else 0
        elif arquetipo == "en_riesgo_caida":
            cobro_fallido = 1 if random.random() < 0.40 else 0
        else:
            cobro_fallido = 1 if random.random() < 0.05 else 0

        sql_pagos.append(
            f"INSERT INTO raw_pagos_erp VALUES ("
            f"'{id_socio}', '{plan}', '{metodo}', '{fecha_venc}', "
            f"{antiguedad_meses}, {veces_renovado}, {cobro_fallido}, {Precios[plan]});"
        )

        # -----------------------------------------------------
        # 3. Generación de Aura App Logs (Mock / Contingencia)
        # -----------------------------------------------------
        if arquetipo == "fiel":
            dias_sin_app = random.randint(0, 6)
            cancelaciones = random.randint(0, 1)
            clases_res = random.randint(2, 10)
            soporte = random.randint(0, 1)
        elif arquetipo == "en_riesgo_caida":
            dias_sin_app = random.randint(8, 25)
            cancelaciones = random.randint(2, 5)
            clases_res = random.randint(0, 2)
            soporte = random.randint(1, 3)
        else:
            dias_sin_app = random.randint(20, 60)
            cancelaciones = random.randint(1, 6)
            clases_res = 0
            soporte = random.randint(1, 4)

        sql_app.append(
            f"INSERT INTO raw_aura_app VALUES ("
            f"'{id_socio}', {dias_sin_app}, {cancelaciones}, {clases_res}, {soporte});"
        )

    # Escritura de los 3 archivos .sql en AURA_FIT/data/
    archivos = {
        "01_torniquetes_iot.sql": sql_torniquetes,
        "02_pasarela_erp.sql": sql_pagos,
        "03_aura_app_logs.sql": sql_app,
    }

    for nombre_archivo, contenido in archivos.items():
        ruta_completa = os.path.join(DATA_DIR, nombre_archivo)
        with open(ruta_completa, "w", encoding="utf-8") as f:
            f.write("\n".join(contenido))
        print(f"[OK] Generado: {ruta_completa} ({len(contenido) - 6} registros INSERT)")


if __name__ == "__main__":
    print("Iniciando simulación de las 3 fuentes de datos de Aura Fit...")
    generar_archivos_sql(num_socios=800)
    print("¡Simulación finalizada con éxito!")