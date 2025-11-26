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

# --- 2. GESTIÓN DE DIRECTORIOS ---
DATA_DIR = "user_data"
IMG_DIR = "fotos"
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
USERS_FILE = os.path.join(DATA_DIR, "users.json")
ACCOUNTS_FILE = os.path.join(DATA_DIR, "accounts_config.json")

# --- 3. SISTEMA DE TEMAS (CSS DINÁMICO) ---
def inject_theme(theme_mode):
    if theme_mode == "Claro (High Contrast)":
        # === PALETA MODO CLARO (TEXTO NEGRO / CASILLAS DEFINIDAS) ===
        css_vars = """
            --bg-app: #ffffff;
            --bg-card: #f3f4f6;       /* Gris muy suave para diferenciar tarjetas del fondo */
            --bg-sidebar: #ffffff;
            --text-main: #000000;     /* NEGRO PURO */
            --text-muted: #333333;    /* Gris muy oscuro para etiquetas */
            --border-color: #9ca3af;  /* Borde más oscuro para que se vean las casillas */
            --input-bg: #ffffff;
            --accent: #0056b3;        /* Azul más oscuro y serio */
            --accent-green: #059669;  /* Verde más oscuro para contraste */
            --accent-red: #dc2626;    /* Rojo más oscuro para contraste */
            --shadow: 0 2px 4px rgba(0,0,0,0.15); /* Sombra más marcada */
            --chart-grid: #e5e7eb;
            --chart-text: #000000;
        """
    else:
        # === PALETA MODO OSCURO (NAVY PRO - TU FAVORITO) ===
        css_vars = """
            --bg-app: #0f172a;
            --bg-card: #1e293b;
            --bg-sidebar: #020617;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --border-color: #334155;
            --input-bg: #1e293b;
            --accent: #3b82f6;
            --accent-green: #34d399;
            --accent-red: #f87171;
            --shadow: 0 4px 6px -1px rgba(0,0,0,0.3);
            --chart-grid: #334155;
            --chart-text: #94a3b8;
        """

    st.markdown(f"""
    <style>
    :root {{ {css_vars} }}

    /* FUENTE GLOBAL */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}

    /* APLICACIÓN GLOBAL */
    .stApp {{ background-color: var(--bg-app); color: var(--text-main); }}
    
    /* TEXTOS (NEGRO EN MODO CLARO) */
    h1, h2, h3, h4, h5, p, li, span, div {{ color: var(--text-main) !important; }}
    .stMarkdown p {{ color: var(--text-main) !important; }}
    
    /* ETIQUETAS DE INPUTS (Labels) */
    label, .stTextInput label, .stNumberInput label, .stSelectbox label {{
        color: var(--text-muted) !important;
        font-weight: 600 !important; /* Más negrita para que se lea bien */
    }}
    
    /* SIDEBAR */
    [data-testid="stSidebar"] {{ background-color: var(--bg-sidebar) !important; border-right: 1px solid var(--border-color); }}
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {{ color: var(--text-muted) !important; }}
    
    /* === CASILLAS (INPUTS) MEJORADAS === */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {{
        background-color: var(--input-bg) !important;
        color: var(--text-main) !important; /* Texto negro al escribir */
        border: 2px solid var(--border-color) !important; /* Borde más grueso */
        border-radius: 8px;
        font-weight: 500;
        box-shadow: inset 0 1px 2px rgba(0,0,0,0.05); /* Sombra interna sutil */
    }}
    
    /* Iconos inputs */
    .stSelectbox svg, .stDateInput svg {{ fill: var(--text-muted) !important; }}
    
    /* MENUS DESPLEGABLES (Opciones) */
    ul[data-baseweb="menu"] {{ background-color: var(--bg-card) !important; border: 1px solid var(--border-color); }}
    li[data-baseweb="option"] {{ color: var(--text-main) !important; font-weight: 500; }}
    
    /* TABS (PESTAÑAS) */
    .stTabs [data-baseweb="tab"] {{
        background-color: var(--bg-card) !important;
        color: var(--text-muted) !important;
        border: 1px solid var(--border-color);
        border-radius: 30px !important;
        padding: 0 25px !important;
        height: 50px;
        box-shadow: var(--shadow);
        font-weight: 700;
    }}
    .stTabs [data-baseweb="tab"][aria-selected="true"] {{
        background-color: var(--accent) !important;
        color: white !important; /* Texto blanco en tab activo */
        border: none !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }}
    .stTabs [data-baseweb="tab-highlight"] {{ display: none; }}
    
    /* TARJETAS ESTRATEGIA */
    .strategy-box {{
        background-color: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 20px;
        box-shadow: var(--shadow);
    }}
    
    /* HUD SCORE */
    .hud-container {{
        background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-app) 100%);
        border: 2px solid var(--accent);
        border-radius: 15px;
        padding: 20px;
        margin-top: 20px;
        box-shadow: var(--shadow);
        display: flex; justify-content: space-between; align-items: center;
    }}
    
    /* CHECKBOXES */
    .stCheckbox label p {{ color: var(--text-main) !important; font-weight: 500; }}
    
    /* CALENDARIO */
    .calendar-header {{ color: var(--text-muted) !important; font-weight: bold; }}
    
    /* BOTONES */
    .stButton button {{
        border: 1px solid var(--accent) !important;
        color: var(--accent) !important;
        font-weight: bold;
        background: transparent;
    }}
    .stButton button:hover {{
        background: var(--accent) !important;
        color: white !important;
    }}
    
    </style>
    """, unsafe_allow_html=True)

