import streamlit as st
import pandas as pd
import os
import json
import calendar
from datetime import datetime
import plotly.graph_objects as go

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Trading Pro Suite", layout="wide", page_icon="📈")

# --- GESTIÓN DE DIRECTORIOS Y USUARIOS ---
DATA_DIR = "user_data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

USERS_FILE = os.path.join(DATA_DIR, "users.json")

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_user(username, password):
    users = load_users()
    users[username] = password
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)
    return True

def verify_user(username, password):
    users = load_users()
    return username in users and users[username] == password

# --- GESTIÓN DE DATOS (POR CUENTA) ---
def get_user_folder(username):
    folder = os.path.join(DATA_DIR, username)
    if not os.path.exists(folder):
        os.makedirs(folder)
    return folder

def get_account_file(username, account_name):
    clean_name = "".join(c for c in account_name if c.isalnum() or c in (' ', '_')).strip().replace(" ", "_")
    return os.path.join(get_user_folder(username), f"{clean_name}.csv")

def get_user_accounts(username):
    folder = get_user_folder(username)
    files = [f.replace(".csv", "").replace("_", " ") for f in os.listdir(folder) if f.endswith(".csv")]
    if not files:
        return ["Principal"] # Cuenta por defecto
    return files

def cargar_trades(username, account_name):
    file_path = get_account_file(username, account_name)
    if not os.path.exists(file_path):
        return pd.DataFrame(columns=["Fecha", "Par", "Tipo", "Resultado", "Dinero", "Ratio", "Notas"])
    return pd.read_csv(file_path)

def guardar_trade(username, account_name, data_dict):
    df = cargar_trades(username, account_name)
    new_row = pd.DataFrame([data_dict])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(get_account_file(username, account_name), index=False)

