import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
import google.generativeai as genai
from PIL import Image

# ==============================================================================
# 1. CONFIGURACIÓN Y ESTILOS (DISEÑO PREMIUM "CONTAINER")
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

        /* --- CONTENEDOR DE SECCIÓN (ESTILO IMAGEN 10) --- */
        .section-container {
            background-color: #161b26; /* Fondo de la tarjeta */
            border: 1px solid #2d3748;
            border-radius: 12px;
            padding: 0; /* Padding 0 para que el header toque los bordes si quisieras, pero usaremos interno */
            margin-bottom: 25px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
            overflow: hidden; /* Para que el header no se salga */
        }

        .section-header-box {
            background-color: #1f2937; /* Un tono ligeramente más claro para el título */
            padding: 15px 25px;
            border-bottom: 1px solid #2d3748;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .section-title-text {
            font-size: 1.1rem;
            font-weight: 800;
            color: #e2e8f0;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .section-score-text {
            font-size: 1.2rem;
            font-weight: 800;
            color: #10b981; /* Verde brillante */
        }

        .section-body {
            padding: 10px 25px 25px 25px; /* Espacio para los toggles */
        }

        /* --- TOGGLES DE LÍNEA --- */
        .toggle-wrapper {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid #2d3748; /* Línea separadora sutil */
        }
        
        .toggle-wrapper:last-child {
            border-bottom: none; /* Quitar línea al último elemento */
        }

        .toggle-label-text {
            font-size: 0.95rem;
            font-weight: 500;
            color: #cbd5e1;
        }

        .right-side-controls {
            display: flex;
            align-items: center;
            gap: 15px; /* Espacio entre +10% y el Switch */
        }

        .points-badge {
            font-size: 0.85rem;
            font-weight: 700;
            color: #10b981;
        }
        
        .points-badge-disabled {
            color: #475569;
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
        
        /* --- ESTILOS DE BOTONES --- */
        .stButton button {
            background-color: #10b981 !important;
            color: #064e3b !important;
            border: none;
            font-weight: 800;
            font-size: 1rem;
            padding: 0.6rem 1.5rem;
            border-radius: 8px;
            transition: all 0.2s;
        }
        .stButton button:hover {
            background-color: #34d399 !important;
            transform: scale(1.02);
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
    "2H, 1H, 30m": [
        ("Trend", 5), ("Touching EMA", 5), ("Break & Retest", 5)
    ],
    "ENTRY SIGNAL": [
        ("SOS (Shift of Structure)", 10), ("Engulfing candlestick", 10)
    ]
}

# --- LÓGICA DE CÁLCULO ---
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
# PÁGINA 1: CHECKLIST (Diseño Contenedor Único)
# ==============================================================================
if st.session_state.page == 'checklist':
    
    total, sec_scores = calculate_totals()
    
    status_txt = "WEAK SETUP"
    score_color = "#ef4444"
    if total >= 60: score_color = "#facc15"; status_txt = "MODERATE"
    if total >= 90: score_color = "#10b981"; status_txt = "🔥 SNIPER ENTRY"

    # Dashboard Score Gigante
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

    # GRIDS PARA LAS SECCIONES (2 Columnas)
    left_col, right_col = st.columns(2, gap="large")
    
    for i, (sec_name, items) in enumerate(STRATEGY.items()):
        target_col = left_col if i % 2 == 0 else right_col
        
        with target_col:
            # 1. INICIO DEL CONTENEDOR (Todo lo de esta sección va dentro)
            current_score = sec_scores.get(sec_name, 0)
            
            # Header del Contenedor (Título + Score)
            st.markdown(f"""
            <div class="section-container">
                <div class="section-header-box">
                    <span class="section-title-text">{sec_name}</span>
                    <span class="section-score-text">{current_score}%</span>
                </div>
                <div class="section-body">
            """, unsafe_allow_html=True)
            
            # 2. CUERPO DEL CONTENEDOR (Lista de Toggles)
            for label, pts in items:
                key = f"{sec_name}_{label}"
                
                # Lógica de bloqueo
                disabled = False
                help_msg = None
                if label == "Round Psych Level":
                    if st.session_state.psych_selected_in and st.session_state.psych_selected_in != sec_name:
                        disabled = True
                        help_msg = "⛔ Ya usado en otra TF"

                # Layout de Fila: Label a la izquierda, (+10% Switch) a la derecha
                c_label, c_ctrl = st.columns([3, 1])
                
                with c_label:
                    color_lbl = "#64748b" if disabled else "#cbd5e1"
                    st.markdown(f"""
                    <div style="display:flex; align-items:center; height:40px;">
                        <span class="toggle-label-text" style="color:{color_lbl}">{label}</span>
                    </div>
                    """, unsafe_allow_html=True)
                    if help_msg: st.caption(help_msg)
                
                with c_ctrl:
                    # Contenedor flex para alinear (+10% y Switch)
                    col_pts = "#475569" if disabled else "#10b981"
                    
                    # Usamos 2 subcolumnas apretadas para simular el "flex"
                    sub_c1, sub_c2 = st.columns([1, 1])
                    with sub_c1:
                        st.markdown(f"<div style='text-align:right; color:{col_pts}; font-weight:bold; font-size:0.85rem; padding-top:10px;'>+{pts}%</div>", unsafe_allow_html=True)
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
                
                # Divisor sutil entre items (menos el último)
                if label != items[-1][0]:
                    st.markdown("<div style='border-bottom:1px solid #2d3748; margin: 5px 0;'></div>", unsafe_allow_html=True)

            # 3. CIERRE DEL CONTENEDOR
            st.markdown("</div></div>", unsafe_allow_html=True)

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
