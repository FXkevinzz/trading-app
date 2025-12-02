import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
import os
from PIL import Image
import google.generativeai as genai

# ==============================================================================
# 1. CONFIGURACIÓN VISUAL (ESTILO DARK NAVY "PERFECT TRADE")
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

        /* --- 1. CONFLUENCE SUMMARY (MINI CARDS ARRIBA A LA IZQUIERDA) --- */
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 10px;
            margin-bottom: 25px;
        }
        .mini-card {
            background-color: #1e293b;
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 10px 5px;
            text-align: center;
        }
        .mini-title { font-size: 0.65rem; color: #cbd5e1; font-weight: 700; text-transform: uppercase; margin-bottom: 5px; }
        .mini-val { font-size: 1.2rem; color: #34d399; font-weight: 800; }

        /* --- 2. CONTENEDOR DE SECCIONES (CHECKLIST) --- */
        div[data-testid="stBorderDomWrapper"] {
            background-color: #1e293b; 
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
        }

        .section-header-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; }
        .section-title { font-size: 0.9rem; font-weight: 800; color: #ffffff; text-transform: uppercase; letter-spacing: 0.5px; }
        .section-score { font-size: 1.2rem; font-weight: 800; color: #34d399; }

        /* --- TOGGLES --- */
        .toggle-label { font-size: 0.95rem; font-weight: 600; color: #e2e8f0; }
        .points-text { color: #34d399; font-weight: 700; font-size: 0.85rem; }
        .points-text-disabled { color: #64748b; font-weight: 600; font-size: 0.85rem; }

        /* --- 3. PANEL DERECHO (TOTAL SCORE FIJO) --- */
        .sticky-score-card {
            background: linear-gradient(180deg, #115e59 0%, #0f172a 100%);
            border: 2px solid #14b8a6;
            border-radius: 16px;
            padding: 30px;
            text-align: center;
            position: sticky;
            top: 20px;
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.3);
        }
        
        .score-big-val {
            font-size: 4rem;
            font-weight: 900;
            color: #ccfbf1;
            line-height: 1;
            text-shadow: 0 0 15px rgba(20, 184, 166, 0.4);
        }
        
        /* --- 4. AYUDA VISUAL (TU ALGO CURIOSO) --- */
        .visual-helper-box {
            background-color: #111827; 
            border: 1px solid #374151; 
            border-left: 4px solid #10b981; 
            border-radius: 8px; 
            padding: 15px; 
            margin-top: 10px; 
            margin-bottom: 15px;
            animation: fadeIn 0.4s ease;
        }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(-5px); } to { opacity: 1; transform: translateY(0); } }
        
        .helper-title { color: #10b981; font-weight: 700; font-size: 0.9rem; margin-bottom: 5px; }
        .helper-text { color: #cbd5e1; font-size: 0.85rem; line-height: 1.4; margin-bottom: 10px; }

        /* --- BOTONES --- */
        .stButton button {
            background-color: #10b981 !important;
            color: #ffffff !important;
            border: none;
            border-radius: 6px;
            font-weight: 600;
            padding: 0.6rem 1.2rem;
            width: 100%;
        }
        </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# ==============================================================================
# 2. DATOS Y LÓGICA
# ==============================================================================

if 'page' not in st.session_state: st.session_state.page = 'checklist'
if 'checklist' not in st.session_state: st.session_state.checklist = {}
if 'psych_selected_in' not in st.session_state: st.session_state.psych_selected_in = None 

# --- DICCIONARIO DE AYUDAS VISUALES (TU "ALGO CURIOSO") ---
HELPER_DATA = {
    "Trend": {
        "title": "Estructura de Mercado",
        "desc": "¿El mercado está haciendo Altos Más Altos (HH) o Bajos Más Bajos (LL)?",
        "img": "trend img.jpg" # Nombre exacto de tu archivo
    },
    "At AOI / Rejected": {
        "title": "Zona de Interés (AOI)",
        "desc": "El precio debe tocar o estar reaccionando en una zona marcada previamente.",
        "img": "ATAOI.jpg"
    },
    "Touching EMA": {
        "title": "EMA 50 Dinámica",
        "desc": "¿El precio está rebotando en la línea de la EMA 50?",
        "img": "EMA.jpg"
    },
    "Round Psych Level": {
        "title": "Nivel Psicológico",
        "desc": "Busca números redondos (ej: 1.2000, 1.2050) cerca del precio.",
        "img": "ROUND-PSYCHO-LEVEL.jpg"
    },
    "Rejection from Previous Structure": {
        "title": "Estructura Previa",
        "desc": "Soporte que se vuelve resistencia (o viceversa).",
        "img": "PREVIOUS STRUCTURE.jpg"
    },
    "Candlestick Rejection from AOI": {
        "title": "Patrón de Velas",
        "desc": "Busca Mechas largas, Dojis o Envolventes.",
        "img": "ATAOIII.jpg" 
    },
    "Break & Retest / Head & Shoulders Pattern": {
        "title": "Patrones Chartistas",
        "desc": "Ruptura y retesteo o cambio de tendencia (HCH).",
        "img": "HEAD&SHOULDERS copy.jpg"
    },
    "SOS": {
        "title": "Shift of Structure (SOS)",
        "desc": "Ruptura del último punto estructural válido.",
        "img": "trend img.jpg"
    },
    "Engulfing candlestick (30m, 1H, 2H, 4H)": {
        "title": "Vela Envolvente",
        "desc": "Vela fuerte que cubre a la anterior confirmando la entrada.",
        "img": "ATAOIII.jpg"
    }
}

STRATEGY = {
    "WEEKLY": [
        ("Trend", 10), 
        ("At AOI / Rejected", 10), 
        ("Touching EMA", 5), 
        ("Round Psych Level", 5), 
        ("Rejection from Previous Structure", 10), 
        ("Candlestick Rejection from AOI", 10), 
        ("Break & Retest / Head & Shoulders Pattern", 10)
    ],
    "DAILY": [
        ("Trend", 10), 
        ("At AOI / Rejected", 10), 
        ("Touching EMA", 5), 
        ("Round Psych Level", 5), 
        ("Rejection from Previous Structure", 10), 
        ("Candlestick Rejection from AOI", 10), 
        ("Break & Retest / Head & Shoulders Pattern", 10)
    ],
    "4H": [
        ("Trend", 5), 
        ("At AOI / Rejected", 5), 
        ("Touching EMA", 5), 
        ("Round Psych Level", 5), 
        ("Rejection from Previous Structure", 10), 
        ("Candlestick Rejection from AOI", 5), 
        ("Break & Retest / Head & Shoulders Pattern", 10)
    ],
    "2H, 1H, 30M": [
        ("Trend", 5), 
        ("Touching EMA", 5), 
        ("Break & Retest / Head & Shoulders Pattern", 5)
    ],
    "ENTRY SIGNAL": [
        ("SOS", 10), 
        ("Engulfing candlestick (30m, 1H, 2H, 4H)", 10)
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
    is_active = st.session_state[key_changed]
    if is_active:
        st.session_state.psych_selected_in = section_changed
        for sec in ["WEEKLY", "DAILY", "4H"]:
            if sec != section_changed:
                other_key = f"{sec}_Round Psych Level"
                if other_key in st.session_state.checklist: st.session_state.checklist[other_key] = False
    else:
        if st.session_state.psych_selected_in == section_changed: st.session_state.psych_selected_in = None

def get_local_image(filename):
    path = os.path.join("foto", filename) # Busca en carpeta 'foto'
    if os.path.exists(path): return path
    return None

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

if st.session_state.page == 'checklist':
    
    total, sec_scores = calculate_totals()
    
    status_txt = "Weak Setup"
    score_color = "#ef4444"
    if total >= 60: score_color = "#facc15"; status_txt = "Moderate Setup"
    if total >= 90: score_color = "#10b981"; status_txt = "🔥 Sniper Entry"

    # --- LAYOUT PRINCIPAL (3 Columnas Izq | 1 Columna Der) ---
    main_col, side_col = st.columns([3, 1], gap="medium")

    # === COLUMNA IZQUIERDA: RESUMEN + CHECKLIST ===
    with main_col:
        
        # 1. CONFLUENCE SUMMARY (MINI CARDS)
        st.markdown('<div style="color:#e2e8f0; font-weight:700; margin-bottom:10px;">CONFLUENCE BREAKDOWN</div>', unsafe_allow_html=True)
        
        # Generar HTML para el Grid de tarjetas
        cards_html = '<div class="summary-grid">'
        # Ordenamos las secciones para mostrarlas
        ordered_sections = ["WEEKLY", "DAILY", "4H", "2H, 1H, 30M", "ENTRY SIGNAL"]
        
        for sec in ordered_sections:
            val = sec_scores.get(sec, 0)
            cards_html += f"""
            <div class="mini-card">
                <div class="mini-title">{sec}</div>
                <div class="mini-val">{val}%</div>
            </div>
            """
        cards_html += '</div>'
        st.markdown(cards_html, unsafe_allow_html=True)

        # 2. CHECKLISTS (TOGGLES)
        for sec_name, items in STRATEGY.items():
            current_sec_score = sec_scores.get(sec_name, 0)
            
            with st.container(border=True):
                # Header Interno
                st.markdown(f"""
                <div class="section-header-row">
                    <div class="section-title">{sec_name}</div>
                    <div class="section-score">{current_sec_score}%</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Toggles
                for label, pts in items:
                    key = f"{sec_name}_{label}"
                    
                    disabled = False
                    if label == "Round Psych Level":
                        if st.session_state.psych_selected_in and st.session_state.psych_selected_in != sec_name:
                            disabled = True

                    # Fila: Texto .... [Pts] [Switch]
                    c1, c2 = st.columns([4, 1])
                    
                    with c1:
                        col_lbl = "#4b5563" if disabled else "#e2e8f0"
                        st.markdown(f"""<div style="padding-top:8px; font-weight:600; font-size:0.9rem; color:{col_lbl};">{label}</div>""", unsafe_allow_html=True)
                    
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
                    
                    # --- TU ALGO CURIOSO (AYUDA VISUAL) ---
                    # Se despliega si el toggle está ON
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
                            # Imagen pequeña (350px)
                            st.image(img_path, width=350)
                        else:
                            st.caption(f"⚠️ Falta: {data['img']}")

                    if label != items[-1][0]:
                        st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)

    # === COLUMNA DERECHA: SCORE + SAVE (FIJO) ===
    with side_col:
        st.markdown(f"""
        <div class="sticky-score-card" style="border-color:{score_color};">
            <div style="color:#ccfbf1; letter-spacing:1px; font-weight:700; font-size:0.8rem; text-transform:uppercase; margin-bottom:15px;">TOTAL SCORE</div>
            <div class="score-big-val" style="color:{score_color};">{total}%</div>
            <div style="font-size:1.1rem; font-weight:700; color:{score_color}; margin-top:10px; margin-bottom:20px;">{status_txt}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if total > 0:
            if st.button("💾 SAVE TRADE", use_container_width=True):
                st.toast("Abriendo modal de guardado...", icon="✅")

# ==============================================================================
# OTRAS PÁGINAS (Placeholders)
# ==============================================================================
elif st.session_state.page == 'history':
    st.title("📖 Trading History")
elif st.session_state.page == 'dashboard':
    st.title("📊 Performance Dashboard")
elif st.session_state.page == 'ai_mentor':
    st.title("🤖 AI Mentor")
