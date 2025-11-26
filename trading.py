import streamlit as st
import pandas as pd
import os
import json
import calendar
from datetime import datetime
import plotly.graph_objects as go
import pytz

# --- 1. CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="Trading Pro Suite", layout="wide", page_icon="🦁")

# --- 2. ESTILOS CSS PROFESIONALES (DARK FINTECH) ---
st.markdown("""
    <style>
    :root {
        --bg-color: #050505;
        --card-bg: #111111;
        --border-color: #333333;
        --accent-green: #00E676;
        --accent-red: #FF1744;
        --accent-yellow: #FFEA00;
        --text-color: #E0E0E0;
    }

    /* GENERAL */
    .stApp { background-color: var(--bg-color); color: var(--text-color); }
    
    /* INPUTS */
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div, .stDateInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: #0a0a0a !important; 
        color: #fff !important; 
        border: 1px solid #444 !important;
        border-radius: 6px;
    }

    /* 2x2 GRID BOXES */
    .strategy-box {
        background-color: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 15px;
        height: 100%;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .strategy-header {
        font-size: 1.1rem;
        font-weight: 700;
        color: #888;
        text-transform: uppercase;
        margin-bottom: 15px;
        border-bottom: 1px solid #333;
        padding-bottom: 5px;
    }

    /* SCORE DASHBOARD (HUD) */
    .hud-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #000;
        border: 1px solid #333;
        border-radius: 12px;
        padding: 20px;
        margin-top: 20px;
    }
    .hud-stat { text-align: center; }
    .hud-label { font-size: 0.8rem; color: #666; text-transform: uppercase; }
    .hud-value { font-size: 1.5rem; font-weight: bold; }
    
    /* MENSAJES DE ESTADO (ALERTAS) */
    .status-sniper { 
        background: rgba(0, 230, 118, 0.1); 
        border: 1px solid var(--accent-green); 
        color: var(--accent-green); 
        padding: 15px; border-radius: 8px; text-align: center; font-weight: bold; font-size: 1.2rem;
    }
    .status-warning { 
        background: rgba(255, 234, 0, 0.1); 
        border: 1px solid var(--accent-yellow); 
        color: var(--accent-yellow); 
        padding: 15px; border-radius: 8px; text-align: center; font-weight: bold;
    }
    .status-stop { 
        background: rgba(255, 23, 68, 0.1); 
        border: 1px solid var(--accent-red); 
        color: var(--accent-red); 
        padding: 15px; border-radius: 8px; text-align: center; font-weight: bold;
    }

    /* CALENDARIO */
    .calendar-container { display: grid; grid-template-columns: repeat(7, 1fr); gap: 5px; margin-top: 10px; }
    .calendar-header { background: #1a1a1a; color: #bbb; text-align: center; padding: 5px; font-weight: bold; font-size: 0.8rem; }
    .calendar-day { min-height: 80px; background: #0e0e0e; padding: 5px; border: 1px solid #222; border-radius: 4px; display: flex; flex-direction: column; justify-content: space-between;}
    .day-val { text-align: right; font-weight: bold; }
    .win-text { color: var(--accent-green); } 
    .loss-text { color: var(--accent-red); }

    /* TABS */
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        background-color: #222 !important; color: white !important; border-top: 2px solid var(--accent-green) !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. GESTIÓN DE DATOS ---
DATA_DIR = "user_data"
IMG_DIR = "fotos"
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
USERS_FILE = os.path.join(DATA_DIR, "users.json")
ACCOUNTS_FILE = os.path.join(DATA_DIR, "accounts_config.json")

def load_json(fp): return json.load(open(fp)) if os.path.exists(fp) else {}
def save_json(fp, data): json.dump(data, open(fp, "w"))
def verify_user(u, p): d = load_json(USERS_FILE); return u in d and d[u] == p
def register_user(u, p): d = load_json(USERS_FILE); d[u] = p; save_json(USERS_FILE, d)

def get_user_accounts(u): d = load_json(ACCOUNTS_FILE); return list(d.get(u, {}).keys()) if u in d else ["Principal"]
def create_account(u, name, bal):
    d = load_json(ACCOUNTS_FILE)
    if u not in d: d[u] = {}
    if name not in d[u]: d[u][name] = bal; save_json(ACCOUNTS_FILE, d)

def get_balance(u, acc):
    d = load_json(ACCOUNTS_FILE)
    ini = d.get(u, {}).get(acc, 0)
    fp = os.path.join(DATA_DIR, u, f"{acc}.csv".replace(" ", "_"))
    pnl = pd.read_csv(fp)["Dinero"].sum() if os.path.exists(fp) else 0
    return ini, ini + pnl

def save_trade(u, acc, data):
    folder = os.path.join(DATA_DIR, u)
    if not os.path.exists(folder): os.makedirs(folder)
    fp = os.path.join(folder, f"{acc}.csv".replace(" ", "_"))
    df = pd.read_csv(fp) if os.path.exists(fp) else pd.DataFrame(columns=["Fecha","Par","Tipo","Resultado","Dinero","Ratio","Notas"])
    df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
    df.to_csv(fp, index=False)

def load_trades(u, acc):
    fp = os.path.join(DATA_DIR, u, f"{acc}.csv".replace(" ", "_"))
    return pd.read_csv(fp) if os.path.exists(fp) else pd.DataFrame(columns=["Fecha","Par","Tipo","Resultado","Dinero","Ratio","Notas"])

# --- 4. FUNCIONES VISUALES ---
def mostrar_imagen(nombre, caption):
    local = os.path.join(IMG_DIR, nombre)
    if os.path.exists(local): st.image(local, caption=caption, use_container_width=True)
    else:
        urls = {
            "bullish_engulfing.png": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/Candlestick_Pattern_Bullish_Engulfing.png/320px-Candlestick_Pattern_Bullish_Engulfing.png",
            "bearish_engulfing.png": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/19/Candlestick_Pattern_Bearish_Engulfing.png/320px-Candlestick_Pattern_Bearish_Engulfing.png",
            "morning_star.png": "https://a.c-dn.net/b/1XlqMQ/Morning-Star-Candlestick-Pattern_body_MorningStar.png.full.png",
            "shooting_star.png": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/67/Candlestick_Pattern_Shooting_Star.png/320px-Candlestick_Pattern_Shooting_Star.png"
        }
        if nombre in urls: st.image(urls[nombre], caption=caption, use_container_width=True)

def change_month(delta):
    d = st.session_state.get('cal_date', datetime.now())
    m, y = d.month + delta, d.year
    if m > 12: m, y = 1, y+1
    elif m < 1: m, y = 12, y-1
    st.session_state['cal_date'] = d.replace(year=y, month=m, day=1)

def render_cal_html(df):
    d = st.session_state.get('cal_date', datetime.now())
    y, m = d.year, d.month
    
    data = {}
    if not df.empty:
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        df_m = df[(df['Fecha'].dt.year==y) & (df['Fecha'].dt.month==m)]
        data = df_m.groupby(df['Fecha'].dt.day)['Dinero'].sum().to_dict()

    cal = calendar.Calendar(firstweekday=0)
    html = '<div class="calendar-container">'
    for h in ["LUN","MAR","MIÉ","JUE","VIE","SÁB","DOM"]: html += f'<div class="calendar-header">{h}</div>'
    
    for week in cal.monthdayscalendar(y, m):
        for day in week:
            if day == 0: html += '<div class="calendar-day" style="opacity:0; border:none;"></div>'
            else:
                val = data.get(day, 0)
                txt = f"${val:,.0f}" if val != 0 else ""
                cls = "win-text" if val > 0 else "loss-text" if val < 0 else "be-text"
                bg = "rgba(0,230,118,0.1)" if val > 0 else "rgba(255,23,68,0.1)" if val < 0 else "#0e0e0e"
                border = "#00E676" if val > 0 else "#FF1744" if val < 0 else "#333"
                html += f'<div class="calendar-day" style="background:{bg}; border:1px solid {border}"><div style="color:#666; font-size:0.8em">{day}</div><div class="{cls} day-val">{txt}</div></div>'
    html += '</div>'
    return html, y, m

# --- 5. LOGIN ---
def login_screen():
    c1,c2,c3 = st.columns([1,1,1])
    with c2:
        st.markdown("<h1 style='text-align:center'>🦁 Trading Suite</h1>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["Ingresar", "Registrarse"])
        with t1:
            u = st.text_input("Usuario")
            p = st.text_input("Password", type="password")
            if st.button("Entrar", type="primary"):
                if verify_user(u, p): st.session_state.user = u; st.rerun()
                else: st.error("Error")
        with t2:
            nu = st.text_input("Nuevo Usuario")
            np = st.text_input("Nueva Password", type="password")
            if st.button("Crear"):
                if nu and np: register_user(nu, np); st.success("Creado!"); st.rerun()

# --- 6. APP PRINCIPAL ---
def main_app():
    user = st.session_state.user
    if 'cal_date' not in st.session_state: st.session_state['cal_date'] = datetime.now()

    # SIDEBAR
    with st.sidebar:
        st.title(f"👤 {user}")
        if st.button("Cerrar Sesión"): st.session_state.user = None; st.rerun()
        st.markdown("---")
        accs = get_user_accounts(user)
        sel_acc = st.selectbox("📂 Cuenta Activa", accs)
        ini, act = get_balance(user, sel_acc)
        
        col_s = "#00E676" if act >= ini else "#FF1744"
        st.markdown(f"""
        <div style="background:#111; padding:20px; border-radius:10px; border:1px solid #333; text-align:center">
            <div style="color:#888; font-size:0.8rem; letter-spacing:1px;">SALDO ACTUAL</div>
            <div style="color:{col_s}; font-size:1.8rem; font-weight:bold">${act:,.2f}</div>
            <div style="color:#555; font-size:0.8rem; margin-top:5px">Inicial: ${ini:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        with st.expander("➕ Nueva Cuenta"):
            na = st.text_input("Nombre")
            nb = st.number_input("Saldo", value=10000.0)
            if st.button("Crear"):
                if na: create_account(user, na, nb); st.rerun()

    # PESTAÑAS
    t_op, t_reg, t_dash, t_cal = st.tabs(["🦁 OPERATIVA", "📝 REGISTRO", "📊 DASHBOARD", "📅 CALENDARIO"])

    # === 1. OPERATIVA (2x2 GRID & SCORE HUD) ===
    with t_op:
        # SECCION 1: BIBLIOTECA DE PATRONES (Separada)
        with st.expander("📘 Biblioteca de Patrones (Referencia Visual)"):
            c_p1, c_p2 = st.columns(2)
            with c_p1:
                st.markdown("**Patrones Alcistas**")
                c_a, c_b = st.columns(2)
                with c_a: mostrar_imagen("bullish_engulfing.png", "Bullish Engulfing")
                with c_b: mostrar_imagen("morning_star.png", "Morning Star")
            with c_p2:
                st.markdown("**Patrones Bajistas**")
                c_c, c_d = st.columns(2)
                with c_c: mostrar_imagen("bearish_engulfing.png", "Bearish Engulfing")
                with c_d: mostrar_imagen("shooting_star.png", "Shooting Star")

        # SECCION 2: OPERATIVA 2x2
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Selector de Modo (Centrado)
        c_mode_l, c_mode_m, c_mode_r = st.columns([1,2,1])
        with c_mode_m:
            modo = st.radio("Modo de Estrategia", ["Swing (W-D-4H)", "Scalping (4H-2H-1H)"], horizontal=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # GRID LAYOUT (FILA 1)
        r1_c1, r1_c2 = st.columns(2)
        
        # GRID LAYOUT (FILA 2)
        r2_c1, r2_c2 = st.columns(2)

        if "Swing" in modo:
            # --- BLOQUE 1: MACRO (W) ---
            with r1_c1:
                with st.container(border=True):
                    st.markdown("<div class='strategy-header'>1. Semanal (W)</div>", unsafe_allow_html=True)
                    tw = st.selectbox("Tendencia W", ["Alcista", "Bajista"], key="tw")
                    st.divider()
                    w_sc = sum([
                        st.checkbox("Rechazo AOI (+10%)", key="w1")*10,
                        st.checkbox("Estructura Previa (+10%)", key="w2")*10,
                        st.checkbox("Patrón Vela (+10%)", key="w3")*10,
                        st.checkbox("EMA 50 (+5%)", key="w4")*5,
                        st.checkbox("Nivel Psicológico (+5%)", key="w5")*5
                    ])

            # --- BLOQUE 2: INTERMEDIO (D) ---
            with r1_c2:
                with st.container(border=True):
                    st.markdown("<div class='strategy-header'>2. Diario (D)</div>", unsafe_allow_html=True)
                    td = st.selectbox("Tendencia D", ["Alcista", "Bajista"], key="td")
                    st.divider()
                    d_sc = sum([
                        st.checkbox("Rechazo AOI (+10%)", key="d1")*10,
                        st.checkbox("Estructura Previa (+10%)", key="d2")*10,
                        st.checkbox("Vela (+10%)", key="d3")*10,
                        st.checkbox("Patrón (+10%)", key="d4")*10,
                        st.checkbox("EMA 50 (+5%)", key="d5")*5
                    ])

            # --- BLOQUE 3: EJECUCIÓN (4H) ---
            with r2_c1:
                with st.container(border=True):
                    st.markdown("<div class='strategy-header'>3. Ejecución (4H)</div>", unsafe_allow_html=
