import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
import google.generativeai as genai
from PIL import Image

# ==============================================================================
# 1. CONFIGURACIÓN Y ESTILOS (CSS PARA TRANSFORMAR EL CONTENEDOR NATIVO)
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

        /* --- TRANSFORMAR EL CONTENEDOR NATIVO EN TU "CARD" --- */
        /* Esto hace que st.container(border=True) se vea como tu diseño */
        div[data-testid="stBorderDomWrapper"] {
            background-color: #161b26; /* Fondo de la tarjeta */
            border: 1px solid #2d3748; /* Borde sutil */
            border-radius: 16px; /* Bordes redondeados */
            padding: 20px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
            transition: all 0.3s ease;
        }
        
        /* Efecto Hover en la tarjeta completa */
        div[data-testid="stBorderDomWrapper"]:hover {
            border-color: #3b82f6; /* Brillo azul al pasar el mouse */
            transform: translateY(-2px);
        }

        /* --- HEADER DE SECCIÓN --- */
        .custom-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            border-bottom: 2px solid #1f2937; /* Línea separadora gruesa */
            padding-bottom: 15px;
        }
        
        .header-title {
            font-size: 1.3rem;
            font-weight: 900;
            color: #e2e8f0;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .header-score {
            font-size: 1.4rem;
            font-weight: 800;
            color: #10b981; /* Verde brillante */
        }

        /* --- ESTILO DE LOS TEXTOS DE LOS TOGGLES --- */
        .toggle-text-active {
            color: #e2e8f0; font-weight: 500; font-size: 1rem;
        }
        .toggle-text-inactive {
            color: #64748b; font-weight: 400; font-size: 1rem;
        }
        .points-badge {
            color: #10b981; font-weight: 700; font-size: 0.9rem; margin-right: 10px;
        }
        .points-badge-disabled {
            color: #475569; font-weight: 700; font-size: 0.9rem; margin-right: 10px;
        }

        /* --- DASHBOARD SCORE (Gigante) --- */
        .total-score-box {
            background: linear-gradient(180deg, #115e59 0%, #042f2e 100%);
            border: 2px solid #14b8a6;
            border-radius: 20px;
            padding: 40px;
            text-align: center;
            margin-bottom: 40px;
            box-shadow: 0 0 20px rgba(20, 184, 166, 0.2);
        }
        .score-val-big {
            font-size: 5rem;
            font-weight: 900;
            color: #ccfbf1;
            line-height: 1;
            text-shadow: 0 0 10px rgba(20, 184, 166, 0.5);
        }
        
        /* --- BOTONES --- */
        .stButton button {
            background-color: #10b981 !important;
            color: #064e3b !important;
            border: none;
            font-weight: 800;
            font-size: 1rem;
            padding: 0.6rem 1.5rem;
            border-radius: 8px;
        }
        </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# ==============================================================================
# 2. LÓGICA Y DATOS
# ==============================================================================

if 'page' not in st.session_state: st.session_state.page = 'checklist'
if 'checklist' not in st.session_state: st.session_state.checklist = {}
# Control exclusivo para el Nivel Psicológico
if 'psych_selected_in' not in st.session_state: st.session_state.psych_selected_in = None 

# ESTRATEGIA (Configuración)
STRATEGY = {
    "WEEKLY": [
        ("Trend", 10), ("At AOI / Rejected", 10), ("Touching EMA", 5), 
        ("Round Psych Level", 5), ("Rejection Structure", 10), 
        ("Candlestick Rejection", 10), ("Break & Retest", 10)
    ],
    "DAILY": [
        ("Trend", 10), ("At AOI / Rejected", 10), ("Touching EMA", 5), 
        ("Round Psych Level", 5), ("Rejection Structure", 10),
        ("Candlestick Rejection", 10), ("Break & Retest", 10)
    ],
    "4H": [
        ("Trend", 5), ("At AOI / Rejected", 5), ("Touching EMA", 5), 
        ("Round Psych Level", 5), ("Rejection Structure", 10),
        ("Candlestick Rejection", 5), ("Break & Retest", 10)
    ],
    "2H, 1H, 30m": [
        ("Trend", 5), ("Touching EMA", 5), ("Break & Retest", 5)
    ],
    "ENTRY SIGNAL": [
        ("SOS (Shift of Structure)", 10), ("Engulfing candlestick", 10)
    ]
}

# --- CÁLCULO DE PUNTOS ---
def calculate_totals():
    total_score = 0
    section_scores = {}
    
    for section, items in STRATEGY.items():
        sec_score = 0
        for label, pts in items:
            key = f"{section}_{label}"
            if st.session_state.checklist.get(key, False):
                sec_score += pts
        section_scores[section] = sec_score
        total_score += sec_score
        
    return total_score, section_scores

# --- CALLBACK (LÓGICA DE BLOQUEO) ---
def handle_psych_logic(section_changed):
    key_changed = f"{section_changed}_Round Psych Level"
    is_active = st.session_state.checklist.get(key_changed, False)
    
    if is_active:
        # Se activó: lo asignamos a esta sección y apagamos los demás
        st.session_state.psych_selected_in = section_changed
        for sec in ["WEEKLY", "DAILY", "4H"]:
            if sec != section_changed:
                other_key = f"{sec}_Round Psych Level"
                if other_key in st.session_state.checklist:
                    st.session_state.checklist[other_key] = False
    else:
        # Se desactivó: liberamos el bloqueo si era el dueño
        if st.session_state.psych_selected_in == section_changed:
            st.session_state.psych_selected_in = None

# ==============================================================================
# 3. INTERFAZ: NAVBAR
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
# PÁGINA 1: CHECKLIST (DISEÑO CAJA ÚNICA)
# ==============================================================================
if st.session_state.page == 'checklist':
    
    total, sec_scores = calculate_totals()
    
    # Textos Dinámicos
    status_txt = "WEAK SETUP"
    score_color = "#ef4444"
    if total >= 60: score_color = "#facc15"; status_txt = "MODERATE"
    if total >= 90: score_color = "#10b981"; status_txt = "🔥 SNIPER ENTRY"

    # --- DASHBOARD SCORE ---
    st.markdown(f"""
    <div class="total-score-box" style="border-color: {score_color};">
        <div style="color:#ccfbf1; letter-spacing:2px; font-weight:600; margin-bottom:10px;">TOTAL OVERALL SCORE</div>
        <div class="score-val-big" style="color:{score_color};">{total}%</div>
        <div style="font-size:1.5rem; font-weight:800; color:{score_color}; margin-top:10px;">{status_txt}</div>
    </div>
    """, unsafe_allow_html=True)

    if total > 0:
        if st.button("💾 GUARDAR TRADE", use_container_width=True):
            st.toast("Abriendo modal...", icon="✅")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- GRID DE SECCIONES ---
    col_izq, col_der = st.columns(2, gap="large")
    
    for i, (sec_name, items) in enumerate(STRATEGY.items()):
        # Alternar columnas
        target_col = col_izq if i % 2 == 0 else col_der
        
        with target_col:
            # PUNTUACIÓN DE LA SECCIÓN ACTUAL
            current_sec_score = sec_scores.get(sec_name, 0)
            
            # --- AQUÍ ESTÁ EL SECRETO: USAMOS st.container(border=True) ---
            # Esto crea la CAJA FÍSICA que rodea todo
            with st.container(border=True):
                
                # 1. HEADER (Dentro de la caja)
                st.markdown(f"""
                <div class="custom-header">
                    <span class="header-title">{sec_name}</span>
                    <span class="header-score">{current_sec_score}%</span>
                </div>
                """, unsafe_allow_html=True)
                
                # 2. LOS TOGGLES (Dentro de la misma caja)
                for label, pts in items:
                    key = f"{sec_name}_{label}"
                    
                    # Logica de bloqueo Psych
                    disabled = False
                    help_txt = None
                    if label == "Round Psych Level":
                        if st.session_state.psych_selected_in and st.session_state.psych_selected_in != sec_name:
                            disabled = True
                            help_txt = "⛔ Usado en otra TF"

                    # Layout de fila
                    c1, c2, c3 = st.columns([5, 2, 1])
                    
                    with c1:
                        # Estilo del texto (si está activo brilla más)
                        is_active = st.session_state.checklist.get(key, False)
                        txt_cls = "toggle-text-active" if is_active and not disabled else "toggle-text-inactive"
                        if disabled: txt_cls = "points-badge-disabled" # Gris si deshabilitado
                        
                        st.markdown(f"""<div style="padding-top:10px;" class="{txt_cls}">{label}</div>""", unsafe_allow_html=True)
                        if help_txt: st.caption(help_txt)
                    
                    with c2:
                        # Puntos (+10%)
                        pt_cls = "points-badge" if not disabled else "points-badge-disabled"
                        st.markdown(f"""<div style="padding-top:10px; text-align:right;" class="{pt_cls}">+{pts}%</div>""", unsafe_allow_html=True)
                    
                    with c3:
                        # El Toggle real
                        val = st.toggle(
                            "x", key=key, 
                            value=st.session_state.checklist.get(key, False),
                            label_visibility="collapsed",
                            disabled=disabled,
                            on_change=handle_psych_logic if label == "Round Psych Level" else None,
                            args=(sec_name,) if label == "Round Psych Level" else None
                        )
                        st.session_state.checklist[key] = val
                    
                    # Separador visual entre items
                    st.markdown("<div style='border-bottom:1px solid #1f2937; margin-bottom:5px;'></div>", unsafe_allow_html=True)

# ==============================================================================
# PÁGINAS RESTANTES (PLACEHOLDERS)
# ==============================================================================
elif st.session_state.page == 'history':
    st.title("📖 Trading History")
    st.info("Lista de trades guardados.")

elif st.session_state.page == 'dashboard':
    st.title("📊 Performance Dashboard")
    st.info("Métricas y Calendario.")

elif st.session_state.page == 'ai_mentor':
    st.title("🤖 AI Mentor")
    st.info("Chat con Gemini Vision.")
