import streamlit as st
import pandas as pd
import os
import json
import calendar
from datetime import datetime
import plotly.graph_objects as go # Usamos Plotly para gráficos pro
import pytz

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Bloomberg Trading Suite", layout="wide", page_icon="📈")

# --- GESTIÓN DE DIRECTORIOS Y USUARIOS ---
DATA_DIR = "user_data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

USERS_FILE = os.path.join(DATA_DIR, "users.json")

def load_users():
    if not os.path.exists(USERS_FILE): return {}
    with open(USERS_FILE, "r") as f: return json.load(f)

def save_user(username, password):
    users = load_users()
    users[username] = password
    with open(USERS_FILE, "w") as f: json.dump(users, f)

def verify_user(username, password):
    users = load_users()
    return username in users and users[username] == password

# --- GESTIÓN DE DATOS (POR CUENTA) ---
def get_user_folder(username):
    folder = os.path.join(DATA_DIR, username)
    if not os.path.exists(folder): os.makedirs(folder)
    return folder

def get_account_file(username, account_name):
    clean_name = "".join(c for c in account_name if c.isalnum() or c in (' ', '_')).strip().replace(" ", "_")
    return os.path.join(get_user_folder(username), f"{clean_name}.csv")

def get_user_accounts(username):
    folder = get_user_folder(username)
    files = [f.replace(".csv", "").replace("_", " ") for f in os.listdir(folder) if f.endswith(".csv")]
    if not files: return ["Principal"]
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

# --- FUNCIÓN IMÁGENES ---
def mostrar_imagen(nombre_archivo, caption):
    links = {
        "bullish_engulfing.png": "https://forexbee.co/wp-content/uploads/2019/10/Bullish-Engulfing-Pattern-1.png",
        "morning_star.png": "https://a.c-dn.net/b/1XlqMQ/Morning-Star-Candlestick-Pattern_body_MorningStar.png.full.png",
        "hammer.png": "https://a.c-dn.net/b/2fPj5H/Hammer-Candlestick-Pattern_body_Hammer.png.full.png",
        "bearish_engulfing.png": "https://forexbee.co/wp-content/uploads/2019/10/Bearish-Engulfing-Pattern.png",
        "shooting_star.png": "https://a.c-dn.net/b/4hQ18X/Shooting-Star-Candlestick_body_ShootingStar.png.full.png"
    }
    if nombre_archivo in links: st.image(links[nombre_archivo], caption=caption)
    else: st.warning(f"⚠️ Falta foto")

