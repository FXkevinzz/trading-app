import streamlit as st
import streamlit.components.v1 as components
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

# --- 3. SISTEMA DE TEMAS (COLORES PREMIUM MEJORADOS) ---
def inject_theme(theme_mode):
    if theme_mode == "Claro (Swiss Design)":
        css_vars = """
            --bg-app: #f8fafc;        /* Gris hielo muy suave */
            --bg-card: #ffffff;       /* Blanco puro */
            --bg-sidebar: #1e293b;    /* Sidebar oscura para contraste */
            --text-main: #0f172a;     /* Azul noche casi negro (Lectura perfecta) */
            --text-muted: #475569;    /* Gris acero fuerte */
            --border-color: #e2e8f0;  /* Bordes sutiles */
            --input-bg: #ffffff;
            --accent: #2563eb;        /* Azul Royal Vibrante */
            --accent-hover: #1d4ed8;
            --accent-green: #16a34a;  /* Verde Esmeralda Sólido */
            --accent-red: #dc2626;    /* Rojo Rubí Sólido */
            --button-text: #ffffff;
            --shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
            --chart-text: #0f172a;
            --chart-grid: #e2e8f0;
        """
    else:
        # Oscuro (Cyber Navy)
        css_vars = """
            --bg-app: #0b1121;        /* Azul Abismo */
            --bg-card: #151e32;       /* Azul Acero Profundo */
            --bg-sidebar: #020617;    /* Casi negro */
            --text-main: #f1f5f9;     /* Blanco Hielo */
            --text-muted: #94a3b8;    /* Gris Azulado */
            --border-color: #2a3655;  /* Borde Azulado */
            --input-bg: #1e293b;
            --accent: #3b82f6;        /* Azul Neón Suave */
            --accent-hover: #60a5fa;
            --accent-green: #00e676;  /* Verde Neón */
            --accent-red: #ff1744;    /* Rojo Neón */
            --button-text: #ffffff;
            --shadow: 0 10px 15px -3px rgba(0,0,0,0.5);
            --chart-text: #94a3b8;
            --chart-grid: #1e293b;
        """

    st.markdown(f"""
    <style>
    :root {{ {css_vars} }}
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}

    /* FONDO Y TEXTOS */
    .stApp {{ background-color: var(--bg-app); color: var(--text-main); }}
    h1, h2, h3, h4, h5, p, li, span, div, label {{ color: var(--text-main) !important; }}
    .stMarkdown p {{ color: var(--text-main) !important; }}
    
    /* SIDEBAR (SIEMPRE OSCURA) */
    [data-testid="stSidebar"] {{ background-color: var(--bg-sidebar) !important; border-right: 1px solid var(--border-color); }}
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {{ color: #f8fafc !important; }}
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label {{ color: #94a3b8 !important; }}
    
    /* INPUTS (ESTILO MODERNO) */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {{
        background-color: var(--input-bg) !important;
        color: var(--text-main) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px;
        padding: 10px;
        transition: border 0.3s;
    }}
    .stTextInput input:focus, .stNumberInput input:focus {{ border-color: var(--accent) !important; }}
    .stSelectbox svg, .stDateInput svg {{ fill: var(--text-muted) !important; }}
    
    /* CHECKBOXES */
    .stCheckbox label p {{ font-weight: 500; }}
    
    /* MENUS */
    ul[data-baseweb="menu"] {{ background-color: var(--bg-card) !important; border: 1px solid var(--border-color); }}
    li[data-baseweb="option"] {{ color: var(--text-main) !important; }}
    
    /* BOTONES (GRADIENTE SUTIL) */
    .stButton button {{
        background: var(--accent) !important;
        color: var(--button-text) !important;
        border: none !important;
        border-radius: 8px;
        font-weight: 600;
        letter-spacing: 0.5px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: transform 0.1s, opacity 0.2s;
    }}
    .stButton button:hover {{ opacity: 0.9; transform: translateY(-1px); }}
    .stButton button:active {{ transform: translateY(1px); }}
    
    /* TABS (CÁPSULA FLOTANTE) */
    .stTabs [data-baseweb="tab-list"] {{ gap: 8px; padding-bottom: 15px; }}
    .stTabs [data-baseweb="tab"] {{
        background-color: var(--bg-card) !important;
        color: var(--text-muted) !important;
        border: 1px solid var(--border-color);
        border-radius: 8px !important;
        padding: 0 20px !important;
        height: 45px;
        box-shadow: var(--shadow);
        font-weight: 600;
    }}
    .stTabs [data-baseweb="tab"][aria-selected="true"] {{
        background-color: var(--accent) !important;
        color: white !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
    }}
    .stTabs [data-baseweb="tab-highlight"] {{ display: none; }}
    
    /* TARJETAS CONTENEDORAS */
    .strategy-box {{
        background-color: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 20px;
        box-shadow: var(--shadow);
    }}
    
    /* EXPANDER (ACORDEON) - MÁS LIMPIO */
    .streamlit-expanderHeader {{
        background-color: var(--bg-card) !important;
        border-radius: 8px !important;
        color: var(--text-main) !important;
        border: 1px solid var(--border-color);
    }}
    .streamlit-expanderContent {{
        background-color: var(--bg-app) !important;
        border: 1px solid var(--border-color);
        border-top: none;
        border-bottom-left-radius: 8px;
        border-bottom-right-radius: 8px;
        padding: 15px !important;
    }}

    /* HUD SCORE */
    .hud-container {{
        background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-app) 100%);
        border: 1px solid var(--accent);
        border-radius: 12px;
        padding: 20px;
        margin-top: 20px;
        box-shadow: var(--shadow);
        display: flex; justify-content: space-between; align-items: center;
    }}
    
    /* CALENDARIO */
    .calendar-header {{ color: var(--text-muted) !important; font-size: 0.75rem; text-transform: uppercase; }}
    
    </style>
    """, unsafe_allow_html=True)

