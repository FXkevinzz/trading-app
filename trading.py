import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
import google.generativeai as genai
from PIL import Image

# ==============================================================================
# 1. CONFIGURACIÓN E INYECCIÓN DE CSS (ESTILO PREMIUM)
# ==============================================================================
st.set_page_config(page_title="The Perfect Trade AI", layout="wide", page_icon="🦁")

def inject_custom_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;800&display=swap');

        /* --- TEMA GLOBAL --- */
        .stApp {
            background-color: #0b0f19; /* Fondo Ultra Dark */
            font-family: 'Inter', sans-serif;
            color: #f1f5f9;
        }
        
        #MainMenu, footer, header {visibility: hidden;}
        .stDeployButton {display:none;}

        /* --- ANIMACIONES Y TARJETAS INTERACTIVAS --- */
        .section-card {
            background-color: #161b26;
            border: 1px solid #2d3748;
            border-radius: 16px;
            padding: 30px; /* Más espacio interno */
            margin-bottom: 30px; /* Separación entre secciones */
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }
        
        /* Efecto HOVER: Se eleva y brilla el borde */
        .section-card:hover {
            transform: translateY(-5px) scale(1.01);
            border-color: #10b981;
            box-shadow: 0 20px 25px -5px rgba(16, 185, 129, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        }

        .section-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 25px;
            border-bottom: 2px solid #2d3748;
            padding-bottom: 15px;
        }
        
        .section-title {
            font-size: 1.5rem; /* Letra más grande */
            font-weight: 800;
            color: #e2e8f0;
            letter-spacing: 1px;
            text-transform: uppercase;
        }

        .section-score {
            font-size: 1.5rem;
            font-weight: 800;
            color: #10b981;
            background: rgba(16, 185, 129, 0.1);
            padding: 5px 15px;
            border-radius: 8px;
        }

        /* --- TOGGLES MÁS GRANDES Y ESTILIZADOS --- */
        .toggle-container {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px 10px;
            border-bottom: 1px solid #2d3748;
            transition: background 0.2s;
        }
        .toggle-container:hover {
            background-color: #1f2937;
            border-radius: 8px;
        }
        .toggle-label {
            font-size: 1.1rem; /* Texto de opciones más grande */
            font-weight: 500;
            color: #cbd5e1;
        }
        .toggle-points {
            font-size: 0.9rem;
            color: #10b981;
            font-weight: 700;
            background: rgba(16, 185, 129, 0.1);
            padding: 2px 8px;
            border-radius: 4px;
            margin-left: 10px;
        }

        /* --- DASHBOARD SCORE --- */
        .total-score-container {
            background: linear-gradient(145deg, #111827, #0f172a);
            border: 2px solid #374151;
            border-radius: 20px;
            padding: 40px;
            text-align: center;
            margin-bottom: 40px;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
        }
        .score-big-number {
            font-size: 5rem; /* Gigante */
            font-weight: 900;
            line-height: 1;
            background: -webkit-linear-gradient(#10b981, #34d399);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        /* --- ESTILOS GENERALES DE INPUTS --- */
        .stButton button {
            background-color: #10b981 !important;
            color: #064e3b !important;
            border: none;
            font-weight: 800;
            font-size: 1.1rem;
            padding: 0.8rem 2rem;
            border-radius: 10px;
            transition: all 0.3s;
        }
        .stButton button:hover {
            background-color: #34d399 !important;
            box-shadow: 0 0 15px rgba(16, 185, 129, 0.5);
        }
        
        /* Ocultar etiquetas de los toggles nativos para usar los custom */
        div[data-testid="stMarkdownContainer"] p {
            font-size: 1.1rem;
        }
        </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# ==============================================================================
# 2. LÓGICA Y DATOS
# ==============================================================================

# Inicialización de Estado
if 'page' not in st.session_state: st.session_state.page = 'checklist'
if 'checklist' not in st.session_state: st.session_state.checklist = {}
# Estado especial para controlar el bloqueo de Niveles Psicológicos
if 'psych_selected_in' not in st.session_state: st.session_state.psych_selected_in = None 

# Definición de la Estrategia
STRATEGY = {
    "WEEKLY": [("Trend", 10), ("At AOI / Rejected", 10), ("Touching EMA", 5), ("Round Psych Level", 5), ("Rejection Structure", 10)],
    "DAILY": [("Trend", 10), ("At AOI / Rejected", 10), ("Touching EMA", 5), ("Round Psych Level", 5), ("Rejection Structure", 10)],
    "4H": [("Trend", 5), ("At AOI / Rejected", 5), ("Touching EMA", 5), ("Round Psych Level", 5), ("Rejection Structure", 10)],
    "2H, 1H, 30m": [("Trend", 5), ("Touching EMA", 5), ("Break & Retest", 5)],
    "ENTRY SIGNAL": [("SOS (Shift of Structure)", 10), ("Engulfing candlestick", 10)]
}

# --- LÓGICA DE CÁLCULO ---
def calculate_totals():
    total_score = 0
    section_scores = {}
    
    for section, items in STRATEGY.items():
        sec_score = 0
        for label, pts in items:
            key = f"{section}_{label}"
            # Verificamos si está marcado en el estado
            if st.session_state.checklist.get(key, False):
                sec_score += pts
        
        section_scores[section] = sec_score
        total_score += sec_score
        
    return total_score, section_scores

# --- CALLBACK PARA NIVEL PSICOLÓGICO ---
def handle_psych_logic(section_changed):
    """
    Esta función asegura que el Nivel Psicológico solo cuente una vez.
    Si se activa en SEMANAL, se desactiva visualmente en DIARIO y 4H, etc.
    """
    key_changed = f"{section_changed}_Round Psych Level"
    is_active = st.session_state.checklist.get(key_changed, False)
    
    if is_active:
        # Si se activó, registramos quién lo tiene y apagamos los otros
        st.session_state.psych_selected_in = section_changed
        # Desactivar en otros timeframes
        for sec in ["WEEKLY", "DAILY", "4H"]:
            if sec != section_changed:
                other_key = f"{sec}_Round Psych Level"
                if other_key in st.session_state.checklist:
                    st.session_state.checklist[other_key] = False
    else:
        # Si se desactivó el actual dueño, liberamos el bloqueo
        if st.session_state.psych_selected_in == section_changed:
            st.session_state.psych_selected_in = None

# ==============================================================================
# 3. INTERFAZ: NAVBAR SUPERIOR
# ==============================================================================
c_nav1, c_nav2 = st.columns([1, 4])
with c_nav1:
    st.markdown('<div style="font-size:1.5rem; font-weight:900; color:#10b981;">🦁 PERFECT TRADE</div>', unsafe_allow_html=True)
with c_nav2:
    b1, b2, b3, b4 = st.columns(4)
    with b1: 
        if st.button("📈 CHECKLIST", use_container_width=True): st.session_state.page = 'checklist'; st.rerun()
    with b2: 
        if st.button("📖 HISTORY", use_container_width=True): st.session_state.page = 'history'; st.rerun()
    with b3: 
        if st.button("📊 DASHBOARD", use_container_width=True): st.session_state.page = 'dashboard'; st.rerun()
    with b4: 
        if st.button("🤖 AI MENTOR", use_container_width=True): st.session_state.page = 'ai_mentor'; st.rerun()

st.markdown("---")

# ==============================================================================
# PÁGINA 1: CHECKLIST INTERACTIVO (MEJORADO)
# ==============================================================================
if st.session_state.page == 'checklist':
    
    # 1. Calcular puntuación ANTES de renderizar para que esté actualizada
    total, sec_scores = calculate_totals()
    
    # Colores dinámicos según puntuación
    score_color = "#ef4444" # Rojo
    status_txt = "WEAK SETUP"
    if total >= 60: score_color = "#facc15"; status_txt = "MODERATE" # Amarillo
    if total >= 90: score_color = "#10b981"; status_txt = "🔥 SNIPER ENTRY" # Verde

    # 2. Dashboard de Puntuación (Gigante y Centrado)
    st.markdown(f"""
    <div class="total-score-container" style="border-color: {score_color};">
        <div style="color:#94a3b8; font-weight:600; letter-spacing:2px; margin-bottom:10px;">TOTAL CONFLUENCE SCORE</div>
        <div class="score-big-number" style="color:{score_color}; -webkit-text-fill-color:{score_color};">{total}%</div>
        <div style="font-size:1.5rem; font-weight:800; color:{score_color}; margin-top:10px;">{status_txt}</div>
    </div>
    """, unsafe_allow_html=True)

    # Botón Guardar (Solo aparece si hay datos)
    if total > 0:
        if st.button("💾 GUARDAR OPERACIÓN EN BITÁCORA", use_container_width=True):
            # Aquí iría la llamada al modal de guardado
            st.toast("Abriendo formulario de guardado...", icon="✅")

    st.markdown("<br>", unsafe_allow_html=True)

    # 3. Renderizado de Secciones (Cards Grandes)
    # Dividimos en 2 columnas grandes para que se vea masivo
    left_col, right_col = st.columns(2, gap="large")
    
    sections = list(STRATEGY.items())
    
    for i, (sec_name, items) in enumerate(sections):
        # Alternar columnas (Zig-Zag)
        target_col = left_col if i % 2 == 0 else right_col
        
        with target_col:
            # HTML Header de la Tarjeta
            current_sec_score = sec_scores.get(sec_name, 0)
            st.markdown(f"""
            <div class="section-card">
                <div class="section-header">
                    <span class="section-title">{sec_name}</span>
                    <span class="section-score">{current_sec_score}%</span>
                </div>
            """, unsafe_allow_html=True)
            
            # Renderizar los Toggles dentro de la tarjeta
            for label, pts in items:
                key = f"{sec_name}_{label}"
                
                # Lógica de Bloqueo de Psych Level
                disabled = False
                help_txt = None
                if label == "Round Psych Level":
                    # Si ya hay un nivel psicológico seleccionado en OTRA sección, deshabilitamos este
                    if st.session_state.psych_selected_in and st.session_state.psych_selected_in != sec_name:
                        disabled = True
                        help_txt = "⛔ Ya seleccionaste Nivel Psicológico en otra temporalidad. Solo cuenta una vez."

                # Usamos columnas nativas de Streamlit para alinear Toggle y Texto
                c_txt, c_tog = st.columns([4, 1])
                
                with c_txt:
                    color_pts = "#10b981" if not disabled else "#475569"
                    st.markdown(f"""
                    <div style="display:flex; align-items:center; height:100%; padding-top:10px;">
                        <span class="toggle-label" style="color:{'#64748b' if disabled else '#e2e8f0'}">{label}</span>
                        <span class="toggle-points" style="background:{'rgba(71,85,105,0.2)' if disabled else 'rgba(16,185,129,0.1)'}; color:{color_pts}">+{pts}%</span>
                    </div>
                    """, unsafe_allow_html=True)
                
                with c_tog:
                    # El Toggle real
                    val = st.toggle(
                        label="x", # Label oculto visualmente
                        key=key,
                        value=st.session_state.checklist.get(key, False),
                        label_visibility="collapsed",
                        disabled=disabled,
                        # Si es Psych Level, activamos el callback
                        on_change=handle_psych_logic if label == "Round Psych Level" else None,
                        args=(sec_name,) if label == "Round Psych Level" else None
                    )
                    # Actualizar estado manualmente si no es Psych (para el cálculo inmediato)
                    st.session_state.checklist[key] = val

                if help_txt:
                    st.caption(help_txt)
                
                st.markdown("<div style='margin-bottom:15px;'></div>", unsafe_allow_html=True) # Espaciador

            st.markdown("</div>", unsafe_allow_html=True) # Cierre del div section-card

# ==============================================================================
# PÁGINA 2: HISTORY (PLACEHOLDER)
# ==============================================================================
elif st.session_state.page == 'history':
    st.title("📖 Trading History")
    st.info("Aquí aparecerán tus trades guardados.")

# ==============================================================================
# PÁGINA 3: DASHBOARD (PLACEHOLDER)
# ==============================================================================
elif st.session_state.page == 'dashboard':
    st.title("📊 Performance Dashboard")
    st.info("Tus métricas y calendario aparecerán aquí.")

# ==============================================================================
# PÁGINA 4: AI MENTOR (PLACEHOLDER)
# ==============================================================================
elif st.session_state.page == 'ai_mentor':
    st.title("🤖 AI Mentor")
    st.info("Sube tus gráficos para análisis.")
