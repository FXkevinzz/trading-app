import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
import google.generativeai as genai
from PIL import Image

# ==============================================================================
# 1. CONFIGURACIÓN Y ESTILOS (DISEÑO EXACTO DARK NAVY)
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

        /* --- CONTENEDOR DE SECCIÓN (CAJA ÚNICA) --- */
        div[data-testid="stBorderDomWrapper"] {
            background-color: #111827; /* Color de fondo de la tarjeta (Gris muy oscuro/Azul) */
            border: 1px solid #1f2937; /* Borde sutil */
            border-radius: 12px; /* Bordes redondeados */
            padding: 0; /* Sin padding global para controlar header/body */
            overflow: hidden; /* Para que el header no se salga */
            margin-bottom: 20px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }

        /* --- HEADER DE SECCIÓN (Dentro del contenedor) --- */
        .section-header-internal {
            background-color: #111827; /* Mismo fondo */
            padding: 15px 20px;
            border-bottom: 1px solid #1f2937;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .section-title-internal {
            font-size: 1rem;
            font-weight: 800;
            color: #e2e8f0;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .section-score-internal {
            font-size: 1.1rem;
            font-weight: 800;
            color: #10b981; /* Verde */
        }

        /* --- CUERPO DE LA SECCIÓN (Toggles) --- */
        .section-body-internal {
            padding: 10px 20px 20px 20px;
        }

        /* --- TOGGLES --- */
        .toggle-row-internal {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid #1f2937;
        }
        .toggle-row-internal:last-child {
            border-bottom: none;
        }

        .toggle-label-text {
            font-size: 0.9rem;
            font-weight: 500;
            color: #cbd5e1;
        }

        .points-badge {
            font-size: 0.8rem;
            font-weight: 700;
            color: #10b981;
            margin-right: 15px;
        }
        .points-badge-disabled {
            color: #4b5563;
            margin-right: 15px;
        }

        /* --- DASHBOARD SCORE (Gigante) --- */
        .total-score-box {
            background: #1f2937; /* Fondo gris oscuro para el dashboard */
            border: 1px solid #374151;
            border-radius: 12px;
            padding: 30px;
            text-align: center;
            margin-bottom: 30px;
        }
        .score-val-big {
            font-size: 4rem;
            font-weight: 900;
            color: #ef4444; /* Rojo por defecto */
            line-height: 1;
        }
        .score-status {
            font-size: 1.2rem;
            font-weight: 700;
            color: #ef4444;
            margin-top: 10px;
        }
        
        /* --- BOTONES --- */
        .stButton button {
            background-color: #10b981 !important; /* Verde */
            color: #ffffff !important;
            border: none;
            font-weight: 600;
            font-size: 0.9rem;
            padding: 0.5rem 1.5rem;
            border-radius: 6px;
        }
        </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# ==============================================================================
# 2. LÓGICA Y DATOS
# ==============================================================================

if 'page' not in st.session_state: st.session_state.page = 'checklist'
if 'checklist' not in st.session_state: st.session_state.checklist = {}
if 'psych_selected_in' not in st.session_state: st.session_state.psych_selected_in = None 

