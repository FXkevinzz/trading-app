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

# --- GESTIÓN DE USUARIOS Y DATOS (BACKEND) ---
DATA_DIR = "user_data"
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
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

def get_user_folder(username):
    folder = os.path.join(DATA_DIR, username)
    if not os.path.exists(folder): os.makedirs(folder)
    return folder

def get_account_file(username, account_name):
    clean = "".join(c for c in account_name if c.isalnum() or c in (' ', '_')).strip().replace(" ", "_")
    return os.path.join(get_user_folder(username), f"{clean}.csv")

def get_user_accounts(username):
    folder = get_user_folder(username)
    files = [f.replace(".csv", "").replace("_", " ") for f in os.listdir(folder) if f.endswith(".csv")]
    if not files: return ["Principal"]
    return files

def cargar_trades(username, account_name):
    path = get_account_file(username, account_name)
    if not os.path.exists(path): return pd.DataFrame(columns=["Fecha", "Par", "Tipo", "Resultado", "Dinero", "Ratio", "Notas"])
    return pd.read_csv(path)

def guardar_trade(username, account_name, data):
    df = cargar_trades(username, account_name)
    new = pd.DataFrame([data])
    df = pd.concat([df, new], ignore_index=True)
    df.to_csv(get_account_file(username, account_name), index=False)

