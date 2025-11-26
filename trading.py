import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import os
import json
import calendar
from datetime import datetime
import plotly.graph_objects as go
import pytz
from PIL import Image
import google.generativeai as genai

# --- 1. CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="Trading Pro Suite AI", layout="wide", page_icon="🦁")

# --- 2. GESTIÓN DE DIRECTORIOS ---
DATA_DIR = "user_data"
IMG_DIR = "fotos"
BRAIN_FILE = os.path.join(DATA_DIR, "brain_wins.json")

if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
USERS_FILE = os.path.join(DATA_DIR, "users.json")
ACCOUNTS_FILE = os.path.join(DATA_DIR, "accounts_config.json")

# --- 3. INTELIGENCIA ARTIFICIAL (VISION + AUDITOR) ---
def init_ai():
    if "GEMINI_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_KEY"])
        return True
    return False

def load_brain():
    if not os.path.exists(BRAIN_FILE): return []
    try: return json.load(open(BRAIN_FILE, "r"))
    except: return []

def save_to_brain(analysis_text, pair, timeframe):
    memory = load_brain()
    new_mem = {
        "date": str(datetime.now()),
        "pair": pair,
        "tf": timeframe,
        "analysis": analysis_text
    }
    memory.append(new_mem)
    try:
        with open(BRAIN_FILE, "w") as f: json.dump(memory, f)
    except: pass

# --- NUEVA FUNCIÓN: AUDITOR DE RENDIMIENTO ---
def generate_performance_audit(df):
    if df.empty: return "No hay suficientes datos para auditar."
    
    # Convertimos los datos a texto para que la IA los lea
    data_str = df.to_string(index=False)
    
    prompt = f"""
    Actúa como un Auditor de Riesgo Senior de un Fondo de Inversión (Prop Firm).
    Tu trabajo es analizar los datos crudos de este trader y encontrar sus fallas y virtudes.
    
    DATOS DEL TRADER (CSV):
    {data_str}
    
    TU MISIÓN:
    Analiza patrones matemáticos y de comportamiento. No seas suave, sé objetivo.
    
    RESPONDE CON ESTE FORMATO:
    1. 🚨 **FUGA DE CAPITAL:** (¿Dónde está perdiendo más dinero? ¿Qué par? ¿Qué tipo de operación?)
    2. ✅ **ZONA DE PODER:** (¿Dónde es más rentable? ¿Compras o Ventas? ¿Qué par?)
    3. ⚖️ **DISCIPLINA:** (¿Está respetando los Ratios? ¿Corta las ganancias antes de tiempo?)
    4. 🧠 **CONSEJO DIRECTO:** (Una sola frase de lo que debe cambiar hoy mismo).
    """
    
    # Usamos Flash porque es rápido y barato para mucho texto
    modelos = ['gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-1.5-pro']
    
    for m in modelos:
        try:
            model = genai.GenerativeModel(m)
            response = model.generate_content(prompt)
            return response.text
        except: continue
    return "Error de conexión con el Auditor IA."

def analyze_chart(image, mode, pair, tf):
    brain = load_brain()
    context = ""
    if brain:
        examples = brain[-2:]
        context = f"TUS MEJORES TRADES PREVIOS:\n{str(examples)}\n\n"
    
    prompt = f"""
    Eres un Mentor de Trading Institucional (SMC). Estrategia: {mode}. Activo: {pair} ({tf}).
    {context}
    Analiza la imagen y valida:
    1. ESTRUCTURA (BOS/CHOCH).
    2. ZONA DE VALOR (Order Block/FVG).
    3. PATRÓN DE ENTRADA.
    
    Responde breve:
    - 🎯 VEREDICTO: [APROBADO / DUDOSO / RECHAZADO]
    - 📊 PROBABILIDAD: 0-100%
    - 📝 ANÁLISIS: (Breve)
    - 💡 CONSEJO: (SL/TP)
    """
    
    modelos = ['gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-1.5-pro']
    for m in modelos:
        try:
            model = genai.GenerativeModel(m)
            return model.generate_content([prompt, image]).text
        except: continue
    return "Error IA Vision."

