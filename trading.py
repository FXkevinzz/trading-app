import streamlit as st
import pandas as pd
import os
import json
import calendar
from datetime import datetime
import plotly.graph_objects as go
import pytz

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Trading Pro Suite", layout="wide", page_icon="🦁")

# --- GESTIÓN DE DIRECTORIOS Y USUARIOS ---
DATA_DIR = "user_data"
IMG_DIR = "fotos"  # Carpeta de fotos locales
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
USERS_FILE = os.path.join(DATA_DIR, "users.json")
ACCOUNTS_FILE = os.path.join(DATA_DIR, "accounts_config.json") # Archivo para guardar saldos iniciales

# --- FUNCIONES DE PERSISTENCIA ---
def load_json(filepath):
    if not os.path.exists(filepath): return {}
    with open(filepath, "r") as f: return json.load(f)

def save_json(filepath, data):
    with open(filepath, "w") as f: json.dump(data, f)

def verify_user(username, password):
    users = load_json(USERS_FILE)
    return username in users and users[username] == password

def register_user(username, password):
    users = load_json(USERS_FILE)
    users[username] = password
    save_json(USERS_FILE, users)

# --- GESTIÓN DE CUENTAS ---
def get_user_folder(username):
    folder = os.path.join(DATA_DIR, username)
    if not os.path.exists(folder): os.makedirs(folder)
    return folder

def get_account_file(username, account_name):
    clean = "".join(c for c in account_name if c.isalnum() or c in (' ', '_')).strip().replace(" ", "_")
    return os.path.join(get_user_folder(username), f"{clean}.csv")

def get_user_accounts(username):
    # Devuelve lista de cuentas
    configs = load_json(ACCOUNTS_FILE)
    if username in configs:
        return list(configs[username].keys())
    return ["Principal"]

def create_account(username, account_name, initial_balance):
    # Guardar configuración de saldo inicial
    configs = load_json(ACCOUNTS_FILE)
    if username not in configs: configs[username] = {}
    
    # Si ya existe, no sobrescribimos saldo inicial
    if account_name not in configs[username]:
        configs[username][account_name] = initial_balance
        save_json(ACCOUNTS_FILE, configs)
        
        # Crear archivo CSV vacío
        file_path = get_account_file(username, account_name)
        if not os.path.exists(file_path):
            df = pd.DataFrame(columns=["Fecha", "Par", "Tipo", "Resultado", "Dinero", "Ratio", "Notas"])
            df.to_csv(file_path, index=False)

def get_account_balance(username, account_name):
    # 1. Obtener saldo inicial
    configs = load_json(ACCOUNTS_FILE)
    initial = 0
    if username in configs and account_name in configs[username]:
        initial = configs[username][account_name]
    
    # 2. Sumar PnL del CSV
    file_path = get_account_file(username, account_name)
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        total_pnl = df["Dinero"].sum()
    else:
        total_pnl = 0
        
    return initial, initial + total_pnl

def guardar_trade(username, account_name, data):
    file_path = get_account_file(username, account_name)
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
    else:
        df = pd.DataFrame(columns=["Fecha", "Par", "Tipo", "Resultado", "Dinero", "Ratio", "Notas"])
    
    new = pd.DataFrame([data])
    df = pd.concat([df, new], ignore_index=True)
    df.to_csv(file_path, index=False)
    return df

# --- FUNCIÓN IMÁGENES (LOCALES) ---
def mostrar_imagen(nombre_archivo, caption):
    ruta_completa = os.path.join(IMG_DIR, nombre_archivo)
    if os.path.exists(ruta_completa):
        st.image(ruta_completa, caption=caption, use_container_width=True)
    else:
        # Fallback si no está la foto local
        st.warning(f"⚠️ No se encontró: {nombre_archivo} en la carpeta {IMG_DIR}")

