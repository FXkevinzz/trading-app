import streamlit as st
import os
from datetime import datetime
import pytz
import google.generativeai as genai

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Set & Forget Ultimate", layout="wide", page_icon="🦁")

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    /* Estilos Generales */
    .stApp {background-color: #0E1117; color: white;}
    [data-testid="stSidebar"] {background-color: #262730 !important;}
    
    /* Contenedores */
    div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] > div[data-testid="stVerticalBlock"] {
        background-color: #161B22; 
        padding: 15px; 
        border-radius: 8px; 
        border: 1px solid #30363D;
    }
    
    /* Textos e Inputs */
    h1, h2, h3, p, span, label {color: white !important;}
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div>div {
        background-color: #0E1117 !important; 
        color: white !important; 
        border: 1px solid #464b5c;
    }
    
    /* Alertas */
    .open-session {background-color: #1f7a1f; color: white !important; padding: 10px; border-radius: 5px; text-align: center; font-weight: bold;}
    .closed-session {background-color: #5c0000; color: white !important; padding: 10px; border-radius: 5px; text-align: center; font-weight: bold;}
    .plan-box {border-left: 5px solid #4CAF50; padding: 15px; background-color: rgba(76, 175, 80, 0.1); border-radius: 5px; margin-top: 10px;}
    img { border-radius: 5px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIÓN IMAGEN ---
def mostrar_imagen(nombre_archivo, caption):
    links = {
        "bullish_engulfing.png": "https://forexbee.co/wp-content/uploads/2019/10/Bullish-Engulfing-Pattern-1.png",
        "morning_star.png": "https://a.c-dn.net/b/1XlqMQ/Morning-Star-Candlestick-Pattern_body_MorningStar.png.full.png",
        "hammer.png": "https://a.c-dn.net/b/2fPj5H/Hammer-Candlestick-Pattern_body_Hammer.png.full.png",
        "bearish_engulfing.png": "https://forexbee.co/wp-content/uploads/2019/10/Bearish-Engulfing-Pattern.png",
        "shooting_star.png": "https://a.c-dn.net/b/4hQ18X/Shooting-Star-Candlestick_body_ShootingStar.png.full.png"
    }
    ruta_local = f"fotos/{nombre_archivo}"
    if os.path.exists(ruta_local): st.image(ruta_local, caption=caption)
    elif nombre_archivo in links: st.image(links[nombre_archivo], caption=caption)
    else: st.warning(f"⚠️ Falta foto")

# --- BARRA LATERAL ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/7210/7210633.png", width=80)
    
    # SELECTOR DE MODO
    modo = st.radio("Modo de Operativa", ["Swing / Day (W-D-4H)", "Scalping (4H-2H-1H)