# --- 4. FUNCIONES BACKEND ---
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
    if init and not os.path.exists(fp): pd.DataFrame(columns=["Fecha","Par","Tipo","Resultado","Dinero","Ratio","Notas"]).to_csv(fp, index=False); return
    if not init:
        df = pd.read_csv(fp) if os.path.exists(fp) else pd.DataFrame(columns=["Fecha","Par","Tipo","Resultado","Dinero","Ratio","Notas"])
        df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
        df.to_csv(fp, index=False)
def load_trades(u, acc):
    fp = os.path.join(DATA_DIR, u, f"{acc}.csv".replace(" ", "_"))
    return pd.read_csv(fp) if os.path.exists(fp) else pd.DataFrame(columns=["Fecha","Par","Tipo","Resultado","Dinero","Ratio","Notas"])

# --- 5. FUNCIONES VISUALES ---
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

def render_cal_html(df, is_dark):
    d = st.session_state.get('cal_date', datetime.now())
    y, m = d.year, d.month
    data = {}
    if not df.empty:
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        df_m = df[(df['Fecha'].dt.year==y) & (df['Fecha'].dt.month==m)]
        data = df_m.groupby(df['Fecha'].dt.day)['Dinero'].sum().to_dict()

    cal = calendar.Calendar(firstweekday=0)
    html = '<div style="display:grid; grid-template-columns:repeat(7, 1fr); gap:8px; margin-top:15px;">'
    
    # Colores para días de la semana
    text_h = "#333333" if not is_dark else "#94a3b8"

    for h in ["LUN","MAR","MIÉ","JUE","VIE","SÁB","DOM"]: 
        html += f'<div style="text-align:center; color:{text_h}; font-size:0.8rem; font-weight:bold; padding:5px;">{h}</div>'
    
    for week in cal.monthdayscalendar(y, m):
        for day in week:
            if day == 0: html += '<div style="opacity:0;"></div>'
            else:
                val = data.get(day, 0)
                txt = f"${val:,.0f}" if val != 0 else ""
                
                bg = "var(--bg-card)"
                border = "var(--border-color)"
                col = "var(--text-main)"
                
                if val > 0:
                    bg = "rgba(16, 185, 129, 0.2)"; border = "var(--accent-green)"; col = "var(--accent-green)"
                elif val < 0:
                    bg = "rgba(239, 68, 68, 0.2)"; border = "var(--accent-red)"; col = "var(--accent-red)"

                html += f'''
                <div style="background:{bg}; border:1px solid {border}; border-radius:8px; min-height:80px; padding:10px; display:flex; flex-direction:column; justify-content:space-between;">
                    <div style="color:var(--text-muted); font-size:0.8rem; font-weight:bold;">{day}</div>
                    <div style="color:{col}; font-weight:bold; text-align:right;">{txt}</div>
                </div>'''
    html += '</div>'
    return html, y, m