# --- 4. SISTEMA DE TEMAS ---
def inject_theme(theme_mode):
    if theme_mode == "Claro (Swiss Design)":
        css_vars = """
            --bg-app: #f8fafc; --bg-card: #ffffff; --bg-sidebar: #1e293b;
            --text-main: #0f172a; --text-muted: #475569; --border-color: #e2e8f0;
            --input-bg: #ffffff; --accent: #2563eb; --accent-green: #16a34a; --accent-red: #dc2626;
            --button-text: #ffffff; --shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
            --chart-text: #0f172a; --chart-grid: #e2e8f0;
        """
    else:
        css_vars = """
            --bg-app: #0b1121; --bg-card: #151e32; --bg-sidebar: #020617;
            --text-main: #f1f5f9; --text-muted: #94a3b8; --border-color: #2a3655;
            --input-bg: #1e293b; --accent: #3b82f6; --accent-green: #00e676; --accent-red: #ff1744;
            --button-text: #ffffff; --shadow: 0 10px 15px -3px rgba(0,0,0,0.5);
            --chart-text: #94a3b8; --chart-grid: #1e293b;
        """

    st.markdown(f"""
    <style>
    :root {{ {css_vars} }}
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}

    .stApp {{ background-color: var(--bg-app); color: var(--text-main); }}
    h1, h2, h3, h4, h5, p, li, span, div, label {{ color: var(--text-main) !important; }}
    .stMarkdown p {{ color: var(--text-main) !important; }}
    
    [data-testid="stSidebar"] {{ background-color: var(--bg-sidebar) !important; border-right: 1px solid var(--border-color); }}
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label {{ color: #94a3b8 !important; }}
    [data-testid="stSidebar"] h1 {{ color: #f8fafc !important; }}

    .stTextInput input, .stNumberInput input, .stDateInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {{
        background-color: var(--input-bg) !important;
        color: var(--text-main) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px;
        padding: 10px;
    }}
    .stSelectbox svg, .stDateInput svg {{ fill: var(--text-muted) !important; }}
    
    ul[data-baseweb="menu"] {{ background-color: var(--bg-card) !important; border: 1px solid var(--border-color); }}
    li[data-baseweb="option"] {{ color: var(--text-main) !important; }}
    
    .stButton button {{
        background: var(--accent) !important;
        color: var(--button-text) !important;
        border: none !important;
        border-radius: 8px;
        font-weight: 600;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: transform 0.1s;
    }}
    .stButton button:active {{ transform: translateY(1px); }}
    
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
    }}
    .stTabs [data-baseweb="tab-highlight"] {{ display: none; }}
    
    .strategy-box {{ background-color: var(--bg-card); border: 1px solid var(--border-color); border-radius: 12px; padding: 20px; box-shadow: var(--shadow); height: 100%; }}
    .strategy-header {{ color: var(--accent); font-weight: 800; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 15px; border-bottom: 1px solid var(--border-color); padding-bottom: 8px; }}
    
    .hud-container {{
        background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-app) 100%);
        border: 1px solid var(--accent);
        border-radius: 12px;
        padding: 20px;
        margin-top: 20px;
        box-shadow: var(--shadow);
        display: flex; justify-content: space-between; align-items: center;
    }}
    .hud-value-large {{ font-size: 3rem; font-weight: 900; color: var(--text-main); line-height: 1; }}
    .stCheckbox label p {{ color: var(--text-main) !important; font-weight: 500; }}
    .status-sniper {{ background-color: rgba(16,185,129,0.15); color: var(--accent-green); border: 1px solid var(--accent-green); padding: 10px 20px; border-radius: 50px; font-weight: bold; }}
    .status-warning {{ background-color: rgba(250,204,21,0.15); color: #d97706; border: 1px solid #facc15; padding: 10px 20px; border-radius: 50px; font-weight: bold; }}
    .status-stop {{ background-color: rgba(239,68,68,0.15); color: var(--accent-red); border: 1px solid var(--accent-red); padding: 10px 20px; border-radius: 50px; font-weight: bold; }}
    
    /* AUDIT BOX STYLES */
    .audit-box {{
        background-color: var(--bg-card);
        border-left: 4px solid var(--accent);
        padding: 20px;
        border-radius: 0 12px 12px 0;
        margin-top: 20px;
        box-shadow: var(--shadow);
    }}
    
    </style>
    """, unsafe_allow_html=True)

# --- 5. FUNCIONES BACKEND ---
def load_json(fp):
    if not os.path.exists(fp): return {}
    try: return json.load(open(fp))
    except: return {}
def save_json(fp, data):
    try: json.dump(data, open(fp, "w"))
    except: pass
def verify_user(u, p):
    if u == "admin" and p == "1234": return True
    d = load_json(USERS_FILE); return u in d and d[u] == p
