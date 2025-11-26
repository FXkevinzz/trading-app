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

# --- 2. ESTILOS CSS PROFESIONALES (DARK FINTECH MEJORADO) ---
st.markdown("""
    <style>
    :root {
        --bg-color: #050505;
        --card-bg: #111111;
        --border-color: #333333;
        --accent-green: #00E676;
        --accent-red: #FF1744;
        --accent-yellow: #FFEA00;
        --accent-blue: #2979FF;
        --text-color: #E0E0E0;
    }

    /* GENERAL */
    .stApp { background-color: var(--bg-color); color: var(--text-color); }
    h1, h2, h3 { font-family: 'Helvetica Neue', sans-serif; font-weight: 700; letter-spacing: 0.05em; }
    
    /* INPUTS MEJORADOS */
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div, .stDateInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: #0a0a0a !important; 
        color: #fff !important; 
        border: 1px solid #444 !important;
        border-radius: 8px;
        padding: 10px;
    }
    
    /* SELECTOR DE MODO PROFESIONAL */
    .mode-selector-box {
        background: linear-gradient(145deg, #1a1a1a, #111111);
        border: 1px solid #333;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
        margin-bottom: 25px;
    }
    .mode-selector-title {
        font-size: 1.2rem;
        font-weight: bold;
        color: var(--accent-blue);
        margin-bottom: 15px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* 2x2 GRID BOXES */
    .strategy-box {
        background-color: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 10px;
        padding: 20px;
        height: 100%;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        transition: all 0.3s ease;
    }
    .strategy-box:hover { border-color: #555; box-shadow: 0 6px 12px rgba(0,0,0,0.5); }
    .strategy-header {
        font-size: 1.1rem; font-weight: 700; color: #aaa; text-transform: uppercase;
        margin-bottom: 15px; border-bottom: 2px solid #222; padding-bottom: 10px;
    }

    /* SCORE DASHBOARD (HUD) MEJORADO */
    .hud-container {
        display: flex; justify-content: space-between; align-items: center;
        background: #080808; border: 1px solid #333; border-radius: 15px;
        padding: 25px; margin-top: 30px; box-shadow: inset 0 0 20px rgba(0,0,0,0.8);
    }
    .hud-stat { text-align: center; }
    .hud-label { font-size: 0.9rem; color: #666; text-transform: uppercase; letter-spacing: 1px;}
    .hud-value-large { font-size: 2.5rem; font-weight: 900; background: -webkit-linear-gradient(eee, #888); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    
    /* MENSAJES DE ESTADO */
    .status-box { padding: 20px; border-radius: 10px; text-align: center; font-weight: bold; font-size: 1.2rem; box-shadow: 0 5px 15px rgba(0,0,0,0.2); }
    .status-sniper { background: rgba(0, 230, 118, 0.15); border: 2px solid var(--accent-green); color: var(--accent-green); }
    .status-warning { background: rgba(255, 234, 0, 0.15); border: 2px solid var(--accent-yellow); color: var(--accent-yellow); }
    .status-stop { background: rgba(255, 23, 68, 0.15); border: 2px solid var(--accent-red); color: var(--accent-red); }

    /* TABS PROFESIONALES */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #111 !important; border: 1px solid #333; border-radius: 5px; padding: 10px 20px;
    }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        background-color: #1a1a1a !important; color: white !important; 
        border: 1px solid var(--accent-blue) !important;
        border-bottom: 3px solid var(--accent-blue) !important;
        box-shadow: 0 0 10px rgba(41, 121, 255, 0.3);
    }
    
    /* CALENDARIO */
    .calendar-container { display: grid; grid-template-columns: repeat(7, 1fr); gap: 5px; margin-top: 10px; }
    .calendar-header { background: #1a1a1a; color: #bbb; text-align: center; padding: 5px; font-weight: bold; font-size: 0.8rem; }
    .calendar-day { min-height: 80px; background: #0e0e0e; padding: 5px; border: 1px solid #222; border-radius: 4px; display: flex; flex-direction: column; justify-content: space-between;}
    .day-val { text-align: right; font-weight: bold; }
    .win-text { color: var(--accent-green); } .loss-text { color: var(--accent-red); }
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
        st.markdown("<h1 style='text-align:center; color:var(--accent-blue)'>🦁 Trading Suite Pro</h1>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["INGRESAR", "REGISTRARSE"])
        with t1:
            u = st.text_input("Usuario")
            p = st.text_input("Password", type="password")
            if st.button("ACCEDER", type="primary", use_container_width=True):
                if verify_user(u, p): st.session_state.user = u; st.rerun()
                else: st.error("Error de acceso")
        with t2:
            nu = st.text_input("Nuevo Usuario")
            np = st.text_input("Nueva Password", type="password")
            if st.button("CREAR CUENTA", use_container_width=True):
                if nu and np: register_user(nu, np); st.success("Creado!"); st.rerun()

# --- 6. APP PRINCIPAL ---
def main_app():
    user = st.session_state.user
    if 'cal_date' not in st.session_state: st.session_state['cal_date'] = datetime.now()

    # SIDEBAR
    with st.sidebar:
        st.title(f"👤 {user.upper()}")
        if st.button("CERRAR SESIÓN", use_container_width=True): st.session_state.user = None; st.rerun()
        st.markdown("---")
        accs = get_user_accounts(user)
        sel_acc = st.selectbox("📂 CUENTA ACTIVA", accs)
        ini, act = get_balance(user, sel_acc)
        
        col_s = "#00E676" if act >= ini else "#FF1744"
        st.markdown(f"""
        <div style="background:linear-gradient(145deg, #1a1a1a, #000); padding:20px; border-radius:12px; border:1px solid #333; text-align:center; box-shadow: 0 4px 10px rgba(0,0,0,0.3);">
            <div style="color:#888; font-size:0.8rem; letter-spacing:1px; margin-bottom:5px;">BALANCE TOTAL</div>
            <div style="color:{col_s}; font-size:2rem; font-weight:900; text-shadow: 0 0 10px {col_s}40;">${act:,.2f}</div>
            <div style="color:#555; font-size:0.8rem; margin-top:5px">Capital Inicial: ${ini:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        with st.expander("➕ NUEVA CUENTA"):
            na = st.text_input("Nombre de Cuenta")
            nb = st.number_input("Capital Inicial ($)", value=10000.0, step=1000.0)
            if st.button("CREAR", use_container_width=True):
                if na: create_account(user, na, nb); st.rerun()

    # TABS PRINCIPALES
    t_op, t_reg, t_dash, t_cal = st.tabs(["🦁 COCKPIT OPERATIVO", "📝 BITÁCORA", "📊 ANALYTICS", "📅 CALENDARIO P&L"])

    # === 1. OPERATIVA (PROFESIONAL) ===
    with t_op:
        # BIBLIOTECA (Compacta)
        with st.expander("📘 REFERENCIA VISUAL DE PATRONES"):
            c_p1, c_p2 = st.columns(2)
            with c_p1:
                st.caption("🐂 Patrones Alcistas")
                c_a, c_b = st.columns(2)
                with c_a: mostrar_imagen("bullish_engulfing.png", "B. Engulfing")
                with c_b: mostrar_imagen("morning_star.png", "Morning Star")
            with c_p2:
                st.caption("🐻 Patrones Bajistas")
                c_c, c_d = st.columns(2)
                with c_c: mostrar_imagen("bearish_engulfing.png", "B. Engulfing")
                with c_d: mostrar_imagen("shooting_star.png", "Shooting Star")

        st.markdown("<br>", unsafe_allow_html=True)
        
        # --- SELECTOR DE MODO PROFESIONAL ---
        st.markdown("""
        <div class="mode-selector-box">
            <div class="mode-selector-title">⚡ CENTRO DE CONTROL DE ESTRATEGIA</div>
        </div>
        """, unsafe_allow_html=True)
        # Usamos columnas para centrar el radio button dentro de la caja visual
        c_ml, c_mm, c_mr = st.columns([1, 2, 1])
        with c_mm:
             modo = st.radio("", ["Swing (W-D-4H)", "Scalping (4H-2H-1H)"], horizontal=True, label_visibility="collapsed")

        st.markdown("<br>", unsafe_allow_html=True)

        # GRID LAYOUT 2x2
        r1_c1, r1_c2 = st.columns(2)
        r2_c1, r2_c2 = st.columns(2)

        if "Swing" in modo:
            # --- BLOQUE 1: MACRO (W) ---
            with r1_c1:
                with st.container():
                    st.markdown('<div class="strategy-box">', unsafe_allow_html=True)
                    st.markdown("<div class='strategy-header'>1. ANÁLISIS SEMANAL (W)</div>", unsafe_allow_html=True)
                    tw = st.selectbox("Tendencia W", ["Alcista", "Bajista"], key="tw")
                    st.divider()
                    w_sc = sum([st.checkbox("Rechazo AOI (+10%)", key="w1")*10, st.checkbox("Estructura Previa (+10%)", key="w2")*10, st.checkbox("Patrón Vela (+10%)", key="w3")*10, st.checkbox("EMA 50 (+5%)", key="w4")*5, st.checkbox("Nivel Psicológico (+5%)", key="w5")*5])
                    st.markdown('</div>', unsafe_allow_html=True)

            # --- BLOQUE 2: INTERMEDIO (D) ---
            with r1_c2:
                with st.container():
                    st.markdown('<div class="strategy-box">', unsafe_allow_html=True)
                    st.markdown("<div class='strategy-header'>2. ANÁLISIS DIARIO (D)</div>", unsafe_allow_html=True)
                    td = st.selectbox("Tendencia D", ["Alcista", "Bajista"], key="td")
                    st.divider()
                    d_sc = sum([st.checkbox("Rechazo AOI (+10%)", key="d1")*10, st.checkbox("Estructura Previa (+10%)", key="d2")*10, st.checkbox("Vela (+10%)", key="d3")*10, st.checkbox("Patrón (+10%)", key="d4")*10, st.checkbox("EMA 50 (+5%)", key="d5")*5])
                    st.markdown('</div>', unsafe_allow_html=True)

            # --- BLOQUE 3: EJECUCIÓN (4H) ---
            with r2_c1:
                with st.container():
                    st.markdown('<div class="strategy-box" style="margin-top:20px;">', unsafe_allow_html=True)
                    st.markdown("<div class='strategy-header'>3. EJECUCIÓN (4H)</div>", unsafe_allow_html=True)
                    t4 = st.selectbox("Tendencia 4H", ["Alcista", "Bajista"], key="t4")
                    st.divider()
                    h4_sc = sum([st.checkbox("Rechazo Vela (+10%)", key="h1")*10, st.checkbox("Patrón (+10%)", key="h2")*10, st.checkbox("En/Rechazo AOI (+5%)", key="h3")*5, st.checkbox("Estructura (+5%)", key="h4")*5, st.checkbox("EMA 50 (+5%)", key="h5")*5])
                    st.markdown('</div>', unsafe_allow_html=True)

            # --- BLOQUE 4: GATILLO ---
            with r2_c2:
                with st.container():
                    st.markdown('<div class="strategy-box" style="margin-top:20px;">', unsafe_allow_html=True)
                    st.markdown("<div class='strategy-header'>4. GATILLO FINAL & SINCRONÍA</div>", unsafe_allow_html=True)
                    if tw==td==t4: st.success("💎 TRIPLE ALINEACIÓN PERFECTA")
                    elif tw==td: st.info("✅ SWING SYNC (W+D)")
                    else: st.warning("⚠️ TENDENCIA MIXTA - RIESGO ALTO")
                    st.divider()
                    st.markdown("**Requisitos Obligatorios:**")
                    sos = st.checkbox("⚡ Shift of Structure")
                    eng = st.checkbox("🕯️ Vela Envolvente")
                    rr = st.checkbox("💰 Ratio > 1:2.5")
                    entry_score = sum([sos*10, eng*10])
                    total = w_sc + d_sc + h4_sc + entry_score
                    st.markdown('</div>', unsafe_allow_html=True)

        else: # SCALPING
            # --- BLOQUE 1 ---
            with r1_c1:
                with st.container():
                    st.markdown('<div class="strategy-box">', unsafe_allow_html=True)
                    st.markdown("<div class='strategy-header'>1. CONTEXTO MACRO (4H)</div>", unsafe_allow_html=True)
                    t4 = st.selectbox("Tendencia 4H", ["Alcista", "Bajista"], key="st4")
                    st.divider()
                    w_sc = sum([st.checkbox("AOI (+5%)", key="sc1")*5, st.checkbox("Estructura (+5%)", key="sc2")*5, st.checkbox("Patrón (+5%)", key="sc3")*5, st.checkbox("EMA 50 (+5%)", key="sc4")*5, st.checkbox("Psicológico (+5%)", key="sc5")*5])
                    st.markdown('</div>', unsafe_allow_html=True)
            # --- BLOQUE 2 ---
            with r1_c2:
                with st.container():
                    st.markdown('<div class="strategy-box">', unsafe_allow_html=True)
                    st.markdown("<div class='strategy-header'>2. CONTEXTO INTERMEDIO (2H)</div>", unsafe_allow_html=True)
                    t2 = st.selectbox("Tendencia 2H", ["Alcista", "Bajista"], key="st2")
                    st.divider()
                    d_sc = sum([st.checkbox("AOI (+5%)", key="sc6")*5, st.checkbox("Estructura (+5%)", key="sc7")*5, st.checkbox("Vela (+5%)", key="sc8")*5, st.checkbox("Patrón (+5%)", key="sc9")*5, st.checkbox("EMA 50 (+5%)", key="sc10")*5])
                    st.markdown('</div>', unsafe_allow_html=True)
            # --- BLOQUE 3 ---
            with r2_c1:
                with st.container():
                    st.markdown('<div class="strategy-box" style="margin-top:20px;">', unsafe_allow_html=True)
                    st.markdown("<div class='strategy-header'>3. EJECUCIÓN (1H)</div>", unsafe_allow_html=True)
                    t1 = st.selectbox("Tendencia 1H", ["Alcista", "Bajista"], key="st1")
                    st.divider()
                    h4_sc = sum([st.checkbox("Vela (+5%)", key="sc11")*5, st.checkbox("Patrón (+5%)", key="sc12")*5, st.checkbox("Estructura (+5%)", key="sc13")*5, st.checkbox("EMA 50 (+5%)", key="sc14")*5])
                    st.markdown('</div>', unsafe_allow_html=True)
            # --- BLOQUE 4 ---
            with r2_c2:
                with st.container():
                    st.markdown('<div class="strategy-box" style="margin-top:20px;">', unsafe_allow_html=True)
                    st.markdown("<div class='strategy-header'>4. GATILLO (M15) & SINCRONÍA</div>", unsafe_allow_html=True)
                    if t4==t2==t1: st.success("💎 TRIPLE ALINEACIÓN")
                    else: st.warning("⚠️ TENDENCIA MIXTA")
                    st.divider()
                    sos = st.checkbox("⚡ SOS M15")
                    eng = st.checkbox("🕯️ Entrada M15")
                    rr = st.checkbox("💰 Ratio > 1:2.5")
                    entry_score = sum([sos*10, eng*10])
                    total = w_sc + d_sc + h4_sc + entry_score + 15
                    st.markdown('</div>', unsafe_allow_html=True)

        # SECCION 3: SCORE DASHBOARD (HUD)
        st.markdown("<br>", unsafe_allow_html=True)
        
        valid = sos and eng and rr
        msg_header, msg_body, css_class = "", "", ""
        
        if not sos:
            msg_header, msg_body, css_class = "⛔ STOP", "Falta Shift of Structure (SOS)", "status-stop"
        elif not eng:
            msg_header, msg_body, css_class = "⚠️ CUIDADO", "Falta Vela de Entrada Válida", "status-warning"
        elif not rr:
            msg_header, msg_body, css_class = "💸 RIESGO", "El Ratio R:B no es suficiente (>1:2.5)", "status-warning"
        elif total >= 90:
            msg_header, msg_body, css_class = "💎 SNIPER ENTRY", "Setup de Alta Probabilidad. Ejecuta.", "status-sniper"
        elif total >= 60 and valid:
            msg_header, msg_body, css_class = "✅ EJECUTAR", "Setup Válido y Confirmado.", "status-sniper"
        else:
            msg_header, msg_body, css_class = "💤 ESPERAR", "Puntaje insuficiente. Paciencia.", "status-warning"

        # Renderizar HUD Profesional
        st.markdown(f"""
        <div class="hud-container">
            <div class="hud-stat">
                <div class="hud-label">PUNTAJE TOTAL ACUMULADO</div>
                <div class="hud-value-large">{total}%</div>
            </div>
            <div style="flex-grow:1; margin:0 30px;">
                <div class="status-box {css_class}">
                    <div>{msg_header}</div>
                    <div style="font-size:0.9rem; font-weight:normal; margin-top:5px; opacity:0.8;">{msg_body}</div>
                </div>
            </div>
            <div class="hud-stat">
                <div class="hud-label">GATILLOS</div>
                <div style="font-size:1.8rem; font-weight:bold; color:{'#00E676' if valid else '#FF1744'}">{'OK' if valid else 'PENDIENTE'}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Barra de progreso visual (limitada a 100% para que no de error el widget)
        visual_progress = min(total, 100)
        st.progress(visual_progress)
        if total > 100:
             st.caption(f"🚀 ¡Puntaje extraordinario! Superaste el 100% por {total-100} puntos.")

        # Plan de Trading Box
        if valid and total >= 60:
            sl = "5-7 pips" if "Swing" in modo else "3-5 pips"
            st.markdown(f"""
            <div style="margin-top:20px; padding:20px; border:1px solid var(--accent-green); border-radius:12px; background:rgba(0,230,118,0.05);">
                <div style="color:var(--accent-green); font-weight:bold; margin-bottom:10px; letter-spacing:1px;">📝 PLAN DE EJECUCIÓN ORDENADO:</div>
                <div style="display:flex; justify-content:space-between; font-size:1.1rem;">
                    <span>🛡️ <b>SL:</b> {sl} (Estructural)</span>
                    <span>🎯 <b>TP:</b> Liquidez Opuesta</span>
                    <span>🧠 <b>Riesgo:</b> 0.5% - 1%</span>
                </div>
            </div>
            """, unsafe_allow_html=True)


    # === 2. REGISTRO ===
    with t_reg:
        st.markdown("<h3 style='color:var(--accent-blue)'>📝 Bitácora de Operaciones</h3>", unsafe_allow_html=True)
        with st.form("reg"):
            c1,c2 = st.columns(2)
            dt = c1.date_input("Fecha Entrada", datetime.now())
            pr = c1.text_input("Par / Activo", "XAUUSD").upper()
            tp = c1.selectbox("Dirección", ["BUY", "SELL"])
            
            rs = c2.selectbox("Resultado Final", ["WIN", "LOSS", "BE"])
            mn = c2.number_input("Profit/Loss ($)", min_value=0.0, step=10.0, help="Introduce el valor positivo.")
            rt = c2.number_input("Ratio R:B Obtenido", value=2.5, step=0.1)
            nt = st.text_area("Notas / Psicología del Trade")
            
            if st.form_submit_button("💾 REGISTRAR TRADE EN BITÁCORA", use_container_width=True):
                real_mn = mn if rs=="WIN" else -mn if rs=="LOSS" else 0
                save_trade(user, sel_acc, {"Fecha":dt,"Par":pr,"Tipo":tp,"Resultado":rs,"Dinero":real_mn,"Ratio":rt,"Notas":nt})
                st.success("Trade registrado correctamente."); st.rerun()

    # === 3. DASHBOARD ===
    with t_dash:
        st.markdown("<h3 style='color:var(--accent-blue)'>📊 Analytics & Performance</h3>", unsafe_allow_html=True)
        df = load_trades(user, sel_acc)
        if not df.empty:
            k1,k2,k3,k4 = st.columns(4)
            wins = len(df[df["Resultado"]=="WIN"])
            net = df['Dinero'].sum()
            
            k1.markdown(f"<div style='background:#111; padding:15px; border-radius:10px; border:1px solid #333; text-align:center'><div style='color:#666; font-size:0.8rem'>BENEFICIO NETO</div><div style='font-size:1.8rem; font-weight:bold; color:{'#00E676' if net>=0 else '#FF1744'}'>${net:,.2f}</div></div>", unsafe_allow_html=True)
            k2.metric("WIN RATE", f"{(wins/len(df)*100):.1f}%")
            k3.metric("TOTAL TRADES", len(df))
            k4.metric("SALDO FINAL", f"${act:,.2f}")
            
            df["Eq"] = ini + df["Dinero"].cumsum()
            fig = go.Figure(go.Scatter(x=df["Fecha"], y=df["Eq"], line=dict(color='#2979FF', width=3), fill='tozeroy', fillcolor='rgba(41, 121, 255, 0.1)'))
            fig.update_layout(title="Curva de Crecimiento (Equity)", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#888'), xaxis=dict(showgrid=False), yaxis=dict(gridcolor='#222'))
            st.plotly_chart(fig, use_container_width=True)
        else: st.info("No hay datos suficientes para el análisis.")

    # === 4. CALENDARIO ===
    with t_cal:
        st.markdown("<h3 style='color:var(--accent-blue)'>📅 Calendario de P&L</h3>", unsafe_allow_html=True)
        c_p, c_t, c_n = st.columns([1,5,1])
        with c_p: 
            if st.button("⬅️ ANT", use_container_width=True): change_month(-1); st.rerun()
        with c_n: 
            if st.button("SIG ➡️", use_container_width=True): change_month(1); st.rerun()
            
        df = load_trades(user, sel_acc)
        html, y, m = render_cal_html(df)
        with c_t: st.markdown(f"<h3 style='text-align:center; color:#E0E0E0; margin:0; text-transform:uppercase; letter-spacing:2px;'>{calendar.month_name[m]} {y}</h3>", unsafe_allow_html=True)
        st.markdown(html, unsafe_allow_html=True)

if 'user' not in st.session_state: st.session_state.user = None
if st.session_state.user: main_app()
else: login_screen()