# --- ESTILOS CSS (MEJORADOS) ---
st.markdown("""
    <style>
    .stApp {background-color: #050505; color: #e0e0e0;}
    
    /* Inputs Estilizados */
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div, .stDateInput>div>div>input {
        background-color: #111 !important; 
        color: #fff !important; 
        border: 1px solid #333;
        border-radius: 5px;
    }

    /* Calendario Aesthetic */
    .calendar-wrapper {
        background: #111;
        border-radius: 10px;
        padding: 10px;
        border: 1px solid #333;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .calendar-container { 
        display: grid; 
        grid-template-columns: repeat(7, 1fr); 
        gap: 5px; 
        margin-top: 10px;
    }
    .calendar-header { 
        background: #222; 
        color: #aaa; 
        text-align: center; 
        padding: 8px; 
        font-weight: bold; 
        border-radius: 4px;
        font-size: 0.9rem;
    }
    .calendar-day { 
        min-height: 90px; 
        background: #0a0a0a; 
        padding: 8px; 
        display: flex; 
        flex-direction: column; 
        justify-content: space-between; 
        border-radius: 6px;
        border: 1px solid #222;
        transition: transform 0.2s;
    }
    .calendar-day:hover {
        border-color: #444;
        transform: translateY(-2px);
    }
    .day-num { color: #555; font-size: 0.8em; font-weight: bold; }
    .day-val { text-align: right; font-weight: bold; font-size: 1.1em; }
    
    /* Colores Resultados */
    .win-text { color: #00ff00; text-shadow: 0 0 5px rgba(0,255,0,0.2); }
    .loss-text { color: #ff3333; text-shadow: 0 0 5px rgba(255,0,0,0.2); }
    .be-text { color: #ffcc00; }

    /* Info Box */
    .balance-box {
        background: linear-gradient(90deg, #111 0%, #0a0a0a 100%);
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #00ff00;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CALENDARIO HTML ---
def render_calendar(year, month, df):
    if not df.empty:
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        df_m = df[(df['Fecha'].dt.year == year) & (df['Fecha'].dt.month == month)]
        data = df_m.groupby(df['Fecha'].dt.day)['Dinero'].sum().to_dict()
    else: data = {}

    cal = calendar.Calendar(firstweekday=0)
    month_days = cal.monthdayscalendar(year, month)
    
    html = '<div class="calendar-wrapper"><div class="calendar-container">'
    for d in ["LUN","MAR","MIÉ","JUE","VIE","SÁB","DOM"]: html += f'<div class="calendar-header">{d}</div>'
    
    for week in month_days:
        for day in week:
            if day == 0: html += '<div class="calendar-day" style="opacity:0.3;"></div>'
            else:
                val = data.get(day, 0)
                txt = f"${val:,.0f}" if val != 0 else ""
                
                # Clase CSS según resultado
                txt_class = "win-text" if val > 0 else "loss-text" if val < 0 else "be-text"
                bg_style = ""
                if val > 0: bg_style = "background: rgba(0, 255, 0, 0.05); border: 1px solid rgba(0,255,0,0.2);"
                elif val < 0: bg_style = "background: rgba(255, 0, 0, 0.05); border: 1px solid rgba(255,0,0,0.2);"
                
                html += f'''
                <div class="calendar-day" style="{bg_style}">
                    <div class="day-num">{day}</div>
                    <div class="day-val {txt_class}">{txt}</div>
                </div>
                '''
    html += '</div></div>'
    return html

# --- LOGIN ---
def login_screen():
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        st.title("🦁 Trading Suite")
        t1, t2 = st.tabs(["Ingresar", "Registrarse"])
        with t1:
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            if st.button("Entrar", type="primary"):
                if verify_user(u, p): st.session_state.user = u; st.rerun()
                else: st.error("Datos incorrectos")
        with t2:
            nu = st.text_input("Nuevo Usuario")
            np = st.text_input("Nueva Contraseña", type="password")
            if st.button("Crear Cuenta"):
                if nu and np: register_user(nu, np); st.success("Usuario Creado"); st.rerun()

# --- APP PRINCIPAL ---
def main_app():
    user = st.session_state.user
    
    # --- SIDEBAR ---
    with st.sidebar:
        st.title(f"👤 {user}")
        if st.button("Cerrar Sesión"): st.session_state.user = None; st.rerun()
        st.markdown("---")
        
        # Selección de Cuenta
        accs = get_user_accounts(user)
        sel_acc = st.selectbox("📂 Seleccionar Cuenta", accs)
        
        # Info Saldo Sidebar
        saldo_ini, saldo_act = get_account_balance(user, sel_acc)
        st.markdown(f"""
        <div style="background:#111; padding:10px; border-radius:5px; border:1px solid #333;">
            <small style="color:#888">Saldo Actual:</small>
            <h2 style="color:#00ff00; margin:0">${saldo_act:,.2f}</h2>
            <small style="color:#555">Inicial: ${saldo_ini:,.2f}</small>
        </div>
        """, unsafe_allow_html=True)

        # Crear Nueva Cuenta
        with st.expander("➕ Crear Nueva Cuenta"):
            n_acc = st.text_input("Nombre (Ej: Fondeo 10k)")
            n_bal = st.number_input("Saldo Inicial ($)", value=10000.0, step=100.0)
            if st.button("Crear") and n_acc:
                create_account(user, n_acc, n_bal)
                st.rerun()

    # --- PESTAÑAS (ORDEN NUEVO: REGISTRO -> DASH -> CAL -> OPERATIVA) ---
    t_reg, t_dash, t_cal, t_op = st.tabs(["📝 REGISTRO", "📊 DASHBOARD", "📅 CALENDARIO", "🦁 OPERATIVA"])

    # === 1. REGISTRO ===
    with t_reg:
        st.subheader(f"📝 Registrar Operación: {sel_acc}")
        
        # Caja de info rápida
        st.info(f"Registrando trade para cuenta con saldo: **${saldo_act:,.2f}**")
        
        with st.form("trade_reg"):
            c1, c2 = st.columns(2)
            dt = c1.date_input("Fecha", datetime.now())
            pr = c1.text_input("Par (Ej: BTCUSD)", "XAUUSD").upper()
            tp = c1.selectbox("Tipo", ["BUY", "SELL"])
            
            rs = c2.selectbox("Resultado", ["WIN", "LOSS", "BE"])
            mn = c2.number_input("Profit/Loss ($)", step=10.0, help="Usa negativo para pérdidas")
            rt = c2.number_input("Ratio (RR)", value=2.5)
            nt = st.text_area("Notas / Emociones")
            
            if st.form_submit_button("💾 Guardar en Bitácora"):
                guardar_trade(user, sel_acc, {"Fecha":dt, "Par":pr, "Tipo":tp, "Resultado":rs, "Dinero":mn, "Ratio":rt, "Notas":nt})
                st.success("Trade Registrado Correctamente")
                st.rerun() # Recargar para actualizar saldos

    # === 2. DASHBOARD ===
    with t_dash:
        st.subheader(f"📊 Estadísticas: {sel_acc}")
        file_path = get_account_file(user, sel_acc)
        
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            if not df.empty:
                # Métricas Principales
                col1, col2, col3, col4 = st.columns(4)
                neto = df["Dinero"].sum()
                wins = len(df[df["Resultado"] == "WIN"])
                total = len(df)
                wr = (wins/total*100) if total > 0 else 0
                
                col1.metric("Beneficio Neto", f"${neto:,.2f}", delta_color="normal")
                col2.metric("Win Rate", f"{wr:.1f}%")
                col3.metric("Total Trades", total)
                col4.metric("Saldo Final", f"${saldo_act:,.2f}")
                
                # Gráfico de Equity
                st.divider()
                df = df.sort_values("Fecha")
                df["Equity"] = saldo_ini + df["Dinero"].cumsum()
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df["Fecha"], y=df["Equity"], mode='lines+markers', 
                                         line=dict(color='#00ff00', width=3), name='Balance'))
                fig.update_layout(
                    title="Curva de Crecimiento (Equity)",
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white'),
                    xaxis=dict(showgrid=False),
                    yaxis=dict(gridcolor='#333')
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay trades registrados aún.")
        else:
            st.info("Cuenta nueva. Registra tu primer trade.")

    # === 3. CALENDARIO ===
    with t_cal:
        st.subheader("📅 Calendario de P&L")
        col_y, col_m = st.columns([1, 5])
        y = col_y.number_input("Año", value=datetime.now().year)
        m_idx = datetime.now().month
        m = col_m.slider("Mes", 1, 12, m_idx)
        
        file_path = get_account_file(user, sel_acc)
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            st.markdown(render_calendar(y, m, df), unsafe_allow_html=True)
        else:
            st.info("Sin datos para mostrar.")

    # === 4. OPERATIVA (TU ESTRATEGIA) ===
    with t_op:
        st.subheader("🦁 Análisis de Estrategia (Set & Forget)")
        
        col_guia, col_check, col_res = st.columns([1, 2, 1.2], gap="medium")

        # GUIA (Fotos Locales)
        with col_guia:
            with st.expander("📖 Chuleta Visual", expanded=True):
                st.caption("Alcistas")
                mostrar_imagen("bullish_engulfing.png", "Bullish Engulfing")
                mostrar_imagen("morning_star.png", "Morning Star")
                st.caption("Bajistas")
                mostrar_imagen("bearish_engulfing.png", "Bearish Engulfing")
                mostrar_imagen("shooting_star.png", "Shooting Star")

        # CHECKLIST
        with col_check:
            modo = st.radio("Modo", ["Swing (W-D-4H)", "Scalping (4H-2H-1H)"], horizontal=True)
            
            if "Swing" in modo:
                c1, c2, c3 = st.columns(3)
                tw = c1.selectbox("Weekly", ["Alcista", "Bajista"], key="tw")
                td = c2.selectbox("Daily", ["Alcista", "Bajista"], key="td")
                t4 = c3.selectbox("4H", ["Alcista", "Bajista"], key="t4")
                
                if tw==td==t4: st.success("💎 TRIPLE SYNC")
                else: st.warning("⚠️ TENDENCIA MIXTA")
                
                score = 0
                st.write("**Confirmaciones:**")
                if st.checkbox("Precio en AOI"): score += 20
                if st.checkbox("Rechazo Estructural / EMA"): score += 20
                if st.checkbox("Patrón de Vela Válido"): score += 20
                
                st.write("**Gatillo:**")
                if st.checkbox("⚡ SOS + Engulfing + Ratio > 1:2.5"): score += 40
                
            else:
                c1, c2, c3 = st.columns(3)
                t4 = c1.selectbox("4H", ["Alcista", "Bajista"], key="st4")
                t2 = c2.selectbox("2H", ["Alcista", "Bajista"], key="st2")
                t1 = c3.selectbox("1H", ["Alcista", "Bajista"], key="st1")
                
                if t4==t2==t1: st.success("💎 TRIPLE SYNC")
                else: st.warning("⚠️ CUIDADO")
                
                score = 0
                if st.checkbox("Rechazo AOI (H1/H2)"): score += 30
                if st.checkbox("Patrón Vela (H1)"): score += 20
                if st.checkbox("⚡ Quiebre M15 + Ratio"): score += 50

        # RESULTADOS
        with col_res:
            st.metric("Probabilidad", f"{score}%")
            st.progress(score)
            if score >= 80:
                st.success("✅ EJECUTAR")
            else:
                st.error("⛔ ESPERAR")

# --- LANZADOR ---
if 'user' not in st.session_state: st.session_state.user = None
if st.session_state.user: main_app()
else: login_screen()
