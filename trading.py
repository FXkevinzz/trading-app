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

# --- 2. ESTILOS CSS (TEMA AZUL NAVY PROFESIONAL - FORZADO) ---
st.markdown("""
    <style>
    /* IMPORTAR FUENTE PROFESIONAL */
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');

    /* === 1. VARIABLES DE COLOR (PALETA AZUL) === */
    :root {
        --bg-main: #0f172a;       /* Fondo Principal (Azul muy oscuro) */
        --bg-card: #1e293b;       /* Fondo Tarjetas (Azul acero oscuro) */
        --bg-sidebar: #020617;    /* Fondo Sidebar (Casi negro) */
        --text-main: #f8fafc;     /* Texto Blanco Hielo */
        --text-muted: #94a3b8;    /* Texto Gris Azulado */
        --accent-blue: #3b82f6;   /* Azul Brillante (Botones/Tabs) */
        --accent-green: #10b981;  /* Verde Profit */
        --accent-red: #ef4444;    /* Rojo Loss */
        --border-color: #334155;  /* Bordes sutiles */
    }

    /* === 2. RESET GLOBAL PARA EVITAR MODO CLARO === */
    html, body, [class*="css"] {
        font-family: 'Roboto', sans-serif;
        color: var(--text-main);
    }
    
    /* FORZAR FONDO PRINCIPAL */
    .stApp {
        background-color: var(--bg-main) !important;
    }

    /* FORZAR SIDEBAR OSCURO */
    [data-testid="stSidebar"] {
        background-color: var(--bg-sidebar) !important;
        border-right: 1px solid var(--border-color);
    }

    /* === 3. INPUTS Y WIDGETS (UNIFICADOS) === */
    .stTextInput>div>div>input, 
    .stNumberInput>div>div>input, 
    .stSelectbox>div>div>div, 
    .stDateInput>div>div>input, 
    .stTextArea>div>div>textarea {
        background-color: var(--bg-card) !important; 
        color: white !important; 
        border: 1px solid var(--border-color) !important;
        border-radius: 6px;
    }
    
    /* Texto de los labels de inputs */
    .stMarkdown label, .stTextInput label, .stSelectbox label, .stNumberInput label {
        color: var(--text-muted) !important;
    }

    /* === 4. BOTONES Y TABS === */
    /* Botones Primarios */
    .stButton button {
        background-color: var(--bg-card) !important;
        color: var(--accent-blue) !important;
        border: 1px solid var(--accent-blue) !important;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        background-color: var(--accent-blue) !important;
        color: white !important;
    }

    /* Tabs Seleccionados */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border-color);
        color: var(--text-muted);
    }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        background-color: var(--accent-blue) !important;
        color: white !important;
        border: none !important;
    }

    /* === 5. COMPONENTES PERSONALIZADOS === */
    
    /* Cajas de Estrategia (Grid) */
    .strategy-box {
        background-color: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 20px;
        height: 100%;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    .strategy-header {
        color: var(--accent-blue);
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 15px;
        border-bottom: 1px solid var(--border-color);
        padding-bottom: 8px;
    }

    /* HUD SCORE (El puntaje grande) */
    .hud-container {
        display: flex; justify-content: space-between; align-items: center;
        background: linear-gradient(90deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid var(--accent-blue);
        border-radius: 12px;
        padding: 25px;
        margin-top: 25px;
        box-shadow: 0 0 15px rgba(59, 130, 246, 0.15);
    }
    .hud-label { color: var(--text-muted); font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; }
    .hud-value-large { font-size: 3rem; font-weight: 900; color: white; line-height: 1; }
    
    /* Estados del Mensaje */
    .status-sniper { color: var(--accent-green); border: 1px solid var(--accent-green); background: rgba(16, 185, 129, 0.1); padding: 10px 20px; border-radius: 50px; font-weight: bold;}
    .status-warning { color: #facc15; border: 1px solid #facc15; background: rgba(250, 204, 21, 0.1); padding: 10px 20px; border-radius: 50px; font-weight: bold;}
    .status-stop { color: var(--accent-red); border: 1px solid var(--accent-red); background: rgba(239, 68, 68, 0.1); padding: 10px 20px; border-radius: 50px; font-weight: bold;}

    /* Calendario */
    .calendar-day { background-color: var(--bg-card); border: 1px solid var(--border-color); color: white; }
    .win-text { color: var(--accent-green); font-weight: bold; }
    .loss-text { color: var(--accent-red); font-weight: bold; }
    
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
    # Estilo Grid CSS Inline para asegurar que funcione
    html = '<div style="display:grid; grid-template-columns:repeat(7, 1fr); gap:6px; margin-top:10px;">'
    for h in ["LUN","MAR","MIÉ","JUE","VIE","SÁB","DOM"]: 
        html += f'<div style="text-align:center; color:#94a3b8; font-size:0.8rem; font-weight:bold; padding:5px;">{h}</div>'
    
    for week in cal.monthdayscalendar(y, m):
        for day in week:
            if day == 0: html += '<div style="opacity:0;"></div>'
            else:
                val = data.get(day, 0)
                txt = f"${val:,.0f}" if val != 0 else ""
                
                # Colores directos
                border = "#334155" # Default border
                bg = "#1e293b" # Default bg
                color = "white"
                
                if val > 0:
                    border = "#10b981"
                    bg = "rgba(16, 185, 129, 0.1)"
                    color = "#10b981"
                elif val < 0:
                    border = "#ef4444"
                    bg = "rgba(239, 68, 68, 0.1)"
                    color = "#ef4444"

                html += f'''
                <div style="background:{bg}; border:1px solid {border}; border-radius:6px; min-height:80px; padding:8px; display:flex; flex-direction:column; justify-content:space-between;">
                    <div style="color:#64748b; font-size:0.8rem; font-weight:bold;">{day}</div>
                    <div style="color:{color}; font-weight:bold; text-align:right;">{txt}</div>
                </div>'''
    html += '</div>'
    return html, y, m

# --- 5. LOGIN ---
def login_screen():
    c1,c2,c3 = st.columns([1,1,1])
    with c2:
        st.markdown("<h1 style='text-align:center; color:#3b82f6;'>🦁 Trading Suite</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#94a3b8;'>Acceso Profesional</p>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["INGRESAR", "REGISTRARSE"])
        with t1:
            u = st.text_input("Usuario")
            p = st.text_input("Password", type="password")
            if st.button("ACCEDER", type="primary", use_container_width=True):
                if verify_user(u, p): st.session_state.user = u; st.rerun()
                else: st.error("Error de credenciales")
        with t2:
            nu = st.text_input("Nuevo Usuario")
            np = st.text_input("Nueva Password", type="password")
            if st.button("CREAR CUENTA", use_container_width=True):
                if nu and np: register_user(nu, np); st.success("Creado!"); st.rerun()

# --- 6. APP PRINCIPAL ---
def main_app():
    user = st.session_state.user
    if 'cal_date' not in st.session_state: st.session_state['cal_date'] = datetime.now()

    # --- SIDEBAR AZUL ---
    with st.sidebar:
        st.title(f"👤 {user.upper()}")
        if st.button("CERRAR SESIÓN", use_container_width=True): st.session_state.user = None; st.rerun()
        st.markdown("---")
        
        accs = get_user_accounts(user)
        sel_acc = st.selectbox("📂 CUENTA ACTIVA", accs)
        ini, act = get_balance(user, sel_acc)
        
        col_s = "#10b981" if act >= ini else "#ef4444"
        st.markdown(f"""
        <div style="background:#0f172a; padding:20px; border-radius:10px; border:1px solid #334155; text-align:center; box-shadow: 0 4px 10px rgba(0,0,0,0.3);">
            <div style="color:#94a3b8; font-size:0.8rem; letter-spacing:1px; margin-bottom:5px;">BALANCE TOTAL</div>
            <div style="color:{col_s}; font-size:2rem; font-weight:900;">${act:,.2f}</div>
            <div style="color:#64748b; font-size:0.8rem; margin-top:5px">Inicial: ${ini:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        with st.expander("➕ NUEVA CUENTA"):
            na = st.text_input("Nombre de Cuenta")
            nb = st.number_input("Capital Inicial ($)", value=10000.0, step=1000.0)
            if st.button("CREAR", use_container_width=True):
                if na: create_account(user, na, nb); st.rerun()

    # --- PESTAÑAS PRINCIPALES ---
    t_op, t_reg, t_dash, t_cal = st.tabs(["🦁 OPERATIVA", "📝 BITÁCORA", "📊 ANALYTICS", "📅 CALENDARIO"])

    # === 1. OPERATIVA (AZUL & ORGANIZADA) ===
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
        
        # Selector de Modo Estilizado
        st.markdown("""
        <div style="background:#1e293b; padding:15px; border-radius:10px; border:1px solid #334155; text-align:center; margin-bottom:20px;">
            <h4 style="margin:0; color:#3b82f6; text-transform:uppercase; letter-spacing:1px;">⚡ CONFIGURACIÓN DE ESTRATEGIA</h4>
        </div>
        """, unsafe_allow_html=True)
        
        c_ml, c_mm, c_mr = st.columns([1, 2, 1])
        with c_mm:
             modo = st.radio("", ["Swing (W-D-4H)", "Scalping (4H-2H-1H)"], horizontal=True, label_visibility="collapsed")

        # GRID 2x2
        r1_c1, r1_c2 = st.columns(2)
        r2_c1, r2_c2 = st.columns(2)

        # Variables de puntuación
        total = 0
        sos, eng, rr = False, False, False

        if "Swing" in modo:
            # W
            with r1_c1:
                st.markdown('<div class="strategy-box">', unsafe_allow_html=True)
                st.markdown("<div class='strategy-header'>1. SEMANAL (W)</div>", unsafe_allow_html=True)
                tw = st.selectbox("Tendencia W", ["Alcista", "Bajista"], key="tw")
                st.divider()
                w_sc = sum([st.checkbox("AOI (+10%)", key="w1")*10, st.checkbox("Estructura (+10%)", key="w2")*10, st.checkbox("Patrón (+10%)", key="w3")*10, st.checkbox("EMA 50 (+5%)", key="w4")*5, st.checkbox("Psicológico (+5%)", key="w5")*5])
                st.markdown('</div>', unsafe_allow_html=True)
            # D
            with r1_c2:
                st.markdown('<div class="strategy-box">', unsafe_allow_html=True)
                st.markdown("<div class='strategy-header'>2. DIARIO (D)</div>", unsafe_allow_html=True)
                td = st.selectbox("Tendencia D", ["Alcista", "Bajista"], key="td")
                st.divider()
                d_sc = sum([st.checkbox("AOI (+10%)", key="d1")*10, st.checkbox("Estructura (+10%)", key="d2")*10, st.checkbox("Vela (+10%)", key="d3")*10, st.checkbox("Patrón (+10%)", key="d4")*10, st.checkbox("EMA 50 (+5%)", key="d5")*5])
                st.markdown('</div>', unsafe_allow_html=True)
            # 4H
            with r2_c1:
                st.markdown('<div class="strategy-box" style="margin-top:20px;">', unsafe_allow_html=True)
                st.markdown("<div class='strategy-header'>3. EJECUCIÓN (4H)</div>", unsafe_allow_html=True)
                t4 = st.selectbox("Tendencia 4H", ["Alcista", "Bajista"], key="t4")
                st.divider()
                h4_sc = sum([st.checkbox("Vela (+10%)", key="h1")*10, st.checkbox("Patrón (+10%)", key="h2")*10, st.checkbox("AOI (+5%)", key="h3")*5, st.checkbox("Estructura (+5%)", key="h4")*5, st.checkbox("EMA 50 (+5%)", key="h5")*5])
                st.markdown('</div>', unsafe_allow_html=True)
            # GATILLO
            with r2_c2:
                st.markdown('<div class="strategy-box" style="margin-top:20px;">', unsafe_allow_html=True)
                st.markdown("<div class='strategy-header'>4. GATILLO FINAL</div>", unsafe_allow_html=True)
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
                st.markdown("<div class='strategy-header'>1. CONTEXTO (4H)</div>", unsafe_allow_html=True)
                t4 = st.selectbox("Tendencia 4H", ["Alcista", "Bajista"], key="st4")
                st.divider()
                w_sc = sum([st.checkbox("AOI (+5%)", key="sc1")*5, st.checkbox("Estructura (+5%)", key="sc2")*5, st.checkbox("Patrón (+5%)", key="sc3")*5, st.checkbox("EMA 50 (+5%)", key="sc4")*5, st.checkbox("Psicológico (+5%)", key="sc5")*5])
                st.markdown('</div>', unsafe_allow_html=True)
            with r1_c2:
                st.markdown('<div class="strategy-box">', unsafe_allow_html=True)
                st.markdown("<div class='strategy-header'>2. CONTEXTO (2H)</div>", unsafe_allow_html=True)
                t2 = st.selectbox("Tendencia 2H", ["Alcista", "Bajista"], key="st2")
                st.divider()
                d_sc = sum([st.checkbox("AOI (+5%)", key="sc6")*5, st.checkbox("Estructura (+5%)", key="sc7")*5, st.checkbox("Vela (+5%)", key="sc8")*5, st.checkbox("Patrón (+5%)", key="sc9")*5, st.checkbox("EMA 50 (+5%)", key="sc10")*5])
                st.markdown('</div>', unsafe_allow_html=True)
            with r2_c1:
                st.markdown('<div class="strategy-box" style="margin-top:20px;">', unsafe_allow_html=True)
                st.markdown("<div class='strategy-header'>3. EJECUCIÓN (1H)</div>", unsafe_allow_html=True)
                t1 = st.selectbox("Tendencia 1H", ["Alcista", "Bajista"], key="st1")
                st.divider()
                h4_sc = sum([st.checkbox("Vela (+5%)", key="sc11")*5, st.checkbox("Patrón (+5%)", key="sc12")*5, st.checkbox("Estructura (+5%)", key="sc13")*5, st.checkbox("EMA 50 (+5%)", key="sc14")*5])
                st.markdown('</div>', unsafe_allow_html=True)
            with r2_c2:
                st.markdown('<div class="strategy-box" style="margin-top:20px;">', unsafe_allow_html=True)
                st.markdown("<div class='strategy-header'>4. GATILLO (M15)</div>", unsafe_allow_html=True)
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
        
        # Determinar estado
        if not sos: msg, css_cl = "FALTA ESTRUCTURA (SOS)", "status-stop"
        elif not eng: msg, css_cl = "FALTA VELA DE ENTRADA", "status-warning"
        elif not rr: msg, css_cl = "RATIO INSUFICIENTE", "status-warning"
        elif total >= 90: msg, css_cl = "💎 SNIPER ENTRY", "status-sniper"
        elif total >= 60 and valid: msg, css_cl = "✅ TRADE VÁLIDO", "status-sniper"
        else: msg, css_cl = "💤 ESPERAR", "status-warning"

        # HTML del HUD
        st.markdown(f"""
        <div class="hud-container">
            <div class="hud-stat">
                <div class="hud-label">PUNTAJE ACUMULADO</div>
                <div class="hud-value-large">{total}%</div>
            </div>
            <div style="flex-grow:1; text-align:center; margin:0 20px;">
                <span class="{css_cl}">{msg}</span>
            </div>
            <div class="hud-stat">
                <div class="hud-label">GATILLOS</div>
                <div style="font-size:1.5rem; font-weight:bold; color:{'#10b981' if valid else '#ef4444'}">
                    {'LISTO' if valid else 'PENDIENTE'}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Barra de progreso visual (tope visual 100)
        st.progress(min(total, 100))

        if valid and total >= 60:
            sl = "5-7 pips" if "Swing" in modo else "3-5 pips"
            st.info(f"📝 PLAN: Stop Loss {sl} | TP: Liquidez Opuesta | Riesgo 1%")

    # === 2. REGISTRO ===
    with t_reg:
        st.markdown("<h3 style='color:#3b82f6'>📝 Registrar Nueva Operación</h3>", unsafe_allow_html=True)
        with st.form("reg"):
            c1,c2 = st.columns(2)
            dt = c1.date_input("Fecha", datetime.now())
            pr = c1.text_input("Par", "XAUUSD").upper()
            tp = c1.selectbox("Tipo", ["BUY", "SELL"])
            
            rs = c2.selectbox("Resultado", ["WIN", "LOSS", "BE"])
            mn = c2.number_input("Monto ($)", min_value=0.0, step=10.0, help="Introduce valor positivo")
            rt = c2.number_input("Ratio", value=2.5)
            nt = st.text_area("Notas")
            
            if st.form_submit_button("GUARDAR EN BITÁCORA", use_container_width=True):
                real_mn = mn if rs=="WIN" else -mn if rs=="LOSS" else 0
                save_trade(user, sel_acc, {"Fecha":dt,"Par":pr,"Tipo":tp,"Resultado":rs,"Dinero":real_mn,"Ratio":rt,"Notas":nt})
                st.success("Guardado!"); st.rerun()

    # === 3. DASHBOARD ===
    with t_dash:
        st.markdown("<h3 style='color:#3b82f6'>📊 Rendimiento</h3>", unsafe_allow_html=True)
        df = load_trades(user, sel_acc)
        if not df.empty:
            k1,k2,k3,k4 = st.columns(4)
            wins = len(df[df["Resultado"]=="WIN"])
            net = df['Dinero'].sum()
            
            k1.markdown(f"<div style='background:#1e293b; padding:15px; border-radius:10px; text-align:center'><div style='color:#94a3b8; font-size:0.8rem'>NETO</div><div style='font-size:1.5rem; font-weight:bold; color:{'#10b981' if net>=0 else '#ef4444'}'>${net:,.2f}</div></div>", unsafe_allow_html=True)
            k2.metric("WIN RATE", f"{(wins/len(df)*100):.1f}%")
            k3.metric("TRADES", len(df))
            k4.metric("SALDO FINAL", f"${act:,.2f}")
            
            df["Eq"] = ini + df["Dinero"].cumsum()
            fig = go.Figure(go.Scatter(x=df["Fecha"], y=df["Eq"], line=dict(color='#3b82f6', width=3), fill='tozeroy', fillcolor='rgba(59, 130, 246, 0.1)'))
            fig.update_layout(title="Curva de Equity", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#94a3b8'), xaxis=dict(showgrid=False), yaxis=dict(gridcolor='#334155'))
            st.plotly_chart(fig, use_container_width=True)
        else: st.info("No hay datos")

    # === 4. CALENDARIO ===
    with t_cal:
        c_p, c_t, c_n = st.columns([1,5,1])
        with c_p: 
            if st.button("⬅️", use_container_width=True): change_month(-1); st.rerun()
        with c_n: 
            if st.button("➡️", use_container_width=True): change_month(1); st.rerun()
            
        df = load_trades(user, sel_acc)
        html, y, m = render_cal_html(df)
        with c_t: st.markdown(f"<h3 style='text-align:center; color:#f8fafc; margin:0'>{calendar.month_name[m]} {y}</h3>", unsafe_allow_html=True)
        st.markdown(html, unsafe_allow_html=True)

if 'user' not in st.session_state: st.session_state.user = None
if st.session_state.user: main_app()
else: login_screen()