# --- 4. FUNCIONES BACKEND ---
def load_json(fp): return json.load(open(fp)) if os.path.exists(fp) else {}
def save_json(fp, data):
    try: json.dump(data, open(fp, "w"))
    except: pass

# Login a prueba de fallos
def verify_user(u, p):
    if u == "admin" and p == "1234": return True
    d = load_json(USERS_FILE)
    return u in d and d[u] == p

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
    cols = ["Fecha","Par","Tipo","Resultado","Dinero","Ratio","Notas"]
    if init:
        if not os.path.exists(fp): pd.DataFrame(columns=cols).to_csv(fp, index=False)
        return
    try: df = pd.read_csv(fp)
    except: df = pd.DataFrame(columns=cols)
    df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
    df.to_csv(fp, index=False)

def load_trades(u, acc):
    fp = os.path.join(DATA_DIR, u, f"{acc}.csv".replace(" ", "_"))
    cols = ["Fecha","Par","Tipo","Resultado","Dinero","Ratio","Notas"]
    if os.path.exists(fp):
        try: return pd.read_csv(fp)
        except: return pd.DataFrame(columns=cols)
    return pd.DataFrame(columns=cols)

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
        try:
            df['Fecha'] = pd.to_datetime(df['Fecha'])
            df_m = df[(df['Fecha'].dt.year==y) & (df['Fecha'].dt.month==m)]
            data = df_m.groupby(df['Fecha'].dt.day)['Dinero'].sum().to_dict()
        except: pass

    cal = calendar.Calendar(firstweekday=0)
    html = '<div style="display:grid; grid-template-columns:repeat(7, 1fr); gap:6px; margin-top:10px;">'
    day_col = "#94a3b8" if is_dark else "#64748b"
    
    for h in ["LUN","MAR","MIÉ","JUE","VIE","SÁB","DOM"]: 
        html += f'<div style="text-align:center; color:{day_col}; font-size:0.75rem; font-weight:bold; padding:5px;">{h}</div>'
    
    for week in cal.monthdayscalendar(y, m):
        for day in week:
            if day == 0: html += '<div style="opacity:0;"></div>'
            else:
                val = data.get(day, 0)
                txt = f"${val:,.0f}" if val != 0 else ""
                bg = "var(--bg-card)"; border = "var(--border-color)"; col = "var(--text-main)"
                
                if val > 0:
                    bg = "rgba(16, 185, 129, 0.15)"; border = "var(--accent-green)"; col = "var(--accent-green)"
                elif val < 0:
                    bg = "rgba(239, 68, 68, 0.15)"; border = "var(--accent-red)"; col = "var(--accent-red)"

                html += f'''
                <div style="background:{bg}; border:1px solid {border}; border-radius:6px; min-height:70px; padding:8px; display:flex; flex-direction:column; justify-content:space-between;">
                    <div style="color:var(--text-muted); font-size:0.7rem; font-weight:bold;">{day}</div>
                    <div style="color:{col}; font-weight:bold; font-size:0.9rem; text-align:right;">{txt}</div>
                </div>'''
    html += '</div>'
    return html, y, m

