import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import os
import json
import calendar
import shutil
import zipfile
import io
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
import pytz
from PIL import Image
import google.generativeai as genai

# ==============================================================================
# 1. CONFIGURACIÓN DE LA PÁGINA
# ==============================================================================
st.set_page_config(
    page_title="Trading Pro Suite AI", 
    layout="wide", 
    page_icon="🦁",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# 2. GESTIÓN DE DIRECTORIOS Y ARCHIVOS DE SISTEMA
# ==============================================================================
DATA_DIR = "user_data"
IMG_DIR = os.path.join(DATA_DIR, "brain_images")
BRAIN_FILE = os.path.join(DATA_DIR, "brain_data.json")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
ACCOUNTS_FILE = os.path.join(DATA_DIR, "accounts_config.json")

# Garantizar que las carpetas existan
for d in [DATA_DIR, IMG_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

# ==============================================================================
# 3. CEREBRO IA (GEMINI 2.0 FLASH + RAG + AUDITOR)
# ==============================================================================
def init_ai():
    if "GEMINI_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_KEY"])
        return True
    return False

@st.cache_data(ttl=60)
def load_brain():
    if not os.path.exists(BRAIN_FILE): return []
    try:
        with open(BRAIN_FILE, "r") as f: return json.load(f)
    except: return []

def save_image_locally(image_obj, filename):
    try:
        path = os.path.join(IMG_DIR, filename)
        image_obj.save(path)
        return path
    except: return None

def save_to_brain(analysis_text, pair, result, mode, images_list=None):
    memory = load_brain()
    saved_paths = []
    if images_list:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        for idx, img in enumerate(images_list):
            fname = f"{pair}_{result}_{timestamp}_{idx}.png"
            path = save_image_locally(img, fname)
            if path: saved_paths.append(path)

    new_mem = {
        "date": str(datetime.now()),
        "pair": pair,
        "mode": mode,
        "result": result,
        "analysis": analysis_text,
        "images": saved_paths
    }
    memory.append(new_mem)
    try:
        with open(BRAIN_FILE, "w") as f: json.dump(memory, f, indent=4)
        load_brain.clear()
    except: pass

def analyze_multiframe(images_data, mode, pair):
    brain = load_brain()
    context = ""
    if brain:
        wins = [x for x in brain if x.get('result') == 'WIN']
        examples = wins[-2:] if len(wins) >= 2 else wins
        context = f"REFERENCIA (TUS MEJORES TRADES PREVIOS):\n{str(examples)}\n\n"
    
    img_desc = ""
    for i, data in enumerate(images_data):
        img_desc += f"IMAGEN {i+1}: Temporalidad {data['tf']}.\n"

    prompt = f"""
    Eres un Mentor de Trading Institucional experto en la estrategia 'Set & Forget' (Alex G).
    Analiza estas {len(images_data)} imágenes del activo {pair} en conjunto.
    
    ESTRATEGIA: {mode}
    {context}
    
    ESTRUCTURA DE IMÁGENES SUMINISTRADAS:
    {img_desc}
    
    TU MISIÓN ES VALIDAR LA "SINCRONIZACIÓN" (TRIPLE SYNC):
    1. ¿La tendencia Macro (Img 1) apoya a la Intermedia (Img 2)?
    2. ¿El precio está reaccionando en una Zona AOI válida en la temporalidad mayor?
    3. ¿La imagen de Gatillo (Img 3) muestra un patrón de entrada claro (SOS + Vela Envolvente)?
    
    Responde con este formato exacto:
    🎯 SINCRONÍA: [PERFECTA / DUDOSA / DESALINEADA]
    📊 PROBABILIDAD: 0-100%
    📝 ANÁLISIS TÉCNICO: (Explica la relación entre las 3 temporalidades)
    💡 CONSEJO DE EJECUCIÓN: (SL/TP sugeridos)
    """
    
    content = [prompt]
    for data in images_data: content.append(data['img'])

    modelos = ['gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-1.5-pro']
    for m in modelos:
        try:
            model = genai.GenerativeModel(m)
            return model.generate_content(content).text
        except: continue
    return "Error de conexión IA. Verifica tu API Key."

