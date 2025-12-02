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

        /* --- FONDO GENERAL --- */
        .stApp {
            background-color: #0f172a; /* Slate 900 */
            font-family: 'Inter', sans-serif;
            color: #f8fafc;
        }
        
        #MainMenu, footer, header {visibility: hidden;}
        .stDeployButton {display:none;}

        /* --- GRID DE RESUMEN --- */
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

        /* --- CONTENEDOR DE SECCIONES --- */
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

        /* --- PANEL DERECHO --- */
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
        .score-big-val { font-size: 4rem; font-weight: 900; color: #ccfbf1; line-height: 1; text-shadow: 0 0 15px rgba(20, 184, 166, 0.4); }
        
        /* --- CAJA DE CONFIRMACIÓN (NUEVO) --- */
        .confirmation-box {
            background-color: #0f172a; 
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 20px;
            margin-top: 10px;
            margin-bottom: 20px;
            animation: slideDown 0.3s ease-out;
            text-align: center;
        }
        @keyframes slideDown { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
        
        .confirm-question { color: #f1f5f9; font-weight: 600; margin-bottom: 15px; font-size: 0.95rem; }

        /* --- BOTONES YES/NO PERSONALIZADOS --- */
        /* Botón general (Save Trade) */
        .stButton button {
            background-color: #10b981 !important;
            color: #ffffff !important;
            border: none; border-radius: 6px; font-weight: 600; padding: 0.6rem 1.2rem; width: 100%;
        }
        
        /* Identificar botones por posición es difícil en Streamlit puro, 
           así que usaremos columnas y orden para el efecto visual */

        </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# ==============================================================================
# 2. DATOS Y LÓGICA
# ==============================================================================

if 'page' not in st.session_state: st.session_state.page = 'checklist'
if 'checklist' not in st.session_state: st.session_state.checklist = {}
if 'psych_selected_in' not in st.session_state: st.session_state.psych_selected_in = None 
# NUEVO: Estado para saber qué estamos confirmando
if 'confirming_key' not in st.session_state: st.session_state.confirming_key = None

# --- DICCIONARIO DE AYUDAS VISUALES ---
HELPER_DATA = {
    "Trend": {
        "title": "Estructura de Mercado",
        "desc": "¿Tu estructura de mercado alcista o bajista se ve así?",
        # Aquí ponemos las DOS imágenes para que salgan lado a lado como en tu ejemplo
        "images": ["trend img.jpg", "Bearish trend.jpg"] 
    },
    "At AOI / Rejected": {
        "title": "Validación de Zona",
        "desc": "¿El precio está reaccionando dentro de la zona marcada?",
        "images": ["ATAOI.jpg"]
    },
    "Touching EMA": {
        "title": "EMA 50",
        "desc": "¿El precio está tocando o rechazando la EMA 50?",
        "images": ["EMA.jpg"]
    },
    "Round Psych Level": {
        "title": "Nivel Psicológico",
        "desc": "¿Hay un número redondo cerca?",
        "images": ["ROUND-PSYCHO-LEVEL.jpg"]
    },
    "Rejection from Previous Structure": {
        "title": "Estructura Previa",
        "desc": "¿Rebote en estructura anterior?",
        "images": ["PREVIOUS STRUCTURE.jpg"]
    },
    "Candlestick Rejection from AOI": {
        "title": "Patrón de Velas",
        "desc": "¿Ves mechas o patrones de rechazo?",
        "images": ["ATAOIII.jpg"]
    },
    "Break & Retest / Head & Shoulders Pattern": {
        "title": "Patrones Chartistas",
        "desc": "¿Ves una ruptura y retesteo o HCH?",
        "images": ["HEAD&SHOULDERS copy.jpg"]
    },
    "SOS": {
        "title": "Shift of Structure",
        "desc": "¿Hubo quiebre de estructura (BOS/CHoCH)?",
        "images": ["trend img.jpg"]
    },
    "Engulfing candlestick (30m, 1H, 2H, 4H)": {
        "title": "Vela Envolvente",
        "desc": "¿Hay una vela envolvente clara?",
        "images": ["ATAOIII.jpg"]
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
            # Solo suma si está True en checklist (que significa CONFIRMADO)
            if st.session_state.checklist.get(key, False):
                sec_score += pts
        section_scores[section] = sec_score
        total_score += sec_score
    return total_score, section_scores

def handle_toggle_change(key, section):
    # Lógica: Cuando tocas el toggle, activamos el modo confirmación para esa key
    current_val = st.session_state[key]
    
    if current_val: # Se encendió
        st.session_state.confirming_key = key # Activamos confirmación
        st.session_state.checklist[key] = False # Mantenemos apagado internamente hasta confirmar
    else: # Se apagó manualmente
        st.session_state.confirming_key = None
        st.session_state.checklist[key] = False
        # Liberar psych logic si aplica
        if "Round Psych Level" in key and st.session_state.psych_selected_in == section:
            st.session_state.psych_selected_in = None

def confirm_yes(key, section):
    st.session_state.checklist[key] = True # Confirmado
    st.session_state[key] = True # Asegurar visual
    st.session_state.confirming_key = None # Cerrar caja
    
    # Lógica especial Psych Level
    if "Round Psych Level" in key:
        st.session_state.psych_selected_in = section
        for sec in ["WEEKLY", "DAILY", "4H"]:
            if sec != section:
                other_key = f"{sec}_Round Psych Level"
                st.session_state.checklist[other_key] = False
                if other_key in st.session_state: st.session_state[other_key] = False

def confirm_no(key):
    st.session_state.checklist[key] = False # Rechazado
    st.session_state[key] = False # Apagar visualmente el toggle
    st.session_state.confirming_key = None # Cerrar caja

def get_local_image(filename):
    paths = [os.path.join("foto", filename), os.path.join("Foto", filename), filename]
    for p in paths:
        if os.path.exists(p): return p
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

    # --- LAYOUT PRINCIPAL ---
    main_col, side_col = st.columns([3, 1], gap="medium")

    # === COLUMNA IZQUIERDA ===
    with main_col:
        
        # 1. SUMMARY
        st.markdown('<div style="color:#e2e8f0; font-weight:700; margin-bottom:10px;">CONFLUENCE BREAKDOWN</div>', unsafe_allow_html=True)
        cards_html = '<div class="summary-grid">'
        for sec in ["WEEKLY", "DAILY", "4H", "2H, 1H, 30M", "ENTRY SIGNAL"]:
            val = sec_scores.get(sec, 0)
            cards_html += f'<div class="mini-card"><div class="mini-title">{sec}</div><div class="mini-val">{val}%</div></div>'
        cards_html += '</div>'
        st.markdown(cards_html, unsafe_allow_html=True)

        # 2. CHECKLIST
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
                    if label == "Round Psych Level" and st.session_state.psych_selected_in and st.session_state.psych_selected_in != sec_name:
                        disabled = True

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
                            # EL TOGGLE MAESTRO
                            st.toggle(
                                "x", key=key, 
                                label_visibility="collapsed",
                                disabled=disabled,
                                on_change=handle_toggle_change,
                                args=(key, sec_name)
                            )
                    
                    # --- CAJA DE CONFIRMACIÓN (TU PEDIDO ESPECIAL) ---
                    # Solo se muestra si este key específico está en modo confirmación
                    if st.session_state.confirming_key == key:
                        
                        st.markdown('<div class="confirmation-box">', unsafe_allow_html=True)
                        
                        # Datos de ayuda
                        if label in HELPER_DATA:
                            data = HELPER_DATA[label]
                            st.markdown(f"<div class='confirm-question'>{data['desc']}</div>", unsafe_allow_html=True)
                            
                            # Mostrar imágenes (soporta 1 o 2)
                            if "images" in data and data["images"]:
                                cols_img = st.columns(len(data["images"]))
                                for idx, img_name in enumerate(data["images"]):
                                    p = get_local_image(img_name)
                                    if p: 
                                        with cols_img[idx]:
                                            st.image(p, use_container_width=True)
                                    else:
                                        st.caption(f"Falta: {img_name}")
                        else:
                            st.markdown("<div class='confirm-question'>¿Confirmas esta condición?</div>", unsafe_allow_html=True)

                        st.markdown("<br>", unsafe_allow_html=True)
                        
                        # BOTONES YES / NO
                        # Usamos columnas para centrarlos
                        cb1, cb2, cb3, cb4 = st.columns([1, 2, 2, 1])
                        with cb2:
                            if st.button("YES", key=f"yes_{key}", type="primary"):
                                confirm_yes(key, sec_name)
                                st.rerun()
                        with cb3:
                            # Botón NO (Estilo rojo mediante key o css trick, aqui usaremos secondary standard)
                            if st.button("NO", key=f"no_{key}"):
                                confirm_no(key)
                                st.rerun()
                        
                        st.markdown('</div>', unsafe_allow_html=True)

                    if label != items[-1][0]:
                        st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)

    # === COLUMNA DERECHA ===
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
                st.toast("Abriendo modal...", icon="✅")

# ==============================================================================
# OTRAS PÁGINAS
# ==============================================================================
elif st.session_state.page == 'history':
    st.title("📖 Trading History")
elif st.session_state.page == 'dashboard':
    st.title("📊 Performance Dashboard")
elif st.session_state.page == 'ai_mentor':
    st.title("🤖 AI Mentor")