# --- 6. LOGIN ---
def login_screen():
    inject_theme("Oscuro (Navy)")
    c1,c2,c3 = st.columns([1,1,1])
    with c2:
        st.markdown("<h1 style='text-align:center; color:var(--accent);'>🦁 Trading Suite</h1>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["INGRESAR", "REGISTRARSE"])
        with t1:
            u = st.text_input("Usuario")
            p = st.text_input("Password", type="password")
            if st.button("ACCEDER", type="primary", use_container_width=True):
                if verify_user(u, p): st.session_state.user = u; st.rerun()
                else: st.error("Error")
        with t2:
            nu = st.text_input("Nuevo Usuario")
            np = st.text_input("Nueva Password", type="password")
            if st.button("CREAR CUENTA", use_container_width=True):
                if nu and np: register_user(nu, np); st.success("Creado!"); st.rerun()

# --- 7. APP PRINCIPAL ---
def main_app():
    user = st.session_state.user
    if 'cal_date' not in st.session_state: st.session_state['cal_date'] = datetime.now()

    # --- SIDEBAR ---
    with st.sidebar:
        st.title(f"👤 {user.upper()}")
        
        # SELECTOR TEMA
        tema = st.radio("🎨 TEMA VISUAL", ["Oscuro (Navy)", "Claro (High Contrast)"], index=0)
        inject_theme(tema)
        is_dark = True if tema == "Oscuro (Navy)" else False
        
        st.markdown("---")
        if st.button("CERRAR SESIÓN", use_container_width=True): st.session_state.user = None; st.rerun()
        st.markdown("---")
        
        accs = get_user_accounts(user)
        sel_acc = st.selectbox("📂 CUENTA ACTIVA", accs)
        ini, act, _ = get_balance_data(user, sel_acc)
        
        col_s = "#10b981" if act >= ini else "#ef4444"
        bg_bal = "rgba(255,255,255,0.05)" if is_dark else "#f3f4f6"
        
        st.markdown(f"""
        <div style="background:{bg_bal}; padding:20px; border-radius:12px; border:1px solid var(--border-color); text-align:center; box-shadow: var(--shadow);">
            <div style="color:var(--text-muted); font-size:0.8rem; letter-spacing:1px; margin-bottom:5px;">BALANCE TOTAL</div>
            <div style="color:{col_s}; font-size:2rem; font-weight:900;">${act:,.2f}</div>
            <div style="color:var(--text-muted); font-size:0.8rem; margin-top:5px">Inicial: ${ini:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        with st.expander("➕ NUEVA CUENTA"):
            na = st.text_input("Nombre")
            nb = st.number_input("Capital ($)", value=100.0)
            if st.button("CREAR", use_container_width=True):
                if na: create_account(user, na, nb); st.rerun()

    # --- CUERPO ---
    t_op, t_reg, t_dash, t_cal = st.tabs(["🦁 OPERATIVA", "📝 BITÁCORA", "📊 ANALYTICS", "📅 CALENDARIO"])

    # === 1. OPERATIVA ===
    with t_op:
        with st.expander("📘 GUÍA VISUAL"):
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
        
        st.markdown(f"""
        <div style="background:var(--bg-card); padding:15px; border-radius:10px; border:1px solid var(--border-color); text-align:center; margin-bottom:20px; box-shadow: var(--shadow);">
            <h4 style="margin:0; color:var(--accent); text-transform:uppercase; letter-spacing:1px;">⚡ CONFIGURACIÓN ESTRATEGIA</h4>
        </div>
        """, unsafe_allow_html=True)
        
        c_ml, c_mm, c_mr = st.columns([1, 2, 1])
        with c_mm:
             modo = st.radio("", ["Swing (W-D-4H)", "Scalping (4H-2H-1H)"], horizontal=True, label_visibility="collapsed")

        r1_c1, r1_c2 = st.columns(2)
        r2_c1, r2_c2 = st.columns(2)
        total = 0; sos, eng, rr = False, False, False

        def header_html(text): return f"<div style='color:var(--accent); font-weight:800; text-transform:uppercase; margin-bottom:15px; border-bottom:2px solid var(--border-color); padding-bottom:8px;'>{text}</div>"

        if "Swing" in modo:
            with r1_c1:
                st.markdown('<div class="strategy-box">', unsafe_allow_html=True)
                st.markdown(header_html("1. SEMANAL (W)"), unsafe_allow_html=True)
                tw = st.selectbox("Tendencia W", ["Alcista", "Bajista"], key="tw")
                st.divider()
                w_sc = sum([st.checkbox("AOI (+10%)", key="w1")*10, st.checkbox("Estructura (+10%)", key="w2")*10, st.checkbox("Patrón (+10%)", key="w3")*10, st.checkbox("EMA 50 (+5%)", key="w4")*5, st.checkbox("Psicológico (+5%)", key="w5")*5])
                st.markdown('</div>', unsafe_allow_html=True)
            with r1_c2:
                st.markdown('<div class="strategy-box">', unsafe_allow_html=True)
                st.markdown(header_html("2. DIARIO (D)"), unsafe_allow_html=True)
                td = st.selectbox("Tendencia D", ["Alcista", "Bajista"], key="td")
                st.divider()
                d_sc = sum([st.checkbox("AOI (+10%)", key="d1")*10, st.checkbox("Estructura (+10%)", key="d2")*10, st.checkbox("Vela (+10%)", key="d3")*10, st.checkbox("Patrón (+10%)", key="d4")*10, st.checkbox("EMA 50 (+5%)", key="d5")*5])
                st.markdown('</div>', unsafe_allow_html=True)
            with r2_c1:
                st.markdown('<div class="strategy-box" style="margin-top:20px;">', unsafe_allow_html=True)
                st.markdown(header_html("3. EJECUCIÓN (4H)"), unsafe_allow_html=True)
                t4 = st.selectbox("Tendencia 4H", ["Alcista", "Bajista"], key="t4")
                st.divider()
                h4_sc = sum([st.checkbox("Vela (+10%)", key="h1")*10, st.checkbox("Patrón (+10%)", key="h2")*10, st.checkbox("AOI (+5%)", key="h3")*5, st.checkbox("Estructura (+5%)", key="h4")*5, st.checkbox("EMA 50 (+5%)", key="h5")*5])
                st.markdown('</div>', unsafe_allow_html=True)
            with r2_c2:
                st.markdown('<div class="strategy-box" style="margin-top:20px;">', unsafe_allow_html=True)
                st.markdown(header_html("4. GATILLO FINAL"), unsafe_allow_html=True)
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
        else:
            with r1_c1:
                st.markdown('<div class="strategy-box">', unsafe_allow_html=True)
                st.markdown(header_html("1. CONTEXTO (4H)"), unsafe_allow_html=True)
                t4 = st.selectbox("Tendencia 4H", ["Alcista", "Bajista"], key="st4")
                st.divider()
                w_sc = sum([st.checkbox("AOI (+5%)", key="sc1")*5, st.checkbox("Estructura (+5%)", key="sc2")*5, st.checkbox("Patrón (+5%)", key="sc3")*5, st.checkbox("EMA 50 (+5%)", key="sc4")*5, st.checkbox("Psicológico (+5%)", key="sc5")*5])
                st.markdown('</div>', unsafe_allow_html=True)
            with r1_c2:
                st.markdown('<div class="strategy-box">', unsafe_allow_html=True)
                st.markdown(header_html("2. CONTEXTO (2H)"), unsafe_allow_html=True)
                t2 = st.selectbox("Tendencia 2H", ["Alcista", "Bajista"], key="st2")
                st.divider()
                d_sc = sum([st.checkbox("AOI (+5%)", key="sc6")*5, st.checkbox("Estructura (+5%)", key="sc7")*5, st.checkbox("Vela (+5%)", key="sc8")*5, st.checkbox("Patrón (+5%)", key="sc9")*5, st.checkbox("EMA 50 (+5%)", key="sc10")*5])
                st.markdown('</div>', unsafe_allow_html=True)
            with r2_c1:
                st.markdown('<div class="strategy-box" style="margin-top:20px;">', unsafe_allow_html=True)
                st.markdown(header_html("3. EJECUCIÓN (1H)"), unsafe_allow_html=True)
                t1 = st.selectbox("Tendencia 1H", ["Alcista", "Bajista"], key="st1")
                st.divider()
                h4_sc = sum([st.checkbox("Vela (+5%)", key="sc11")*5, st.checkbox("Patrón (+5%)", key="sc12")*5, st.checkbox("Estructura (+5%)", key="sc13")*5, st.checkbox("EMA 50 (+5%)", key="sc14")*5])
                st.markdown('</div>', unsafe_allow_html=True)
            with r2_c2:
                st.markdown('<div class="strategy-box" style="margin-top:20px;">', unsafe_allow_html=True)
                st.markdown(header_html("4. GATILLO (M15)"), unsafe_allow_html=True)
                if t4==t2==t1: st.success("💎 TRIPLE ALINEACIÓN")
                else: st.warning("⚠️ TENDENCIA MIXTA")
                st.divider()
                sos = st.checkbox("⚡ SOS M15")
                eng = st.checkbox("🕯️ Entrada M15")
                rr = st.checkbox("💰 Ratio > 1:2.5")
                entry_score = sum([sos*10, eng*10])
                total = w_sc + d_sc + h4_sc + entry_score + 15
                st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        valid = sos and eng and rr
        
        msg, css_cl = "💤 ESPERAR", "status-warning"
        if not sos: msg, css_cl = "⛔ FALTA ESTRUCTURA", "status-stop"
        elif not eng: msg, css_cl = "⚠️ FALTA VELA", "status-warning"
        elif not rr: msg, css_cl = "💸 RATIO BAJO", "status-warning"
        elif total >= 90: msg, css_cl = "💎 SNIPER ENTRY", "status-sniper"
        elif total >= 60 and valid: msg, css_cl = "✅ TRADE VÁLIDO", "status-sniper"

        st.markdown(f"""
        <div class="hud-container">
            <div class="hud-stat">
                <div class="hud-label">PUNTAJE TOTAL</div>
                <div class="hud-value">{total}%</div>
            </div>
            <div style="flex-grow:1; text-align:center; margin:0 20px;">
                <span class="{css_cl}">{msg}</span>
            </div>
            <div class="hud-stat">
                <div class="hud-label">ESTADO</div>
                <div style="font-size:1.5rem; font-weight:bold; color:{'var(--accent-green)' if valid else 'var(--accent-red)'}">
                    {'LISTO' if valid else 'PENDIENTE'}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.progress(min(total, 100))

    # === 2. REGISTRO ===
    with t_reg:
        st.markdown(f"<h3 style='color:var(--accent)'>📝 Registrar Trade</h3>", unsafe_allow_html=True)
        with st.form("reg"):
            c1,c2 = st.columns(2)
            dt = c1.date_input("Fecha", datetime.now())
            pr = c1.text_input("Par", "XAUUSD").upper()
            tp = c1.selectbox("Tipo", ["BUY", "SELL"])
            rs = c2.selectbox("Resultado", ["WIN", "LOSS", "BE"])
            mn = c2.number_input("Monto ($)", min_value=0.0, step=10.0)
            rt = c2.number_input("Ratio", value=2.5)
            nt = st.text_area("Notas")
            if st.form_submit_button("GUARDAR", use_container_width=True):
                real_mn = mn if rs=="WIN" else -mn if rs=="LOSS" else 0
                save_trade(user, sel_acc, {"Fecha":dt,"Par":pr,"Tipo":tp,"Resultado":rs,"Dinero":real_mn,"Ratio":rt,"Notas":nt})
                st.success("Guardado!"); st.rerun()

    # === 3. DASHBOARD ===
    with t_dash:
        st.markdown(f"<h3 style='color:var(--accent)'>📊 Rendimiento: {sel_acc}</h3>", unsafe_allow_html=True)
        _, _, df = get_balance_data(user, sel_acc)
        if not df.empty:
            k1,k2,k3,k4 = st.columns(4)
            wins = len(df[df["Resultado"]=="WIN"])
            net = df['Dinero'].sum()
            
            k1.markdown(f"<div class='strategy-box' style='text-align:center'><div style='color:var(--text-muted); font-size:0.8rem'>NETO</div><div style='font-size:1.5rem; font-weight:bold; color:{'var(--accent-green)' if net>=0 else 'var(--accent-red)'}'>${net:,.2f}</div></div>", unsafe_allow_html=True)
            k2.metric("WIN RATE", f"{(wins/len(df)*100):.1f}%")
            k3.metric("TRADES", len(df))
            k4.metric("SALDO FINAL", f"${act:,.2f}")
            
            st.markdown("#### Curva de Crecimiento")
            df = df.sort_values("Fecha")
            fechas = [df["Fecha"].iloc[0]] if not df.empty else [datetime.now().date()]
            valores = [ini]
            acum = ini
            for _, r in df.iterrows():
                fechas.append(r["Fecha"])
                acum += r["Dinero"]
                valores.append(acum)

            grid_col = "#334155" if is_dark else "#e5e7eb"
            text_col = "#94a3b8" if is_dark else "#000000"
            
            fig = go.Figure(go.Scatter(x=fechas, y=valores, mode='lines+markers', line=dict(color='#3b82f6', width=3), fill='tozeroy'))
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color=text_col), xaxis=dict(showgrid=False), yaxis=dict(gridcolor=grid_col))
            st.plotly_chart(fig, use_container_width=True)
        else: st.info("Sin datos")

    # === 4. CALENDARIO ===
    with t_cal:
        c_p, c_t, c_n = st.columns([1,5,1])
        with c_p: 
            if st.button("⬅️", use_container_width=True): change_month(-1); st.rerun()
        with c_n: 
            if st.button("➡️", use_container_width=True): change_month(1); st.rerun()
            
        _, _, df = get_balance_data(user, sel_acc)
        html, y, m = render_cal_html(df, is_dark)
        with c_t: st.markdown(f"<h3 style='text-align:center; color:var(--text-main); margin:0'>{calendar.month_name[m]} {y}</h3>", unsafe_allow_html=True)
        st.markdown(html, unsafe_allow_html=True)

if 'user' not in st.session_state: st.session_state.user = None
if st.session_state.user: main_app()
else: login_screen()
