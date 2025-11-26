import streamlit as st
import pandas as pd
import os
import json
import calendar
from datetime import datetime
import plotly.graph_objects as go
import pytz

# --- 1. CONFIGURACIÓN DE PÁGINA (SIEMPRE PRIMERO) ---
st.set_page_config(page_title="Trading Pro Suite", layout="wide", page_icon="🦁")

# --- 2. ESTILOS CSS (ALTO CONTRASTE CORREGIDO) ---
st.markdown("""
    <style>
    /* FORZAR MODO OSCURO GLOBAL */
    .stApp {
        background-color: #000000 !important;
    }
    
    /* FORZAR TEXTOS A BLANCO */
    h1, h2, h3, h4, h5, h6, p, span, div, label, li {
        color: #e0e0e0 !important;
    }
    
    /* INPUTS (Cajas de texto y números) */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: #1a1a1a !important;
        color: #ffffff !important;
        border: 1px solid #444 !important;
    }
    
    /* PESTAÑAS (TABS) */
    .stTabs [data-baseweb="tab-list"] button {
        background-color: #111 !important;
        color: #888 !important;
    }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        background-color: #333 !important;
        color: #00ff00 !important;
        border-top: 2px solid #00ff00 !important;
    }

    /* BOTONES */
    button {
        border: 1px solid #444 !important;
        color: white !important;
    }

    /* CALENDARIO */
    .calendar-container { 
        display: grid; 
        grid-template-columns: repeat(7, 1fr); 
        gap: 5px; 
        margin-top: 10px; 
    }
    .calendar-header { 
        background: #222; 
        color: #ff9900 !important; 
        text-align: center; 
        padding: 8px; 
        font-weight: bold; 
        border-radius: 4px; 
    }
    .calendar-day { 
        min-height: 100px; 
        background: #0a0a0a; 
        padding: 8px; 
        display: flex; 
        flex-direction: column; 
        justify-content: space-between; 
        border-radius: 6px; 
        border: 1px solid #333;
    }
    .day-num { color: #666 !important; font-size: 0.9em; font-weight: bold; }
    .day-val { text-align: right; font-weight: bold; font-size: 1.1em; }
    
    /* COLORES DE RESULTADOS */
    .win-text { color: #00ff00 !important; }
    .loss-text { color: #ff3333 !important; }
    
    /* ALERTAS / PLAN */
    .plan-box {
        border-left: 5px solid #4CAF50; 
        padding: 15px; 
        background-color: #0d1a0d; 
        border-radius: 5px; 
        margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. GESTIÓN DE DIRECTORIOS ---
DATA_DIR = "user_data"
IMG_DIR = "fotos"
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
USERS_FILE = os.path.join(DATA_DIR, "users.json")
ACCOUNTS_FILE = os.path.join(DATA_DIR, "accounts_config.json")

# --- 4. FUNCIONES BACKEND ---
def load_json(filepath):
    if not os.path.exists(filepath): return {}
    try:
        with open(filepath, "r") as f: return json.load(f)
    except: return {}

def save_json(filepath, data):
    with open(filepath, "w") as f: json.dump(data, f)

def verify_user(username, password):
    users = load_json(USERS_FILE)
    return username in users and users[username] == password

def register_user(username, password):
    users = load_json(USERS_FILE)
    users[username] = password
    save_json(USERS_FILE, users)

def get_user_folder(username):
    folder = os.path.join(DATA_DIR, username)
    if not os.path.exists(folder): os.makedirs(folder)
    return folder

def get_account_file(username, account_name):
    clean = "".join(c for c in account_name if c.isalnum() or c in (' ', '_')).strip().replace(" ", "_")
    return os.path.join(get_user_folder(username), f"{clean}.csv")

def get_user_accounts(username):
    configs = load_json(ACCOUNTS_FILE)
    if username in configs: return list(configs[username].keys())
    return ["Principal"]

def create_account(username, account_name, initial_balance):
    configs = load_json(ACCOUNTS_FILE)
    if username not in configs: configs[username] = {}
    if account_name not in configs[username]:
        configs[username][account_name] = initial_balance
        save_json(ACCOUNTS_FILE, configs)
        file_path = get_account_file(username, account_name)
        if not os.path.exists(file_path):
            df = pd.DataFrame(columns=["Fecha", "Par", "Tipo", "Resultado", "Dinero", "Ratio", "Notas"])
            df.to_csv(file_path, index=False)

def get_account_balance(username, account_name):
    configs = load_json(ACCOUNTS_FILE)
    initial = configs.get(username, {}).get(account_name, 0)
    file_path = get_account_file(username, account_name)
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        total_pnl = df["Dinero"].sum()
    else: total_pnl = 0
    return initial, initial + total_pnl

def guardar_trade(username, account_name, data):
    file_path = get_account_file(username, account_name)
    if os.path.exists(file_path): df = pd.read_csv(file_path)
    else: df = pd.DataFrame(columns=["Fecha", "Par", "Tipo", "Resultado", "Dinero", "Ratio", "Notas"])
    new = pd.DataFrame([data])
    df = pd.concat([df, new], ignore_index=True)
    df.to_csv(file_path, index=False)

# --- 5. FUNCIÓN IMÁGENES ---
def mostrar_imagen(nombre_archivo, caption):
    # Intentar cargar local
    ruta_local = os.path.join(IMG_DIR, nombre_archivo)
    if os.path.exists(ruta_local):
        st.image(ruta_local, caption=caption, use_container_width=True)
    else:
        # Links de respaldo
        links = {
            "bullish_engulfing.png": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/Candlestick_Pattern_Bullish_Engulfing.png/320px-Candlestick_Pattern_Bullish_Engulfing.png",
            "morning_star.png": "https://a.c-dn.net/b/1XlqMQ/Morning-Star-Candlestick-Pattern_body_MorningStar.png.full.png",
            "bearish_engulfing.png": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/19/Candlestick_Pattern_Bearish_Engulfing.png/320px-Candlestick_Pattern_Bearish_Engulfing.png",
            "shooting_star.png": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/67/Candlestick_Pattern_Shooting_Star.png/320px-Candlestick_Pattern_Shooting_Star.png"
        }
        if nombre_archivo in links: st.image(links[nombre_archivo], caption=caption, use_container_width=True)
        else: st.warning(f"⚠️ Imagen faltante: {nombre_archivo}")

# --- 6. FUNCIONES VISUALES (CALENDARIO) ---
def change_month(amount):
    current_date = st.session_state.get('cal_date', datetime.now())
    new_month = current_date.month + amount
    new_year = current_date.year
    if new_month > 12:
        new_month = 1
        new_year += 1
    elif new_month < 1:
        new_month = 12
        new_year -= 1
    st.session_state['cal_date'] = current_date.replace(year=new_year, month=new_month, day=1)

def render_calendar_html(df):
    current_date = st.session_state.get('cal_date', datetime.now())
    year = current_date.year
    month = current_date.month
    
    if not df.empty:
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        df_m = df[(df['Fecha'].dt.year == year) & (df['Fecha'].dt.month == month)]
        data = df_m.groupby(df['Fecha'].dt.day)['Dinero'].sum().to_dict()
    else: data = {}

    cal = calendar.Calendar(firstweekday=0)
    month_days = cal.monthdayscalendar(year, month)
    
    html = '<div class="calendar-container">'
    for d in ["LUN","MAR","MIÉ","JUE","VIE","SÁB","DOM"]: html += f'<div class="calendar-header">{d}</div>'
    
    for week in month_days:
        for day in week:
            if day == 0: html += '<div class="calendar-day" style="opacity:0.0;"></div>'
            else:
                val = data.get(day, 0)
                txt = f"${val:,.0f}" if val != 0 else ""
                txt_class = "win-text" if val > 0 else "loss-text" if val < 0 else ""
                bg = "rgba(0,255,0,0.1)" if val > 0 else "rgba(255,0,0,0.1)" if val < 0 else "#0a0a0a"
                border = "#00ff00" if val > 0 else "#ff0000" if val < 0 else "#333"
                
                html += f'''
                <div class="calendar-day" style="background:{bg}; border:1px solid {border}">
                    <div class="day-num">{day}</div>
                    <div class="day-val {txt_class}">{txt}</div>
                </div>
                '''
    html += '</div>'
    return html, year, month

# --- 7. PANTALLA LOGIN ---
def login_screen():
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        st.title("🦁 Trading Suite")
        t1, t2 = st.tabs(["Ingresar", "Registrarse"])
        with t1:
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            if st.button("Entrar", type="primary"):
                if verify_user(u, p): 
                    st.session_state.user = u
                    st.rerun()
                else: st.error("Datos incorrectos")
        with t2:
            nu = st.text_input("Nuevo Usuario")
            np = st.text_input("Nueva Contraseña", type="password")
            if st.button("Crear Cuenta"):
                if nu and np: 
                    register_user(nu, np)
                    st.success("Usuario Creado")
                    st.rerun()

# --- 8. APLICACIÓN PRINCIPAL ---
def main_app():
    user = st.session_state.user
    if 'cal_date' not in st.session_state: st.session_state['cal_date'] = datetime.now()

    # --- SIDEBAR ---
    with st.sidebar:
        st.title(f"👤 {user}")
        if st.button("Cerrar Sesión"): 
            st.session_state.user = None
            st.rerun()
        st.markdown("---")
        
        accs = get_user_accounts(user)
        sel_acc = st.selectbox("📂 Cuenta Activa", accs)
        
        saldo_ini, saldo_act = get_account_balance(user, sel_acc)
        color = "#00ff00" if saldo_act >= saldo_ini else "#ff3333"
        
        st.markdown(f"""
        <div style="background:#111; padding:15px; border-radius:10px; border:1px solid #333; text-align:center;">
            <p style="color:#888; margin:0; font-size:0.8em">SALDO ACTUAL</p>
            <h2 style="color:{color}; margin:5px 0">${saldo_act:,.2f}</h2>
            <p style="color:#555; margin:0; font-size:0.8em">Inicio: ${saldo_ini:,.2f}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        with st.expander("➕ Nueva Cuenta"):
            n_acc = st.text_input("Nombre")
            n_bal = st.number_input("Saldo Inicial ($)", value=10000.0)
            if st.button("Crear"):
                if n_acc:
                    create_account(user, n_acc, n_bal)
                    st.rerun()

    # --- PESTAÑAS ---
    t_op, t_reg, t_dash, t_cal = st.tabs(["🦁 OPERATIVA", "📝 REGISTRO", "📊 DASHBOARD", "📅 CALENDARIO"])

    # 1. OPERATIVA
    with t_op:
        st.subheader("🦁 Análisis de Estrategia")
        col_guia, col_check, col_res = st.columns([1, 2, 1.2], gap="medium")

        with col_guia:
            st.markdown("### 📖 Patrones")
            with st.expander("🐂 Alcistas", expanded=True):
                st.caption("Bullish Engulfing"); mostrar_imagen("bullish_engulfing.png", "B. Engulfing")
                st.caption("Morning Star"); mostrar_imagen("morning_star.png", "Morning Star")
            with st.expander("🐻 Bajistas"):
                st.caption("Bearish Engulfing"); mostrar_imagen("bearish_engulfing.png", "B. Engulfing")
                st.caption("Shooting Star"); mostrar_imagen("shooting_star.png", "Shooting Star")

        with col_check:
            modo = st.radio("Modo", ["Swing (W-D-4H)", "Scalping (4H-2H-1H)"], horizontal=True)
            
            if "Swing" in modo:
                c1,c2,c3 = st.columns(3)
                tw = c1.selectbox("W", ["Alcista", "Bajista"], key="tw")
                td = c2.selectbox("D", ["Alcista", "Bajista"], key="td")
                t4 = c3.selectbox("4H", ["Alcista", "Bajista"], key="t4")
                
                if tw==td==t4: st.success("💎 TRIPLE SYNC")
                elif tw==td: st.info("✅ SWING SYNC")
                else: st.warning("⚠️ MIXTO")
                
                st.divider()
                w_sc = sum([st.checkbox(f"W: {x} (+10%)", key=f"w{i}")*10 for i,x in enumerate(["AOI","Estructura","Vela"])])
                d_sc = sum([st.checkbox(f"D: {x} (+10%)", key=f"d{i}")*10 for i,x in enumerate(["AOI","Estructura","Vela"])])
                h4_sc = sum([st.checkbox(f"4H: {x} (+10%)", key=f"h4{i}")*10 for i,x in enumerate(["AOI","Estructura","Vela"])])
                
                st.markdown("**Gatillo**")
                trig = sum([st.checkbox("⚡ SOS")*10, st.checkbox("🕯️ Engulfing")*10, st.checkbox("💰 Ratio")*0])
                total = w_sc + d_sc + h4_sc + trig
                valid = trig >= 20 # Al menos SOS y Engulfing
            else:
                c1,c2,c3 = st.columns(3)
                t4 = c1.selectbox("4H", ["Alcista", "Bajista"], key="s4")
                t2 = c2.selectbox("2H", ["Alcista", "Bajista"], key="s2")
                t1 = c3.selectbox("1H", ["Alcista", "Bajista"], key="s1")
                
                if t4==t2==t1: st.success("💎 TRIPLE SYNC")
                else: st.warning("⚠️ CUIDADO")
                
                st.divider()
                s4_sc = sum([st.checkbox(f"4H: {x} (+5%)", key=f"sc4{i}")*5 for i,x in enumerate(["AOI","Estructura","Patron"])])
                s2_sc = sum([st.checkbox(f"2H: {x} (+5%)", key=f"sc2{i}")*5 for i,x in enumerate(["AOI","Estructura","Vela"])])
                s1_sc = sum([st.checkbox(f"1H: {x} (+5%)", key=f"sc1{i}")*5 for i,x in enumerate(["Vela","Patron","EMA"])])
                
                st.markdown("**Gatillo (M15)**")
                trig = sum([st.checkbox("⚡ SOS M15")*10, st.checkbox("🕯️ Entrada")*10])
                total = s4_sc + s2_sc + s1_sc + trig + 15
                valid = trig >= 20

        with col_res:
            st.metric("Probabilidad", f"{min(total, 100)}%")
            st.progress(min(total, 100))
            if valid and total >= 60:
                st.success("✅ EJECUTAR")
                sl = "5-7 pips" if "Swing" in modo else "3-5 pips"
                st.markdown(f'<div class="plan-box">SL: {sl}<br>TP: Liquidez</div>', unsafe_allow_html=True)
            elif not valid: st.error("⛔ FALTA GATILLO")
            else: st.warning("💤 ESPERAR")

    # 2. REGISTRO
    with t_reg:
        st.subheader("📝 Nuevo Registro")
        with st.form("reg"):
            c1,c2 = st.columns(2)
            dt = c1.date_input("Fecha", datetime.now())
            pr = c1.text_input("Par", "XAUUSD").upper()
            tp = c1.selectbox("Tipo", ["BUY", "SELL"])
            rs = c2.selectbox("Resultado", ["WIN", "LOSS", "BE"])
            mn = c2.number_input("P/L ($)", step=10.0, help="Negativo si perdiste")
            rt = c2.number_input("Ratio", value=2.5)
            nt = st.text_area("Notas")
            if st.form_submit_button("Guardar"):
                guardar_trade(user, sel_acc, {"Fecha":dt,"Par":pr,"Tipo":tp,"Resultado":rs,"Dinero":mn,"Ratio":rt,"Notas":nt})
                st.success("Guardado!"); st.rerun()

    # 3. DASHBOARD
    with t_dash:
        st.subheader("📊 Estadísticas")
        fp = get_account_file(user, sel_acc)
        if os.path.exists(fp):
            df = pd.read_csv(fp)
            if not df.empty:
                k1,k2,k3,k4 = st.columns(4)
                wins = len(df[df["Resultado"]=="WIN"])
                k1.metric("Neto", f"${df['Dinero'].sum():,.2f}")
                k2.metric("WinRate", f"{(wins/len(df)*100):.1f}%")
                k3.metric("Trades", len(df))
                k4.metric("Saldo", f"${saldo_act:,.2f}")
                
                df["Eq"] = saldo_ini + df["Dinero"].cumsum()
                fig = go.Figure(go.Scatter(x=df["Fecha"], y=df["Eq"], line=dict(color='#00ff00', width=3)))
                fig.update_layout(title="Curva de Crecimiento", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
                st.plotly_chart(fig, use_container_width=True)
            else: st.info("Sin trades")
        else: st.info("Cuenta vacía")

    # 4. CALENDARIO
    with t_cal:
        st.subheader(f"📅 Calendario: {sel_acc}")
        c_prev, c_tit, c_next = st.columns([1,5,1])
        with c_prev: 
            if st.button("⬅️"): change_month(-1); st.rerun()
        with c_next: 
            if st.button("➡️"): change_month(1); st.rerun()
            
        fp = get_account_file(user, sel_acc)
        if os.path.exists(fp):
            df = pd.read_csv(fp)
            html, y, m = render_calendar_html(df)
            with c_tit: st.markdown(f"<h3 style='text-align:center; color:#ff9900'>{calendar.month_name[m]} {y}</h3>", unsafe_allow_html=True)
            st.markdown(html, unsafe_allow_html=True)
        else: st.info("Sin datos")

# --- MAIN EXECUTION ---
if 'user' not in st.session_state: st.session_state.user = None
if st.session_state.user: main_app()
else: login_screen()
