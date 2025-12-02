import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
import google.generativeai as genai
from PIL import Image

# ==============================================================================
# 1. CONFIGURACIÓN VISUAL (REPLICA EXACTA)
# ==============================================================================
st.set_page_config(page_title="The Perfect Trade AI", layout="wide", page_icon="🦁")

def inject_custom_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        /* --- FONDO GENERAL --- */
        .stApp {
            background-color: #0f172a; /* Slate 900 */
            font-family: 'Inter', sans-serif;
            color: #f8fafc;
        }
        
        #MainMenu, footer, header {visibility: hidden;}
        .stDeployButton {display:none;}

        /* --- CONTENEDOR DE LA TARJETA (WEEKLY, DAILY...) --- */
        /* Afecta a st.container(border=True) */
        div[data-testid="stBorderDomWrapper"] {
            background-color: #1e293b; /* Slate 800 */
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
        }

        /* --- HEADER DE SECCIÓN (TÍTULO Y PORCENTAJE) --- */
        .section-header-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 25px; /* Espacio antes de los toggles */
        }
        
        .section-title {
            font-size: 0.9rem;
            font-weight: 800;
            color: #ffffff;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .section-score {
            font-size: 1.5rem;
            font-weight: 800;
            color: #34d399; /* Verde esmeralda brillante */
        }

        /* --- FILAS DE TOGGLES --- */
        /* Alineación perfecta: Label a la izq, Puntos y Switch a la der */
        .toggle-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px; /* Espaciado entre filas */
        }

        .toggle-label {
            font-size: 0.95rem;
            font-weight: 600;
            color: #e2e8f0; /* Blanco suave */
        }

        .toggle-right-group {
            display: flex;
            align-items: center;
            gap: 12px; /* Espacio entre +10% y el Switch */
        }

        .points-text {
            color: #34d399; /* Verde neón para el texto */
            font-weight: 700;
            font-size: 0.85rem;
        }
        
        .points-text-disabled {
            color: #64748b; /* Gris para deshabilitado */
            font-weight: 600;
            font-size: 0.85rem;
        }

        /* --- DASHBOARD SUMMARY (CAJA GIGANTE) --- */
        .summary-box {
            background-color: #164e63; /* Cyan oscuro de fondo base */
            background: linear-gradient(180deg, #115e59 0%, #0f172a 100%);
            border: 1px solid #14b8a6;
            border-radius: 16px;
            padding: 40px;
            text-align: center;
            margin-bottom: 40px;
        }
        
        .summary-title {
            color: #ccfbf1;
            font-size: 0.9rem;
            font-weight: 700;
            letter-spacing: 1px;
            text-transform: uppercase;
            margin-bottom: 10px;
        }
        
        .summary-score-big {
            font-size: 5rem;
            font-weight: 900;
            color: #ef4444; /* Rojo por defecto */
            line-height: 1;
        }
        
        .summary-status {
            font-size: 1.2rem;
            font-weight: 700;
            color: #ef4444;
            margin-top: 10px;
        }

        /* --- BOTONES --- */
        .stButton button {
            background-color: #10b981 !important;
            color: #ffffff !important;
            border: none;
            border-radius: 6px;
            font-weight: 600;
            padding: 0.6rem 1.2rem;
        }
        </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# ==============================================================================
# 2. LÓGICA
# ==============================================================================

if 'page' not in st.session_state: st.session_state.page = 'checklist'
if 'checklist' not in st.session_state: st.session_state.checklist = {}
if 'psych_selected_in' not in st.session_state: st.session_state.psych_selected_in = None 

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
    "2H, 1H, 30M": [
        ("Trend", 5), ("Touching EMA", 5), ("Break & Retest", 5)
    ],
    "ENTRY SIGNAL": [
        ("SOS (Shift of Structure)", 10), ("Engulfing candlestick", 10)
    ]
}

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

def handle_psych_logic(section_changed):
    key_changed = f"{section_changed}_Round Psych Level"
    is_active = st.session_state.checklist.get(key_changed, False)
    if is_active:
        st.session_state.psych_selected_in = section_changed
        for sec in ["WEEKLY", "DAILY", "4H"]:
            if sec != section_changed:
                other_key = f"{sec}_Round Psych Level"
                if other_key in st.session_state.checklist: st.session_state.checklist[other_key] = False
    else:
        if st.session_state.psych_selected_in == section_changed: st.session_state.psych_selected_in = None

