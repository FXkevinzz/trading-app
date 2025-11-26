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

# --- 2. ESTILOS CSS DINÁMICOS (CLARO & OSCURO) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');

    /* === PALETA DE COLORES INTELIGENTE === */
    /* Por defecto (MODO CLARO - Clean Fintech) */
    :root {
        --bg-main: #f1f5f9;
        --bg-card: #ffffff;
        --bg-sidebar: #0f172a; /* Sidebar siempre oscura para contraste profesional */
        --text-main: #0f172a;
        --text-card: #0f172a;
        --text-muted: #64748b;
        --border-color: #e2e8f0;
        --accent-blue: #2563eb;
        --accent-green: #10b981;
        --accent-red: #ef4444;
        --shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        --input-bg: #ffffff;
        --tab-bg: #ffffff;
        --tab-text: #64748b;
    }

    /* Detección automática de MODO OSCURO (Dark Navy) */
    @media (prefers-color-scheme: dark) {
        :root {
            --bg-main: #0f172a;       /* Vuelve el Azul Profundo */
            --bg-card: #1e293b;       /* Tarjetas Azul Acero */
            --bg-sidebar: #020617;    /* Sidebar casi negra */
            --text-main: #f8fafc;     /* Texto Blanco Hielo */
            --text-card: #f8fafc;
            --text-muted: #94a3b8;    /* Texto Gris Azulado */
            --border-color: #334155;  /* Bordes sutiles oscuros */
            --accent-blue: #3b82f6;   /* Azul más brillante */
            --accent-green: #34d399;  
            --accent-red: #f87171;    
            --shadow: 0 4px 6px -1px rgba(0,0,0,0.3);
            --input-bg: #1e293b;
            --tab-bg: #1e293b;
            --tab-text: #94a3b8;
        }
    }

    /* === APLICACIÓN DE ESTILOS === */
    
    /* Estructura General */
    .stApp {
        background-color: var(--bg-main);
        color: var(--text-main);
        font-family: 'Inter', sans-serif;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: var(--bg-sidebar);
        border-right: 1px solid var(--border-color);
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: #f8fafc !important; }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label { color: #94a3b8 !important; }

    /* Tarjetas (Cards) */
    .strategy-box {
        background-color: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 20px;
        box-shadow: var(--shadow);
        height: 100%;
    }
    
    /* Encabezados de Sección */
    .section-title {
        color: var(--accent-blue);
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 15px;
        border-bottom: 2px solid var(--border-color);
        padding-bottom: 10px;
    }

    /* Inputs, Selects y Áreas de texto */
    .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] > div, .stDateInput input, .stTextArea textarea {
        background-color: var(--input-bg) !important;
        color: var(--text-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px;
    }
    /* Corrección de iconos en selects */
    .stSelectbox svg, .stDateInput svg { fill: var(--text-muted) !important; }
    /* Textos de ayuda en inputs */
    .stNumberInput div[data-baseweb="input"] { color: var(--text-card); }

    /* Pestañas (Tabs) Tipo Cápsula */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; background: transparent; padding-bottom: 10px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: var(--tab-bg) !important;
        border: 1px solid var(--border-color);
        border-radius: 25px !important;
        color: var(--tab-text) !important;
        font-weight: 600;
        padding: 0 25px !important;
        box-shadow: var(--shadow);
        transition: all 0.3s ease;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: var(--accent-blue) !important;
        color: white !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4);
    }
    .stTabs [data-baseweb="tab-highlight"] { display: none; }

    /* HUD Dashboard (Puntaje) */
    .hud-container {
        background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-main) 100%);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 25px;
        margin-top: 20px;
        box-shadow: var(--shadow);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .hud-label { color: var(--text-muted); font-size: 0.8rem; font-weight: 700; letter-spacing: 1px; }
    .hud-value { color: var(--text-card); font-size: 2.5rem; font-weight: 800; line-height: 1; }

    /* Estados / Alertas */
    .status-sniper { background-color: rgba(16, 185, 129, 0.15); color: var(--accent-green); border: 1px solid var(--accent-green); padding: 12px; border-radius: 8px; font-weight: bold; text-align: center;}
    .status-warning { background-color: rgba(250, 204, 21, 0.15); color: #d97706; border: 1px solid #facc15; padding: 12px; border-radius: 8px; font-weight: bold; text-align: center;}
    .status-stop { background-color: rgba(239, 68, 68, 0.15); color: var(--accent-red); border: 1px solid var(--accent-red); padding: 12px; border-radius: 8px; font-weight: bold; text-align: center;}

    /* Checkboxes */
    .stCheckbox label p { color: var(--text-card) !important; }

    /* Calendario */
    .calendar-header { color: var(--text-muted); font-weight: bold; font-size: 0.8rem; text-align: center; }
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
    if name not in d[u]: d[u][name] = bal; save_json(ACCOUNTS_FILE, d); save_trade(u, name, None, init=True)

def get_balance_data(u, acc):
    d = load_json(ACCOUNTS_FILE)
    ini = d.get(u, {}).get(acc, 0.0)
    fp = os.path.join(DATA_DIR, u, f"{acc}.csv".replace(" ", "_"))
    df = pd.read_csv(fp) if os.path.exists(fp) else pd.DataFrame()
    pnl = df["Dinero"].sum() if not df.empty else 0
    return ini, ini + pnl, df

def save_trade(u, acc, data, init=False):
    folder = os.path.join(DATA_DIR, u)
    if not os.path.exists(folder): os.makedirs(folder)
    fp = os.path.join(folder, f"{acc}.csv".replace(" ", "_"))
    if init and not os.path.exists(fp):
        pd.DataFrame(columns=["Fecha","Par","Tipo","Resultado","Dinero","Ratio","Notas"]).to_csv(fp, index=False)
        return
    if not init:
        df = pd.read_csv(fp) if os.path.exists(fp) else pd.DataFrame(columns=["Fecha","Par","Tipo","Resultado","Dinero","Ratio","Notas"])
        df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
        df.to_csv(fp, index=False)

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
    html = '<div style="display:grid; grid-template-columns:repeat(7, 1fr); gap:8px; margin-top:15px;">'
    for h in ["LUN","MAR","MIÉ","JUE","VIE","SÁB","DOM"]: 
        html += f'<div class="calendar-header">{h}</div>'
    
    for week in cal.monthdayscalendar(y, m):
        for day in week:
            if day == 0: html += '<div style="opacity:0;"></div>'
            else:
                val = data.get(day, 0)
                txt = f"${val:,.0f}" if val != 0 else ""
                
                # Colores adaptables (CSS Variables)
                bg = "var(--bg-card)"
                border = "var(--border-color)"
                col = "var(--text-card)"
                
                if val > 0:
                    bg = "rgba(16, 185, 129, 0.15)"; border = "var(--accent-green)"; col = "var(--accent-green)"
                elif val < 0:
                    bg = "rgba(239, 68, 68, 0.15)"; border = "var(--accent-red)"; col = "var(--accent-red)"

                html += f'''
                <div style="background:{bg}; border:1px solid {border}; border-radius:8px; min-height:80px; padding:10px; display:flex; flex-direction:column; justify-content:space-between;">
                    <div style="color:var(--text-muted); font-size:0.8rem; font-weight:bold;">{day}</div>
                    <div style="color:{col}; font-weight:bold; text-align:right;">{txt}</div>
                </div>'''
    html += '</div>'
    return html, y, m

# --- 5. LOGIN ---
def login_screen():
    c1,c2,c3 = st.columns([1,1,1])
    with c2:
        st.markdown("<h1 style='text-align:center; color:var(--accent-blue);'>🦁 Trading Suite</h1>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["INGRESAR", "REGISTRARSE"])
        with t1:
            u = st.text_input("Usuario")
            p = st.text_input("Password", type="password")
            if st.button("ACCEDER", type="primary", use_container_width=True):
                if verify_user(u, p): st.session_state.user = u; st.rerun()
                else: st.error("Datos incorrectos")
        with t2:
            nu = st.text_input("Nuevo Usuario")
            np = st.text_input("Nueva Password", type="password")
            if st.button("CREAR CUENTA", use_container_width=True):
                if nu and np: register_user(nu, np); st.success("Creado!"); st.rerun()

# --- 6. APP PRINCIPAL ---
def main_app():
    user = st.session_state.user
    if 'cal_date' not in st.session_state: st.session_state['cal_date'] = datetime.now()

    # --- SIDEBAR ---
    with st.sidebar:
        st.title(f"👤 {user.upper()}")
        if st.button("CERRAR SESIÓN", use_container_width=True): st.session_state.user = None; st.rerun()
        st.markdown("---")
        
        accs = get_user_accounts(user)
        sel_acc = st.selectbox("📂 CUENTA ACTIVA", accs)
        ini, act, df = get_balance_data(user, sel_acc)
        
        col_s = "#10b981" if act >= ini else "#ef4444"
        st.markdown(f"""
        <div style="background:rgba(255,255,255,0.05); padding:20px; border-radius:12px; border:1px solid rgba(255,255,255,0.1); text-align:center;">
            <div style="color:#94a3b8; font-size:0.8rem; letter-spacing:1px; margin-bottom:5px;">BALANCE TOTAL</div>
            <div style="color:{col_s}; font-size:2rem; font-weight:900;">${act:,.2f}</div>
            <div style="color:#64748b; font-size:0.8rem; margin-top:5px">Inicial: ${ini:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        with st.expander("➕ NUEVA CUENTA"):
            na = st.text_input("Nombre de Cuenta")
            nb = st.number_input("Capital Inicial ($)", value=100.0, step=100.0)
            if st.button("CREAR", use_container_width=True):
                if na: create_account(user, na, nb); st.rerun()

    # --- PESTAÑAS PRINCIPALES ---
    t_op, t_reg, t_dash, t_cal = st.tabs(["🦁 OPERATIVA", "📝 BITÁCORA", "📊 ANALYTICS", "📅 CALENDARIO"])

    # === 1. OPERATIVA ===
    with t_op:
        with st.expander("📘 GUÍA VISUAL DE PATRONES"):
            c1, c2 = st.columns(2)
            with c1:
                st.info("🐂 ALCISTAS")
                ca, cb = st.columns(2)
                with ca: mostrar_imagen("bullish_engulfing.png", "B. Engulfing")
                with cb: mostrar_imagen("morning_star.png", "Morning Star")
            with c2:
                st.info("🐻 BAJISTAS")
                cc, cd = st.columns(2)
                with cc: mostrar_imagen("bearish_engulfing.png", "B. Engulfing")
                with cd: mostrar_imagen("shooting_star.png", "Shooting Star")

        st.markdown("<br>", unsafe_allow_html=True)
        
        # Selector de Modo
        st.markdown("""
        <div style="background:var(--bg-card); padding:15px; border-radius:10px; border:1px solid var(--border-color); text-align:center; margin-bottom:20px; box-shadow: var(--shadow);">
            <h4 style="margin:0; color:var(--accent-blue); text-transform:uppercase; letter-spacing:1px;">⚡ CONFIGURACIÓN DE ESTRATEGIA</h4>
        </div>
        """, unsafe_allow_html=True)
        
        c_ml, c_mm, c_mr = st.columns([1, 2, 1])
        with c_mm:
             modo = st.radio("", ["Swing (W-D-4H)", "Scalping (4H-2H-1H)"], horizontal=True, label_visibility="collapsed")

        # GRID 2x2
        r1_c1, r1_c2 = st.columns(2)
        r2_c1, r2_c2 = st.columns(2)

        total = 0
        sos, eng, rr = False, False, False

        if "Swing" in modo:
            with r1_c1:
                st.markdown('<div class="strategy-box">', unsafe_allow_html=True)
                st.markdown("<div class='section-title'>1. SEMANAL (W)</div>", unsafe_allow_html=True)
                tw = st.selectbox("Tendencia W", ["Alcista", "Bajista"], key="tw")
                st.divider()
                w_sc = sum([st.checkbox("AOI (+10%)", key="w1")*10, st.checkbox("Estructura (+10%)", key="w2")*10, st.checkbox("Patrón (+10%)", key="w3")*10, st.checkbox("EMA 50 (+5%)", key="w4")*5, st.checkbox("Psicológico (+5%)", key="w5")*5])
                st.markdown('</div>', unsafe_allow_html=True)
            with r1_c2:
                st.markdown('<div class="strategy-box">', unsafe_allow_html=True)
                st.markdown("<div class='section-title'>2. DIARIO (D)</div>", unsafe_allow_html=True)
                td = st.selectbox("Tendencia D", ["Alcista", "Bajista"], key="td")
                st.divider()
                d_sc = sum([st.checkbox("AOI (+10%)", key="d1")*10, st.checkbox("Estructura (+10%)", key="d2")*10, st.checkbox("Vela (+10%)", key="d3")*10, st.checkbox("Patrón (+10%)", key="d4")*10, st.checkbox("EMA 50 (+5%)", key="d5")*5])
                st.markdown('</div>', unsafe_allow_html=True)
            with r2_c1:
                st.markdown('<div class="strategy-box" style="margin-top:20px;">', unsafe_allow_html=True)
                st.markdown("<div class='section-title'>3. EJECUCIÓN (4H)</div>", unsafe_allow_html=True)
                t4 = st.selectbox("Tendencia 4H", ["Alcista", "Bajista"], key="t4")
                st.divider()
                h4_sc = sum([st.checkbox("Vela (+10%)", key="h1")*10, st.checkbox("Patrón (+10%)", key="h2")*10, st.checkbox("AOI (+5%)", key="h3")*5, st.checkbox("Estructura (+5%)", key="h4")*5, st.checkbox("EMA 50 (+5%)", key="h5")*5])
                st.markdown('</div>', unsafe_allow_html=True)
            with r2_c2:
                st.markdown('<div class="strategy-box" style="margin-top:20px;">', unsafe_allow_html=True)
                st.markdown("<div class='section-title'>4. GATILLO FINAL</div>", unsafe_allow_html=True)
                if tw==td==t4: st.success("💎 TRIPLE ALINEACIÓN")
                elif tw==td: st.info("✅ SWING SYNC")
                else: st.warning("⚠️ TENDENCIA MIXTA")
                st.divider()
                sos = st.checkbox("⚡ Shift of Structure")
                eng = st.checkbox("🕯️ Vela Envolvente")
                rr = st.checkbox("💰 Ratio > 1:2.5")
                entry_score = sum([sos*10, eng*10])
                total = w_sc + d_sc + h4_sc + entry_score
                st.markdown('</div>', unsafe_allow_html=True)

        else: # Scalping
            with r1_c1:
                st.markdown('<div class="strategy-box">', unsafe_allow_html=True)
                st.markdown("<div class='section-title'>1. CONTEXTO (4H)</div>", unsafe_allow_html=True)
                t4 = st.selectbox("Tendencia 4H", ["Alcista", "Bajista"], key="st4")
                st.divider()
                w_sc = sum([st.checkbox("AOI (+5%)", key="sc1")*5, st.checkbox("Estructura (+5%)", key="sc2")*5, st.checkbox("Patrón (+5%)", key="sc3")*5, st.checkbox("EMA 50 (+5%)", key="sc4")*5, st.checkbox("Psicológico (+5%)", key="sc5")*5])
                st.markdown('</div>', unsafe_allow_html=True)
            with r1_c2:
                st.markdown('<div class="strategy-box">', unsafe_allow_html=True)
                st.markdown("<div class='section-title'>2. CONTEXTO (2H)</div>", unsafe_allow_html=True)
                t2 = st.selectbox("Tendencia 2H", ["Alcista", "Bajista"], key="st2")
                st.divider()
                d_sc = sum([st.checkbox("AOI (+5%)", key="sc6")*5, st.checkbox("Estructura (+5%)", key="sc7")*5, st.checkbox("Vela (+5%)", key="sc8")*5, st.checkbox("Patrón (+5%)", key="sc9")*5, st.checkbox("EMA 50 (+5%)", key="sc10")*5])
                st.markdown('</div>', unsafe_allow_html=True)
            with r2_c1:
                st.markdown('<div class="strategy-box" style="margin-top:20px;">', unsafe_allow_html=True)
                st.markdown("<div class='section-title'>3. EJECUCIÓN (1H)</div>", unsafe_allow_html=True)
                t1 = st.selectbox("Tendencia 1H", ["Alcista", "Bajista"], key="st1")
                st.divider()
                h4_sc = sum([st.checkbox("Vela (+5%)", key="sc11")*5, st.checkbox("Patrón (+5%)", key="sc12")*5, st.checkbox("Estructura (+5%)", key="sc13")*5, st.checkbox("EMA 50 (+5%)", key="sc14")*5])
                st.markdown('</div>', unsafe_allow_html=True)
            with r2_c2:
                st.markdown('<div class="strategy-box" style="margin-top:20px;">', unsafe_allow_html=True)
                st.markdown("<div class='section-title'>4. GATILLO (M15)</div>", unsafe_allow_html=True)
                if t4==t2==t1: st.success("💎 TRIPLE ALINEACIÓN")
                else: st.warning("⚠️ TENDENCIA MIXTA")
                st.divider()
                sos = st.checkbox("⚡ SOS M15")
                eng = st.checkbox("🕯️ Entrada M15")
                rr = st.checkbox("💰 Ratio > 1:2.5")
                entry_score = sum([sos*10, eng*10])
                total = w_sc + d_sc + h4_sc + entry_score + 15
                st.markdown('</div>', unsafe_allow_html=True)

        # --- HUD DE RESULTADOS ---
        st.markdown("<br>", unsafe_allow_html=True)
        valid = sos and eng and rr
        
        msg, css_cl = "💤 ESPERAR", "status-warning"
        if not sos: msg, css_cl = "⛔ FALTA ESTRUCTURA", "status-stop"
        elif not eng: msg, css_cl = "⚠️ FALTA VELA", "status-warning"
        elif not rr: msg, css_cl = "💸 RATIO BAJO", "status-warning"
        elif total >= 90: msg, css_cl = "💎 SNIPER ENTRY", "status-sniper"
        elif total >= 60 and valid: msg, css_cl = "✅ TRADE VÁLIDO", "status-sniper"

        # HUD DINÁMICO
        st.markdown(f"""
        <div class="hud-container">
            <div class="hud-stat">
                <div class="hud-label">PUNTAJE</div>
                <div class="hud-value">{total}%</div>
            </div>
            <div style="flex-grow:1; text-align:center; margin:0 20px;">
                <span class="{css_cl}">{msg}</span>
            </div>
            <div class="hud-stat">
                <div class="hud-label">GATILLOS</div>
                <div style="font-size:1.5rem; font-weight:bold; color:{'var(--accent-green)' if valid else 'var(--accent-red)'}">
                    {'LISTO' if valid else 'PENDIENTE'}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.progress(min(total, 100))

        if valid and total >= 60:
            sl = "5-7 pips" if "Swing" in modo else "3-5 pips"
            st.info(f"📝 PLAN: Stop Loss {sl} | TP: Liquidez Opuesta | Riesgo 1%")

    # === 2. REGISTRO ===
    with t_reg:
        st.markdown("<h3 style='color:var(--accent-blue)'>📝 Registrar Operación</h3>", unsafe_allow_html=True)
        with st.form("reg"):
            c1,c2 = st.columns(2)
            dt = c1.date_input("Fecha", datetime.now())
            pr = c1.text_input("Par", "XAUUSD").upper()
            tp = c1.selectbox("Tipo", ["BUY", "SELL"])
            rs = c2.selectbox("Resultado", ["WIN", "LOSS", "BE"])
            mn = c2.number_input("Monto ($)", min_value=0.0, step=10.0)
            rt = c2.number_input("Ratio", value=2.5)
            nt = st.text_area("Notas")
            if st.form_submit_button("GUARDAR TRADE", use_container_width=True):
                real_mn = mn if rs=="WIN" else -mn if rs=="LOSS" else 0
                save_trade(user, sel_acc, {"Fecha":dt,"Par":pr,"Tipo":tp,"Resultado":rs,"Dinero":real_mn,"Ratio":rt,"Notas":nt})
                st.success("Guardado!"); st.rerun()

    # === 3. DASHBOARD ===
    with t_dash:
        st.markdown(f"<h3 style='color:var(--accent-blue)'>📊 Rendimiento: {sel_acc}</h3>", unsafe_allow_html=True)
        if not df.empty:
            k1,k2,k3,k4 = st.columns(4)
            wins = len(df[df["Resultado"]=="WIN"])
            net = df['Dinero'].sum()
            
            k1.markdown(f"<div style='background:var(--bg-card); padding:15px; border-radius:10px; border:1px solid var(--border-color); text-align:center'><div style='color:var(--text-muted); font-size:0.8rem'>NETO</div><div style='font-size:1.5rem; font-weight:bold; color:{'var(--accent-green)' if net>=0 else 'var(--accent-red)'}'>${net:,.2f}</div></div>", unsafe_allow_html=True)
            k2.metric("WIN RATE", f"{(wins/len(df)*100):.1f}%")
            k3.metric("TRADES", len(df))
            k4.metric("SALDO FINAL", f"${act:,.2f}")
            
            st.markdown("#### Curva de Crecimiento (Desde Capital Inicial)")
            df = df.sort_values("Fecha")
            
            # Lógica Equity
            fechas = [df["Fecha"].iloc[0]] if not df.empty else [datetime.now().date()]
            valores = [ini]
            acum = ini
            for _, r in df.iterrows():
                fechas.append(r["Fecha"])
                acum += r["Dinero"]
                valores.append(acum)

            fig = go.Figure(go.Scatter(x=fechas, y=valores, mode='lines+markers', line=dict(color='#3b82f6', width=3), fill='tozeroy'))
            # Colores de la gráfica dinámicos según el tema
            grid_col = "#334155" # Default dark
            font_col = "#94a3b8"
            
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color=font_col), xaxis=dict(showgrid=False), yaxis=dict(gridcolor=grid_col))
            st.plotly_chart(fig, use_container_width=True)
        else: st.info("Sin datos")

    # === 4. CALENDARIO ===
    with t_cal:
        c_p, c_t, c_n = st.columns([1,5,1])
        with c_p: 
            if st.button("⬅️", use_container_width=True): change_month(-1); st.rerun()
        with c_n: 
            if st.button("➡️", use_container_width=True): change_month(1); st.rerun()
            
        html, y, m = render_cal_html(df)
        with c_t: st.markdown(f"<h3 style='text-align:center; margin:0'>{calendar.month_name[m]} {y}</h3>", unsafe_allow_html=True)
        st.markdown(html, unsafe_allow_html=True)

if 'user' not in st.session_state: st.session_state.user = None
if st.session_state.user: main_app()
else: login_screen()
