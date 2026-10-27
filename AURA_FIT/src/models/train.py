import os
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score, recall_score, mean_absolute_error

# Soporte para LightGBM nativo con fallback a Scikit-Learn
try:
    from lightgbm import LGBMClassifier, LGBMRegressor
    USAR_LGBM = True
except ImportError:
    from sklearn.ensemble import HistGradientBoostingClassifier as LGBMClassifier
    from sklearn.ensemble import HistGradientBoostingRegressor as LGBMRegressor
    USAR_LGBM = False

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_PATH = os.path.join(BASE_DIR, "data", "df_master_features.parquet")
MODELS_DIR = os.path.join(BASE_DIR, "models")


def cargar_datos_master():
    """Carga la tabla maestra consolidada."""
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"No existe el archivo maestro en: {DATA_PATH}. Ejecuta feature_engineering.py primero.")
    return pd.read_parquet(DATA_PATH)


def clasificar_semaforo(probabilidad: float) -> str:
    """
    Semáforo algorítmico automatizado según Diapositiva 7:
      - Riesgo Alto: > 70%
      - Riesgo Medio: 40% - 70%
      - Riesgo Bajo: < 40%
    """
    if probabilidad > 0.70:
        return "Alto"
    elif probabilidad >= 0.40:
        return "Medio"
    else:
        return "Bajo"


def preparar_features(df: pd.DataFrame):
    """
    Selecciona variables predictivas evitando 'data leakage' directo sobre el target.
    Se excluye 'dias_sin_asistencia' para forzar que el modelo aprenda de la desaceleración
    (caída de frecuencia en 15d, ratio mensual, fricción financiera y canales digitales).
    """
    features_predictivas = [
        "var_asistencia_15d",
        "promedio_visitas_mensuales",
        "ultima_hora_ingreso",
        "dias_vinculado",
        "antiguedad_meses",
        "veces_renovado",
        "cobro_fallido_reciente",
        "dias_sin_abrir_app",
        "cancelaciones_app_30d",
        "clases_grupales_reservadas",
        "interacciones_soporte"
    ]

    df_encoded = df.copy()
    plan_mapping = {"Aura Fit": 1, "Aura Black": 2, "Aura Elite": 3}
    df_encoded["plan_cat"] = df_encoded["plan_actual"].map(plan_mapping).fillna(1)

    columnas_modelo = features_predictivas + ["plan_cat"]
    X = df_encoded[columnas_modelo]
    return X, df_encoded, columnas_modelo


def entrenar_modelo_churn(X: pd.DataFrame, y: pd.Series):
    """
    Entrena el clasificador LightGBM para predecir probabilidades continuas de fuga.
    """
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    if USAR_LGBM:
        modelo = LGBMClassifier(
            n_estimators=100,
            learning_rate=0.04,
            max_depth=3,
            num_leaves=8,
            random_state=42,
            verbose=-1
        )
    else:
        modelo = LGBMClassifier(
            max_iter=100,
            learning_rate=0.04,
            max_depth=3,
            max_leaf_nodes=8,
            random_state=42
        )

    modelo.fit(X_train, y_train)

    y_pred = modelo.predict(X_test)
    y_prob = modelo.predict_proba(X_test)[:, 1]

    rec = recall_score(y_test, y_pred)
    roc = roc_auc_score(y_test, y_prob)

    print("\n" + "=" * 60)
    print(" EVALUACIÓN DEL MODELO DE CHURN (lgbm_adopcion.pkl)")
    print("=" * 60)
    print(f"• Motor utilizado: {'LightGBM' if USAR_LGBM else 'HistGradientBoosting (Scikit-Learn)'}")
    print(f"• Recall (Meta CoE >= 80%): {rec * 100:.2f}%")
    print(f"• ROC-AUC (Meta CoE >= 0.78): {roc:.4f}")
    print("\nReporte de clasificación en test set:")
    print(classification_report(y_test, y_pred, target_names=["Activo", "Fuga"]))

    return modelo