# Definición de la Estrategia (Orden Exacto)
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
    "2H, 1H, 30M": [ # Nombre ajustado a mayúsculas como en imagen
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

# --- CALLBACK PARA PSYCH LEVEL ---
def handle_psych_logic(section_changed):
    key_changed = f"{section_changed}_Round Psych Level"
    is_active = st.session_state.checklist.get(key_changed, False)
    
    if is_active:
        st.session_state.psych_selected_in = section_changed
        for sec in ["WEEKLY", "DAILY", "4H"]:
            if sec != section_changed:
                other_key = f"{sec}_Round Psych Level"
                if other_key in st.session_state.checklist:
                    st.session_state.checklist[other_key] = False
    else:
        if st.session_state.psych_selected_in == section_changed:
            st.session_state.psych_selected_in = None

# ==============================================================================
# 3. INTERFAZ: NAVBAR
# ==============================================================================
c_nav1, c_nav2 = st.columns([1, 4])
with c_nav1:
    st.markdown('<div style="font-size:1.2rem; font-weight:800; color:#fff; display:flex; align-items:center;">🦁 THE PERFECT TRADE</div>', unsafe_allow_html=True)
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
# PÁGINA 1: CHECKLIST (DISEÑO EXACTO)
# ==============================================================================
if st.session_state.page == 'checklist':
    
    total, sec_scores = calculate_totals()
    
    status_txt = "Weak Setup"
    score_color = "#ef4444"
    if total >= 60: score_color = "#facc15"; status_txt = "Moderate Setup"
    if total >= 90: score_color = "#10b981"; status_txt = "🔥 Sniper Entry"

    # --- DASHBOARD SCORE (Gigante) ---
    st.markdown(f"""
    <div class="total-score-box" style="border-top: 4px solid {score_color};">
        <div style="color:#9ca3af; letter-spacing:1px; font-weight:600; font-size:0.9rem; text-transform:uppercase;">TOTAL OVERALL SCORE</div>
        <div class="score-val-big" style="color:{score_color};">{total}%</div>
        <div class="score-status" style="color:{score_color};">{status_txt}</div>
    </div>
    """, unsafe_allow_html=True)

    if total > 0:
        if st.button("💾 SAVE TRADE", use_container_width=True):
            st.toast("Abriendo modal...", icon="✅")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- SECCIONES EN GRID (2 Columnas) ---
    col_izq, col_der = st.columns(2, gap="large")
    
    for i, (sec_name, items) in enumerate(STRATEGY.items()):
        target_col = col_izq if i % 2 == 0 else col_der
        
        with target_col:
            # Puntuación actual
            current_sec_score = sec_scores.get(sec_name, 0)
            
            # --- CAJA CONTENEDORA (st.container con border=True) ---
            # El CSS arriba lo transforma en tu tarjeta Dark Navy
            with st.container(border=True):
                
                # 1. HEADER INTERNO
                st.markdown(f"""
                <div class="section-header-internal">
                    <span class="section-title-internal">{sec_name}</span>
                    <span class="section-score-internal">{current_sec_score}%</span>
                </div>
                """, unsafe_allow_html=True)
                
                # 2. CUERPO (TOGGLES)
                st.markdown('<div class="section-body-internal">', unsafe_allow_html=True)
                
                for label, pts in items:
                    key = f"{sec_name}_{label}"
                    
                    disabled = False
                    if label == "Round Psych Level":
                        if st.session_state.psych_selected_in and st.session_state.psych_selected_in != sec_name:
                            disabled = True

                    # Fila Flex: Label a la izquierda | (+10% Switch) a la derecha
                    c1, c2 = st.columns([3, 1])
                    
                    with c1:
                        col_lbl = "#4b5563" if disabled else "#cbd5e1"
                        st.markdown(f"""<div style="padding-top:10px; color:{col_lbl}; font-weight:500; font-size:0.9rem;">{label}</div>""", unsafe_allow_html=True)
                    
                    with c2:
                        # Usamos columnas anidadas para pegar el texto al switch
                        sub_c1, sub_c2 = st.columns([1, 1])
                        with sub_c1:
                            pts_cls = "points-badge" if not disabled else "points-badge-disabled"
                            st.markdown(f"""<div style="padding-top:10px; text-align:right;" class="{pts_cls}">+{pts}%</div>""", unsafe_allow_html=True)
                        with sub_c2:
                            val = st.toggle(
                                "x", key=key, 
                                value=st.session_state.checklist.get(key, False),
                                label_visibility="collapsed",
                                disabled=disabled,
                                on_change=handle_psych_logic if label == "Round Psych Level" else None,
                                args=(sec_name,) if label == "Round Psych Level" else None
                            )
                            st.session_state.checklist[key] = val
                    
                    # Separador
                    if label != items[-1][0]:
                        st.markdown("<div style='border-bottom:1px solid #1f2937; margin: 5px 0;'></div>", unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True) # Cierre body

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