# ==============================================================================
# 3. INTERFAZ
# ==============================================================================
c_nav1, c_nav2 = st.columns([1, 4])
with c_nav1:
    st.markdown('<div style="font-size:1.2rem; font-weight:800; color:#fff;">🦁 PERFECT TRADE</div>', unsafe_allow_html=True)
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

if st.session_state.page == 'checklist':
    
    total, sec_scores = calculate_totals()
    
    status_txt = "Weak Setup"
    score_color = "#ef4444"
    if total >= 60: score_color = "#facc15"; status_txt = "Moderate Setup"
    if total >= 90: score_color = "#10b981"; status_txt = "🔥 Sniper Entry"

    # --- DASHBOARD SUMMARY ---
    st.markdown(f"""
    <div class="summary-box" style="border-color:{score_color};">
        <div class="summary-title">TOTAL OVERALL SCORE</div>
        <div class="summary-score-big" style="color:{score_color};">{total}%</div>
        <div class="summary-status" style="color:{score_color};">{status_txt}</div>
    </div>
    """, unsafe_allow_html=True)

    if total > 0:
        if st.button("💾 SAVE TRADE", use_container_width=True):
            st.toast("Abriendo modal...", icon="✅")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- GRID DE SECCIONES (2 Columnas) ---
    col_izq, col_der = st.columns(2, gap="large")
    
    for i, (sec_name, items) in enumerate(STRATEGY.items()):
        target_col = col_izq if i % 2 == 0 else col_der
        
        with target_col:
            # Puntuación actual
            current_sec_score = sec_scores.get(sec_name, 0)
            
            # --- CAJA "THE PERFECT TRADE" ---
            with st.container(border=True):
                
                # Header Interno: Título a la Izq, Score Verde a la Der
                st.markdown(f"""
                <div class="section-header-row">
                    <div class="section-title">{sec_name}</div>
                    <div class="section-score">{current_sec_score}%</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("<div style='font-size:0.8rem; color:#64748b; margin-top:-15px; margin-bottom:20px;'>0% confluence</div>", unsafe_allow_html=True)

                # Filas de Toggles
                for label, pts in items:
                    key = f"{sec_name}_{label}"
                    
                    disabled = False
                    if label == "Round Psych Level":
                        if st.session_state.psych_selected_in and st.session_state.psych_selected_in != sec_name:
                            disabled = True

                    # ESTRUCTURA DE FILA: Texto ................ +10% Switch
                    c1, c2 = st.columns([4, 1])
                    
                    with c1:
                        # Label a la izquierda
                        col_lbl = "#4b5563" if disabled else "#e2e8f0"
                        st.markdown(f"""<div style="padding-top:8px; font-weight:600; font-size:0.95rem; color:{col_lbl};">{label}</div>""", unsafe_allow_html=True)
                    
                    with c2:
                        # Grupo Derecha: Texto Verde + Switch
                        # Usamos HTML para el texto verde y st.toggle para el switch
                        # pero necesitamos que estén en la misma línea visual.
                        # Truco: Columnas anidadas muy pegadas.
                        sc1, sc2 = st.columns([1, 1])
                        with sc1:
                            p_cls = "points-text" if not disabled else "points-text-disabled"
                            st.markdown(f"""<div style="padding-top:8px; text-align:right;" class="{p_cls}">+{pts}%</div>""", unsafe_allow_html=True)
                        with sc2:
                            val = st.toggle(
                                "x", key=key, 
                                value=st.session_state.checklist.get(key, False),
                                label_visibility="collapsed",
                                disabled=disabled,
                                on_change=handle_psych_logic if label == "Round Psych Level" else None,
                                args=(sec_name,) if label == "Round Psych Level" else None
                            )
                            st.session_state.checklist[key] = val
                    
                    # Separador visual entre filas (Espacio vacío o línea muy sutil)
                    st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)

# ==============================================================================
# PLACEHOLDERS OTRAS PÁGINAS
# ==============================================================================
elif st.session_state.page == 'history':
    st.title("📖 Trading History")
elif st.session_state.page == 'dashboard':
    st.title("📊 Performance Dashboard")
elif st.session_state.page == 'ai_mentor':
    st.title("🤖 AI Mentor")
