# ⚙️ Guía de Instalación y Ejecución en Máquina Nueva

Este documento detalla el paso a paso para configurar, instalar y ejecutar de forma 100% automatizada el MVP de **Aura Fit** en cualquier computador nuevo (Windows, macOS o Linux).

---

## 📋 1. Requisitos del Sistema

1. **Python 3.10, 3.11 o 3.12** instalado en el sistema.
   * Para verificarlo, abre una terminal y ejecuta:
     ```bash
     python --version
     ```
2. **Git** (opcional, si se clona directamente desde GitHub).
3. **Visual Studio Code** (editor recomendado)[cite: 3].

---

## 📦 2. Contenido de `requirements.txt`

Asegúrate de que el archivo `requirements.txt` contenga las siguientes dependencias[cite: 3]:

```text
pandas>=2.0.0
numpy>=1.24.0
pyarrow>=12.0.0
scikit-learn>=1.3.0
lightgbm>=4.0.0
joblib>=1.3.0
streamlit>=1.32.0
```

---

## 🛠️ 3. Instalación Paso a Paso

### Paso 1: Descargar o clonar el repositorio
Abre una terminal (PowerShell, CMD o Bash) y ubícate en la carpeta raíz del proyecto:

```bash
git clone <URL_DEL_REPOSITORIO>
cd AURA_FIT
```

### Paso 2: Crear y activar un entorno virtual (`.venv`)
Se recomienda crear un entorno aislado para instalar las librerías sin afectar el sistema base:

* **En Windows (PowerShell):**
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  ```
  > **Nota:** Si Windows PowerShell muestra un aviso de permisos al activar el entorno, ejecuta primero este comando y vuelve a intentarlo:
  > ```powershell
  > Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
  > ```

* **En Windows (CMD):**
  ```cmd
  python -m venv .venv
  .\.venv\Scripts\activate.bat
  ```

* **En macOS / Linux:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

### Paso 3: Instalar las dependencias del proyecto
Con el entorno virtual activo, instala los paquetes listados en `requirements.txt`[cite: 3]:

```bash
python -m pip install --upgrade pip
pip install -r AURA-FIT-ML/AURA_FIT/requirements.txt
```
*(Si tu terminal ya se encuentra dentro de la subcarpeta `AURA-FIT-ML/AURA_FIT`, ejecuta simplemente `pip install -r requirements.txt`).*

---

## 🚀 4. Ejecución Automatizada del Pipeline (Un Solo Comando)

El proyecto cuenta con el script orquestador **`ejecucion.py`**, el cual ejecuta de principio a fin todas las etapas del MVP y muestra los logs de avance en consola[cite: 3]:

1. **Paso 0 (`simulate_data.py`):** Verifica si existen los 3 archivos `.sql` en `data/` (`01_torniquetes_iot.sql`, `02_pasarela_erp.sql`, `03_aura_app_logs.sql`) y los genera automáticamente si no están presentes[cite: 5, 6, 7].
2. **Paso 1 (`extraction.py`):** Carga los scripts `.sql` en una base de datos relacional SQLite en memoria y extrae las tablas crudas[cite: 8].
3. **Paso 2 (`cleaning.py`):** Homologa los formatos mixtos de fechas y elimina el 100% de los registros duplicados[cite: 2, 8].
4. **Paso 3 (`feature_engineering.py`):** Calcula las variables de comportamiento (días sin asistencia, caída quincenal, promedio mensual), aplica el motor de reglas explicables y exporta `df_master_features.parquet`[cite: 1, 2, 9].
5. **Paso 4 (`train.py`):** Entrena los modelos LightGBM (`lgbm_adopcion.pkl` y `lgbm_monto.pkl`), evalúa Recall y ROC-AUC en consola y asigna el semáforo algorítmico[cite: 1, 11].
6. **Paso 5 (`app.py`):** Inicia el servidor local de **Streamlit** y abre automáticamente el Dashboard en el navegador predeterminado[cite: 12].

Para ejecutar todo el flujo, corre el siguiente comando:

```bash
python AURA-FIT-ML/AURA_FIT/src/data_processing/ejecucion.py
```

---

## 🖥️ 5. Comandos para Ejecución Modular (Opcional)

Si ya corriste el pipeline una vez y deseas ejecutar únicamente una etapa específica:

* **Lanzar únicamente el Dashboard Ejecutivo en Streamlit:**
  ```bash
  python -m streamlit run AURA-FIT-ML/AURA_FIT/src/dashboard/app.py
  ```

* **Regenerar los datos simulados (`.sql`):**
  ```bash
  python AURA-FIT-ML/AURA_FIT/src/data_processing/simulate_data.py
  ```

* **Ejecutar solo la extracción y limpieza de datos:**
  ```bash
  python AURA-FIT-ML/AURA_FIT/src/data_processing/cleaning.py
  ```

* **Ejecutar solo la ingeniería de características:**
  ```bash
  python AURA-FIT-ML/AURA_FIT/src/data_processing/feature_engineering.py
  ```

* **Reentrenar únicamente los modelos de Machine Learning:**
  ```bash
  python AURA-FIT-ML/AURA_FIT/src/models/train.py
  ```

---

## 🔧 6. Solución de Problemas Frecuentes (Troubleshooting)

| Situación | Causa Común | Solución |
| :--- | :--- | :--- |
| Error: `'streamlit' no se reconoce como un comando...`[cite: 12] | La carpeta `Scripts` de Python no está en el `PATH` global de Windows[cite: 12]. | Ejecuta Streamlit invocando el módulo desde Python: `python -m streamlit run ...`[cite: 12]. |
| El navegador o sistema operativo está en **Modo Oscuro** | El navegador invierte colores de texto por defecto. | Usa el selector **"🎨 Tema Visual del Tablero: ☀️ Claro (PPTX) \| 🌙 Oscuro"** ubicado en la parte superior de la barra lateral izquierda del Dashboard. |
| Aviso `UserWarning: Could not find the number of physical cores`[cite: 10, 11] | Librería `loky` de `joblib` consultando núcleos en Windows[cite: 10, 11]. | Es un aviso informativo que no afecta el entrenamiento; el sistema utiliza automáticamente los núcleos lógicos[cite: 10, 11]. |