def generate_audit_report(df):
    if df.empty: return "Sin datos para auditar."
    csv_txt = df.to_string()
    prompt = f"""Audita estos trades como un experto en riesgo:\n{csv_txt}\nDetecta: Fugas, Zonas de Poder y da un consejo."""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        return model.generate_content(prompt).text
    except: return "Error en Auditoría."

# ==============================================================================
# 4. SISTEMA DE TEMAS Y CSS (PESTAÑAS REDONDAS)
# ==============================================================================
def inject_theme(theme_mode):
    if theme_mode == "Claro (Swiss Design)":
        css_vars = """
            --bg-app: #f8fafc;
            --bg-card: #ffffff;
            --bg-sidebar: #1e293b;
            --text-main: #0f172a;
            --text-muted: #475569;
            --border-color: #e2e8f0;
            --input-bg: #ffffff;
            --accent: #2563eb;
            --accent-green: #16a34a;
            --accent-red: #dc2626;
            --button-text: #ffffff;
            --shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
            --chart-text: #0f172a;
            --chart-grid: #e2e8f0;
        """
    else:
        # Modo Oscuro (Cyber Navy)
        css_vars = """
            --bg-app: #0b1121;
            --bg-card: #151e32;
            --bg-sidebar: #020617;
            --text-main: #f1f5f9;
            --text-muted: #94a3b8;
            --border-color: #2a3655;
            --input-bg: #1e293b;
            --accent: #3b82f6;
            --accent-green: #00e676;
            --accent-red: #ff1744;
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

    .stApp {{ background-color: var(--bg-app); color: var(--text-main); }}
    h1, h2, h3, h4, h5, p, label, span, div {{ color: var(--text-main) !important; }}
    [data-testid="stSidebar"] {{ background-color: var(--bg-sidebar); border-right: 1px solid var(--border-color); }}
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {{ color: #f8fafc !important; }}
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label {{ color: #94a3b8 !important; }}
    
    /* Inputs */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {{
        background-color: var(--input-bg) !important; color: var(--text-main) !important; border: 1px solid var(--border-color) !important; border-radius: 8px; padding: 10px;
    }}
    .stSelectbox svg, .stDateInput svg {{ fill: var(--text-muted) !important; }}
    ul[data-baseweb="menu"] {{ background-color: var(--bg-card) !important; border: 1px solid var(--border-color); }}
    li[data-baseweb="option"] {{ color: var(--text-main) !important; }}
    
    /* Botones */
    .stButton button {{
        background: var(--accent) !important; color: var(--button-text) !important; border: none !important; border-radius: 8px; font-weight: bold; box-shadow: var(--shadow);
    }}
    
    /* --- PESTAÑAS REDONDAS (ESTILO CÁPSULA) --- */
    .stTabs [data-baseweb="tab-list"] {{ gap: 10px; padding-bottom: 15px; }}
    .stTabs [data-baseweb="tab"] {{
        background-color: var(--bg-card) !important;
        color: var(--text-muted) !important;
        border: 1px solid var(--border-color);
        border-radius: 50px !important; /* REDONDEADO EXTREMO */
        padding: 0 25px !important;
        height: 45px;
        box-shadow: var(--shadow);
        font-weight: 600;
        transition: all 0.3s;
    }}
    .stTabs [data-baseweb="tab"][aria-selected="true"] {{
        background-color: var(--accent) !important;
        color: white !important;
        border: none !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }}
    .stTabs [data-baseweb="tab-highlight"] {{ display: none; }}
    
    /* Cards */
    .strategy-box {{ background-color: var(--bg-card); border: 1px solid var(--border-color); padding: 20px; border-radius: 12px; box-shadow: var(--shadow); height: 100%; }}
    .strategy-header {{ color: var(--accent); font-weight: 800; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 15px; border-bottom: 1px solid var(--border-color); padding-bottom: 8px; }}
    
    /* HUD */
    .hud-container {{ background: linear-gradient(135deg, var(--bg-card), var(--bg-app)); border: 1px solid var(--accent); border-radius: 12px; padding: 20px; display: flex; align-items: center; justify-content: space-between; }}
    .hud-value-large {{ font-size: 3rem; font-weight: 900; color: var(--text-main); }}
    
    /* Checkboxes */
    .stCheckbox label p {{ color: var(--text-main) !important; font-weight: 500; }}
    
    /* Estados */
    .status-sniper {{ background: rgba(16,185,129,0.15); color: var(--accent-green); border: 1px solid var(--accent-green); padding: 10px 20px; border-radius: 50px; font-weight: bold; }}
    .status-warning {{ background: rgba(250,204,21,0.15); color: #d97706; border: 1px solid #facc15; padding: 10px 20px; border-radius: 50px; font-weight: bold; }}
    .status-stop {{ background: rgba(239,68,68,0.15); color: var(--accent-red); border: 1px solid var(--accent-red); padding: 10px 20px; border-radius: 50px; font-weight: bold; }}
    
    .calendar-header {{ color: var(--text-muted) !important; }}
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# 5. FUNCIONES DE BASE DE DATOS
# ==============================================================================
def load_json(fp):
    if not os.path.exists(fp): return {}
    try: with open(fp, "r") as f: return json.load(f)
    except: return {}

def save_json(fp, data):
    try: with open(fp, "w") as f: json.dump(data, f)
    except: pass

def verify_user(u, p):
    if u == "admin" and p == "1234": return True
    d = load_json(USERS_FILE)
    return u in d and d[u] == p

def register_user(u, p): d = load_json(USERS_FILE); d[u] = p; save_json(USERS_FILE, d)
def get_user_accounts(u): d = load_json(ACCOUNTS_FILE); return list(d.get(u, {}).keys()) if u in d else ["Principal"]

def create_account(u, name, bal):
    d = load_json(ACCOUNTS_FILE)
    d.setdefault(u, {})[name] = bal
    save_json(ACCOUNTS_FILE, d)
    save_trade(u, name, None, init=True)

def create_backup_zip():
    shutil.make_archive("backup_trading", 'zip', DATA_DIR)
    return "backup_trading.zip"

def restore_backup(uploaded_file):
    try:
        with zipfile.ZipFile(uploaded_file, 'r') as z: z.extractall(DATA_DIR)
        return True
    except: return False

def delete_trade(u, acc, index):
    fp = os.path.join(DATA_DIR, u, f"{acc}.csv".replace(" ", "_"))
    try:
        df = pd.read_csv(fp)
        df = df.drop(index)
        df.to_csv(fp, index=False)
        get_balance_data.clear() 
        return True
    except: return False

@st.cache_data(ttl=5)
def get_balance_data(u, acc):
    d = load_json(ACCOUNTS_FILE)
    ini = d.get(u, {}).get(acc, 0.0)
    fp = os.path.join(DATA_DIR, u, f"{acc}.csv".replace(" ", "_"))
    if os.path.exists(fp):
        try:
            df = pd.read_csv(fp)
            pnl = df["Dinero"].sum() if not df.empty else 0
        except: df = pd.DataFrame(); pnl = 0
    else: df = pd.DataFrame(); pnl = 0
    return ini, ini + pnl, df

def save_trade(u, acc, data, init=False):
    folder = os.path.join(DATA_DIR, u)
    if not os.path.exists(folder): os.makedirs(folder)
    fp = os.path.join(folder, f"{acc}.csv".replace(" ", "_"))
    cols = ["Fecha","Par","Tipo","Resultado","Dinero","Ratio","Notas"]
    if init:
        if not os.path.exists(fp): pd.DataFrame(columns=cols).to_csv(fp, index=False)
        return
    try: df = pd.read_csv(fp) if os.path.exists(fp) else pd.DataFrame(columns=cols)
    except: df = pd.DataFrame(columns=cols)
    if data:
        df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
        df.to_csv(fp, index=False)
        get_balance_data.clear()

def load_trades(u, acc):
    fp = os.path.join(DATA_DIR, u, f"{acc}.csv".replace(" ", "_"))
    if os.path.exists(fp):
        try: return pd.read_csv(fp)
        except: return pd.DataFrame(columns=["Fecha","Par","Tipo","Resultado","Dinero","Ratio","Notas"])
    return pd.DataFrame(columns=["Fecha","Par","Tipo","Resultado","Dinero","Ratio","Notas"])

# ==============================================================================
# 6. FUNCIONES VISUALES
# ==============================================================================
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

def render_heatmap(df, is_dark):
    if df.empty: return None
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    df['Dia'] = df['Fecha'].dt.day_name()
    grouped = df.groupby('Dia')['Dinero'].sum().reset_index()
    fig = px.bar(grouped, x='Dia', y='Dinero', color='Dinero', color_continuous_scale=['red', 'green'])
    bg = 'rgba(0,0,0,0)'; text_col = '#94a3b8' if is_dark else '#0f172a'
    fig.update_layout(paper_bgcolor=bg, plot_bgcolor=bg, font=dict(color=text_col), title="PnL por Día")
    return fig

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
    for h in ["LUN","MAR","MIÉ","JUE","VIE","SÁB","DOM"]: html += f'<div style="text-align:center; color:{day_col}; font-size:0.8rem; font-weight:bold; padding:5px;">{h}</div>'
    
    for week in cal.monthdayscalendar(y, m):
        for day in week:
            if day == 0: html += '<div style="opacity:0;"></div>'
            else:
                val = data.get(day, 0); txt = f"${val:,.0f}" if val != 0 else ""
                bg = "var(--bg-card)"; border = "var(--border-color)"; col = "var(--text-main)"
                if val > 0: bg="rgba(16,185,129,0.15)"; border="var(--accent-green)"; col="var(--accent-green)"
                elif val < 0: bg="rgba(239,68,68,0.15)"; border="var(--accent-red)"; col="var(--accent-red)"
                html += f'<div style="background:{bg}; border:1px solid {border}; border-radius:8px; min-height:80px; padding:5px; display:flex; flex-direction:column; justify-content:space-between;"><div style="color:var(--text-muted); font-size:0.8rem;">{day}</div><div style="color:{col}; font-weight:bold; text-align:right;">{txt}</div></div>'
    html += '</div>'
    return html, y, m

def change_month(delta):
    d = st.session_state.get('cal_date', datetime.now())
    m, y = d.month + delta, d.year
    if m > 12: m = 1; y += 1
    elif m < 1: m = 12; y -= 1
    st.session_state['cal_date'] = d.replace(year=y, month=m, day=1)

# ==============================================================================
# 7. PANTALLA DE LOGIN
# ==============================================================================
def login_screen():
    inject_theme("Oscuro (Cyber Navy)")
    c1,c2,c3 = st.columns([1,1,1])
    with c2:
        st.markdown("<h1 style='text-align:center; color:var(--accent);'>🦁 Trading Suite AI</h1>", unsafe_allow_html=True)
        t1, t2, t3 = st.tabs(["INGRESAR", "REGISTRARSE", "RESTAURAR"])
        with t1:
            u = st.text_input("Usuario", key="l_u"); p = st.text_input("Password", type="password", key="l_p")
            if st.button("ACCEDER", use_container_width=True, key="b_l"):
                if verify_user(u, p): st.session_state.user = u; st.rerun()
                else: st.error("Error (Prueba: admin/1234)")
        with t2:
            nu = st.text_input("Nuevo Usuario", key="r_u"); np = st.text_input("Nueva Password", type="password", key="r_p")
            if st.button("CREAR CUENTA", use_container_width=True, key="b_r"): register_user(nu, np); st.success("Creado!"); st.rerun()
        with t3:
            uploaded_zip = st.file_uploader("Subir backup.zip", type="zip")
            if uploaded_zip and st.button("RESTAURAR DATOS"):
                try:
                    with zipfile.ZipFile(uploaded_zip, 'r') as z: z.extractall(DATA_DIR)
                    st.success("Datos restaurados. Inicia sesión.")
                except: st.error("Archivo inválido")

# ==============================================================================
# 8. APLICACIÓN PRINCIPAL
# ==============================================================================
def main_app():
    user = st.session_state.user
    if 'cal_date' not in st.session_state: st.session_state['cal_date'] = datetime.now()
    if 'global_pair' not in st.session_state: st.session_state.global_pair = "XAUUSD"
    if 'global_mode' not in st.session_state: st.session_state.global_mode = "Swing (W-D-4H)"
    if 'ai_temp_result' not in st.session_state: st.session_state.ai_temp_result = None
    if 'ai_temp_images' not in st.session_state: st.session_state.ai_temp_images = None

    with st.sidebar:
        st.title(f"👤 {user.upper()}")
        tema = st.radio("🎨 TEMA", ["Oscuro (Cyber Navy)", "Claro (Swiss Design)"], index=0)
        inject_theme(tema)
        is_dark = True if tema == "Oscuro (Cyber Navy)" else False
        
        st.markdown("---")
        with st.expander("🧮 CALCULADORA"):
            c_risk = st.number_input("Riesgo %", 1.0); c_sl = st.number_input("SL (Pips)", 5.0)
            accs = get_user_accounts(user); sel_acc = st.selectbox("Cuenta", accs)
            _, act_bal, _ = get_balance_data(user, sel_acc)
            if c_sl > 0:
                risk_usd = act_bal * (c_risk/100); lots = risk_usd / (c_sl * 10)
                st.success(f"Lotes: **{lots:.2f}** (${risk_usd:.0f})")

        st.markdown("---")
        if st.button("CERRAR SESIÓN", use_container_width=True): st.session_state.user = None; st.rerun()
        
        ini, act, df_bal = get_balance_data(user, sel_acc)
        col_s = "#10b981" if act >= ini else "#ef4444"
        st.markdown(f"""<div style="background:rgba(255,255,255,0.05); padding:15px; border-radius:10px; border:1px solid rgba(255,255,255,0.1); text-align:center;"><div style="color:#94a3b8; font-size:0.8rem;">BALANCE</div><div style="color:{col_s}; font-size:1.8rem; font-weight:bold">${act:,.2f}</div></div>""", unsafe_allow_html=True)
        
        c_new, c_bkp = st.columns(2)
        with c_new:
            with st.popover("➕"):
                na = st.text_input("Nombre"); nb = st.number_input("Capital", 100.0)
                if st.button("Crear"): create_account(user, na, nb); st.rerun()
        with c_bkp:
            zip_path = create_backup_zip()
            with open(zip_path, "rb") as f: st.download_button("💾", f, "backup.zip", "application/zip")

    tabs = st.tabs(["🦁 OPERATIVA", "🧠 IA VISION", "📝 BITÁCORA", "📊 ANALYTICS", "📅 CALENDARIO", "📰 NOTICIAS"])

    # TAB 1: OPERATIVA
    with tabs[0]:
        st.markdown('<div class="strategy-box">', unsafe_allow_html=True)
        c_mod = st.columns([1,2,1])
        with c_mod[1]: st.session_state.global_mode = st.radio("", ["Swing (W-D-4H)", "Scalping (4H-2H-1H)"], horizontal=True, label_visibility="collapsed")
        st.markdown("---"); st.session_state.global_pair = st.text_input("ACTIVO GLOBAL", st.session_state.global_pair).upper()
        st.markdown('</div><br>', unsafe_allow_html=True)

        r1, r2 = st.columns(2)
        total = 0; sos, eng, rr = False, False, False
        with r1:
            st.markdown('<div class="strategy-box"><h5>1. CONTEXTO MACRO</h5>', unsafe_allow_html=True)
            w1 = st.checkbox("Rechazo AOI (+10%)")
            w2 = st.checkbox("Estructura (+10%)")
            w3 = st.checkbox("Patrón (+10%)")
            st.markdown('</div>', unsafe_allow_html=True)
        with r2:
            st.markdown('<div class="strategy-box"><h5>2. GATILLO</h5>', unsafe_allow_html=True)
            sos = st.checkbox("⚡ SOS (Obligatorio)")
            eng = st.checkbox("🕯️ Envolvente (Obligatorio)")
            rr = st.checkbox("💰 Ratio > 1:2.5")
            st.markdown('</div>', unsafe_allow_html=True)
        
        total = (w1+w2+w3)*10 + (sos+eng)*10
        valid = sos and eng and rr
        msg, css = "ESPERAR", "status-warning"
        if valid and total>=50: msg, css = "VALIDO", "status-sniper"
        st.markdown(f"""<div class="hud-container"><div class="hud-stat"><div class="hud-label">TOTAL</div><div class="hud-value-large">{total}%</div></div><div style="flex-grow:1; text-align:center; margin:0 20px;"><span class="{css}">{msg}</span></div></div>""", unsafe_allow_html=True)

    # TAB 2: IA VISION
    with tabs[1]:
        sub_ia = st.tabs(["👁️ ANÁLISIS", "📘 PLAYBOOK"])
        with sub_ia[0]:
            if not init_ai(): st.error("Falta API KEY")
            else:
                c_img, c_res = st.columns([1, 1.5])
                with c_img:
                    col_up1, col_up2, col_up3 = st.columns(3)
                    with col_up1: img1 = st.file_uploader("1. MACRO", type=["jpg","png"], key="u1")
                    with col_up2: img2 = st.file_uploader("2. INTERMEDIO", type=["jpg","png"], key="u2")
                    with col_up3: img3 = st.file_uploader("3. GATILLO", type=["jpg","png"], key="u3")
                    
                    c_tf1, c_tf2, c_tf3 = st.columns(3)
                    with c_tf1: tf1 = st.selectbox("TF 1", ["W", "D"], key="tf1")
                    with c_tf2: tf2 = st.selectbox("TF 2", ["4H", "1H"], key="tf2")
                    with c_tf3: tf3 = st.selectbox("TF 3", ["15M", "5M"], key="tf3")

                    if st.button("🦁 ANALIZAR SINCRONÍA", type="primary", use_container_width=True):
                        images_data = []
                        if img1: images_data.append({'img': Image.open(img1), 'tf': tf1})
                        if img2: images_data.append({'img': Image.open(img2), 'tf': tf2})
                        if img3: images_data.append({'img': Image.open(img3), 'tf': tf3})
                        
                        if not images_data: st.warning("Sube imágenes.")
                        else:
                            with st.spinner("Analizando..."):
                                res = analyze_multiframe(images_data, st.session_state.global_mode, st.session_state.global_pair)
                                st.session_state.ai_temp_result = res
                                st.session_state.ai_temp_images = [x['img'] for x in images_data]
                with c_res:
                    if st.session_state.ai_temp_result:
                        st.markdown('<div class="strategy-box">', unsafe_allow_html=True)
                        st.markdown(st.session_state.ai_temp_result)
                        st.markdown('</div>', unsafe_allow_html=True)

        with sub_ia[1]:
            st.markdown("### 📘 Galería de Maestría")
            brain_data = load_brain()
            wins = [x for x in brain_data if x.get('result') == 'WIN' and x.get('images')]
            if wins:
                for trade in wins:
                    with st.expander(f"🏆 {trade['pair']} - {trade['date'][:16]}"):
                        cols = st.columns(len(trade['images']))
                        for idx, img_path in enumerate(trade['images']):
                            if os.path.exists(img_path): cols[idx].image(img_path)
                        st.write(trade['analysis'])
            else: st.info("Sin trades ganadores guardados.")

    # TAB 3: BITÁCORA
    with tabs[2]:
        c_form, c_hist = st.columns([1, 1.5])
        with c_form:
            st.markdown('<div class="strategy-box">', unsafe_allow_html=True)
            with st.form("reg_trade"):
                dt = st.date_input("Fecha", datetime.now())
                pr = st.text_input("Par", st.session_state.global_pair)
                tp = st.selectbox("Tipo", ["BUY","SELL"]); rs = st.selectbox("Resultado", ["WIN", "LOSS", "BE"])
                mn = st.number_input("PnL ($)", step=10.0); rt = st.number_input("Ratio", 2.5); nt = st.text_area("Notas")
                if st.form_submit_button("GUARDAR"):
                    rm = mn if rs=="WIN" else -abs(mn) if rs=="LOSS" else 0
                    save_trade(user, sel_acc, {"Fecha":dt,"Par":pr,"Tipo":tp,"Resultado":rs,"Dinero":rm,"Ratio":rt,"Notas":nt})
                    
                    if rs == "WIN" and st.session_state.ai_temp_result and st.session_state.ai_temp_images:
                        save_to_brain(st.session_state.ai_temp_result, pr, rs, st.session_state.global_mode, st.session_state.ai_temp_images)
                        st.toast("🧠 ¡Guardado en Playbook!", icon="📸")
                        st.session_state.ai_temp_result = None
                        st.session_state.ai_temp_images = None
                    st.success("Guardado"); st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        
        with c_hist:
            df_h = load_trades(user, sel_acc)
            if not df_h.empty:
                for idx, row in df_h.iterrows():
                    c1, c2 = st.columns([4, 1])
                    with c1: st.info(f"{row['Fecha']} | {row['Par']} | {row['Resultado']} | ${row['Dinero']}")
                    with c2: 
                        if st.button("🗑️", key=f"del_{idx}"):
                            delete_trade(user, sel_acc, idx)
                            st.rerun()
            else: st.info("Sin trades.")

    # TAB 4: ANALYTICS
    with tabs[3]:
        if not df_bal.empty:
            st.markdown("#### 📈 Equity Curve")
            fig = go.Figure(go.Scatter(x=df_bal["Fecha"], y=df_bal["Dinero"].cumsum() + ini, mode='lines+markers'))
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("#### 🔥 Heatmap"); fig_h = render_heatmap(df_bal, is_dark); st.plotly_chart(fig_h, use_container_width=True)
            if st.button("AUDITAR RENDIMIENTO"):
                if init_ai(): st.info(generate_audit_report(df_bal))
        else: st.info("Sin datos")

    # TAB 5: CALENDARIO
    with tabs[4]:
        st.subheader(f"📅 Visual P&L")
        c_p, c_t, c_n = st.columns([1,5,1])
        with c_p: 
            if st.button("⬅️"): change_month(-1); st.rerun()
        with c_n: 
            if st.button("➡️"): change_month(1); st.rerun()
        _, _, df = get_balance_data(user, sel_acc)
        html, y, m = render_cal_html(df, is_dark)
        with c_t: st.markdown(f"<h3 style='text-align:center; color:var(--text-main); margin:0'>{calendar.month_name[m]} {y}</h3>", unsafe_allow_html=True)
        st.markdown(html, unsafe_allow_html=True)

    # TAB 6: NOTICIAS
    with tabs[5]:
        tv = "dark" if is_dark else "light"
        html = f"""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-events.js" async>{{"colorTheme": "{tv}","isTransparent": true,"width": "100%","height": "800","locale": "es","importanceFilter": "-1,0","currencyFilter": "USD,EUR,GBP,JPY,AUD,CAD,CHF,NZD"}}</script></div>"""
        components.html(html, height=800)

if 'user' not in st.session_state: st.session_state.user = None
if st.session_state.user: main_app()
else: login_screen()
