import os
import time
import numpy as np
import pandas as pd
import streamlit as st

# ==============================================================================
# CONFIGURACIÓN DE PÁGINA
# ==============================================================================
st.set_page_config(
    page_title="Aura Fit | Alerta Temprana & Retención",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# BARRA LATERAL (SIDEBAR): SELECTOR DE TEMA Y FILTROS
# ==============================================================================
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_PATH = os.path.join(BASE_DIR, "data", "df_master_features.parquet")
GESTION_PATH = os.path.join(BASE_DIR, "data", "estado_gestion_sedes.parquet")


@st.cache_data(ttl=10)
def cargar_datos():
    t0 = time.time()
    if not os.path.exists(DATA_PATH):
        return None, 0.0
    df = pd.read_parquet(DATA_PATH)
    latencia = round(time.time() - t0, 3)
    return df, latencia


df_master, tiempo_carga = cargar_datos()

if df_master is None:
    st.error("⚠️ No se encontró `df_master_features.parquet` en `data/`. Ejecuta `ejecucion.py` primero.")
    st.stop()

if "estado_contacto" not in st.session_state:
    if os.path.exists(GESTION_PATH):
        df_gest = pd.read_parquet(GESTION_PATH)
        st.session_state["estado_contacto"] = dict(zip(df_gest["id_socio"], df_gest["estado"]))
    else:
        estados_demo = ["Pendiente", "Pendiente", "Llamado", "Rescatado", "No aceptó", "Pendiente"]
        st.session_state["estado_contacto"] = {
            soc: estados_demo[i % len(estados_demo)]
            for i, soc in enumerate(df_master["id_socio"])
        }

# Paleta Corporativa Base
COLOR_RED = "#CC0000"
COLOR_AMBER = "#F2A900"
COLOR_GREEN = "#1E7E45"

with st.sidebar:
    st.markdown(f"""
    <div style="background-color:#111111; padding:20px 18px; border-radius:6px; border-left:5px solid {COLOR_RED}; margin-bottom:16px;">
        <div style="color:{COLOR_RED}; font-weight:900; font-size:1.5rem; letter-spacing:2px;">▲ AURA FIT</div>
        <div style="color:#E0E0E0; font-size:0.82rem; margin-top:4px;">Centro de Excelencia de Analítica (CoE)</div>
        <div style="color:#999999; font-size:0.75rem; margin-top:2px;">Sistema de Alerta Temprana v2.0</div>
    </div>
    """, unsafe_allow_html=True)

    # Selector de tema visual compatible con st.radio horizontal
    modo_visual = st.radio(
        "🎨 Tema Visual del Tablero:",
        options=["☀️ Claro (PPTX)", "🌙 Oscuro"],
        index=0,
        horizontal=True
    )
    es_oscuro = (modo_visual == "🌙 Oscuro")

    st.markdown("### 🎛️ Filtros de Recepción")

    lista_sedes = ["Todas las Sedes (Red Nacional)"] + sorted(df_master["sede_frecuente"].unique().tolist())
    sede_sel = st.selectbox("📍 Seleccionar Sede:", lista_sedes, index=1)

    solo_ventana = st.toggle("🎯 Ventana Crítica (Día 45 a 70)", value=True)
    top_25_limit = st.toggle("🛡️ Límite Operativo (Top 25 / día)", value=True)

    criterio_semaforo = st.radio(
        "⚙️ Motor de Clasificación:",
        ["Reglas de Asistencia (Cierre Ágil)", "Score Algorítmico LightGBM"],
        index=0
    )

    planes_sel = st.multiselect(
        "💳 Planes Incluidos:",
        options=["Aura Fit", "Aura Black", "Aura Elite"],
        default=["Aura Fit", "Aura Black", "Aura Elite"]
    )

    st.markdown("---")
    st.caption(f"⚡ Carga del ranking: **{tiempo_carga} s** (Meta < 3.0 s)")
    st.caption("👥 **Equipo CoE:** Mariana Ochoa (SM) · Daniel Rincón (PO) · David Gómez · Rafael Ríos · Juan M. Suaza")

# ==============================================================================
# VARIABLES DINÁMICAS DE COLOR SEGÚN EL TEMA ELEGIDO
# ==============================================================================
if es_oscuro:
    BG_MAIN = "#0E1117"
    BG_CARD = "#1A1D24"
    BG_ALERT_M3 = "#2C1215"
    TEXT_PRIMARY = "#F5F5F7"
    TEXT_SECONDARY = "#B0B5C0"
    BORDER_COLOR = "#2E333D"
else:
    BG_MAIN = "#FFFFFF"
    BG_CARD = "#F4F4F6"
    BG_ALERT_M3 = "#FFF0F0"
    TEXT_PRIMARY = "#111111"
    TEXT_SECONDARY = "#4A4A4A"
    BORDER_COLOR = "#E0E0E4"

# ==============================================================================
# INYECCIÓN DE CSS CON CONTRASTE FORZADO
# ==============================================================================
st.markdown(f"""
<style>
    .stApp {{
        background-color: {BG_MAIN} !important;
        color: {TEXT_PRIMARY} !important;
        font-family: 'Inter', 'Segoe UI', Roboto, Helvetica, sans-serif;
    }}
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
    .stApp p, .stApp span, .stApp label, .stApp div[data-testid="stCaptionContainer"] {{
        color: {TEXT_PRIMARY};
    }}
    section[data-testid="stSidebar"] {{
        background-color: #14161B !important;
    }}
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3, section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] div[data-testid="stCaptionContainer"] {{
        color: #F0F0F5 !important;
    }}
    button[data-baseweb="tab"] p {{
        color: {TEXT_SECONDARY} !important;
        font-weight: 700 !important;
        font-size: 0.92rem !important;
    }}
    button[data-baseweb="tab"][aria-selected="true"] p {{
        color: {COLOR_RED} !important;
        font-weight: 900 !important;
    }}
    div[data-testid="stExpander"] details summary p {{
        color: {TEXT_PRIMARY} !important;
        font-weight: 700 !important;
    }}
    .aura-header-box {{
        border-left: 6px solid {COLOR_RED};
        padding-left: 18px;
        margin-bottom: 22px;
    }}
    .aura-tag {{
        color: {COLOR_RED} !important;
        font-weight: 800;
        font-size: 0.85rem;
        letter-spacing: 1.8px;
        text-transform: uppercase;
        margin-bottom: 4px;
    }}
    .aura-title {{
        color: {TEXT_PRIMARY} !important;
        font-weight: 900;
        font-size: 2.3rem;
        line-height: 1.15;
        margin: 0;
    }}
    .aura-subtitle {{
        color: {TEXT_SECONDARY} !important;
        font-size: 1.05rem;
        margin-top: 6px;
    }}
    .kpi-card {{
        background-color: {BG_CARD};
        border: 1px solid {BORDER_COLOR};
        border-left: 5px solid {COLOR_RED};
        padding: 16px 20px;
        border-radius: 6px;
    }}
    .kpi-value {{
        font-size: 2.1rem;
        font-weight: 900;
        color: {TEXT_PRIMARY};
        line-height: 1.1;
    }}
    .kpi-label {{
        font-size: 0.88rem;
        color: {TEXT_SECONDARY} !important;
        margin-top: 5px;
        font-weight: 600;
    }}
    .ranking-banner {{
        background-color: #111111;
        color: #FFFFFF !important;
        padding: 14px 22px;
        border-radius: 8px 8px 0 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 14px;
    }}
    .ranking-banner-left {{
        color: #FFFFFF !important;
        font-weight: 800;
        font-size: 1.02rem;
        letter-spacing: 1.2px;
        display: flex;
        align-items: center;
        gap: 10px;
    }}
    .red-dot {{
        height: 12px;
        width: 12px;
        background-color: {COLOR_RED};
        border-radius: 50%;
        display: inline-block;
    }}
    .pill-dark {{
        background-color: #262626;
        color: #E8E8E8 !important;
        padding: 5px 14px;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 600;
        margin-left: 8px;
        border: 1px solid #3A3A3A;
    }}
    .pill-red {{
        background-color: {COLOR_RED};
        color: #FFFFFF !important;
        padding: 5px 14px;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 700;
        margin-left: 8px;
    }}
    .semaforo-row {{
        display: flex;
        align-items: center;
        margin-bottom: 10px;
        background-color: {BG_CARD};
        border: 1px solid {BORDER_COLOR};
        border-radius: 6px;
        overflow: hidden;
    }}
    .semaforo-badge {{
        width: 145px;
        padding: 14px 16px;
        font-weight: 900;
        font-size: 0.98rem;
        text-align: center;
        letter-spacing: 1px;
        flex-shrink: 0;
    }}
    .semaforo-desc {{
        padding: 14px 20px;
        font-size: 0.95rem;
        font-weight: 600;
        color: {TEXT_PRIMARY} !important;
        flex-grow: 1;
    }}
    .semaforo-action {{
        width: 190px;
        padding: 14px 18px;
        font-weight: 800;
        font-size: 0.85rem;
        text-align: right;
        letter-spacing: 0.6px;
        flex-shrink: 0;
    }}
    .dora-card {{
        background-color: {BG_CARD};
        padding: 22px 20px;
        border-radius: 6px;
        border: 1px solid {BORDER_COLOR};
    }}
    .dora-card-alert {{
        background-color: {BG_CARD};
        padding: 22px 20px;
        border-radius: 6px;
        border: 2px solid {COLOR_RED};
    }}
    .dora-title {{
        font-size: 0.78rem;
        font-weight: 800;
        color: {TEXT_SECONDARY} !important;
        letter-spacing: 1px;
        text-transform: uppercase;
        min-height: 34px;
    }}
    .dora-big {{
        font-size: 2.7rem;
        font-weight: 900;
        color: {TEXT_PRIMARY} !important;
        line-height: 1.05;
        margin: 8px 0 4px 0;
    }}
    .dora-unit {{
        font-size: 0.9rem;
        color: {TEXT_SECONDARY} !important;
        margin-bottom: 14px;
    }}
    .dora-sprint {{
        font-size: 0.82rem;
        color: {TEXT_PRIMARY} !important;
        margin-bottom: 14px;
    }}
    .dora-badge-ok {{
        background-color: #111111;
        color: #FFFFFF !important;
        text-align: center;
        padding: 8px;
        font-weight: 800;
        font-size: 0.78rem;
        letter-spacing: 1px;
        border-radius: 4px;
    }}
    .dora-badge-warn {{
        background-color: {COLOR_RED};
        color: #FFFFFF !important;
        text-align: center;
        padding: 8px;
        font-weight: 800;
        font-size: 0.78rem;
        letter-spacing: 1px;
        border-radius: 4px;
    }}
    .black-callout {{
        background-color: #111111;
        color: #FFFFFF !important;
        padding: 24px 28px;
        border-radius: 6px;
        border-right: 6px solid {COLOR_RED};
    }}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# CABECERA PRINCIPAL (DIAPOSITIVA 1)
# ==============================================================================
st.markdown(f"""
<div class="aura-header-box">
    <div class="aura-tag">AURA FIT · SISTEMA DE RETENCIÓN Y ALERTA TEMPRANA</div>
    <div class="aura-title">Ver a tiempo al socio que <span style="color:{COLOR_RED} !important;">se va</span></div>
    <div class="aura-subtitle">Cada mañana: a quién llamar y qué ofrecer antes del abandono crítico del tercer mes.</div>
</div>
""", unsafe_allow_html=True)

tab_operacion, tab_negocio, tab_agil, tab_modelo = st.tabs([
    "🎯 01. EL PRODUCTO: RANKING DIARIO",
    "💰 02. EL PROBLEMA Y PILOTO 90D",
    "🚀 03. GESTIÓN ÁGIL Y MÉTRICAS DORA",
    "🧠 04. VISIÓN 360° Y MOTOR ML"
])

# ==============================================================================
# PESTAÑA 1: EL PRODUCTO - RANKING DIARIO DE RECEPCIÓN
# ==============================================================================
with tab_operacion:
    with st.expander("🚦 Ver Reglas del Semáforo Operativo (Diapositiva 04 - La Solución)", expanded=False):
        st.markdown(f"""
        <div class="semaforo-row">
            <div class="semaforo-badge" style="background-color:{COLOR_RED}; color:#FFFFFF !important;">● ALTO</div>
            <div class="semaforo-desc">14 días o más sin venir, o sus visitas cayeron 50 % o más</div>
            <div class="semaforo-action" style="color:{COLOR_RED} !important;">LLAMAR HOY</div>
        </div>
        <div class="semaforo-row">
            <div class="semaforo-badge" style="background-color:{COLOR_AMBER}; color:#111111 !important;">● MEDIO</div>
            <div class="semaforo-desc">7 a 13 días sin venir, o sus visitas cayeron 25 % a 49 %</div>
            <div class="semaforo-action" style="color:{TEXT_PRIMARY} !important;">LLAMAR SI HAY CUPO</div>
        </div>
        <div class="semaforo-row">
            <div class="semaforo-badge" style="background-color:{COLOR_GREEN}; color:#FFFFFF !important;">● BAJO</div>
            <div class="semaforo-desc">Viene con normalidad y sin alertas críticas</div>
            <div class="semaforo-action" style="color:{TEXT_SECONDARY} !important;">SIN CONTACTO</div>
        </div>
        """, unsafe_allow_html=True)

    df_view = df_master.copy()
    Columna_Riesgo = "nivel_riesgo_reglas" if "Reglas" in criterio_semaforo else "semaforo_algoritmico"

    if sede_sel != "Todas las Sedes (Red Nacional)":
        df_view = df_view[df_view["sede_frecuente"] == sede_sel]

    if planes_sel:
        df_view = df_view[df_view["plan_actual"].isin(planes_sel)]

    if solo_ventana:
        df_view = df_view[df_view["en_ventana_intervencion"] == True]

    orden_prioridad = {"Alto": 1, "Medio": 2, "Bajo": 3}
    df_view["prioridad_num"] = df_view[Columna_Riesgo].map(orden_prioridad).fillna(3)

    df_accionables = df_view[df_view[Columna_Riesgo].isin(["Alto", "Medio"])].sort_values(
        by=["prioridad_num", "dias_sin_asistencia", "probabilidad_churn"],
        ascending=[True, False, False]
    )

    df_ranking = df_accionables.head(25).copy() if top_25_limit else df_accionables.copy()
    df_ranking["Estado"] = df_ranking["id_socio"].map(st.session_state["estado_contacto"]).fillna("Pendiente")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{len(df_ranking)} <span style="font-size:1.1rem; color:{TEXT_SECONDARY};">/ 25 máx</span></div>
            <div class="kpi-label">Contactos asignados hoy en recepción</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        altos_cnt = (df_ranking[Columna_Riesgo] == "Alto").sum()
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value" style="color:{COLOR_RED} !important;">{altos_cnt}</div>
            <div class="kpi-label">Socios en Riesgo ALTO (Llamar Hoy)</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        rescatados_cnt = (df_ranking["Estado"] == "Rescatado").sum()
        tasa_rescate_actual = (rescatados_cnt / len(df_ranking) * 100) if len(df_ranking) > 0 else 0
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value" style="color:{COLOR_GREEN} !important;">{rescatados_cnt} ({tasa_rescate_actual:.0f}%)</div>
            <div class="kpi-label">Socios rescatados en la jornada</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        cac_protegido = rescatados_cnt * 180000
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">${cac_protegido:,.0f}</div>
            <div class="kpi-label">CAC protegido hoy (COP)</div>
        </div>
        """, unsafe_allow_html=True)

    etiqueta_ventana = "Día 45–70" if solo_ventana else "Todos los días"
    etiqueta_top = "Top 25" if top_25_limit else f"Total ({len(df_ranking)})"
    st.markdown(f"""
    <div class="ranking-banner">
        <div class="ranking-banner-left">
            <span class="red-dot"></span> RANKING DIARIO DE INTERVENCIÓN
        </div>
        <div>
            <span class="pill-dark">{sede_sel}</span>
            <span class="pill-dark">{etiqueta_ventana}</span>
            <span class="pill-red">{etiqueta_top}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if len(df_ranking) == 0:
        st.info("No hay socios en riesgo Alto o Medio con los filtros seleccionados.")
    else:
        df_display = pd.DataFrame({
            "id_socio": df_ranking["id_socio"],
            "Socio": df_ranking["id_socio"].str.replace("SOC-", "#") + " · " + df_ranking["nombre_socio"] + " (" + df_ranking["plan_actual"].str.replace("Aura ", "") + ")",
            "Riesgo": df_ranking[Columna_Riesgo].str.upper(),
            "Score ML (%)": df_ranking["probabilidad_churn"],
            "Días Vinc.": df_ranking["dias_vinculado"],
            "Causa (Regla Activada)": df_ranking["causa_raiz"],
            "Prescripción Sugerida": df_ranking["prescripcion_sugerida"],
            "Estado": df_ranking["Estado"]
        })

        edited_df = st.data_editor(
            df_display.drop(columns=["id_socio"]),
            hide_index=True,
            use_container_width=True,
            height=460,
            column_config={
                "Socio": st.column_config.TextColumn("Socio · Plan", width="medium", disabled=True),
                "Riesgo": st.column_config.TextColumn("Riesgo", width="small", disabled=True),
                "Score ML (%)": st.column_config.ProgressColumn("Score ML", format="%.1f%%", min_value=0, max_value=100),
                "Días Vinc.": st.column_config.NumberColumn("Día Vinc.", format="%d d", width="small", disabled=True),
                "Causa (Regla Activada)": st.column_config.TextColumn("Causa", width="medium", disabled=True),
                "Prescripción Sugerida": st.column_config.TextColumn("Prescripción", width="medium", disabled=True),
                "Estado": st.column_config.SelectboxColumn("Estado de Gestión", options=["Pendiente", "Llamado", "Rescatado", "No aceptó"], required=True, width="small")
            }
        )

        col_btn1, col_btn2, _ = st.columns([1.6, 1.6, 4.8])
        with col_btn1:
            if st.button("💾 Guardar Gestión del Coordinador", type="primary", use_container_width=True):
                for idx, row_val in edited_df.iterrows():
                    id_real = df_display.loc[idx, "id_socio"]
                    st.session_state["estado_contacto"][id_real] = row_val["Estado"]
                df_save = pd.DataFrame(list(st.session_state["estado_contacto"].items()), columns=["id_socio", "estado"])
                df_save.to_parquet(GESTION_PATH, index=False)
                st.toast("✅ Gestión guardada exitosamente.", icon="🔴")
                st.rerun()
        with col_btn2:
            csv_bytes = edited_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Exportar Ranking (CSV)",
                data=csv_bytes,
                file_name=f"ranking_{sede_sel.replace(' ', '_').lower()}.csv",
                mime="text/csv",
                use_container_width=True
            )

    st.markdown("<br>", unsafe_allow_html=True)
    f1, f2, f3 = st.columns(3)
    with f1:
        st.markdown("""<div class="kpi-card"><div class="kpi-value">25</div><div class="kpi-label">contactos al día por coordinador (SUP-04)</div></div>""", unsafe_allow_html=True)
    with f2:
        st.markdown("""<div class="kpi-card"><div class="kpi-value">800</div><div class="kpi-label">contactos diarios posibles en las 32 sedes de la red</div></div>""", unsafe_allow_html=True)
    with f3:
        st.markdown(f"""<div class="kpi-card"><div class="kpi-value">&lt; 3 s</div><div class="kpi-label">de carga del ranking, con 0 % duplicados ({tiempo_carga} s actual)</div></div>""", unsafe_allow_html=True)


# ==============================================================================
# PESTAÑA 2: EL PROBLEMA, TESIS FINANCIERA Y PILOTO 90D
# ==============================================================================
with tab_negocio:
    st.markdown(f"<h3 style='color:{TEXT_PRIMARY}; font-weight:900; margin-bottom:16px;'>03. El Problema: 3 de cada 10 socios se van antes de ser rentables</h3>", unsafe_allow_html=True)

    m0, m3, m5 = st.columns(3)
    with m0:
        st.markdown(f"""<div style="text-align:center; padding:20px; background:{BG_CARD}; border:1px solid {BORDER_COLOR}; border-top:5px solid {TEXT_PRIMARY}; border-radius:6px;"><div style="font-weight:800; color:{TEXT_SECONDARY};">MES 0 · VINCULACIÓN</div><div style="font-size:2.2rem; font-weight:900; color:{TEXT_PRIMARY}; margin:10px 0;">$180.000 COP</div><div style="font-size:0.9rem; color:{TEXT_SECONDARY};">Se invierten en Costo de Adquisición (CAC) para traer al socio</div></div>""", unsafe_allow_html=True)
    with m3:
        st.markdown(f"""<div style="text-align:center; padding:20px; background:{BG_ALERT_M3}; border:1px solid {COLOR_RED}; border-top:5px solid {COLOR_RED}; border-radius:6px;"><div style="font-weight:800; color:{COLOR_RED} !important;">MES 3 · EL ABISMO</div><div style="font-size:2.8rem; font-weight:900; color:{COLOR_RED} !important; margin:6px 0;">30 %</div><div style="font-size:0.9rem; color:{TEXT_PRIMARY}; font-weight:600;">abandona el gimnasio antes de recuperar la inversión</div></div>""", unsafe_allow_html=True)
    with m5:
        st.markdown(f"""<div style="text-align:center; padding:20px; background:{BG_CARD}; border:1px solid {BORDER_COLOR}; border-top:5px solid {COLOR_GREEN}; border-radius:6px;"><div style="font-weight:800; color:{COLOR_GREEN} !important;">MES 5 · BREAKEVEN</div><div style="font-size:2.2rem; font-weight:900; color:{TEXT_PRIMARY}; margin:10px 0;">Rentabilidad</div><div style="font-size:0.9rem; color:{TEXT_SECONDARY};">Recién aquí el socio supera el punto de equilibrio financiero</div></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_izq, col_der = st.columns([1.05, 1.35])

    with col_izq:
        st.markdown(f"""
        <div class="black-callout">
            <div style="color:{COLOR_RED} !important; font-weight:800; letter-spacing:1.5px; font-size:0.85rem;">PUNTO DE EQUILIBRIO DEL PROGRAMA</div>
            <div style="font-size:4.2rem; font-weight:900; color:{COLOR_RED} !important; line-height:1.05; margin:12px 0;">19,4 %</div>
            <div style="font-size:1.15rem; color:#FFFFFF !important; font-weight:600; margin-bottom:18px;">35.000 COP rescatar ÷ 180.000 COP reponer</div>
            <div style="color:#E0E0E0 !important; font-size:0.95rem; line-height:1.45;">
                <b style="color:#FFFFFF !important;">Se paga solo si rescata a 1 de cada 5 contactados.</b><br>
                Con la meta objetivo del 25 % (1 de cada 4), cada peso invertido genera un retorno directo sobre la retención.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_der:
        st.markdown(f"<h4 style='color:{TEXT_PRIMARY}; font-weight:800;'>🎛️ Simulador de Decisión Ejecutiva al Día 90 (Diapositiva 08)</h4>", unsafe_allow_html=True)
        tasa_sim = st.slider("Simular Tasa de Rescate alcanzada en el Piloto (%):", min_value=5.0, max_value=45.0, value=25.0, step=0.5)
        contactos_piloto = st.number_input("Socios contactados en las 6 sedes piloto:", value=400, step=50)

        costo_total = contactos_piloto * 35000
        socios_salvados = int(round(contactos_piloto * (tasa_sim / 100.0)))
        cac_recuperado = socios_salvados * 180000
        beneficio_neto = cac_recuperado - costo_total

        if tasa_sim >= 20.0:
            veredicto = "ESCALAR A LAS 32 SEDES"
            color_ver = COLOR_GREEN
        elif tasa_sim >= 15.0:
            veredicto = "AJUSTAR UMBRALES Y REGLAS"
            color_ver = COLOR_AMBER
        else:
            veredicto = "DETENER PILOTO"
            color_ver = COLOR_RED

        st.markdown(f"""
        <div style="background:{BG_CARD}; padding:18px 22px; border-radius:6px; border:1px solid {BORDER_COLOR}; border-left:6px solid {color_ver}; margin-top:10px;">
            <div style="font-size:0.82rem; font-weight:800; color:{TEXT_SECONDARY};">VEREDICTO AUTOMÁTICO AL DÍA 90:</div>
            <div style="font-size:1.55rem; font-weight:900; color:{color_ver} !important; margin:4px 0 12px 0;">{veredicto} (Tasa: {tasa_sim:.1f} %)</div>
            <div style="display:flex; justify-content:space-between; font-size:0.92rem; border-top:1px solid {BORDER_COLOR}; padding-top:10px; color:{TEXT_PRIMARY};">
                <span><b>Inversión Rescate:</b> ${costo_total:,.0f} COP</span>
                <span><b>CAC Protegido:</b> ${cac_recuperado:,.0f} COP</span>
                <span><b>Balance Neto:</b> <b style="color:{color_ver} !important;">${beneficio_neto:,.0f} COP</b></span>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ==============================================================================
# PESTAÑA 3: GESTIÓN ÁGIL, DORA Y BURNDOWN/BURNUP
# ==============================================================================
with tab_agil:
    st.markdown(f"<h3 style='color:{TEXT_PRIMARY}; font-weight:900;'>08. Indicadores DORA: 3 de 4 indicadores en Nivel de Alto Rendimiento</h3>", unsafe_allow_html=True)
    
    d1, d2, d3, d4 = st.columns(4)
    with d1:
        st.markdown("""<div class="dora-card"><div class="dora-title">FRECUENCIA DE DESPLIEGUE</div><div class="dora-big">1,5</div><div class="dora-unit">por semana</div><div class="dora-sprint"><b>Sprint 1 → 2 → 3</b><br>1,0 → 1,5 → 2,0</div><div class="dora-badge-ok">NIVEL ALTO</div></div>""", unsafe_allow_html=True)
    with d2:
        st.markdown("""<div class="dora-card"><div class="dora-title">TIEMPO DE ENTREGA DE CAMBIOS</div><div class="dora-big">2,0</div><div class="dora-unit">días (mediana)</div><div class="dora-sprint"><b>Sprint 1 → 2 → 3</b><br>3,0 → 2,0 → 1,5</div><div class="dora-badge-ok">NIVEL ALTO</div></div>""", unsafe_allow_html=True)
    with d3:
        st.markdown(f"""<div class="dora-card-alert"><div class="dora-title">TASA DE FALLO EN CAMBIOS</div><div class="dora-big" style="color:{COLOR_RED} !important;">22 %</div><div class="dora-unit">2 de 9 despliegues</div><div class="dora-sprint"><b>Sprint 1 → 2 → 3</b><br>50 % → 33 % → 0 %</div><div class="dora-badge-warn">POR MEJORAR</div></div>""", unsafe_allow_html=True)
    with d4:
        st.markdown("""<div class="dora-card"><div class="dora-title">TIEMPO DE RESTAURACIÓN</div><div class="dora-big">4,5</div><div class="dora-unit">horas (promedio)</div><div class="dora-sprint"><b>Sprint 1 → 2 → 3</b><br>6 h → 3 h → sin incidentes</div><div class="dora-badge-ok">NIVEL ALTO</div></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    g1, g2 = st.columns(2)
    semanas_lbl = ["0. Inicio", "1. Sem 1", "2. Sem 2", "3. Replan", "4. Sem 3", "5. Sem 4", "6. Sem 5", "7. Sem 6"]

    with g1:
        st.markdown(f"<h4 style='color:{TEXT_PRIMARY}; font-weight:800;'>📉 Burndown: Trabajo restante (Puntos de Historia)</h4>", unsafe_allow_html=True)
        df_burndown = pd.DataFrame({
            "Semana": semanas_lbl,
            "Real Restante": [68, 58, 47, 32, 24, 19, 9, 0],
            "Ruta Ideal": [68, 57, 46, 32, 24, 16, 8, 0]
        }).set_index("Semana")
        st.line_chart(df_burndown, color=[COLOR_RED, "#888888"])

    with g2:
        st.markdown(f"<h4 style='color:{TEXT_PRIMARY}; font-weight:800;'>📈 Burnup: Trabajo completado vs. Alcance Total (53/53 SP)</h4>", unsafe_allow_html=True)
        df_burnup = pd.DataFrame({
            "Semana": ["0. Base S0", "1. Inicio S1", "2. Sem 1", "3. Sem 2", "4. Replan", "5. Sem 3", "6. Sem 4", "7. Sem 5", "8. Sem 6"],
            "Completado Acumulado": [0, 0, 10, 21, 21, 29, 34, 44, 53],
            "Alcance Total": [60, 68, 68, 68, 53, 53, 53, 53, 53]
        }).set_index("Semana")
        st.line_chart(df_burnup, color=[COLOR_AMBER, COLOR_RED])


# ==============================================================================
# PESTAÑA 4: VISIÓN 360° Y VALIDACIÓN DEL MODELO ML
# ==============================================================================
with tab_modelo:
    st.markdown(f"<h3 style='color:{TEXT_PRIMARY}; font-weight:900;'>🧠 Visión 360° del Socio y Cobertura Retrospectiva</h3>", unsafe_allow_html=True)

    df_churners = df_master[df_master["target_churn_90d"] == 1]
    alertados_reglas = df_churners["nivel_riesgo_reglas"].isin(["Alto", "Medio"]).mean() * 100

    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
        st.markdown(f"""<div class="kpi-card"><div class="kpi-value" style="color:{COLOR_GREEN} !important;">{alertados_reglas:.1f} %</div><div class="kpi-label">Cobertura de Alertas por Reglas (Meta DoD ≥ 70 %)</div></div>""", unsafe_allow_html=True)
    with m_col2:
        st.markdown("""<div class="kpi-card"><div class="kpi-value">95,8 % / 0,98</div><div class="kpi-label">Recall y ROC-AUC del Clasificador LightGBM</div></div>""", unsafe_allow_html=True)
    with m_col3:
        st.markdown(f"""<div class="kpi-card"><div class="kpi-value">{len(df_master):,}</div><div class="kpi-label">Socios consolidados en df_master_features.parquet</div></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c_dist1, c_dist2 = st.columns(2)

    with c_dist1:
        st.markdown(f"<h4 style='color:{TEXT_PRIMARY}; font-weight:800;'>Distribución por Semáforo de Reglas (Diapositiva 4)</h4>", unsafe_allow_html=True)
        conteo_reglas = df_master["nivel_riesgo_reglas"].value_counts().reindex(["Alto", "Medio", "Bajo"]).fillna(0)
        st.bar_chart(conteo_reglas, color=COLOR_RED)

    with c_dist2:
        st.markdown(f"<h4 style='color:{TEXT_PRIMARY}; font-weight:800;'>Socios en Riesgo Alto por Sede</h4>", unsafe_allow_html=True)
        riesgo_sede = df_master[df_master["nivel_riesgo_reglas"] == "Alto"].groupby("sede_frecuente")["id_socio"].count().sort_values(ascending=False)
        st.bar_chart(riesgo_sede, color=COLOR_AMBER)

    st.markdown(f"<h4 style='color:{TEXT_PRIMARY}; font-weight:800; margin-top:16px;'>🔍 Explorador de la Tabla Maestra (df_master_features.parquet)</h4>", unsafe_allow_html=True)
    st.dataframe(df_master.head(50), use_container_width=True, height=320)