# --- FUNCIÓN IMÁGENES (ENLACES ESTABLES) ---
def mostrar_imagen(nombre_archivo, caption):
    # Usamos enlaces de Wikimedia Commons que son estables y públicos
    links = {
        "bullish_engulfing.png": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/Candlestick_Pattern_Bullish_Engulfing.png/320px-Candlestick_Pattern_Bullish_Engulfing.png",
        "bearish_engulfing.png": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/19/Candlestick_Pattern_Bearish_Engulfing.png/320px-Candlestick_Pattern_Bearish_Engulfing.png",
        "hammer.png": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/30/Candlestick_Pattern_Hammer.png/320px-Candlestick_Pattern_Hammer.png",
        "shooting_star.png": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/67/Candlestick_Pattern_Shooting_Star.png/320px-Candlestick_Pattern_Shooting_Star.png",
        "morning_star.png": "https://a.c-dn.net/b/1XlqMQ/Morning-Star-Candlestick-Pattern_body_MorningStar.png.full.png" # Este suele funcionar bien
    }
    
    if nombre_archivo in links: 
        st.image(links[nombre_archivo], caption=caption, width=200)
    else: 
        st.warning(f"⚠️ Imagen no disponible: {nombre_archivo}")

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .stApp {background-color: #0E1117; color: white;}
    
    /* Contenedores */
    div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] > div[data-testid="stVerticalBlock"] {
        background-color: #161B22; padding: 15px; border-radius: 8px; border: 1px solid #30363D;
    }
    /* Inputs */
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div {
        background-color: #0E1117 !important; color: white !important; border: 1px solid #444;
    }
    /* Calendario */
    .calendar-container { display: grid; grid-template-columns: repeat(7, 1fr); gap: 3px; background: #222; border: 1px solid #444; }
    .calendar-header { background: #111; color: #ff9900; text-align: center; padding: 5px; font-weight: bold; }
    .calendar-day { min-height: 80px; background: #000; padding: 5px; display: flex; flex-direction: column; justify-content: space-between; }
    .day-num { color: #666; font-size: 0.8em; }
    .day-val { text-align: right; font-weight: bold; }
    
    /* Alertas */
    .plan-box {border-left: 5px solid #4CAF50; padding: 15px; background-color: rgba(76, 175, 80, 0.1); border-radius: 5px; margin-top: 10px;}
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
    
    html = '<div class="calendar-container">'
    for d in ["LUN","MAR","MIÉ","JUE","VIE","SÁB","DOM"]: html += f'<div class="calendar-header">{d}</div>'
    
    for week in month_days:
        for day in week:
            if day == 0: html += '<div class="calendar-day" style="background:#111;"></div>'
            else:
                val = data.get(day, 0)
                color = "#00ff00" if val > 0 else "#ff4444" if val < 0 else "#555"
                txt = f"${val:,.0f}" if val != 0 else "-"
                html += f'<div class="calendar-day"><div class="day-num">{day}</div><div class="day-val" style="color:{color}">{txt}</div></div>'
    html += '</div>'
    return html

# --- GRÁFICOS ---
def plot_charts(df):
    if df.empty: return
    df = df.sort_values("Fecha")
    df['Equity'] = df['Dinero'].cumsum()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Fecha'], y=df['Equity'], mode='lines+markers', line=dict(color='#00ff00')))
    fig.update_layout(title="Equity Curve", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
    st.plotly_chart(fig, use_container_width=True)

# --- PANTALLAS ---
def login():
    c1,c2,c3 = st.columns([1,1,1])
    with c2:
        st.title("🔒 Trading Access")
        t1, t2 = st.tabs(["LOGIN", "REGISTRO"])
        with t1:
            u = st.text_input("Usuario")
            p = st.text_input("Pass", type="password")
            if st.button("Entrar"):
                if verify_user(u, p): st.session_state.user = u; st.rerun()
                else: st.error("Error")
        with t2:
            nu = st.text_input("Nuevo User")
            np = st.text_input("Nueva Pass", type="password")
            if st.button("Crear"):
                if nu and np: save_user(nu, np); st.success("Creado!")

def app():
    user = st.session_state.user
    with st.sidebar:
        st.title(f"👤 {user}")
        if st.button("Salir"): st.session_state.user = None; st.rerun()
        st.divider()
        accs = get_user_accounts(user)
        sel_acc = st.selectbox("Cuenta", accs)
        with st.expander("Nueva Cuenta"):
            n_acc = st.text_input("Nombre")
            if st.button("Crear") and n_acc: guardar_trade(user, n_acc, {"Fecha":datetime.now(),"Dinero":0}); st.rerun()
        
        st.divider()
        # SELECTOR DE MODO
        modo = st.radio("Modo Operativa", ["Swing / Day (W-D-4H)", "Scalping (4H-2H-1H)"])
        
        tz = pytz.timezone('America/Guayaquil')
        h = datetime.now(tz).hour
        st.markdown(f"**Mercado:** {'❌ CERRADO' if 15<=h<19 else '✅ ABIERTO'}")

    # --- DEFINICIÓN DE PESTAÑAS (NOMBRES CORREGIDOS) ---
    tab_op, tab_cal, tab_dash, tab_reg = st.tabs(["🦁 OPERATIVA", "📅 CALENDARIO", "📊 DASHBOARD", "📝 REGISTRO"])

    # === TAB 1: OPERATIVA ===
    with tab_op:
        c_guia, c_check, c_res = st.columns([1, 2, 1.2], gap="medium")

        # 1. IMÁGENES
        with c_guia:
            st.header("📖 Chuleta")
            with st.expander("🐂 Alcistas", expanded=True):
                st.markdown("### Bullish Engulfing"); mostrar_imagen("bullish_engulfing.png", "Verde envuelve roja")
                st.markdown("### Morning Star"); mostrar_imagen("morning_star.png", "Giro 3 velas")
                st.markdown("### Hammer"); mostrar_imagen("hammer.png", "Rechazo abajo")
            with st.expander("🐻 Bajistas"):
                st.markdown("### Bearish Engulfing"); mostrar_imagen("bearish_engulfing.png", "Roja envuelve verde")
                st.markdown("### Shooting Star"); mostrar_imagen("shooting_star.png", "Rechazo arriba")

        # 2. CHECKLIST DETALLADO
        with c_check:
            if "Swing" in modo:
                st.subheader("🔗 Tendencias (W / D / 4H)")
                c1, c2, c3 = st.columns(3)
                # USAMOS NOMBRES DE VARIABLE ÚNICOS PARA NO CHOCAR
                trend_w = c1.selectbox("Semanal", ["Alcista", "Bajista"], key="tw")
                trend_d = c2.selectbox("Diario", ["Alcista", "Bajista"], key="td")
                trend_4h = c3.selectbox("4 Horas", ["Alcista", "Bajista"], key="t4")
                
                if trend_w == trend_d == trend_4h: st.success("💎 TRIPLE SYNC")
                elif trend_w == trend_d: st.info("✅ SWING SYNC")
                elif trend_d == trend_4h: st.info("✅ DAY SYNC")
                else: st.warning("⚠️ MIXTO")
                
                st.divider()
                # Puntuaciones SWING
                c_a, c_b = st.columns(2)
                with c_a:
                    st.caption("1. Semanal (W)")
                    w_sc = sum([
                        st.checkbox("En/Rechazo AOI (+10%)", key="w1")*10,
                        st.checkbox("Rechazo Estruc. Previa (+10%)", key="w2")*10,
                        st.checkbox("Patrones (+10%)", key="w3")*10,
                        st.checkbox("Rechazo EMA 50 (+5%)", key="w4")*5,
                        st.checkbox("Nivel Psicológico (+5%)", key="w5")*5
                    ])
                with c_b:
                    st.caption("2. Diario (D)")
                    d_sc = sum([
                        st.checkbox("En/Rechazo AOI (+10%)", key="d1")*10,
                        st.checkbox("Rechazo Estruc. Previa (+10%)", key="d2")*10,
                        st.checkbox("Rechazo Vela (+10%)", key="d3")*10,
                        st.checkbox("Patrones (+10%)", key="d4")*10,
                        st.checkbox("Rechazo EMA 50 (+5%)", key="d5")*5
                    ])
                st.divider()
                c_c, c_d = st.columns(2)
                with c_c:
                    st.caption("3. Ejecución (4H)")
                    h4_sc = sum([
                        st.checkbox("Rechazo Vela (+10%)", key="h1")*10,
                        st.checkbox("Patrones (+10%)", key="h2")*10,
                        st.checkbox("En/Rechazo AOI (+5%)", key="h3")*5,
                        st.checkbox("Rechazo Estructura (+5%)", key="h4")*5,
                        st.checkbox("Rechazo EMA 50 (+5%)", key="h5")*5
                    ])
                with c_d:
                    st.caption("4. GATILLO (Obligatorio)")
                    entry_sos = st.checkbox("⚡ Shift of Structure", key="e1")
                    entry_eng = st.checkbox("🕯️ Vela Envolvente", key="e2")
                    entry_rr = st.checkbox("💰 Ratio 1:2.5", key="e3")
                    entry_score = sum([entry_sos*10, entry_eng*10])
                
                total = w_sc + d_sc + h4_sc + entry_score

            else:
                # LÓGICA SCALPING
                st.subheader("🔗 Tendencias (4H / 2H / 1H)")
                c1, c2, c3 = st.columns(3)
                trend_4h = c1.selectbox("4H", ["Alcista", "Bajista"], key="st4")
                trend_2h = c2.selectbox("2H", ["Alcista", "Bajista"], key="st2")
                trend_1h = c3.selectbox("1H", ["Alcista", "Bajista"], key="st1")
                
                if trend_4h == trend_2h == trend_1h: st.success("💎 TRIPLE SYNC")
                elif trend_4h == trend_2h: st.info("✅ 4H-2H SYNC")
                elif trend_2h == trend_1h: st.info("✅ 2H-1H SYNC")
                else: st.warning("⚠️ MIXTO")

                st.divider()
                c_a, c_b = st.columns(2)
                with c_a:
                    st.caption("1. Contexto 4H")
                    w_sc = sum([
                        st.checkbox("En/Rechazo AOI (+5%)", key="sc1")*5,
                        st.checkbox("Rechazo Estruc. (+5%)", key="sc2")*5,
                        st.checkbox("Patrones (+5%)", key="sc3")*5,
                        st.checkbox("Rechazo EMA 50 (+5%)", key="sc4")*5,
                        st.checkbox("Psicológico (+5%)", key="sc5")*5
                    ])
                with c_b:
                    st.caption("2. Contexto 2H")
                    d_sc = sum([
                        st.checkbox("En/Rechazo AOI (+5%)", key="sc6")*5,
                        st.checkbox("Rechazo Estruc. (+5%)", key="sc7")*5,
                        st.checkbox("Rechazo Vela (+5%)", key="sc8")*5,
                        st.checkbox("Patrones (+5%)", key="sc9")*5,
                        st.checkbox("Rechazo EMA 50 (+5%)", key="sc10")*5
                    ])
                st.divider()
                c_c, c_d = st.columns(2)
                with c_c:
                    st.caption("3. Ejecución (1H)")
                    h4_sc = sum([
                        st.checkbox("Rechazo Vela (+5%)", key="sc11")*5,
                        st.checkbox("Patrones (+5%)", key="sc12")*5,
                        st.checkbox("Rechazo Estruc. (+5%)", key="sc13")*5,
                        st.checkbox("Rechazo EMA 50 (+5%)", key="sc14")*5
                    ])
                with c_d:
                    st.caption("4. GATILLO (M15/M30)")
                    entry_sos = st.checkbox("⚡ SOS", key="se1")
                    entry_eng = st.checkbox("🕯️ Vela Entrada", key="se2")
                    entry_rr = st.checkbox("💰 Ratio 1:2.5", key="se3")
                    entry_score = sum([entry_sos*10, entry_eng*10])
                
                total = w_sc + d_sc + h4_sc + entry_score + 10

        # 3. RESULTADOS
        with c_res:
            is_valid = entry_sos and entry_eng and entry_rr
            
            def get_advice():
                if not entry_sos: return "⛔ STOP: Falta Estructura"
                if not entry_eng: return "⚠️ CUIDADO: Falta Vela"
                if not entry_rr: return "💸 RIESGO: Mal Ratio"
                if total >= 90: return "💎 SNIPER: Ejecuta"
                return "💤 ESPERA"
            
            msg = get_advice()
            st.header("🤖 Análisis")
            if "STOP" in msg: st.error(msg)
            elif "CUIDADO" in msg: st.warning(msg)
            elif "SNIPER" in msg: st.success(msg)
            else: st.info(msg)
            
            st.divider()
            st.metric("Probabilidad", f"{min(total, 100)}%")
            st.progress(min(total, 100))
            
            if is_valid and total >= 60:
                st.success("### ✅ EJECUTAR")
                plan = "<b>Swing:</b> SL 5-7 pips<br><b>Scalp:</b> SL 3-5 pips"
                st.markdown(f'<div class="plan-box">{plan}</div>', unsafe_allow_html=True)
            else:
                st.error("### ❌ NO OPERAR")

    # === TAB 2: CALENDARIO ===
    with tab_cal:
        st.subheader(f"📅 Calendario: {sel_acc}")
        df = cargar_trades(user, sel_acc)
        df_real = df[df['Dinero'] != 0]
        y = st.number_input("Año", value=2025)
        m = st.slider("Mes", 1, 12, datetime.now().month)
        st.markdown(render_calendar(y, m, df_real), unsafe_allow_html=True)

    # === TAB 3: DASHBOARD ===
    with tab_dash:
        st.subheader(f"📊 Métricas: {sel_acc}")
        df = cargar_trades(user, sel_acc)
        df_res = df[df['Resultado'].notna()]
        if not df_res.empty:
            k1,k2,k3 = st.columns(3)
            net = df_res['Dinero'].sum()
            wins = len(df_res[df_res['Dinero']>0])
            k1.metric("Neto", f"${net:,.2f}")
            k2.metric("Wins", wins)
            k3.metric("Total Trades", len(df_res))
            plot_charts(df_res)
        else: st.info("Sin datos")

    # === TAB 4: REGISTRO ===
    with tab_reg:
        st.subheader("📝 Registrar")
        with st.form("reg"):
            c1,c2 = st.columns(2)
            dt = c1.date_input("Fecha", datetime.now())
            pr = c1.text_input("Par", "XAUUSD")
            tp = c1.selectbox("Tipo", ["BUY", "SELL"])
            rs = c2.selectbox("Resultado", ["WIN", "LOSS", "BE"])
            mn = c2.number_input("Dinero ($)", step=10.0)
            rt = c2.number_input("Ratio", value=2.5)
            nt = st.text_area("Notas")
            if st.form_submit_button("Guardar"):
                guardar_trade(user, sel_acc, {"Fecha":dt, "Par":pr, "Tipo":tp, "Resultado":rs, "Dinero":mn, "Ratio":rt, "Notas":nt})
                st.success("Guardado")

if 'user' not in st.session_state: st.session_state.user = None
if st.session_state.user: app()
else: login()