# --- 6. LOGIN ---
def login_screen():
    inject_theme("Oscuro (Cyber Navy)")
    c1,c2,c3 = st.columns([1,1,1])
    with c2:
        st.markdown("<h1 style='text-align:center; color:var(--accent);'>🦁 Trading Suite</h1>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["INGRESAR", "REGISTRARSE"])
        with t1:
            u = st.text_input("Usuario", key="l_u")
            p = st.text_input("Password", type="password", key="l_p")
            if st.button("ACCEDER", type="primary", use_container_width=True, key="b_l"):
                if verify_user(u, p): st.session_state.user = u; st.rerun()
                else: st.error("Error (Intenta: admin/1234)")
        with t2:
            nu = st.text_input("Nuevo Usuario", key="r_u")
            np = st.text_input("Nueva Password", type="password", key="r_p")
            if st.button("CREAR CUENTA", use_container_width=True, key="b_r"):
                if nu and np: register_user(nu, np); st.success("Creado!"); st.rerun()

# --- 7. APP PRINCIPAL ---
def main_app():
    user = st.session_state.user
    if 'cal_date' not in st.session_state: st.session_state['cal_date'] = datetime.now()

    with st.sidebar:
        st.title(f"👤 {user.upper()}")
        tema = st.radio("🎨 TEMA VISUAL", ["Oscuro (Cyber Navy)", "Claro (Swiss Design)"], index=0)
        inject_theme(tema)
        is_dark = True if tema == "Oscuro (Cyber Navy)" else False
        
        st.markdown("---")
        if st.button("CERRAR SESIÓN", use_container_width=True): st.session_state.user = None; st.rerun()
        st.markdown("---")
        
        accs = get_user_accounts(user)
        sel_acc = st.selectbox("📂 CUENTA ACTIVA", accs)
        ini, act, _ = get_balance_data(user, sel_acc)
        
        col_s = "#10b981" if act >= ini else "#ef4444"
        st.markdown(f"""
        <div style="background:var(--bg-card); padding:15px; border-radius:10px; border:1px solid var(--border-color); text-align:center; box-shadow: var(--shadow);">
            <div style="color:var(--text-muted); font-size:0.8rem; letter-spacing:1px; margin-bottom:5px;">BALANCE TOTAL</div>
            <div style="color:{col_s}; font-size:1.8rem; font-weight:bold;">${act:,.2f}</div>
            <div style="color:var(--text-muted); font-size:0.8rem; margin-top:5px">Inicial: ${ini:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        with st.expander("➕ NUEVA CUENTA"):
            na = st.text_input("Nombre")
            nb = st.number_input("Capital ($)", value=100.0)
            if st.button("CREAR", use_container_width=True):
                if na: create_account(user, na, nb); st.rerun()

    t_op, t_reg, t_dash, t_cal, t_news = st.tabs(["🦁 OPERATIVA", "📝 BITÁCORA", "📊 ANALYTICS", "📅 CALENDARIO", "📰 NOTICIAS"])

    # === OPERATIVA ===
    with t_op:
        with st.expander("📘 GUÍA VISUAL PATRONES"):
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
        with c_mm: modo = st.radio("", ["Swing (W-D-4H)", "Scalping (4H-2H-1H)"], horizontal=True, label_visibility="collapsed")

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
            <div class="hud-stat"><div class="hud-label">PUNTAJE TOTAL</div><div class="hud-value">{total}%</div></div>
            <div style="flex-grow:1; text-align:center; margin:0 20px;"><span class="{css_cl}">{msg}</span></div>
            <div class="hud-stat"><div class="hud-label">ESTADO</div><div style="font-size:1.5rem; font-weight:bold; color:{'var(--accent-green)' if valid else 'var(--accent-red)'}">{'LISTO' if valid else 'PENDIENTE'}</div></div>
        </div>
        """, unsafe_allow_html=True)
        st.progress(min(total, 100))

    # === 2. BITÁCORA (CON AGRUPACIÓN POR DÍAS) ===
    with t_reg:
        c_form, c_hist = st.columns([1, 1.5])
        
        with c_form:
            st.markdown(f"<h3 style='color:var(--accent)'>📝 Nuevo Registro</h3>", unsafe_allow_html=True)
            with st.container():
                st.markdown('<div class="strategy-box">', unsafe_allow_html=True)
                with st.form("reg"):
                    dt = st.date_input("Fecha", datetime.now())
                    c_a, c_b = st.columns(2)
                    pr = c_a.text_input("Par", "XAUUSD").upper()
                    tp = c_b.selectbox("Tipo", ["BUY", "SELL"])
                    rs = st.selectbox("Resultado", ["WIN", "LOSS", "BE"])
                    mn = st.number_input("Monto ($)", min_value=0.0, step=10.0)
                    rt = st.number_input("Ratio", value=2.5)
                    nt = st.text_area("Notas")
                    if st.form_submit_button("GUARDAR TRADE", use_container_width=True):
                        real_mn = mn if rs=="WIN" else -mn if rs=="LOSS" else 0
                        save_trade(user, sel_acc, {"Fecha":dt,"Par":pr,"Tipo":tp,"Resultado":rs,"Dinero":real_mn,"Ratio":rt,"Notas":nt})
                        st.success("Guardado!"); st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

        with c_hist:
            st.markdown(f"<h3 style='color:var(--accent)'>📜 Historial (Agrupado)</h3>", unsafe_allow_html=True)
            df_h = load_trades(user, sel_acc)
            if not df_h.empty:
                df_h['Fecha'] = pd.to_datetime(df_h['Fecha'])
                df_h = df_h.sort_values("Fecha", ascending=False)
                
                # Agrupar por fecha
                unique_dates = df_h['Fecha'].dt.date.unique()
                
                for d in unique_dates:
                    day_data = df_h[df_h['Fecha'].dt.date == d]
                    day_pnl = day_data['Dinero'].sum()
                    color_pnl = "🟢" if day_pnl >= 0 else "🔴"
                    
                    with st.expander(f"📅 {d} | {color_pnl} PnL: ${day_pnl:,.2f}"):
                        st.dataframe(day_data[['Par', 'Tipo', 'Resultado', 'Dinero', 'Ratio', 'Notas']], use_container_width=True)
            else:
                st.info("No hay trades registrados.")

    # === 3. ANALYTICS ===
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
            line_hex = "#3b82f6" if is_dark else "#2563eb"
            text_hex = "#94a3b8" if is_dark else "#0f172a"
            grid_hex = "#1e293b" if is_dark else "#e2e8f0"
            fig = go.Figure(go.Scatter(x=fechas, y=valores, mode='lines+markers', line=dict(color=line_hex, width=3), fill='tozeroy'))
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color=text_hex), xaxis=dict(showgrid=False), yaxis=dict(gridcolor=grid_hex))
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

    # === 5. NOTICIAS ===
    with t_news:
        st.markdown(f"<h3 style='color:var(--accent)'>📰 Calendario Económico Global</h3>", unsafe_allow_html=True)
        tv_theme = "dark" if is_dark else "light"
        html_code = f"""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-events.js" async>{{"colorTheme": "{tv_theme}","isTransparent": true,"width": "100%","height": "600","locale": "es","importanceFilter": "-1,0,1","currencyFilter": "USD,EUR,GBP,JPY,AUD,CAD,CHF,NZD"}}</script></div>"""
        components.html(html_code, height=600, scrolling=True)

if 'user' not in st.session_state: st.session_state.user = None
if st.session_state.user: main_app()
else: login_screen()