# --- ESTILOS CSS (BLOOMBERG CALENDAR) ---
st.markdown("""
    <style>
    .stApp {background-color: #0E1117; color: white;}
    
    /* Login Box */
    .login-box {background: #161B22; padding: 2rem; border-radius: 10px; border: 1px solid #333;}
    
    /* Calendario CSS Grid */
    .calendar-container {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 5px;
        margin-top: 10px;
    }
    .calendar-header {
        font-weight: bold;
        text-align: center;
        background-color: #262730;
        padding: 10px;
        border-radius: 4px;
        color: #aaa;
    }
    .calendar-day {
        min-height: 100px;
        background-color: #1c1c1c;
        border: 1px solid #333;
        border-radius: 4px;
        padding: 5px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: 0.3s;
    }
    .calendar-day:hover { border-color: #555; }
    .day-number { font-weight: bold; font-size: 1.1em; color: #666; }
    .day-profit { font-weight: bold; font-size: 1.2em; text-align: right; margin-top: auto;}
    
    .win-day { background-color: rgba(31, 122, 31, 0.3) !important; border: 1px solid #1f7a1f !important; }
    .loss-day { background-color: rgba(92, 0, 0, 0.3) !important; border: 1px solid #5c0000 !important; }
    
    /* Inputs */
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div {
        background-color: #0d1117 !important; color: white !important; border: 1px solid #30363d;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIÓN DE CALENDARIO HTML ---
def render_calendar_html(year, month, df_trades):
    # Filtrar trades del mes y año
    if not df_trades.empty:
        df_trades['Fecha'] = pd.to_datetime(df_trades['Fecha'])
        df_month = df_trades[(df_trades['Fecha'].dt.year == year) & (df_trades['Fecha'].dt.month == month)]
        # Agrupar por día y sumar dinero
        daily_pnl = df_month.groupby(df_trades['Fecha'].dt.day)['Dinero'].sum().to_dict()
    else:
        daily_pnl = {}

    cal = calendar.Calendar(firstweekday=0) # 0 = Lunes
    month_days = cal.monthdayscalendar(year, month)
    
    days_header = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    
    html = '<div class="calendar-container">'
    
    # Headers
    for d in days_header:
        html += f'<div class="calendar-header">{d}</div>'
    
    # Días
    for week in month_days:
        for day in week:
            if day == 0:
                html += '<div class="calendar-day" style="background:transparent; border:none;"></div>'
            else:
                pnl = daily_pnl.get(day, 0)
                css_class = "calendar-day"
                pnl_str = ""
                
                if day in daily_pnl:
                    pnl_val = daily_pnl[day]
                    if pnl_val > 0:
                        css_class += " win-day"
                        pnl_str = f'<span style="color:#4caf50;">+${pnl_val:,.2f}</span>'
                    elif pnl_val < 0:
                        css_class += " loss-day"
                        pnl_str = f'<span style="color:#ff4b4b;">-${abs(pnl_val):,.2f}</span>'
                    else:
                        pnl_str = '<span style="color:#888;">$0.00</span>'
                
                html += f"""
                <div class="{css_class}">
                    <div class="day-number">{day}</div>
                    <div class="day-profit">{pnl_str}</div>
                </div>
                """
    html += '</div>'
    return html

# --- LOGIN SYSTEM ---
if 'user' not in st.session_state:
    st.session_state.user = None

def main_app():
    user = st.session_state.user
    
    # --- SIDEBAR: GESTIÓN DE CUENTAS ---
    with st.sidebar:
        st.title(f"👤 {user}")
        if st.button("Cerrar Sesión"):
            st.session_state.user = None
            st.rerun()
            
        st.markdown("---")
        st.subheader("💳 Tus Cuentas")
        
        # Selector de Cuenta
        accounts = get_user_accounts(user)
        
        # Crear nueva cuenta
        with st.expander("➕ Nueva Cuenta"):
            new_acc_name = st.text_input("Nombre (Ej: Challenge 10k)")
            if st.button("Crear") and new_acc_name:
                # Crear archivo vacío
                guardar_trade(user, new_acc_name, {"Fecha": datetime.now(), "Dinero": 0}) # Dummy init
                st.success("Creada!")
                st.rerun()

        selected_account = st.selectbox("Seleccionar Cuenta Activa", accounts)
        st.info(f"Operando en: **{selected_account}**")

    # --- TABS PRINCIPALES ---
    tab1, tab2, tab3 = st.tabs(["🦁 OPERATIVA", "📅 CALENDARIO & PNL", "📝 REGISTRAR TRADE"])

    # === TAB 1: OPERATIVA (CHECKLIST) ===
    with tab1:
        st.header("Checklist de Entrada")
        col1, col2 = st.columns([1, 2])
        with col1:
            modo = st.radio("Estilo", ["Swing", "Scalping"])
        with col2:
            st.markdown("### Reglas de Oro")
            c1, c2, c3 = st.columns(3)
            c1.checkbox("Estructura a favor")
            c2.checkbox("Zona de Valor (AOI)")
            c3.checkbox("Patrón de Vela (Gatillo)")
            
            confirm = st.checkbox("✅ CONFIRMADO: Riesgo gestionado")
            if confirm:
                st.success("Setup validado. Ejecuta con confianza.")

    # === TAB 2: CALENDARIO Y ESTADÍSTICAS ===
    with tab2:
        st.header(f"📅 Rendimiento: {selected_account}")
        
        # Cargar datos
        df = cargar_trades(user, selected_account)
        df = df[df["Resultado"].notna()] # Limpiar vacíos
        
        if not df.empty:
            # Filtros de fecha para el calendario
            col_y, col_m = st.columns([1, 4])
            with col_y:
                year = st.number_input("Año", value=datetime.now().year)
            with col_m:
                month_names = list(calendar.month_name)[1:]
                month_idx = datetime.now().month - 1
                month_str = st.selectbox("Mes", month_names, index=month_idx)
                month = month_names.index(month_str) + 1

            # Renderizar Calendario
            st.markdown(render_calendar_html(year, month, df), unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Estadísticas Globales
            wins = df[df["Dinero"] > 0]
            losses = df[df["Dinero"] < 0]
            
            tot_pnl = df["Dinero"].sum()
            win_rate = (len(wins) / len(df) * 100) if len(df) > 0 else 0
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Net Profit", f"${tot_pnl:,.2f}", delta_color="normal")
            m2.metric("Win Rate", f"{win_rate:.1f}%")
            m3.metric("Trades Ganados", len(wins))
            m4.metric("Trades Perdidos", len(losses))

        else:
            st.info("No hay datos en esta cuenta aún.")

    # === TAB 3: REGISTRO ===
    with tab3:
        st.header("📝 Registrar Operación")
        st.markdown(f"Registrando en cuenta: **{selected_account}**")
        
        with st.form("entry_form"):
            c1, c2 = st.columns(2)
            with c1:
                date = st.date_input("Fecha", datetime.now())
                pair = st.text_input("Par (Ej: XAUUSD)", "EURUSD").upper()
                tipo = st.selectbox("Tipo", ["BUY", "SELL"])
            with c2:
                result = st.selectbox("Resultado", ["WIN", "LOSS", "BE"])
                # AQUÍ ESTÁ LA CLAVE PARA EL CALENDARIO
                money = st.number_input("Profit/Loss ($)", step=10.0, format="%.2f", help="Usa negativo para pérdidas (ej: -50)")
                ratio = st.number_input("Ratio Obtenido", value=0.0)
            
            notes = st.text_area("Notas")
            
            if st.form_submit_button("💾 Guardar Trade"):
                data = {
                    "Fecha": date, "Par": pair, "Tipo": tipo,
                    "Resultado": result, "Dinero": money,
                    "Ratio": ratio, "Notas": notes
                }
                guardar_trade(user, selected_account, data)
                st.success("Guardado exitosamente! Ve al calendario para verlo.")

# --- PANTALLA DE LOGIN ---
def login_screen():
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        st.title("🔒 Trading Suite Access")
        st.markdown("Acceso seguro multi-usuario")
        
        tab_login, tab_reg = st.tabs(["Ingresar", "Registrarse"])
        
        with tab_login:
            username = st.text_input("Usuario", key="l_user")
            password = st.text_input("Contraseña", type="password", key="l_pass")
            if st.button("Entrar", type="primary"):
                if verify_user(username, password):
                    st.session_state.user = username
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")
        
        with tab_reg:
            new_user = st.text_input("Nuevo Usuario", key="r_user")
            new_pass = st.text_input("Nueva Contraseña", type="password", key="r_pass")
            if st.button("Crear Cuenta"):
                if new_user and new_pass:
                    load_users() # Check if exists logic could be added
                    save_user(new_user, new_pass)
                    st.success("Usuario creado! Ahora haz login.")
                else:
                    st.warning("Llena todos los campos")

# --- CONTROLADOR ---
if st.session_state.user:
    main_app()
else:
    login_screen()