def register_user(u, p): d = load_json(USERS_FILE); d[u] = p; save_json(USERS_FILE, d)
def get_user_accounts(u): d = load_json(ACCOUNTS_FILE); return list(d.get(u, {}).keys()) if u in d else ["Principal"]
def create_account(u, name, bal): d = load_json(ACCOUNTS_FILE); d.setdefault(u, {})[name] = bal; save_json(ACCOUNTS_FILE, d); save_trade(u, name, None, init=True)
def get_balance_data(u, acc):
    d = load_json(ACCOUNTS_FILE); ini = d.get(u, {}).get(acc, 0.0)
    fp = os.path.join(DATA_DIR, u, f"{acc}.csv".replace(" ", "_"))
    df = pd.read_csv(fp) if os.path.exists(fp) else pd.DataFrame()
    pnl = df["Dinero"].sum() if not df.empty else 0
    return ini, ini + pnl, df
def save_trade(u, acc, data, init=False):
    folder = os.path.join(DATA_DIR, u); os.makedirs(folder, exist_ok=True)
    fp = os.path.join(folder, f"{acc}.csv".replace(" ", "_"))
    cols = ["Fecha","Par","Tipo","Resultado","Dinero","Ratio","Notas"]
    if init and not os.path.exists(fp): pd.DataFrame(columns=cols).to_csv(fp, index=False); return
    df = pd.read_csv(fp) if os.path.exists(fp) else pd.DataFrame(columns=cols)
    if data: df = pd.concat([df, pd.DataFrame([data])], ignore_index=True); df.to_csv(fp, index=False)
def load_trades(u, acc):
    fp = os.path.join(DATA_DIR, u, f"{acc}.csv".replace(" ", "_"))
    return pd.read_csv(fp) if os.path.exists(fp) else pd.DataFrame(columns=["Fecha","Par","Tipo","Resultado","Dinero","Ratio","Notas"])

# --- 6. FUNCIONES VISUALES ---
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
    html = '<div style="display:grid; grid-template-columns:repeat(7, 1fr); gap:8px; margin-top:15px;">'
    day_col = "#94a3b8" if is_dark else "#64748b"
    for h in ["LUN","MAR","MIÉ","JUE","VIE","SÁB","DOM"]: 
        html += f'<div style="text-align:center; color:{day_col}; font-size:0.8rem; font-weight:bold; padding:5px;">{h}</div>'
    
    for week in cal.monthdayscalendar(y, m):
        for day in week:
            if day == 0: html += '<div style="opacity:0;"></div>'
            else:
                val = data.get(day, 0)
                txt = f"${val:,.0f}" if val != 0 else ""
                bg = "var(--bg-card)"; border = "var(--border-color)"; col = "var(--text-main)"
                if val > 0: bg = "rgba(16, 185, 129, 0.15)"; border = "var(--accent-green)"; col = "var(--accent-green)"
                elif val < 0: bg = "rgba(239, 68, 68, 0.15)"; border = "var(--accent-red)"; col = "var(--accent-red)"
                html += f'<div style="background:{bg}; border:1px solid {border}; border-radius:8px; min-height:80px; padding:10px; display:flex; flex-direction:column; justify-content:space-between;"><div style="color:var(--text-muted); font-size:0.8rem; font-weight:bold;">{day}</div><div style="color:{col}; font-weight:bold; text-align:right;">{txt}</div></div>'
    html += '</div>'
    return html, y, m

def change_month(delta):
    d = st.session_state.get('cal_date', datetime.now())
    m, y = d.month + delta, d.year
    if m > 12: m, y = 1, y+1
    elif m < 1: m, y = 12, y-1
    st.session_state['cal_date'] = d.replace(year=y, month=m, day=1)

