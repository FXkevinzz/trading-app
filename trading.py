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

# ==========================================
# 1. CONFIGURACIÓN INICIAL
# ==========================================
st.set_page_config(
    page_title="Trading Pro Suite AI", 
    layout="wide", 
    page_icon="🦁",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. GESTIÓN DE DIRECTORIOS Y ARCHIVOS
# ==========================================
DATA_DIR = "user_data"
IMG_DIR = "fotos"
BRAIN_FILE = os.path.join(DATA_DIR, "brain_data.json") # Base de datos de la IA

# Crear carpetas si no existen
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

if not os.path.exists(IMG_DIR):
    os.makedirs(IMG_DIR) # Asegúrate de poner tus fotos aquí

USERS_FILE = os.path.join(DATA_DIR, "users.json")
ACCOUNTS_FILE = os.path.join(DATA_DIR, "accounts_config.json")

# ==========================================
# 3. INTELIGENCIA ARTIFICIAL (CEREBRO)
# ==========================================
def init_ai():
    """Inicializa la conexión con Google Gemini."""
    if "GEMINI_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_KEY"])
        return True
    return False

def load_brain():
    """Carga el historial de aprendizaje de la IA."""
    if not os.path.exists(BRAIN_FILE):
        return []
    try:
        with open(BRAIN_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_to_brain(pair, timeframe, result, mode, analysis_text, notes):
    """
    Guarda el trade en la memoria de la IA para futuro aprendizaje.
    Guarda WIN, LOSS y BE para evitar sesgos.
    """
    memory = load_brain()
    new_memory = {
        "timestamp": str(datetime.now()),
        "pair": pair,
        "timeframe": timeframe,
        "strategy_mode": mode,
        "result": result,       # WIN / LOSS / BE
        "analysis": analysis_text,
        "user_notes": notes
    }
    memory.append(new_memory)
    try:
        with open(BRAIN_FILE, "w") as f:
            json.dump(memory, f, indent=4)
    except Exception as e:
        st.error(f"Error guardando en cerebro: {e}")

def generate_performance_audit(df):
    """Genera una auditoría de riesgo basada en el CSV de trades."""
    if df.empty:
        return "No hay suficientes datos registrados para realizar una auditoría."
    
    # Preparamos los datos para que la IA los lea
    data_str = df.to_string(index=False)
    
    prompt = f"""
    Actúa como un Auditor de Riesgo Senior de un Fondo de Inversión (Prop Firm).
    Tu objetivo es analizar los datos crudos de este trader y encontrar patrones.

    DATOS DEL TRADER (CSV):
    {data_str}

    TU MISIÓN - DETECTA Y RESPONDE:
    1. 🚨 FUGA DE CAPITAL: ¿Dónde está perdiendo más dinero? (Analiza Pares, Horas o Días si están disponibles, o Patrones de Loss).
    2. ✅ ZONA DE PODER: ¿En qué activo o dirección (Buy/Sell) es más rentable?
    3. 🧠 PSICOLOGÍA: ¿Ves patrones de sobre-operativa o ratios negativos?
    4. 💡 CONSEJO ACCIONABLE: Una instrucción directa para mejorar la rentabilidad esta semana.
    """
    
    # Intentamos modelos en orden de capacidad/velocidad
    modelos = ['gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-1.5-pro']
    
    for m in modelos:
        try:
            model = genai.GenerativeModel(m)
            response = model.generate_content(prompt)
            return response.text
        except:
            continue
            
    return "Error: No se pudo conectar con el Auditor IA. Verifica tu conexión o API Key."

def analyze_chart(image, mode, pair, tf):
    """Analiza un gráfico subido usando Visión Computacional + Estrategia Set & Forget."""
    
    # 1. Recuperar contexto (RAG)
    brain = load_brain()
    context = ""
    if brain:
        # Filtramos solo los WINS para usarlos como ejemplos de "lo que buscamos"
        wins = [entry for entry in brain if entry.get('result') == 'WIN']
        # Tomamos los últimos 3 ejemplos
        examples = wins[-3:] if len(wins) >= 3 else wins
        if examples:
            context = f"REFERENCIA: Aquí tienes ejemplos de tus mejores trades pasados:\n{str(examples)}\n\n"
    
    # 2. Prompt del Sistema (Basado estrictamente en tu PDF)
    prompt = f"""
    Eres un Mentor de Trading Institucional experto en la estrategia 'Set & Forget' (Alex G).
    Tu trabajo es validar si el gráfico cumple las reglas estrictas del PDF.
    
    ESTRATEGIA ACTIVA: {mode}
    ACTIVO: {pair} | TEMPORALIDAD: {tf}
    
    {context}
    
    ANALIZA LA IMAGEN BUSCANDO ESTAS REGLAS DE ORO:
    1. TENDENCIA Y SINCRONIZACIÓN: ¿Hay alineación entre temporalidades (Ej: W y D alcistas)?
    2. ZONA (AOI): ¿El precio está reaccionando en una zona de Oferta/Demanda válida o rebotando en la EMA?
    3. GATILLO (VELAS): ¿Ves una Vela Envolvente (Engulfing), Morning/Evening Star o Pinbar clara?
    
    IMPORTANTE: Si no hay 'Shift of Structure' o 'Patrón de Vela', el trade es inválido.
    
    Responde con este formato exacto:
    🎯 VEREDICTO: [APROBADO / DUDOSO / DENEGADO]
    📊 PROBABILIDAD: 0-100% (Basado en la calidad del setup)
    📝 ANÁLISIS TÉCNICO: (Explica Estructura, AOI y Patrón detectado)
    💡 CONSEJO: (Gestión de riesgo: SL 5-7 pips y TP en liquidez)
    """
    
    # 3. Ejecución con Cascada de Modelos
    modelos = ['gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-1.5-pro']
    
    for m in modelos:
        try:
            model = genai.GenerativeModel(m)
            response = model.generate_content([prompt, image])
            return response.text
        except:
            continue
            
    return "Error de conexión IA. Verifica tu API Key."

# ==========================================
# 4. SISTEMA DE TEMAS Y CSS (ESTILOS)
# ==========================================
def inject_theme(theme_mode):
    if theme_mode == "Claro (Swiss Design)":
        # --- MODO CLARO ---
        css_vars = """
            --bg-app: #f8fafc;
            --bg-card: #ffffff;
            --bg-sidebar: #1e293b; /* Sidebar oscura para contraste */
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
        # --- MODO OSCURO (Cyber Navy) ---
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
    
    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
    }}

    /* FONDO Y TEXTOS */
    .stApp {{
        background-color: var(--bg-app);
        color: var(--text-main);
    }}
    
    h1, h2, h3, h4, h5, p, li, span, div, label {{
        color: var(--text-main) !important;
    }}
    
    .stMarkdown p {{
        color: var(--text-main) !important;
    }}
    
    /* SIDEBAR (SIEMPRE OSCURA PARA CONTRASTE) */
    [data-testid="stSidebar"] {{
        background-color: var(--bg-sidebar) !important;
        border-right: 1px solid var(--border-color);
    }}
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {{
        color: #f8fafc !important;
    }}
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label {{
        color: #94a3b8 !important;
    }}
    
    /* INPUTS (ESTILO MODERNO) */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {{
        background-color: var(--input-bg) !important;
        color: var(--text-main) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px;
        padding: 10px;
        transition: border 0.3s;
    }}
    
    .stTextInput input:focus, .stNumberInput input:focus {{
        border-color: var(--accent) !important;
    }}
    
    .stSelectbox svg, .stDateInput svg {{
        fill: var(--text-muted) !important;
    }}
    
    /* CHECKBOXES */
    .stCheckbox label p {{
        font-weight: 500;
    }}
    
    /* MENUS DESPLEGABLES */
    ul[data-baseweb="menu"] {{
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border-color);
    }}
    li[data-baseweb="option"] {{
        color: var(--text-main) !important;
    }}
    
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
    .stButton button:hover {{
        opacity: 0.9;
        transform: translateY(-1px);
    }}
    .stButton button:active {{
        transform: translateY(1px);
    }}
    
    /* TABS (CÁPSULA FLOTANTE) */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        padding-bottom: 15px;
    }}
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
        height: 100%;
    }}
    .strategy-header {{
        color: var(--accent);
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 15px;
        border-bottom: 1px solid var(--border-color);
        padding-bottom: 8px;
    }}
    
    /* EXPANDER (ACORDEON) */
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
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}
    .hud-value-large {{
        font-size: 3rem;
        font-weight: 900;
        color: var(--text-main);
        line-height: 1;
    }}
    
    /* ESTADOS DE ALERTA */
    .status-sniper {{
        background-color: rgba(16, 185, 129, 0.15);
        color: var(--accent-green);
        border: 1px solid var(--accent-green);
        padding: 10px 20px;
        border-radius: 50px;
        font-weight: bold;
    }}
    .status-warning {{
        background-color: rgba(250, 204, 21, 0.15);
        color: #d97706;
        border: 1px solid #facc15;
        padding: 10px 20px;
        border-radius: 50px;
        font-weight: bold;
    }}
    .status-stop {{
        background-color: rgba(239, 68, 68, 0.15);
        color: var(--accent-red);
        border: 1px solid var(--accent-red);
        padding: 10px 20px;
        border-radius: 50px;
        font-weight: bold;
    }}
    
    /* CALENDARIO */
    .calendar-header {{
        color: var(--text-muted) !important;
        font-size: 0.75rem;
        text-transform: uppercase;
    }}
    
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 5. FUNCIONES DE BACKEND (DATOS)
# ==========================================
def load_json(fp):
    if not os.path.exists(fp): return {}
    try:
        with open(fp, "r") as f:
            return json.load(f)
    except: return {}

def save_json(fp, data):
    try:
        with open(fp, "w") as f:
            json.dump(data, f)
    except: pass

def verify_user(u, p):
    # PUERTA TRASERA DE SEGURIDAD
    if u == "admin" and p == "1234": return True
    d = load_json(USERS_FILE)
    return u in d and d[u] == p

def register_user(u, p):
    d = load_json(USERS_FILE)
    d[u] = p
    save_json(USERS_FILE, d)

def get_user_accounts(u):
    d = load_json(ACCOUNTS_FILE)
    return list(d.get(u, {}).keys()) if u in d else ["Principal"]

def create_account(u, name, bal):
    d = load_json(ACCOUNTS_FILE)
    if u not in d: d[u] = {}
    if name not in d[u]:
        d[u][name] = bal
        save_json(ACCOUNTS_FILE, d)
        save_trade(u, name, None, init=True)

def get_balance_data(u, acc):
    d = load_json(ACCOUNTS_FILE)
    ini = d.get(u, {}).get(acc, 0.0)
    fp = os.path.join(DATA_DIR, u, f"{acc}.csv".replace(" ", "_"))
    
    if os.path.exists(fp):
        try:
            df = pd.read_csv(fp)
            pnl = df["Dinero"].sum() if not df.empty else 0
        except:
            df = pd.DataFrame()
            pnl = 0
    else:
        df = pd.DataFrame()
        pnl = 0
        
    return ini, ini + pnl, df

def save_trade(u, acc, data, init=False):
    folder = os.path.join(DATA_DIR, u)
    if not os.path.exists(folder): os.makedirs(folder)
    fp = os.path.join(folder, f"{acc}.csv".replace(" ", "_"))
    
    cols = ["Fecha","Par","Tipo","Resultado","Dinero","Ratio","Notas"]
    
    if init:
        if not os.path.exists(fp): pd.DataFrame(columns=cols).to_csv(fp, index=False)
        return

    try:
        df = pd.read_csv(fp) if os.path.exists(fp) else pd.DataFrame(columns=cols)
    except:
        df = pd.DataFrame(columns=cols)
        
    if data:
        df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
        df.to_csv(fp, index=False)

def load_trades(u, acc):
    fp = os.path.join(DATA_DIR, u, f"{acc}.csv".replace(" ", "_"))
    cols = ["Fecha","Par","Tipo","Resultado","Dinero","Ratio","Notas"]
    if os.path.exists(fp):
        try:
            return pd.read_csv(fp)
        except:
            return pd.DataFrame(columns=cols)
    return pd.DataFrame(columns=cols)

# ==========================================
# 6. FUNCIONES VISUALES AUXILIARES
# ==========================================
def mostrar_imagen(nombre, caption):
    local = os.path.join(IMG_DIR, nombre)
    if os.path.exists(local):
        st.image(local, caption=caption, use_container_width=True)
    else:
        # Fallback para evitar errores visuales si faltan imágenes
        st.warning(f"Imagen no encontrada: {nombre}")

def change_month(delta):
    d = st.session_state.get('cal_date', datetime.now())
    m, y = d.month + delta, d.year
    if m > 12:
        m = 1
        y += 1
    elif m < 1:
        m = 12
        y -= 1
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
                
                bg = "var(--bg-card)"
                border = "var(--border-color)"
                col = "var(--text-main)"
                
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

# ==========================================
# 7. PANTALLA DE LOGIN
# ==========================================
def login_screen():
    inject_theme("Oscuro (Cyber Navy)")
    c1,c2,c3 = st.columns([1,1,1])
    with c2:
        st.markdown("<h1 style='text-align:center; color:var(--accent);'>🦁 Trading Suite AI</h1>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["INGRESAR", "REGISTRARSE"])
        
        with t1:
            u = st.text_input("Usuario", key="l_u")
            p = st.text_input("Password", type="password", key="l_p")
            if st.button("ACCEDER", use_container_width=True, key="b_l"):
                if verify_user(u, p): 
                    st.session_state.user = u
                    st.rerun()
                else: 
                    st.error("Error (Prueba: admin/1234)")
        
        with t2:
            nu = st.text_input("Nuevo Usuario", key="r_u")
            np = st.text_input("Nueva Password", type="password", key="r_p")
            if st.button("CREAR CUENTA", use_container_width=True, key="b_r"):
                if nu and np: 
                    register_user(nu, np)
                    st.success("Creado!")
                    st.rerun()

# ==========================================
# 8. APLICACIÓN PRINCIPAL
# ==========================================
def main_app():
    user = st.session_state.user
    
    # Variables globales de sesión
    if 'cal_date' not in st.session_state: st.session_state['cal_date'] = datetime.now()
    if 'global_pair' not in st.session_state: st.session_state.global_pair = "XAUUSD"
    if 'global_mode' not in st.session_state: st.session_state.global_mode = "Swing (W-D-4H)"
    if 'ai_temp_result' not in st.session_state: st.session_state.ai_temp_result = None

    with st.sidebar:
        st.title(f"👤 {user.upper()}")
        tema = st.radio("🎨 TEMA", ["Oscuro (Cyber Navy)", "Claro (Swiss Design)"], index=0)
        inject_theme(tema)
        is_dark = True if tema == "Oscuro (Cyber Navy)" else False
        
        st.markdown("---")
        if st.button("CERRAR SESIÓN", use_container_width=True): 
            st.session_state.user = None
            st.rerun()
        
        accs = get_user_accounts(user)
        sel_acc = st.selectbox("📂 CUENTA ACTIVA", accs)
        ini, act, _ = get_balance_data(user, sel_acc)
        
        col_s = "#10b981" if act >= ini else "#ef4444"
        st.markdown(f"""
        <div style="background:rgba(255,255,255,0.05); padding:15px; border-radius:10px; border:1px solid rgba(255,255,255,0.1); text-align:center;">
            <div style="color:#94a3b8; font-size:0.8rem;">BALANCE</div>
            <div style="color:{col_s}; font-size:1.8rem; font-weight:bold">${act:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("➕ NUEVA CUENTA"):
            na = st.text_input("Nombre")
            nb = st.number_input("Capital", 100.0)
            if st.button("CREAR"): 
                create_account(user, na, nb)
                st.rerun()

    tabs = st.tabs(["🦁 OPERATIVA", "🧠 IA VISION", "📝 BITÁCORA", "📊 ANALYTICS", "📅 CALENDARIO", "📰 NOTICIAS"])

    # --- TAB 1: OPERATIVA MANUAL ---
    with tabs[0]:
        # Guía Visual
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
        
        # Sincronización Global
        st.markdown('<div class="strategy-box">', unsafe_allow_html=True)
        c_mod = st.columns([1,2,1])
        with c_mod[1]: 
            st.session_state.global_mode = st.radio("", ["Swing (W-D-4H)", "Scalping (4H-2H-1H)"], horizontal=True, label_visibility="collapsed")
        
        st.markdown("---")
        st.session_state.global_pair = st.text_input("ACTIVO A OPERAR (Sincronizado)", st.session_state.global_pair).upper()
        st.markdown('</div><br>', unsafe_allow_html=True)
        
        # --- CHECKLIST DETALLADO (ESTRATEGIA PDF) ---
        r1_c1, r1_c2 = st.columns(2)
        r2_c1, r2_c2 = st.columns(2)
        total = 0; sos, eng, rr = False, False, False
        modo = st.session_state.global_mode

        def header(t): return f"<div class='strategy-header'>{t}</div>"

        if "Swing" in modo:
            with r1_c1:
                st.markdown('<div class="strategy-box">', unsafe_allow_html=True)
                st.markdown(header("1. CONTEXTO SEMANAL (W)"), unsafe_allow_html=True)
                tw = st.selectbox("Tendencia W", ["Alcista", "Bajista"], key="tw")
                w_sc = sum([
                    st.checkbox("Rechazo en AOI (+10%)", key="w1")*10,
                    st.checkbox("Rechazo Estructura Previa (+10%)", key="w2")*10,
                    st.checkbox("Patrón de Vela (Rechazo) (+10%)", key="w3")*10,
                    st.checkbox("Patrón Mercado (H&S, Doble) (+10%)", key="w4")*10,
                    st.checkbox("Rechazo EMA 50 (+5%)", key="w5")*5,
                    st.checkbox("Nivel Psicológico (+5%)", key="w6")*5
                ])
                st.markdown('</div>', unsafe_allow_html=True)
            
            with r1_c2:
                st.markdown('<div class="strategy-box">', unsafe_allow_html=True)
                st.markdown(header("2. CONTEXTO DIARIO (D)"), unsafe_allow_html=True)
                td = st.selectbox("Tendencia D", ["Alcista", "Bajista"], key="td")
                d_sc = sum([
                    st.checkbox("Rechazo en AOI (+10%)", key="d1")*10,
                    st.checkbox("Rechazo Estructura Previa (+10%)", key="d2")*10,
                    st.checkbox("Patrón de Vela (Rechazo) (+10%)", key="d3")*10,
                    st.checkbox("Patrón Mercado (+10%)", key="d4")*10,
                    st.checkbox("Rechazo EMA 50 (+5%)", key="d5")*5
                ])
                st.markdown('</div>', unsafe_allow_html=True)

            with r2_c1:
                st.markdown('<div class="strategy-box" style="margin-top:20px">', unsafe_allow_html=True)
                st.markdown(header("3. EJECUCIÓN (4H)"), unsafe_allow_html=True)
                t4 = st.selectbox("Tendencia 4H", ["Alcista", "Bajista"], key="t4")
                h4_sc = sum([
                    st.checkbox("Rechazo Vela (+10%)", key="h1")*10,
                    st.checkbox("Patrón Mercado (+10%)", key="h2")*10,
                    st.checkbox("Rechazo Estructura Previa (+5%)", key="h3")*5,
                    st.checkbox("EMA 50 (+5%)", key="h4")*5
                ])
                st.markdown('</div>', unsafe_allow_html=True)
            
            with r2_c2:
                st.markdown('<div class="strategy-box" style="margin-top:20px">', unsafe_allow_html=True)
                st.markdown(header("4. GATILLO FINAL"), unsafe_allow_html=True)
                if tw==td==t4: st.success("💎 TRIPLE ALINEACIÓN (W+D+4H)")
                elif tw==td: st.info("✅ SWING SYNC (W+D)")
                
                sos = st.checkbox("⚡ Shift of Structure (SOS) [Obligatorio]")
                eng = st.checkbox("🕯️ Vela Envolvente [Obligatorio]")
                pat_ent = st.checkbox("Patrón en Entrada (+5%)")
                rr = st.checkbox("💰 Ratio Mínimo 1:2.5")
                
                entry_score = sum([sos*10, eng*10, pat_ent*5])
                total = w_sc + d_sc + h4_sc + entry_score

        else: # Scalping
            # Lógica de Scalping (Simplificada para no alargar, pero funcional)
            with r1_c1:
                st.markdown('<div class="strategy-box">', unsafe_allow_html=True)
                st.markdown(header("1. CONTEXTO (4H)"), unsafe_allow_html=True)
                t4 = st.selectbox("Trend 4H", ["Alcista", "Bajista"], key="s4")
                w_sc = sum([st.checkbox("AOI (+5%)", key="sc1")*5, st.checkbox("Estructura (+5%)", key="sc2")*5, st.checkbox("Patrón (+5%)", key="sc3")*5, st.checkbox("EMA 50 (+5%)", key="sc4")*5, st.checkbox("Psicológico (+5%)", key="sc5")*5])
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
                if t4==t2==t1: st.success("💎 TRIPLE ALINEACIÓN")
                sos = st.checkbox("⚡ SOS"); eng = st.checkbox("🕯️ Entrada"); pat_ent = st.checkbox("Patrón (+5%)"); rr = st.checkbox("💰 Ratio")
                entry_score = sum([sos*10, eng*10, pat_ent*5])
                total = w_sc + d_sc + h4_sc + entry_score + 15

        # HUD DE PUNTUACIÓN
        st.markdown("<br>", unsafe_allow_html=True)
        valid = sos and eng and rr
        
        msg, css_cl = "💤 ESPERAR", "status-warning"
        if not sos: msg, css_cl = "⛔ FALTA SOS", "status-stop"
        elif not eng: msg, css_cl = "⚠️ FALTA VELA DE ENTRADA", "status-warning"
        elif not rr: msg, css_cl = "💸 RATIO BAJO", "status-warning"
        elif total >= 90: msg, css_cl = "💎 SNIPER ENTRY (A+)", "status-sniper"
        elif total >= 60 and valid: msg, css_cl = "✅ TRADE VÁLIDO", "status-sniper"
        
        st.markdown(f"""
        <div class="hud-container">
            <div class="hud-stat"><div class="hud-label">PUNTAJE</div><div class="hud-value-large">{total}%</div></div>
            <div style="flex-grow:1; text-align:center; margin:0 20px;"><span class="{css_cl}">{msg}</span></div>
            <div class="hud-stat"><div class="hud-label">ESTADO</div><div style="font-size:1.5rem; font-weight:bold; color:{'var(--accent-green)' if valid else 'var(--accent-red)'}">{'LISTO' if valid else 'PENDIENTE'}</div></div>
        </div>
        """, unsafe_allow_html=True)
        st.progress(min(total, 100))

    # --- TAB 2: IA VISION ---
    with tabs[1]:
        st.markdown(f"<h3 style='color:var(--accent)'>🧠 Mentor IA</h3>", unsafe_allow_html=True)
        if not init_ai():
            st.error("⚠️ API KEY NO DETECTADA.")
        else:
            c_img, c_res = st.columns([1, 1.5])
            with c_img:
                uploaded_file = st.file_uploader("Sube tu captura", type=["jpg", "png", "jpeg"])
                if uploaded_file:
                    image = Image.open(uploaded_file)
                    st.image(image, caption="Gráfico", use_container_width=True)
                    st.markdown("---")
                    ai_pair = st.text_input("Par", st.session_state.global_pair, disabled=True)
                    ai_tf = st.selectbox("Temporalidad", ["M15", "H1", "H4", "Daily"])
                    
                    if st.button("🦁 ANALIZAR CON IA", type="primary", use_container_width=True):
                        with st.spinner("Analizando Estructura, AOI y Velas..."):
                            res_text = analyze_chart(image, st.session_state.global_mode, ai_pair, ai_tf)
                            st.session_state.ai_temp_result = res_text
            
            with c_res:
                if st.session_state.ai_temp_result:
                    st.markdown('<div class="strategy-box">', unsafe_allow_html=True)
                    st.markdown("### 🤖 Veredicto del Mentor")
                    st.markdown(st.session_state.ai_temp_result)
                    st.markdown('</div>', unsafe_allow_html=True)
                    st.info("Este análisis se guardará en el cerebro automáticamente si registras el trade.")

    # --- TAB 3: BITÁCORA ---
    with tabs[2]:
        c_form, c_hist = st.columns([1, 1.5])
        
        with c_form:
            st.markdown(f"<h3 style='color:var(--accent)'>📝 Registrar Trade</h3>", unsafe_allow_html=True)
            st.markdown('<div class="strategy-box">', unsafe_allow_html=True)
            with st.form("reg_trade"):
                dt = st.date_input("Fecha", datetime.now())
                pr = st.text_input("Par", st.session_state.global_pair)
                tp = st.selectbox("Tipo", ["BUY","SELL"])
                rs = st.selectbox("Resultado", ["WIN", "LOSS", "BE"])
                mn = st.number_input("Monto PnL ($)", min_value=0.0, step=10.0, help="Pon valor positivo")
                rt = st.number_input("Ratio", value=2.5)
                nt = st.text_area("Notas")
                
                if st.form_submit_button("GUARDAR TRADE", use_container_width=True):
                    # Lógica de guardado
                    real_mn = mn if rs=="WIN" else -mn if rs=="LOSS" else 0
                    save_trade(user, sel_acc, {"Fecha":dt,"Par":pr,"Tipo":tp,"Resultado":rs,"Dinero":real_mn,"Ratio":rt,"Notas":nt})
                    
                    # Guardar en Cerebro IA (Cualquier resultado)
                    if st.session_state.ai_temp_result:
                        save_to_brain(st.session_state.global_pair, "Auto", rs, st.session_state.global_mode, st.session_state.ai_temp_result, nt)
                        st.toast("🧠 ¡Cerebro actualizado!", icon="🦁")
                        st.session_state.ai_temp_result = None
                        
                    st.success("Guardado!"); st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        with c_hist:
            st.markdown(f"<h3 style='color:var(--accent)'>📜 Historial</h3>", unsafe_allow_html=True)
            df_h = load_trades(user, sel_acc)
            if not df_h.empty:
                df_h['Fecha'] = pd.to_datetime(df_h['Fecha'])
                df_h = df_h.sort_values("Fecha", ascending=False)
                for d in df_h['Fecha'].dt.date.unique():
                    dd = df_h[df_h['Fecha'].dt.date == d]
                    pnl = dd['Dinero'].sum()
                    icon = "🟢" if pnl >= 0 else "🔴"
                    with st.expander(f"{icon} {d} | PnL: ${pnl:,.2f}"): st.dataframe(dd)
            else: st.info("Sin trades.")

    # --- TAB 4: ANALYTICS ---
    with tabs[3]:
        st.markdown(f"<h3 style='color:var(--accent)'>📊 Rendimiento</h3>", unsafe_allow_html=True)
        _, _, df = get_balance_data(user, sel_acc)
        if not df.empty:
            st.markdown("#### 📈 Curva de Crecimiento")
            df = df.sort_values("Fecha")
            fechas = [df["Fecha"].iloc[0]] if not df.empty else [datetime.now().date()]
            valores = [ini]; acum = ini
            for _, r in df.iterrows():
                fechas.append(r["Fecha"]); acum += r["Dinero"]; valores.append(acum)
            
            line_col = "#3b82f6" if is_dark else "#2563eb"
            text_col = "#94a3b8" if is_dark else "#0f172a"
            fig = go.Figure(go.Scatter(x=fechas, y=valores, mode='lines+markers', line=dict(color=line_col, width=3), fill='tozeroy'))
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color=text_col), xaxis=dict(showgrid=False))
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            st.markdown(f"<h3 style='color:var(--accent)'>🕵️ Auditor IA</h3>", unsafe_allow_html=True)
            if st.button("AUDITAR MI RENDIMIENTO", type="primary"):
                if not init_ai(): st.error("Falta API Key")
                else:
                    with st.spinner("Auditando..."):
                        st.info(generate_performance_audit(df))
        else: st.info("Sin datos")

    # --- TAB 5: CALENDARIO ---
    with tabs[4]:
        st.subheader(f"📅 Visual P&L")
        c_p, c_t, c_n = st.columns([1,5,1])
        with c_p: 
            if st.button("⬅️", use_container_width=True): change_month(-1); st.rerun()
        with c_n: 
            if st.button("➡️", use_container_width=True): change_month(1); st.rerun()
        _, _, df = get_balance_data(user, sel_acc)
        html, y, m = render_cal_html(df, is_dark)
        with c_t: st.markdown(f"<h3 style='text-align:center; color:var(--text-main); margin:0'>{calendar.month_name[m]} {y}</h3>", unsafe_allow_html=True)
        st.markdown(html, unsafe_allow_html=True)

    # --- TAB 6: NOTICIAS ---
    with tabs[5]:
        st.markdown(f"<h3 style='color:var(--accent)'>📰 Calendario Económico</h3>", unsafe_allow_html=True)
        tv_theme = "dark" if is_dark else "light"
        html_code = f"""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-events.js" async>{{"colorTheme": "{tv_theme}","isTransparent": true,"width": "100%","height": "800","locale": "es","importanceFilter": "-1,0","currencyFilter": "USD,EUR,GBP,JPY,AUD,CAD,CHF,NZD"}}</script></div>"""
        components.html(html_code, height=800, scrolling=True)

if 'user' not in st.session_state: st.session_state.user = None
if st.session_state.user: main_app()
else: login_screen()