# --- ESTILOS CSS (BLOOMBERG DARK) ---
st.markdown("""
    <style>
    .stApp {background-color: #000000; color: #e0e0e0;}
    
    /* Inputs */
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div {
        background-color: #1a1a1a !important; color: #00ff00 !important; border: 1px solid #333;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #111; border: 1px solid #333; color: #888; }
    .stTabs [aria-selected="true"] { background-color: #00ff00 !important; color: black !important; font-weight: bold;}

    /* Calendario */
    .calendar-container { display: grid; grid-template-columns: repeat(7, 1fr); gap: 2px; background-color: #333; border: 1px solid #444;}
    .calendar-header { background-color: #111; color: #ff9900; font-weight: bold; text-align: center; padding: 5px; }
    .calendar-day { min-height: 80px; background-color: #000; padding: 5px; display: flex; flex-direction: column; justify-content: space-between; }
    .day-number { color: #555; font-size: 0.9em; }
    .day-profit { text-align: right; font-weight: bold; font-size: 1.1em; }
    
    /* Operativa Box */
    .op-box { background-color: #111; padding: 15px; border-left: 3px solid #ff9900; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- CALENDARIO HTML ---
def render_calendar_html(year, month, df_trades):
    if not df_trades.empty:
        df_trades['Fecha'] = pd.to_datetime(df_trades['Fecha'])
        df_month = df_trades[(df_trades['Fecha'].dt.year == year) & (df_trades['Fecha'].dt.month == month)]
        daily_pnl = df_month.groupby(df_trades['Fecha'].dt.day)['Dinero'].sum().to_dict()
    else: daily_pnl = {}

    cal = calendar.Calendar(firstweekday=0)
    month_days = cal.monthdayscalendar(year, month)
    days = ["LUN", "MAR", "MIÉ", "JUE", "VIE", "SÁB", "DOM"]
    
    html = '<div class="calendar-container">'
    for d in days: html += f'<div class="calendar-header">{d}</div>'
    
    for week in month_days:
        for day in week:
            if day == 0: html += '<div class="calendar-day" style="background:#0a0a0a;"></div>'
            else:
                pnl = daily_pnl.get(day, 0)
                color = "#00ff00" if pnl > 0 else "#ff3333" if pnl < 0 else "#444"
                pnl_txt = f"${pnl:,.0f}" if pnl != 0 else "-"
                html += f'<div class="calendar-day"><div class="day-number">{day}</div><div class="day-profit" style="color:{color}">{pnl_txt}</div></div>'
    html += '</div>'
    return html

# --- GRÁFICOS PLOTLY ---
def plot_equity_curve(df):
    if df.empty: return None
    df = df.sort_values("Fecha")
    df['Acumulado'] = df['Dinero'].cumsum()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Fecha'], y=df['Acumulado'], mode='lines+markers', 
                             line=dict(color='#00ff00', width=2), marker=dict(size=6), name='Balance'))
    fig.update_layout(
        title="Curva de Crecimiento (Equity)",
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e0e0e0'), xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#333')
    )
    return fig

# --- LOGIN ---
def login_screen():
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        st.title("🔒 Terminal Access")
        tab1, tab2 = st.tabs(["LOGIN", "REGISTER"])
        with tab1:
            u = st.text_input("Usuario", key="l_u")
            p = st.text_input("Password", type="password", key="l_p")
            if st.button("INGRESAR", type="primary"):
                if verify_user(u, p):
                    st.session_state.user = u
                    st.rerun()
                else: st.error("Acceso Denegado")
        with tab2:
            nu = st.text_input("Nuevo Usuario", key="r_u")
            np = st.text_input("Nueva Password", type="password", key="r_p")
            if st.button("CREAR CUENTA"):
                if nu and np: save_user(nu, np); st.success("Creado OK")

# --- APP ---
def main_app():
    user = st.session_state.user
    
    # SIDEBAR
    with st.sidebar:
        st.title(f"👤 TRADER: {user.upper()}")
        if st.button("LOGOUT"):
            st.session_state.user = None
            st.rerun()
        
        st.markdown("---")
        st.caption("CUENTAS ACTIVAS")
        accounts = get_user_accounts(user)
        
        # Nueva cuenta
        with st.expander("➕ Agregar Cuenta"):
            new_acc = st.text_input("Nombre (ej: Prop 100k)")
            if st.button("Crear") and new_acc:
                guardar_trade(user, new_acc, {"Fecha": datetime.now(), "Dinero": 0})
                st.rerun()
                
        selected_account = st.selectbox("Seleccionar Cuenta", accounts)
        
        # Estado mercado
        tz = pytz.timezone('America/Guayaquil')
        hora = datetime.now(tz).hour
        estado = "🔴 CERRADO" if 15 <= hora < 19 else "🟢 ABIERTO (Active Session)"
        st.markdown(f"**MARKET STATUS:** {estado}")

    # TABS
    tab_op, tab_cal, tab_stats, tab_reg = st.tabs(["🦁 OPERATIVA", "📅 CALENDARIO", "📊 ANALYTICS", "📝 REGISTRO"])

    # 1. OPERATIVA (CHECKLIST COMPLETO)
    with tab_op:
        c1, c2 = st.columns([1, 2])
        with c1:
            modo = st.radio("MODO", ["SWING (W-D-4H)", "SCALPING (4H-2H-1H)"])
            st.image("https://forexbee.co/wp-content/uploads/2019/10/Bullish-Engulfing-Pattern-1.png", caption="Bullish Engulfing")
        
        with c2:
            st.markdown('<div class="op-box">', unsafe_allow_html=True)
            if "Swing" in modo:
                st.subheader("🛠️ SWING SETUP")
                col_a, col_b, col_c = st.columns(3)
                tw = col_a.selectbox("Weekly", ["UP", "DOWN"])
                td = col_b.selectbox("Daily", ["UP", "DOWN"])
                t4 = col_c.selectbox("H4", ["UP", "DOWN"])
                
                if tw==td==t4: st.success("💎 TRIPLE CONFLUENCIA DETECTADA")
                elif tw==td: st.info("✅ SWING ALINEADO")
                else: st.warning("⚠️ TENDENCIA MIXTA - RIESGO ALTO")
                
                st.markdown("---")
                score = 0
                st.write("**CONFIRMACIONES:**")
                if st.checkbox("Precio en Zona de Valor (AOI)"): score += 20
                if st.checkbox("Rechazo de Estructura / EMA 50"): score += 20
                if st.checkbox("Patrón de Vela (H4/Daily)"): score += 20
                
                st.write("**GATILLO (OBLIGATORIO):**")
                entry = st.checkbox("⚡ Shift of Structure + Vela Envolvente")
                ratio = st.checkbox("💰 Ratio Riesgo/Beneficio > 1:2.5")
                
                if entry and ratio: score += 40
            
            else: # Scalping
                st.subheader("⚡ SCALP SETUP")
                col_a, col_b, col_c = st.columns(3)
                t4 = col_a.selectbox("H4", ["UP", "DOWN"])
                t2 = col_b.selectbox("H2", ["UP", "DOWN"])
                t1 = col_c.selectbox("H1", ["UP", "DOWN"])
                
                if t4==t2==t1: st.success("💎 TRIPLE CONFLUENCIA")
                else: st.warning("⚠️ CUIDADO: TENDENCIA MIXTA")
                
                score = 0
                if st.checkbox("Rechazo AOI (H1/H2)"): score += 25
                if st.checkbox("Patrón Vela (H1)"): score += 25
                entry = st.checkbox("⚡ Quiebre Estructura M15")
                ratio = st.checkbox("💰 Ratio > 1:2.5")
                if entry and ratio: score += 50

            st.markdown('</div>', unsafe_allow_html=True)
            
            # Resultado Score
            st.progress(score)
            if score >= 80:
                st.success("✅ EJECUTAR TRADE - ALTA PROBABILIDAD")
            elif score >= 50:
                st.warning("⚠️ TRADE ARRIESGADO - FALTAN CONFIRMACIONES")
            else:
                st.error("⛔ NO OPERAR - ESPERAR MEJOR SETUP")

    # 2. CALENDARIO
    with tab_cal:
        st.subheader(f"📅 P&L CALENDAR: {selected_account}")
        df = cargar_trades(user, selected_account)
        df = df[df["Dinero"] != 0] # Solo trades con dinero
        
        c_y, c_m = st.columns([1, 4])
        year = c_y.number_input("Año", value=datetime.now().year)
        mes_idx = datetime.now().month
        month_names = list(calendar.month_name)[1:]
        mes_sel = c_m.selectbox("Mes", month_names, index=mes_idx-1)
        month = month_names.index(mes_sel) + 1
        
        st.markdown(render_calendar_html(year, month, df), unsafe_allow_html=True)

    # 3. ANALYTICS (PLOTLY)
    with tab_stats:
        st.subheader(f"📊 PERFORMANCE: {selected_account}")
        df = cargar_trades(user, selected_account)
        df = df[df["Resultado"].notna()]
        
        if not df.empty:
            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            net_pl = df["Dinero"].sum()
            wins = len(df[df["Dinero"] > 0])
            total = len(df)
            wr = (wins/total*100) if total > 0 else 0
            
            kpi1.metric("Net P&L", f"${net_pl:,.2f}", delta_color="normal")
            kpi2.metric("Win Rate", f"{wr:.1f}%")
            kpi3.metric("Trades", total)
            kpi4.metric("Avg Trade", f"${df['Dinero'].mean():.2f}")
            
            # GRAFICOS PLOTLY
            col_chart1, col_chart2 = st.columns([2, 1])
            with col_chart1:
                fig_eq = plot_equity_curve(df)
                if fig_eq: st.plotly_chart(fig_eq, use_container_width=True)
            
            with col_chart2:
                # Pie Chart Win/Loss
                counts = df['Resultado'].value_counts()
                fig_pie = go.Figure(data=[go.Pie(labels=counts.index, values=counts.values, hole=.5)])
                fig_pie.update_layout(title="Win vs Loss", paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#e0e0e0'))
                st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Registra trades para ver las gráficas.")

    # 4. REGISTRO
    with tab_reg:
        st.subheader("📝 Nuevo Registro de Trade")
        with st.form("add_trade"):
            col_a, col_b = st.columns(2)
            fecha = col_a.date_input("Fecha", datetime.now())
            par = col_a.text_input("Par (ej: BTCUSD)", "EURUSD").upper()
            tipo = col_a.selectbox("Tipo", ["BUY", "SELL"])
            
            res = col_b.selectbox("Resultado", ["WIN", "LOSS", "BE"])
            dinero = col_b.number_input("Profit/Loss ($)", step=10.0, help="Usa negativo para pérdidas (-50)")
            ratio = col_b.number_input("Ratio Obtenido", value=2.5)
            
            nota = st.text_area("Notas / Emociones")
            
            if st.form_submit_button("💾 GUARDAR TRADE"):
                guardar_trade(user, selected_account, {
                    "Fecha": fecha, "Par": par, "Tipo": tipo,
                    "Resultado": res, "Dinero": dinero, "Ratio": ratio, "Notas": nota
                })
                st.success("Trade guardado exitosamente.")

# --- LANZADOR ---
if 'user' not in st.session_state: st.session_state.user = None

if st.session_state.user:
    main_app()
else:
    login_screen()