# --- 7. LOGIN ---
def login_screen():
    inject_theme("Oscuro (Cyber Navy)")
    c1,c2,c3 = st.columns([1,1,1])
    with c2:
        st.markdown("<h1 style='text-align:center; color:var(--accent);'>🦁 Trading Suite AI</h1>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["INGRESAR", "REGISTRARSE"])
        with t1:
            u = st.text_input("Usuario", key="l_u"); p = st.text_input("Password", type="password", key="l_p")
            if st.button("ACCEDER", use_container_width=True, key="b_l"):
                if verify_user(u, p): st.session_state.user = u; st.rerun()
                else: st.error("Error (Prueba: admin/1234)")
        with t2:
            nu = st.text_input("Nuevo Usuario", key="r_u"); np = st.text_input("Nueva Password", type="password", key="r_p")
            if st.button("CREAR CUENTA", use_container_width=True, key="b_r"):
                if nu and np: register_user(nu, np); st.success("Creado!"); st.rerun()

# --- 8. APP PRINCIPAL ---
def main_app():
    user = st.session_state.user
    if 'cal_date' not in st.session_state: st.session_state['cal_date'] = datetime.now()

    with st.sidebar:
        st.title(f"👤 {user.upper()}")
        tema = st.radio("🎨 TEMA", ["Oscuro (Cyber Navy)", "Claro (Swiss Design)"], index=0)
        inject_theme(tema)
        is_dark = True if tema == "Oscuro (Cyber Navy)" else False
        
        st.markdown("---")
        if st.button("CERRAR SESIÓN", use_container_width=True): st.session_state.user = None; st.rerun()
        
        accs = get_user_accounts(user)
        sel_acc = st.selectbox("📂 CUENTA ACTIVA", accs)
        ini, act, _ = get_balance_data(user, sel_acc)
        
        st.markdown(f"""<div style="background:rgba(255,255,255,0.05); padding:15px; border-radius:10px; border:1px solid rgba(255,255,255,0.1); text-align:center;"><div style="color:#94a3b8; font-size:0.8rem;">BALANCE</div><div style="color:{'#10b981' if act>=ini else '#ef4444'}; font-size:1.8rem; font-weight:bold">${act:,.2f}</div></div>""", unsafe_allow_html=True)
        with st.expander("➕ NUEVA CUENTA"):
            na = st.text_input("Nombre"); nb = st.number_input("Capital", 100.0)
            if st.button("CREAR"): create_account(user, na, nb); st.rerun()

    tabs = st.tabs(["🦁 OPERATIVA", "🧠 IA VISION", "📝 BITÁCORA", "📊 ANALYTICS", "📰 NOTICIAS"])

    # TAB 1: OPERATIVA MANUAL
    with tabs[0]:
        st.markdown('<div class="strategy-box">', unsafe_allow_html=True)
        c_mod = st.columns([1,2,1])
        with c_mod[1]: modo = st.radio("", ["Swing (W-D-4H)", "Scalping (4H-2H-1H)"], horizontal=True, label_visibility="collapsed")
        st.markdown('</div><br>', unsafe_allow_html=True)
        
        # GRID 2x2 (RESTORED)
        r1_c1, r1_c2 = st.columns(2); r2_c1, r2_c2 = st.columns(2)
        total = 0; sos, eng, rr = False, False, False

        def header(t): return f"<div class='strategy-header'>{t}</div>"

        if "Swing" in modo:
            with r1_c1:
                st.markdown('<div class="strategy-box">', unsafe_allow_html=True)
                st.markdown(header("1. SEMANAL (W)"), unsafe_allow_html=True)
                tw = st.selectbox("Trend W", ["Alcista", "Bajista"], key="tw")
                w_sc = sum([st.checkbox("AOI (+10%)", key="w1")*10, st.checkbox("Estructura (+10%)", key="w2")*10, st.checkbox("Patrón (+10%)", key="w3")*10, st.checkbox("EMA 50 (+5%)", key="w4")*5, st.checkbox("Psico (+5%)", key="w5")*5])
                st.markdown('</div>', unsafe_allow_html=True)
            with r1_c2:
                st.markdown('<div class="strategy-box">', unsafe_allow_html=True)
                st.markdown(header("2. DIARIO (D)"), unsafe_allow_html=True)
                td = st.selectbox("Trend D", ["Alcista", "Bajista"], key="td")
                d_sc = sum([st.checkbox("AOI (+10%)", key="d1")*10, st.checkbox("Estructura (+10%)", key="d2")*10, st.checkbox("Vela (+10%)", key="d3")*10, st.checkbox("Patrón (+10%)", key="d4")*10, st.checkbox("EMA 50 (+5%)", key="d5")*5])
                st.markdown('</div>', unsafe_allow_html=True)
            with r2_c1:
                st.markdown('<div class="strategy-box" style="margin-top:20px">', unsafe_allow_html=True)
                st.markdown(header("3. EJECUCIÓN (4H)"), unsafe_allow_html=True)
                t4 = st.selectbox("Trend 4H", ["Alcista", "Bajista"], key="t4")
                h4_sc = sum([st.checkbox("Vela (+10%)", key="h1")*10, st.checkbox("Patrón (+10%)", key="h2")*10, st.checkbox("AOI (+5%)", key="h3")*5, st.checkbox("Estructura (+5%)", key="h4")*5, st.checkbox("EMA 50 (+5%)", key="h5")*5])
                st.markdown('</div>', unsafe_allow_html=True)
            with r2_c2:
                st.markdown('<div class="strategy-box" style="margin-top:20px">', unsafe_allow_html=True)
                st.markdown(header("4. GATILLO"), unsafe_allow_html=True)
                if tw==td==t4: st.success("💎 TRIPLE SYNC")
                sos = st.checkbox("⚡ SOS"); eng = st.checkbox("🕯️ Vela"); rr = st.checkbox("💰 Ratio")
                entry_score = sum([sos*10, eng*10])
                total = w_sc + d_sc + h4_sc + entry_score
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            with r1_c1:
                st.markdown('<div class="strategy-box">', unsafe_allow_html=True)
                st.markdown(header("1. CONTEXTO (4H)"), unsafe_allow_html=True)
                t4 = st.selectbox("Trend 4H", ["Alcista", "Bajista"], key="s4")
                w_sc = sum([st.checkbox("AOI (+5%)", key="s1")*5, st.checkbox("Estructura (+5%)", key="s2")*5, st.checkbox("Patrón (+5%)", key="s3")*5, st.checkbox("EMA 50 (+5%)", key="s4")*5, st.checkbox("Psico (+5%)", key="s5")*5])
                st.markdown('</div>', unsafe_allow_html=True)
            with r1_c2:
                st.markdown('<div class="strategy-box">', unsafe_allow_html=True)
                st.markdown(header("2. CONTEXTO (2H)"), unsafe_allow_html=True)
                t2 = st.selectbox("Trend 2H", ["Alcista", "Bajista"], key="s2t")
                d_sc = sum([st.checkbox("AOI (+5%)", key="s21")*5, st.checkbox("Estructura (+5%)", key="s22")*5, st.checkbox("Vela (+5%)", key="s23")*5, st.checkbox("Patrón (+5%)", key="s24")*5, st.checkbox("EMA 50 (+5%)", key="s25")*5])
                st.markdown('</div>', unsafe_allow_html=True)
            with r2_c1:
                st.markdown('<div class="strategy-box" style="margin-top:20px">', unsafe_allow_html=True)
                st.markdown(header("3. EJECUCIÓN (1H)"), unsafe_allow_html=True)
                t1 = st.selectbox("Trend 1H", ["Alcista", "Bajista"], key="s1t")
                h4_sc = sum([st.checkbox("Vela (+5%)", key="s31")*5, st.checkbox("Patrón (+5%)", key="s32")*5, st.checkbox("Estructura (+5%)", key="s33")*5, st.checkbox("EMA 50 (+5%)", key="s34")*5])
                st.markdown('</div>', unsafe_allow_html=True)
            with r2_c2:
                st.markdown('<div class="strategy-box" style="margin-top:20px">', unsafe_allow_html=True)
                st.markdown(header("4. GATILLO (M15)"), unsafe_allow_html=True)
                if t4==t2==t1: st.success("💎 TRIPLE SYNC")
                sos = st.checkbox("⚡ SOS"); eng = st.checkbox("🕯️ Vela"); rr = st.checkbox("💰 Ratio")
                entry_score = sum([sos*10, eng*10])
                total = w_sc + d_sc + h4_sc + entry_score + 15
                st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        valid = sos and eng and rr
        msg, css_cl = "💤 ESPERAR", "status-warning"
        if not sos: msg, css_cl = "⛔ FALTA SOS", "status-stop"
        elif not eng: msg, css_cl = "⚠️ FALTA VELA", "status-warning"
        elif total >= 90: msg, css_cl = "💎 SNIPER", "status-sniper"
        
        st.markdown(f"""<div class="hud-container"><div class="hud-stat"><div class="hud-label">TOTAL</div><div class="hud-value-large">{total}%</div></div><div style="flex-grow:1; text-align:center; margin:0 20px;"><span class="{css_cl}">{msg}</span></div></div>""", unsafe_allow_html=True)

    # TAB 2: IA VISION
    with tabs[1]:
        st.markdown(f"<h3 style='color:var(--accent)'>🧠 Análisis de Gráficos con IA</h3>", unsafe_allow_html=True)
        if not init_ai():
            st.error("⚠️ API KEY NO DETECTADA. Configura 'GEMINI_KEY' en .streamlit/secrets.toml")
        else:
            c_img, c_res = st.columns([1, 1.5])
            with c_img:
                uploaded_file = st.file_uploader("Sube tu captura", type=["jpg", "png", "jpeg"])
                if uploaded_file:
                    image = Image.open(uploaded_file)
                    st.image(image, caption="Gráfico a Analizar", use_container_width=True)
                    st.markdown("---")
                    ai_pair = st.text_input("Par", "XAUUSD"); ai_tf = st.selectbox("Temporalidad", ["M15", "H1", "H4", "Daily"])
                    if st.button("🦁 ANALIZAR", type="primary", use_container_width=True):
                        with st.spinner("Analizando..."):
                            res_text = analyze_chart(image, modo, ai_pair, ai_tf)
                            st.session_state['last_analysis'] = res_text
            with c_res:
                if 'last_analysis' in st.session_state:
                    st.markdown('<div class="strategy-box">', unsafe_allow_html=True)
                    st.markdown("### 🤖 Veredicto")
                    st.markdown(st.session_state['last_analysis'])
                    st.markdown('</div><br>', unsafe_allow_html=True)
                    if st.button("💾 GUARDAR APRENDIZAJE", use_container_width=True):
                        save_to_brain(st.session_state['last_analysis'], ai_pair, ai_tf)
                        st.success("¡Aprendido!")

    # TAB 3: BITÁCORA
    with tabs[2]:
        st.markdown(f"<h3 style='color:var(--accent)'>📝 Registrar Trade</h3>", unsafe_allow_html=True)
        with st.form("reg_trade"):
            c1,c2 = st.columns(2)
            dt = c1.date_input("Fecha"); pr = c1.text_input("Par", "XAUUSD")
            tp = c1.selectbox("Tipo", ["BUY","SELL"]); rs = c2.selectbox("Res", ["WIN","LOSS"])
            mn = c2.number_input("Monto", step=10.0); rt = c2.number_input("Ratio", 2.5)
            if st.form_submit_button("GUARDAR"):
                rm = mn if rs=="WIN" else -mn
                save_trade(user, sel_acc, {"Fecha":dt,"Par":pr,"Tipo":tp,"Resultado":rs,"Dinero":rm,"Ratio":rt,"Notas":""})
                st.success("Guardado"); st.rerun()

    # TAB 4: ANALYTICS (CON AUDITOR IA)
    with tabs[3]:
        _, _, df = get_balance_data(user, sel_acc)
        
        if not df.empty:
            # === SECCIÓN DE GRÁFICOS ===
            st.markdown(f"<h3 style='color:var(--accent)'>📊 Rendimiento Visual</h3>", unsafe_allow_html=True)
            fig = go.Figure(go.Scatter(x=df["Fecha"], y=df["Dinero"].cumsum(), mode='lines+markers'))
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='gray'))
            st.plotly_chart(fig, use_container_width=True)
            
            # === SECCIÓN DE AUDITOR IA (NUEVO) ===
            st.markdown("---")
            st.markdown(f"<h3 style='color:var(--accent)'>🕵️ Auditor de Riesgo IA</h3>", unsafe_allow_html=True)
            st.info("La IA analizará todo tu historial para encontrar patrones ocultos.")
            
            if st.button("🦁 AUDITAR MI RENDIMIENTO CON IA", type="primary", use_container_width=True):
                if not init_ai():
                    st.error("⚠️ Falta API KEY")
                else:
                    with st.spinner("🔍 La IA está leyendo tu historial y buscando fugas de capital..."):
                        report = generate_performance_audit(df)
                        st.markdown(f"""
                        <div class="audit-box">
                            <h4 style="color:var(--accent)">📋 REPORTE DE AUDITORÍA</h4>
                            {report}
                        </div>
                        """, unsafe_allow_html=True)
        else: 
            st.info("Registra trades para activar el análisis.")

    # TAB 5: NOTICIAS
    with tabs[4]:
        tv_theme = "dark" if is_dark else "light"
        html_code = f"""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-events.js" async>{{"colorTheme": "{tv_theme}","isTransparent": true,"width": "100%","height": "800","locale": "es","importanceFilter": "-1,0","currencyFilter": "USD,EUR,GBP,JPY,AUD,CAD,CHF,NZD"}}</script></div>"""
        components.html(html_code, height=800, scrolling=True)

if 'user' not in st.session_state: st.session_state.user = None
if st.session_state.user: main_app()
else: login_screen()
