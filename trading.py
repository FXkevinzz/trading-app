import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
import google.generativeai as genai
from PIL import Image

# ==============================================================================
# 1. CONFIGURACIÓN Y ESTILOS (DISEÑO FINAL CON ANIMACIONES)
# ==============================================================================
st.set_page_config(page_title="The Perfect Trade AI", layout="wide", page_icon="🦁")

def inject_custom_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;800&display=swap');

        /* --- TEMA GLOBAL --- */
        .stApp {
            background-color: #0b0f19; /* Fondo Ultra Dark (Casi Negro) */
            font-family: 'Inter', sans-serif;
            color: #f1f5f9;
        }
        
        #MainMenu, footer, header {visibility: hidden;}
        .stDeployButton {display:none;}

        /* --- MAGIC: ESTILO Y ANIMACIÓN DE LA CAJA (st.container) --- */
        
        /* 1. El estado normal de la caja */
        div[data-testid="stBorderDomWrapper"] {
            background-color: #1e293b; /* Color visible (Gris Azulado) */
            border: 2px solid #334155; /* Borde sutil inicial */
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); /* Animación suave con rebote */
        }
        
        /* 2. La Animación al pasar el mouse (HOVER) */
        div[data-testid="stBorderDomWrapper"]:hover {
            background-color: #1f2937; /* Se aclara un poco */
            border-color: #10b981; /* Borde se pone VERDE NEÓN */
            transform: translateY(-8px) scale(1.01); /* Se eleva y crece un poco */
            box-shadow: 0 20px 30px -10px rgba(16, 185, 129, 0.2); /* Sombra verde */
        }

        /* --- HEADER DENTRO DE LA CAJA --- */
        .custom-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            border-bottom: 2px solid #334155; /* Línea separadora */
            padding-bottom: 15px;
        }
        
        .header-title {
            font-size: 1.4rem;
            font-weight: 900;
            color: #fff;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.5);
        }

        .header-score {
            font-size: 1.5rem;
            font-weight: 800;
            color: #34d399; /* Verde menta */
            background: rgba(16, 185, 129, 0.15);
            padding: 5px 15px;
            border-radius: 8px;
        }

        /* --- TEXTOS DE LOS TOGGLES --- */
        .toggle-text-active {
            color: #ffffff; font-weight: 600; font-size: 1rem;
            text-shadow: 0 0 10px rgba(255,255,255,0.3);
        }
        .toggle-text-inactive {
            color: #94a3b8; font-weight: 400; font-size: 1rem;
        }
        
        .points-badge {
            color: #10b981; font-weight: 700; font-size: 0.9rem; margin-right: 10px;
            background: rgba(16, 185, 129, 0.1); padding: 2px 8px; border-radius: 4px;
        }
        .points-badge-disabled {
            color: #475569; font-weight: 700; font-size: 0.9rem; margin-right: 10px;
        }

        /* --- DASHBOARD SCORE (GIGANTE) --- */
        .total-score-box {
            background: linear-gradient(180deg, #0f766e 0%, #042f2e 100%);
            border: 2px solid #2dd4bf;
            border-radius: 24px;
            padding: 40px;
            text-align: center;
            margin-bottom: 40px;
            box-shadow: 0 0 40px rgba(20, 184, 166, 0.3);
            animation: pulse-glow 3s infinite alternate;
        }
        @keyframes pulse-glow {
            from { box-shadow: 0 0 20px rgba(20, 184, 166, 0.2); }
            to { box-shadow: 0 0 50px rgba(45, 212, 191, 0.5); }
        }
        
        .score-val-big {
            font-size: 6rem;
            font-weight: 900;
            color: #ffffff;
            line-height: 1;
            text-shadow: 0 5px 15px rgba(0,0,0,0.5);
        }
        
        /* --- BOTONES --- */
        .stButton button {
            background-color: #10b981 !important;
            color: #064e3b !important;
            border: none;
            font-weight: 800;
            font-size: 1rem;
            padding: 0.7rem 2rem;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4);
            transition: all 0.3s;
        }
        .stButton button:hover {
            transform: scale(1.05);
            box-shadow: 0 6px 20px rgba(16, 185, 129, 0.6);
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

# Definición de la Estrategia
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

# --- CÁLCULO ---
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

# --- CALLBACK BLOQUEO ---
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
    st.markdown('<div style="font-size:1.5rem; font-weight:900; color:#10b981; text-shadow: 0 0 10px rgba(16,185,129,0.5);">🦁 PERFECT TRADE</div>', unsafe_allow_html=True)
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
# PÁGINA 1: CHECKLIST (DISEÑO ANIMADO)
# ==============================================================================
if st.session_state.page == 'checklist':
    
    total, sec_scores = calculate_totals()
    
    status_txt = "WEAK SETUP"
    score_color = "#ef4444"
    if total >= 60: score_color = "#facc15"; status_txt = "MODERATE"
    if total >= 90: score_color = "#10b981"; status_txt = "🔥 SNIPER ENTRY"

    # Score Box
    st.markdown(f"""
    <div class="total-score-box" style="border-color: {score_color};">
        <div style="color:#ccfbf1; letter-spacing:3px; font-weight:600; margin-bottom:15px; font-size:1.2rem;">TOTAL OVERALL SCORE</div>
        <div class="score-val-big" style="color:{score_color};">{total}%</div>
        <div style="font-size:2rem; font-weight:800; color:{score_color}; margin-top:15px; text-transform:uppercase;">{status_txt}</div>
    </div>
    """, unsafe_allow_html=True)

    if total > 0:
        if st.button("💾 GUARDAR TRADE", use_container_width=True):
            st.toast("Abriendo modal...", icon="✅")

    st.markdown("<br>", unsafe_allow_html=True)

    # Grid de Secciones
    col_izq, col_der = st.columns(2, gap="large")
    
    for i, (sec_name, items) in enumerate(STRATEGY.items()):
        target_col = col_izq if i % 2 == 0 else col_der
        
        with target_col:
            current_sec_score = sec_scores.get(sec_name, 0)
            
            # --- CAJA CON BORDE NATIVO (Animada por CSS) ---
            with st.container(border=True):
                
                # Header Interno
                st.markdown(f"""
                <div class="custom-header">
                    <span class="header-title">{sec_name}</span>
                    <span class="header-score">{current_sec_score}%</span>
                </div>
                """, unsafe_allow_html=True)
                
                # Toggles
                for label, pts in items:
                    key = f"{sec_name}_{label}"
                    
                    disabled = False
                    help_txt = None
                    if label == "Round Psych Level":
                        if st.session_state.psych_selected_in and st.session_state.psych_selected_in != sec_name:
                            disabled = True
                            help_txt = "⛔ Usado en otra TF"

                    # Columnas: Texto | Puntos | Switch
                    c1, c2, c3 = st.columns([5, 2, 1])
                    
                    with c1:
                        is_active = st.session_state.checklist.get(key, False)
                        txt_cls = "toggle-text-active" if is_active and not disabled else "toggle-text-inactive"
                        if disabled: txt_cls = "points-badge-disabled"
                        
                        st.markdown(f"""<div style="padding-top:10px;" class="{txt_cls}">{label}</div>""", unsafe_allow_html=True)
                        if help_txt: st.caption(help_txt)
                    
                    with c2:
                        pt_cls = "points-badge" if not disabled else "points-badge-disabled"
                        st.markdown(f"""<div style="padding-top:10px; text-align:right;"><span class="{pt_cls}">+{pts}%</span></div>""", unsafe_allow_html=True)
                    
                    with c3:
                        val = st.toggle(
                            "x", key=key, 
                            value=st.session_state.checklist.get(key, False),
                            label_visibility="collapsed",
                            disabled=disabled,
                            on_change=handle_psych_logic if label == "Round Psych Level" else None,
                            args=(sec_name,) if label == "Round Psych Level" else None
                        )
                        st.session_state.checklist[key] = val
                    
                    st.markdown("<div style='border-bottom:1px solid #334155; margin-bottom:8px; opacity:0.5;'></div>", unsafe_allow_html=True)

# ==============================================================================
# OTRAS PÁGINAS (Placeholders)
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
