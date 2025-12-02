import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
import google.generativeai as genai
from PIL import Image

# ==============================================================================
# 1. CONFIGURACIÓN VISUAL (CSS DE ALTO CONTRASTE Y ANIMACIÓN)
# ==============================================================================
st.set_page_config(page_title="The Perfect Trade AI", layout="wide", page_icon="🦁")

def inject_custom_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');

        /* --- 1. FONDO GENERAL (MUY OSCURO PARA CONTRASTE) --- */
        .stApp {
            background-color: #020617; /* Casi negro */
            font-family: 'Inter', sans-serif;
            color: #f8fafc;
        }
        
        #MainMenu, footer, header {visibility: hidden;}
        .stDeployButton {display:none;}

        /* --- 2. LA CAJA MAGICA (st.container) --- */
        /* Esta clase afecta a los st.container(border=True) */
        div[data-testid="stBorderDomWrapper"] {
            background-color: #1e293b; /* GRIS ACERO (Se nota la diferencia con el fondo) */
            border: 2px solid #334155;
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5); /* Sombra fuerte */
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); /* Animación suave */
        }

        /* --- 3. ANIMACIÓN AL PASAR EL MOUSE (HOVER) --- */
        div[data-testid="stBorderDomWrapper"]:hover {
            border-color: #10b981; /* Borde VERDE NEÓN */
            background-color: #252f45; /* Se aclara ligeramente */
            transform: translateY(-5px); /* SE LEVANTA */
            box-shadow: 0 15px 30px -5px rgba(16, 185, 129, 0.15); /* Resplandor verde */
        }

        /* --- HEADER DENTRO DE LA CAJA (Weekly - 0%) --- */
        .box-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #334155;
        }
        .box-title {
            font-size: 1.1rem;
            font-weight: 900;
            color: #ffffff;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .box-score {
            font-size: 1.2rem;
            font-weight: 800;
            color: #34d399; /* Verde claro */
        }

        /* --- FILAS DE TOGGLES --- */
        .row-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            height: 45px;
            border-bottom: 1px solid #334155; /* Línea separadora sutil */
        }
        .row-item:last-child { border-bottom: none; }

        .label-text {
            color: #cbd5e1;
            font-weight: 500;
            font-size: 0.95rem;
        }
        
        .points-tag {
            background-color: rgba(16, 185, 129, 0.1);
            color: #10b981;
            padding: 4px 8px;
            border-radius: 6px;
            font-weight: 700;
            font-size: 0.8rem;
            margin-right: 12px;
        }
        .points-tag-disabled {
            background-color: rgba(71, 85, 105, 0.2);
            color: #64748b;
            padding: 4px 8px;
            border-radius: 6px;
            font-weight: 700;
            font-size: 0.8rem;
            margin-right: 12px;
        }

        /* --- DASHBOARD SCORE GIGANTE --- */
        .score-hero {
            background: linear-gradient(135deg, #111827 0%, #1f2937 100%);
            border: 2px solid #10b981;
            border-radius: 20px;
            padding: 30px;
            text-align: center;
            margin-bottom: 40px;
            box-shadow: 0 0 25px rgba(16, 185, 129, 0.2);
        }
        .hero-number {
            font-size: 5rem;
            font-weight: 900;
            color: #fff;
            line-height: 1;
            text-shadow: 0 0 15px rgba(16, 185, 129, 0.6);
        }
        .hero-text {
            color: #10b981;
            font-size: 1.5rem;
            font-weight: 800;
            text-transform: uppercase;
            margin-top: 10px;
        }

        /* --- BOTONES --- */
        .stButton button {
            background-color: #10b981 !important;
            color: #022c22 !important;
            font-weight: 800;
            border-radius: 8px;
            border: none;
            transition: transform 0.1s;
        }
        .stButton button:hover {
            transform: scale(1.02);
            background-color: #34d399 !important;
        }
        </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# ==============================================================================
# 2. LÓGICA DE NEGOCIO
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
# 3. INTERFAZ: NAVBAR
# ==============================================================================
c_nav1, c_nav2 = st.columns([1, 4])
with c_nav1:
    st.markdown('<div style="font-size:1.3rem; font-weight:900; color:#fff;">🦁 PERFECT TRADE</div>', unsafe_allow_html=True)
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
# PÁGINA 1: CHECKLIST (DISEÑO CAJAS DE ALTO CONTRASTE)
# ==============================================================================
if st.session_state.page == 'checklist':
    
    total, sec_scores = calculate_totals()
    
    status_txt = "WEAK SETUP"
    score_color = "#ef4444"
    if total >= 60: score_color = "#facc15"; status_txt = "MODERATE"
    if total >= 90: score_color = "#10b981"; status_txt = "🔥 SNIPER ENTRY"

    # DASHBOARD GIGANTE SUPERIOR
    st.markdown(f"""
    <div class="score-hero" style="border-color:{score_color}; box-shadow: 0 0 30px {score_color}40;">
        <div style="color:#94a3b8; font-weight:600; letter-spacing:2px; margin-bottom:10px;">TOTAL OVERALL SCORE</div>
        <div class="hero-number" style="color:{score_color}; text-shadow: 0 0 20px {score_color}60;">{total}%</div>
        <div class="hero-text" style="color:{score_color};">{status_txt}</div>
    </div>
    """, unsafe_allow_html=True)

    if total > 0:
        if st.button("💾 GUARDAR TRADE", use_container_width=True):
            st.toast("Abriendo modal...", icon="✅")

    st.markdown("<br>", unsafe_allow_html=True)

    # GRID DE SECCIONES
    col_izq, col_der = st.columns(2, gap="large")
    
    for i, (sec_name, items) in enumerate(STRATEGY.items()):
        target_col = col_izq if i % 2 == 0 else col_der
        
        with target_col:
            current_score = sec_scores.get(sec_name, 0)
            
            # --- CAJA CON BORDE NATIVO (Animada por CSS) ---
            with st.container(border=True):
                
                # HEADER INTERNO (Personalizado)
                st.markdown(f"""
                <div class="box-header">
                    <span class="box-title">{sec_name}</span>
                    <span class="box-score">{current_score}%</span>
                </div>
                """, unsafe_allow_html=True)
                
                # LISTA DE TOGGLES
                for label, pts in items:
                    key = f"{sec_name}_{label}"
                    
                    # Lógica de bloqueo
                    disabled = False
                    if label == "Round Psych Level":
                        if st.session_state.psych_selected_in and st.session_state.psych_selected_in != sec_name:
                            disabled = True

                    # ESTRUCTURA DE FILA: Texto .......... [Badge] [Switch]
                    c_txt, c_ctrl = st.columns([3, 1])
                    
                    with c_txt:
                        col_lbl = "#475569" if disabled else "#cbd5e1"
                        st.markdown(f"""<div style="padding-top:12px; font-weight:500; color:{col_lbl};">{label}</div>""", unsafe_allow_html=True)
                    
                    with c_ctrl:
                        # Usamos columnas anidadas para pegar el badge al toggle
                        sub_c1, sub_c2 = st.columns([1, 1])
                        with sub_c1:
                            # Badge de puntos (+10%)
                            badge_cls = "points-tag-disabled" if disabled else "points-tag"
                            st.markdown(f"""<div style="padding-top:10px; text-align:right;"><span class="{badge_cls}">+{pts}%</span></div>""", unsafe_allow_html=True)
                        with sub_c2:
                            # Switch Real
                            val = st.toggle(
                                "x", key=key, 
                                value=st.session_state.checklist.get(key, False),
                                label_visibility="collapsed",
                                disabled=disabled,
                                on_change=handle_psych_logic if label == "Round Psych Level" else None,
                                args=(sec_name,) if label == "Round Psych Level" else None
                            )
                            st.session_state.checklist[key] = val
                    
                    # Separador visual
                    if label != items[-1][0]:
                        st.markdown("<div style='border-bottom:1px solid #334155; margin-bottom:5px;'></div>", unsafe_allow_html=True)

# ==============================================================================
# OTRAS PÁGINAS
# ==============================================================================
elif st.session_state.page == 'history':
    st.title("📖 Trading History")
elif st.session_state.page == 'dashboard':
    st.title("📊 Performance Dashboard")
elif st.session_state.page == 'ai_mentor':
    st.title("🤖 AI Mentor")
