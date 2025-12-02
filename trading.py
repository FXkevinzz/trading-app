import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
import os
from PIL import Image
import google.generativeai as genai

# ==============================================================================
# 1. CONFIGURACIÓN VISUAL (ESTILO DARK NAVY)
# ==============================================================================
st.set_page_config(page_title="The Perfect Trade AI", layout="wide", page_icon="🦁")

def inject_custom_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        .stApp { background-color: #0f172a; font-family: 'Inter', sans-serif; color: #f8fafc; }
        #MainMenu, footer, header {visibility: hidden;}
        .stDeployButton {display:none;}

        /* CAJA CHECKLIST */
        div[data-testid="stBorderDomWrapper"] {
            background-color: #1e293b; border: 1px solid #334155;
            border-radius: 12px; padding: 24px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); margin-bottom: 20px;
        }

        /* HEADER */
        .section-header-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; }
        .section-title { font-size: 0.9rem; font-weight: 800; color: #ffffff; text-transform: uppercase; letter-spacing: 0.5px; }
        .section-score { font-size: 1.5rem; font-weight: 800; color: #34d399; }

        /* TOGGLES */
        .toggle-label { font-size: 0.95rem; font-weight: 600; color: #e2e8f0; }
        .points-text { color: #34d399; font-weight: 700; font-size: 0.85rem; }
        .points-text-disabled { color: #64748b; font-weight: 600; font-size: 0.85rem; }

        /* SCORE DERECHO */
        .sticky-score-card {
            background: linear-gradient(180deg, #115e59 0%, #0f172a 100%);
            border: 1px solid #14b8a6; border-radius: 16px; padding: 30px;
            text-align: center; position: sticky; top: 20px;
        }
        .score-big-val { font-size: 4.5rem; font-weight: 900; color: #fff; line-height: 1; }
        
        /* AYUDA VISUAL */
        .visual-helper-box {
            background-color: #111827; border: 1px solid #374151; border-left: 4px solid #10b981;
            border-radius: 8px; padding: 15px; margin-top: 10px; margin-bottom: 15px;
            animation: fadeIn 0.3s ease-in-out;
        }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(-5px); } to { opacity: 1; transform: translateY(0); } }
        .helper-title { color: #10b981; font-weight: 700; font-size: 0.9rem; margin-bottom: 5px; }
        .helper-text { color: #cbd5e1; font-size: 0.9rem; line-height: 1.4; margin-bottom: 10px; }

        .stButton button { background-color: #10b981 !important; color: #ffffff !important; border: none; border-radius: 6px; font-weight: 600; padding: 0.6rem 1.2rem; width: 100%; }
        </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# ==============================================================================
# 2. LOGICA Y DATOS
# ==============================================================================

if 'page' not in st.session_state: st.session_state.page = 'checklist'
if 'checklist' not in st.session_state: st.session_state.checklist = {}
if 'psych_selected_in' not in st.session_state: st.session_state.psych_selected_in = None 

# --- NOMBRES EXACTOS DE ARCHIVOS ---
# Asegúrate de que tu carpeta se llame "foto" (minúsculas) y los archivos sean idénticos a esto:
HELPER_DATA = {
    "Trend": {
        "title": "Estructura de Mercado",
        "desc": "¿Estructura alcista (HH/HL) o bajista (LH/LL)?",
        "img": "trend img.jpg"
    },
    "At AOI / Rejected": {
        "title": "Zona de Interés (AOI)",
        "desc": "El precio debe estar tocando o reaccionando a la zona.",
        "img": "ATAOI.jpg"
    },
    "Touching EMA": {
        "title": "Rechazo Dinámico (50 EMA)",
        "desc": "El precio toca o rechaza la EMA 50.",
        "img": "EMA.jpg"
    },
    "Round Psych Level": {
        "title": "Nivel Psicológico",
        "desc": "Número redondo cercano (ej. 1.5000).",
        "img": "ROUND-PSYCHO-LEVEL.jpg"
    },
    "Rejection from Previous Structure": {
        "title": "Estructura Previa",
        "desc": "Rebote en un Alto o Bajo anterior.",
        "img": "PREVIOUS STRUCTURE.jpg"
    },
    "Candlestick Rejection from AOI": {
        "title": "Patrón de Velas",
        "desc": "Mechas largas, Dojis o Envolventes en la zona.",
        "img": "ATAOIII.jpg" 
    },
    "Break & Retest / Head & Shoulders Pattern": {
        "title": "Patrones Avanzados",
        "desc": "Ruptura y Retesteo o Hombro-Cabeza-Hombro.",
        "img": "HEAD&SHOULDERS copy.jpg"
    },
    "SOS": {
        "title": "Cambio de Estructura (SOS)",
        "desc": "Ruptura del último alto/bajo válido.",
        "img": "trend img.jpg"
    },
    "Engulfing candlestick (30m, 1H, 2H, 4H)": {
        "title": "Vela Gatillo",
        "desc": "Vela envolvente clara que confirma la dirección.",
        "img": "ATAOIII.jpg"
    }
}

STRATEGY = {
    "WEEKLY": [
        ("Trend", 10), ("At AOI / Rejected", 10), ("Touching EMA", 5), 
        ("Round Psych Level", 5), ("Rejection from Previous Structure", 10), 
        ("Candlestick Rejection from AOI", 10), ("Break & Retest / Head & Shoulders Pattern", 10)
    ],
    "DAILY": [
        ("Trend", 10), ("At AOI / Rejected", 10), ("Touching EMA", 5), 
        ("Round Psych Level", 5), ("Rejection from Previous Structure", 10), 
        ("Candlestick Rejection from AOI", 10), ("Break & Retest / Head & Shoulders Pattern", 10)
    ],
    "4H": [
        ("Trend", 5), ("At AOI / Rejected", 5), ("Touching EMA", 5), 
        ("Round Psych Level", 5), ("Rejection from Previous Structure", 10), 
        ("Candlestick Rejection from AOI", 5), ("Break & Retest / Head & Shoulders Pattern", 10)
    ],
    "2H, 1H, 30M": [
        ("Trend", 5), ("Touching EMA", 5), ("Break & Retest / Head & Shoulders Pattern", 5)
    ],
    "ENTRY SIGNAL": [
        ("SOS", 10), ("Engulfing candlestick (30m, 1H, 2H, 4H)", 10)
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

# --- CORRECCIÓN LÓGICA DE BLOQUEO ---
def handle_psych_logic(section_changed):
    key_changed = f"{section_changed}_Round Psych Level"
    # CORRECCIÓN IMPORTANTE: Leer el estado directamente del widget, no del dict checklist
    # (Streamlit actualiza el estado del widget antes de ejecutar el callback)
    is_active = st.session_state[key_changed]
    
    if is_active:
        st.session_state.psych_selected_in = section_changed
        # Forzar apagado en otras secciones
        for sec in ["WEEKLY", "DAILY", "4H"]:
            if sec != section_changed:
                other_key = f"{sec}_Round Psych Level"
                # Si existe en el estado, lo apagamos
                if other_key in st.session_state.checklist: 
                    st.session_state.checklist[other_key] = False
    else:
        # Si se desactivó el dueño, liberamos el bloqueo
        if st.session_state.psych_selected_in == section_changed:
            st.session_state.psych_selected_in = None

def get_local_image(filename):
    # Busca en carpeta 'foto' (minúscula)
    path = os.path.join("foto", filename)
    if os.path.exists(path):
        return path
    # Intenta en 'Foto' (mayúscula) por si acaso
    path_cap = os.path.join("Foto", filename)
    if os.path.exists(path_cap):
        return path_cap
    return None

# ==============================================================================
# 3. INTERFAZ
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

if st.session_state.page == 'checklist':
    
    total, sec_scores = calculate_totals()
    
    status_txt = "Weak Setup"
    score_color = "#ef4444"
    if total >= 60: score_color = "#facc15"; status_txt = "Moderate Setup"
    if total >= 90: score_color = "#10b981"; status_txt = "🔥 Sniper Entry"

    main_col, side_col = st.columns([3, 1], gap="large")

    with main_col:
        for sec_name, items in STRATEGY.items():
            current_sec_score = sec_scores.get(sec_name, 0)
            
            with st.container(border=True):
                st.markdown(f"""
                <div class="section-header-row">
                    <div class="section-title">{sec_name}</div>
                    <div class="section-score">{current_sec_score}%</div>
                </div>
                """, unsafe_allow_html=True)
                
                for label, pts in items:
                    key = f"{sec_name}_{label}"
                    
                    disabled = False
                    if label == "Round Psych Level":
                        if st.session_state.psych_selected_in and st.session_state.psych_selected_in != sec_name:
                            disabled = True

                    c1, c2 = st.columns([3, 1])
                    
                    with c1:
                        col_lbl = "#4b5563" if disabled else "#e2e8f0"
                        st.markdown(f"""<div style="padding-top:8px; font-weight:600; font-size:0.95rem; color:{col_lbl};">{label}</div>""", unsafe_allow_html=True)
                    
                    with c2:
                        sub_c1, sub_c2 = st.columns([1, 1])
                        with sub_c1:
                            pts_cls = "points-text" if not disabled else "points-text-disabled"
                            st.markdown(f"""<div style="padding-top:8px; text-align:right;" class="{pts_cls}">+{pts}%</div>""", unsafe_allow_html=True)
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
                    
                    # --- HELPER VISUAL ---
                    if val and label in HELPER_DATA:
                        data = HELPER_DATA[label]
                        img_path = get_local_image(data['img'])
                        
                        st.markdown(f"""
                        <div class="visual-helper-box">
                            <div class="helper-title">👁️ {data['title']}</div>
                            <div class="helper-text">{data['desc']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if img_path:
                            # IMAGEN MÁS PEQUEÑA (Width 350)
                            st.image(img_path, width=350)
                        else:
                            # Mensaje de ayuda si no encuentra la foto
                            st.caption(f"⚠️ Falta archivo: foto/{data['img']}")

                    if label != items[-1][0]:
                        st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)

    with side_col:
        st.markdown(f"""
        <div class="sticky-score-card" style="border-color:{score_color};">
            <div style="color:#ccfbf1; letter-spacing:1px; font-weight:700; font-size:0.9rem; text-transform:uppercase; margin-bottom:15px;">TOTAL SCORE</div>
            <div class="score-big-val" style="color:{score_color};">{total}%</div>
            <div style="font-size:1.2rem; font-weight:700; color:{score_color}; margin-top:10px; margin-bottom:20px;">{status_txt}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if total > 0:
            if st.button("💾 SAVE TRADE", use_container_width=True):
                st.toast("Abriendo modal de guardado...", icon="✅")

# ==============================================================================
# OTRAS PÁGINAS
# ==============================================================================
elif st.session_state.page == 'history':
    st.title("📖 Trading History")
elif st.session_state.page == 'dashboard':
    st.title("📊 Performance Dashboard")
elif st.session_state.page == 'ai_mentor':
    st.title("🤖 AI Mentor")
