import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
import os
from PIL import Image

# ==============================================================================
# 1. CONFIGURACIÓN VISUAL (ESTILO DARK NAVY "THE PERFECT TRADE")
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

        /* --- CONTENEDOR DE LA TARJETA (CHECKLIST) --- */
        div[data-testid="stBorderDomWrapper"] {
            background-color: #1e293b; /* Slate 800 */
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
        }

        /* --- HEADER DE SECCIÓN --- */
        .section-header-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 25px;
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
            color: #34d399; /* Verde esmeralda */
        }

        /* --- TOGGLES Y TEXTO --- */
        .toggle-label {
            font-size: 0.95rem;
            font-weight: 600;
            color: #e2e8f0;
        }

        .points-text {
            color: #34d399;
            font-weight: 700;
            font-size: 0.85rem;
        }
        
        .points-text-disabled {
            color: #64748b;
            font-weight: 600;
            font-size: 0.85rem;
        }

        /* --- PANEL DERECHO (SCORE FLOTANTE) --- */
        .sticky-score-card {
            background: linear-gradient(180deg, #115e59 0%, #0f172a 100%);
            border: 1px solid #14b8a6;
            border-radius: 16px;
            padding: 30px;
            text-align: center;
            position: sticky;
            top: 20px;
        }
        
        .score-big-val {
            font-size: 4.5rem;
            font-weight: 900;
            color: #fff;
            line-height: 1;
        }
        
        /* --- AYUDA VISUAL (ALERTA DESPLEGABLE) --- */
        .visual-helper-box {
            background-color: #111827; /* Fondo más oscuro */
            border: 1px solid #374151;
            border-left: 4px solid #10b981; /* Borde verde a la izquierda */
            border-radius: 8px;
            padding: 15px;
            margin-top: 10px;
            margin-bottom: 15px;
            animation: fadeIn 0.3s ease-in-out;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-5px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .helper-title {
            color: #10b981;
            font-weight: 700;
            font-size: 0.9rem;
            margin-bottom: 5px;
        }
        
        .helper-text {
            color: #cbd5e1;
            font-size: 0.9rem;
            line-height: 1.4;
        }

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
# 2. CONFIGURACIÓN DE ESTRATEGIA Y AYUDAS VISUALES
# ==============================================================================

if 'page' not in st.session_state: st.session_state.page = 'checklist'
if 'checklist' not in st.session_state: st.session_state.checklist = {}
if 'psych_selected_in' not in st.session_state: st.session_state.psych_selected_in = None 

# --- DICCIONARIO DE AYUDAS LIMPIO ---
HELPER_DATA = {
    "Trend": {
        "title": "Estructura de Mercado",
        "desc": "¿Tu estructura de mercado alcista o bajista se ve así?\nBusca Altos Más Altos (HH) y Bajos Más Altos (HL) para compras, o viceversa.",
        "img": "trend.png" 
    },
    "At AOI / Rejected": {
        "title": "Zona de Interés (AOI)",
        "desc": "¿El precio está tocando o dentro de la zona marcada?\nRecuerda: Si el precio está flotando lejos de la zona, NO es válido.",
        "img": "aoi.png"
    },
    "Touching EMA": {
        "title": "Rechazo Dinámico (50 EMA)",
        "desc": "¿El precio está tocando o rechazando la línea de la EMA 50 en este momento?",
        "img": "ema.png"
    },
    "Round Psych Level": {
        "title": "Nivel Psicológico",
        "desc": "¿Hay un número redondo cerca (ej. 1.5000, 150.00, .500)?\nLos bancos usan estos niveles como imanes.",
        "img": "psych.png"
    },
    "Rejection Structure": {
        "title": "Estructura Previa",
        "desc": "¿El precio está rebotando en un Alto o Bajo anterior que ahora actúa como soporte/resistencia?",
        "img": "structure.png"
    },
    "Candlestick Rejection": {
        "title": "Patrón de Velas",
        "desc": "¿Ves patrones de rechazo claros como Pinbars (Martillo), Dojis o Envolventes en la zona?",
        "img": "candles.png"
    },
    "Break & Retest": {
        "title": "Ruptura y Retesteo",
        "desc": "¿El precio rompió la zona y regresó para probarla antes de continuar?",
        "img": "retest.png"
    },
    "SOS (Shift of Structure)": {
        "title": "Cambio de Estructura (SOS)",
        "desc": "¿En temporalidad menor, el precio rompió el último alto/bajo validando el cambio de tendencia?",
        "img": "sos.png"
    },
    "Engulfing candlestick": {
        "title": "Vela Gatillo",
        "desc": "¿Tienes una vela envolvente clara que confirme la entrada?",
        "img": "engulfing.png"
    }
}

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

def get_local_image(filename):
    """Busca la imagen en la carpeta 'foto'."""
    path = os.path.join("foto", filename)
    if os.path.exists(path):
        return path
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

    # --- LAYOUT PRINCIPAL: 2 COLUMNAS (Checklist Izq | Score Der) ---
    main_col, side_col = st.columns([3, 1], gap="large")

    # === COLUMNA IZQUIERDA: EL CHECKLIST ===
    with main_col:
        for sec_name, items in STRATEGY.items():
            current_sec_score = sec_scores.get(sec_name, 0)
            
            # CAJA CONTENEDORA
            with st.container(border=True):
                # HEADER
                st.markdown(f"""
                <div class="section-header-row">
                    <div class="section-title">{sec_name}</div>
                    <div class="section-score">{current_sec_score}%</div>
                </div>
                """, unsafe_allow_html=True)
                
                # LISTA DE TOGGLES
                for label, pts in items:
                    key = f"{sec_name}_{label}"
                    
                    # Logica bloqueo
                    disabled = False
                    if label == "Round Psych Level":
                        if st.session_state.psych_selected_in and st.session_state.psych_selected_in != sec_name:
                            disabled = True

                    # FILA FLEX
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
                    
                    # --- VISUAL HELPER PARA TODOS ---
                    # Se activa si el toggle está ON y existe ayuda para ese label
                    if val and label in HELPER_DATA:
                        data = HELPER_DATA[label]
                        
                        # Buscamos si existe imagen en la carpeta 'foto'
                        img_path = get_local_image(data['img'])
                        
                        # Renderizamos la caja de ayuda
                        st.markdown(f"""
                        <div class="visual-helper-box">
                            <div class="helper-title">👁️ {data['title']}</div>
                            <div class="helper-text">{data['desc']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Si existe la imagen, la mostramos
                        if img_path:
                            st.image(img_path, use_container_width=True)

                    # Separador visual
                    if label != items[-1][0]:
                        st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)

    # === COLUMNA DERECHA: SCORE + GUARDAR (FIJO) ===
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