def entrenar_modelo_monto(X: pd.DataFrame, df_encoded: pd.DataFrame):
    """
    Estima el valor monetario en riesgo proyectado por socio (meses faltantes a breakeven).
    """
    meses_para_breakeven = np.maximum(1, 5 - df_encoded["antiguedad_meses"])
    y_monto = df_encoded["costo_mensual_cop"] * meses_para_breakeven

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_monto, test_size=0.25, random_state=42
    )

    if USAR_LGBM:
        regresor = LGBMRegressor(
            n_estimators=80,
            learning_rate=0.05,
            max_depth=3,
            random_state=42,
            verbose=-1
        )
    else:
        regresor = LGBMRegressor(
            max_iter=80,
            learning_rate=0.05,
            max_depth=3,
            random_state=42
        )

    regresor.fit(X_train, y_train)

    y_pred_monto = regresor.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred_monto)

    print("=" * 60)
    print(" EVALUACIÓN DEL MODELO DE VALOR EN RIESGO (lgbm_monto.pkl)")
    print("=" * 60)
    print(f"• Error Absoluto Medio (MAE): ${mae:,.0f} COP")

    return regresor


def aplicar_semaforo_a_master(df: pd.DataFrame, modelo_churn, modelo_monto, X: pd.DataFrame):
    """
    Calcula probabilidades continuas, valor en riesgo y asigna las bandas
    del semáforo algorítmico al dataset maestro.
    """
    # 1. Probabilidades continuas y estimación financiera
    probs = modelo_churn.predict_proba(X)[:, 1]
    montos_riesgo = modelo_monto.predict(X)

    df["probabilidad_churn"] = np.round(probs * 100, 1)
    df["monto_en_riesgo_cop"] = np.round(montos_riesgo, 0).astype(int)

    # 2. Asignación del Semáforo Algorítmico (Diapositiva 7)
    df["semaforo_algoritmico"] = [clasificar_semaforo(p) for p in probs]

    # Guardar la tabla enriquecida
    df.to_parquet(DATA_PATH, index=False)

    print("\n" + "=" * 60)
    print(" DISTRIBUCIÓN DEL SEMÁFORO ALGORÍTMICO (AURA FIT)")
    print("=" * 60)
    distribucion = df["semaforo_algoritmico"].value_counts()
    for nivel in ["Alto", "Medio", "Bajo"]:
        conteo = distribucion.get(nivel, 0)
        pct = (conteo / len(df)) * 100
        print(f"  • Riesgo {nivel:<5}: {conteo:>4} socios ({pct:>5.1f}%)")
    print("=" * 60)


def guardar_artefactos(modelo_churn, modelo_monto, columnas):
    """Serializa modelos y metadatos en la carpeta models/."""
    os.makedirs(MODELS_DIR, exist_ok=True)

    joblib.dump(modelo_churn, os.path.join(MODELS_DIR, "lgbm_adopcion.pkl"))
    joblib.dump(modelo_monto, os.path.join(MODELS_DIR, "lgbm_monto.pkl"))
    joblib.dump(columnas, os.path.join(MODELS_DIR, "features_config.pkl"))

    print("\n[OK] Artefactos exportados exitosamente en la carpeta models/.")


def ejecutar_entrenamiento():
    """Ejecución del pipeline de entrenamiento."""
    df = cargar_datos_master()
    X, df_encoded, cols = preparar_features(df)
    y = df_encoded["target_churn_90d"]

    modelo_churn = entrenar_modelo_churn(X, y)
    modelo_monto = entrenar_modelo_monto(X, df_encoded)
    
    # Aplicación del semáforo y enriquecimiento de la tabla maestra
    aplicar_semaforo_a_master(df, modelo_churn, modelo_monto, X)
    guardar_artefactos(modelo_churn, modelo_monto, cols)


if __name__ == "__main__":
    ejecutar_entrenamiento()