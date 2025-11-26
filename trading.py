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

# --- 2. ESTILOS CSS (BLOOMBERG DARK) ---
st.markdown("""
    <style>
    /* MODO OSCURO GLOBAL */
    .stApp { background-color: #050505; color: #e0e0e0; }
    
    /* INPUTS */
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div, .stDateInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: #111 !important; color: #fff !important; border: 1px solid #333 !important;
    }
    
    /* CALENDARIO */
    .calendar-container { display: grid; grid-template-columns: repeat(7, 1fr); gap: 5px; margin-top: 10px; }
    .calendar-header { background: #222; color: #ff9900; text-align: center; padding: 5px; font-weight: bold; border-radius: 4px; }
    .calendar-day { min-height: 90px; background: #0a0a0a; padding: 5px; display: flex; flex-direction: column; justify-content: space-between; border: 1px solid #222; border-radius: 4px; }
    .day-num { color: #666; font-size: 0.8em; font-weight: bold; }
    .day-val { text-align: right; font-weight: bold; font-size: 1.0em; }
    .win-text { color: #00ff00; } .loss-text { color: #ff3333; }
    
    /* PLAN BOX */
    .plan-box {border-left: 5px solid #4CAF50; padding: 15px; background-color: rgba(76, 175, 80, 0.1); border-radius: 5px; margin-top: 10px;}
    
    /* TABS */
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        background-color: #333 !important; color: #00ff00 !important; border-top: 2px solid #00ff00 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. GESTIÓN DE DATOS ---
DATA_DIR = "user_data"
IMG_DIR = "fotos"
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
USERS_FILE = os.path.join(DATA_DIR, "users.json")
ACCOUNTS_FILE = os.path.join(DATA_DIR, "accounts_config.json")

# Funciones de carga/guardado
def load_json(fp): return json.load(open(fp)) if os.path.exists(fp) else {}
def save_json(fp, data): json.dump(data, open(fp, "w"))

# Usuarios
def verify_user(u, p): d = load_json(USERS_FILE); return u in d and d[u] == p
def register_user(u, p): d = load_json(USERS_FILE); d[u] = p; save_json(USERS_FILE, d)

# Cuentas
def get_user_accounts(u): d = load_json(ACCOUNTS_FILE); return list(d.get(u, {}).keys()) if u in d else ["Principal"]
def create_account(u, name, bal):
    d = load_json(ACCOUNTS_FILE)
    if u not in d: d[u] = {}
    if name not in d[u]: d[u][name] = bal; save_json(ACCOUNTS_FILE, d)

def get_balance(u, acc):
    d = load_json(ACCOUNTS_FILE)
    ini = d.get(u, {}).get(acc, 0)
    fp = os.path.join(DATA_DIR, u, f"{acc}.csv".replace(" ", "_"))
    pnl = pd.read_csv(fp)["Dinero"].sum() if os.path.exists(fp) else 0
    return ini, ini + pnl

def save_trade(u, acc, data):
    folder = os.path.join(DATA_DIR, u)
    if not os.path.exists(folder): os.makedirs(folder)
    fp = os.path.join(folder, f"{acc}.csv".replace(" ", "_"))
    df = pd.read_csv(fp) if os.path.exists(fp) else pd.DataFrame(columns=["Fecha","Par","Tipo","Resultado","Dinero","Ratio","Notas"])
    df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
    df.to_csv(fp, index=False)
    return df

def load_trades(u, acc):
    fp = os.path.join(DATA_DIR, u, f"{acc}.csv".replace(" ", "_"))
    return pd.read_csv(fp) if os.path.exists(fp) else pd.DataFrame(columns=["Fecha","Par","Tipo","Resultado","Dinero","Ratio","Notas"])

# --- 4. FUNCIONES VISUALES ---
def mostrar_imagen(nombre, caption):
    local = os.path.join(IMG_DIR, nombre)
    if os.path.exists(local): st.image(local, caption=caption, use_container_width=True)
    else:
        # Fallback web
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

def render_cal_html(df):
    d = st.session_state.get('cal_date', datetime.now())
    y, m = d.year, d.month
    
    data = {}
    if not df.empty:
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        df_m = df[(df['Fecha'].dt.year==y) & (df['Fecha'].dt.month==m)]
        data = df_m.groupby(df['Fecha'].dt.day)['Dinero'].sum().to_dict()

    cal = calendar.Calendar(firstweekday=0)
    html = '<div class="calendar-container">'
    for h in ["LUN","MAR","MIÉ","JUE","VIE","SÁB","DOM"]: html += f'<div class="calendar-header">{h}</div>'
    
    for week in cal.monthdayscalendar(y, m):
        for day in week:
            if day == 0: html += '<div class="calendar-day" style="opacity:0;"></div>'
            else:
                val = data.get(day, 0)
                txt = f"${val:,.0f}" if val != 0 else ""
                cls = "win-text" if val > 0 else "loss-text" if val < 0 else ""
                bg = "rgba(0,255,0,0.1)" if val > 0 else "rgba(255,0,0,0.1)" if val < 0 else "#0a0a0a"
                border = "#00ff00" if val > 0 else "#ff3333" if val < 0 else "#222"
                html += f'<div class="calendar-day" style="background:{bg}; border:1px solid {border}"><div class="day-num">{day}</div><div class="day-val {cls}">{txt}</div></div>'
    html += '</div>'
    return html, y, m

# --- 5. LOGIN ---
def login_screen():
    c1,c2,c3 = st.columns([1,1,1])
    with c2:
        st.title("🦁 Trading Suite")
        t1, t2 = st.tabs(["Ingresar", "Registrarse"])
        with t1:
            u = st.text_input("Usuario")
            p = st.text_input("Password", type="password")
            if st.button("Entrar", type="primary"):
                if verify_user(u, p): st.session_state.user = u; st.rerun()
                else: st.error("Error")
        with t2:
            nu = st.text_input("Nuevo Usuario")
            np = st.text_input("Nueva Password", type="password")
            if st.button("Crear"):
                if nu and np: register_user(nu, np); st.success("Creado!"); st.rerun()

# --- 6. APP PRINCIPAL ---
def main_app():
    user = st.session_state.user
    if 'cal_date' not in st.session_state: st.session_state['cal_date'] = datetime.now()

    # SIDEBAR
    with st.sidebar:
        st.title(f"👤 {user}")
        if st.button("Cerrar Sesión"): st.session_state.user = None; st.rerun()
        st.divider()
        
        # Selector Cuentas
        accs = get_user_accounts(user)
        sel_acc = st.selectbox("📂 Cuenta Activa", accs)
        ini, act = get_balance(user, sel_acc)
        
        # Info Saldo
        col_s = "#00ff00" if act >= ini else "#ff3333"
        st.markdown(f"""
        <div style="background:#111; padding:15px; border-radius:10px; border:1px solid #333; text-align:center">
            <small style="color:#888">SALDO ACTUAL</small>
            <h2 style="color:{col_s}; margin:5px 0">${act:,.2f}</h2>
            <small style="color:#555">Inicio: ${ini:,.2f}</small>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        with st.expander("➕ Nueva Cuenta"):
            na = st.text_input("Nombre")
            nb = st.number_input("Saldo", value=10000.0)
            if st.button("Crear") and na: create_account(user, na, nb); st.rerun()

    # PESTAÑAS (ORDEN SOLICITADO: OPERATIVA -> REGISTRO -> DASH -> CAL)
    t_op, t_reg, t_dash, t_cal = st.tabs(["🦁 OPERATIVA", "📝 REGISTRO", "📊 DASHBOARD", "📅 CALENDARIO"])

    # === 1. OPERATIVA (TU LÓGICA ORIGINAL) ===
    with t_op:
        st.subheader("🦁 Análisis de Estrategia")
        col_guia, col_check, col_res = st.columns([1, 2, 1.2], gap="medium")

        with col_guia:
            st.markdown("### 📖 Chuleta")
            with st.expander("🐂 Alcistas", expanded=True):
                st.caption("Bullish Engulfing"); mostrar_imagen("bullish_engulfing.png", "B. Engulfing")
                st.caption("Morning Star"); mostrar_imagen("morning_star.png", "Morning Star")
                st.caption("Hammer"); mostrar_imagen("hammer.png", "Hammer")
            with st.expander("🐻 Bajistas"):
                st.caption("Bearish Engulfing"); mostrar_imagen("bearish_engulfing.png", "B. Engulfing")
                st.caption("Shooting Star"); mostrar_imagen("shooting_star.png", "Shooting Star")

        with col_check:
            modo = st.radio("Modo", ["Swing (W-D-4H)", "Scalping (4H-2H-1H)"], horizontal=True)
            
            if "Swing" in modo:
                # --- SWING LOGIC ---
                st.markdown("#### 🔗 Tendencias")
                c1,c2,c3 = st.columns(3)
                tw = c1.selectbox("Semanal (W)", ["Alcista", "Bajista"], key="tw")
                td = c2.selectbox("Diario (D)", ["Alcista", "Bajista"], key="td")
                t4 = c3.selectbox("4 Horas (4H)", ["Alcista", "Bajista"], key="t4")
                
                if tw==td==t4: st.success("💎 TRIPLE SYNC")
                elif tw==td: st.info("✅ SWING SYNC")
                elif td==t4: st.info("✅ DAY SYNC")
                else: st.warning("⚠️ MIXTO")
                
                st.divider()
                c_a, c_b = st.columns(2)
                with c_a:
                    st.markdown("**1. Semanal (W)**")
                    w_sc = sum([
                        st.checkbox("En/Rechazo AOI (+10%)", key="w1")*10,
                        st.checkbox("Rechazo Estruc. Previa (+10%)", key="w2")*10,
                        st.checkbox("Patrones (+10%)", key="w3")*10,
                        st.checkbox("Rechazo EMA 50 (+5%)", key="w4")*5,
                        st.checkbox("Nivel Psicológico (+5%)", key="w5")*5
                    ])
                with c_b:
                    st.markdown("**2. Diario (D)**")
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
                    st.markdown("**3. Ejecución (4H)**")
                    h4_sc = sum([
                        st.checkbox("Rechazo Vela (+10%)", key="h1")*10,
                        st.checkbox("Patrones (+10%)", key="h2")*10,
                        st.checkbox("En/Rechazo AOI (+5%)", key="h3")*5,
                        st.checkbox("Rechazo Estructura (+5%)", key="h4")*5,
                        st.checkbox("Rechazo EMA 50 (+5%)", key="h5")*5
                    ])
                with c_d:
                    st.markdown("**4. GATILLO**")
                    sos = st.checkbox("⚡ Shift of Structure", key="e1")
                    eng = st.checkbox("🕯️ Vela Envolvente", key="e2")
                    rr = st.checkbox("💰 Ratio 1:2.5", key="e3")
                    entry_score = sum([sos*10, eng*10])
                
                total = w_sc + d_sc + h4_sc + entry_score

            else:
                # --- SCALPING LOGIC ---
                st.markdown("#### 🔗 Tendencias")
                c1,c2,c3 = st.columns(3)
                t4 = c1.selectbox("4H", ["Alcista", "Bajista"], key="st4")
                t2 = c2.selectbox("2H", ["Alcista", "Bajista"], key="st2")
                t1 = c3.selectbox("1H", ["Alcista", "Bajista"], key="st1")
                
                if t4==t2==t1: st.success("💎 TRIPLE SYNC")
                elif t4==t2: st.info("✅ 4H-2H SYNC")
                elif t2==t1: st.info("✅ 2H-1H SYNC")
                else: st.warning("⚠️ MIXTO")
                
                st.divider()
                c_a, c_b = st.columns(2)
                with c_a:
                    st.markdown("**1. Contexto 4H**")
                    w_sc = sum([
                        st.checkbox("En/Rechazo AOI (+5%)", key="sc1")*5,
                        st.checkbox("Rechazo Estruc. Previa (+5%)", key="sc2")*5,
                        st.checkbox("Patrones (+5%)", key="sc3")*5,
                        st.checkbox("Rechazo EMA 50 (+5%)", key="sc4")*5,
                        st.checkbox("Nivel Psicológico (+5%)", key="sc5")*5
                    ])
                with c_b:
                    st.markdown("**2. Contexto 2H**")
                    d_sc = sum([
                        st.checkbox("En/Rechazo AOI (+5%)", key="sc6")*5,
                        st.checkbox("Rechazo Estruc. Previa (+5%)", key="sc7")*5,
                        st.checkbox("Rechazo Vela (+5%)", key="sc8")*5,
                        st.checkbox("Patrones (+5%)", key="sc9")*5,
                        st.checkbox("Rechazo EMA 50 (+5%)", key="sc10")*5
                    ])
                
                st.divider()
                c_c, c_d = st.columns(2)
                with c_c:
                    st.markdown("**3. Ejecución (1H)**")
                    h4_sc = sum([
                        st.checkbox("Rechazo Vela (+5%)", key="sc11")*5,
                        st.checkbox("Patrones (+5%)", key="sc12")*5,
                        st.checkbox("Rechazo Estruc. Previa (+5%)", key="sc13")*5,
                        st.checkbox("Rechazo EMA 50 (+5%)", key="sc14")*5
                    ])
                with c_d:
                    st.markdown("**4. GATILLO (M15/M30)**")
                    sos = st.checkbox("⚡ SOS", key="se1")
                    eng = st.checkbox("🕯️ Vela Envolvente", key="se2")
                    rr = st.checkbox("💰 Ratio 1:2.5", key="se3")
                    entry_score = sum([sos*10, eng*10])
                
                total = w_sc + d_sc + h4_sc + entry_score + 10

        with col_res:
            valid = sos and eng and rr
            def get_msg():
                if not sos: return "⛔ Falta Estructura"
                if not eng: return "⚠️ Falta Vela"
                if not rr: return "💸 Mal Ratio"
                if total >= 90: return "💎 SNIPER"
                return "💤 ESPERA"
            
            msg = get_msg()
            st.metric("Score", f"{min(total, 100)}%")
            st.progress(min(total, 100))
            if "SNIPER" in msg: st.success(msg)
            elif "Falta" in msg: st.error(msg)
            else: st.warning(msg)
            
            if valid and total >= 60:
                st.success("✅ EJECUTAR")
                sl = "5-7 pips" if "Swing" in modo else "3-5 pips"
                st.markdown(f'<div class="plan-box">Stop: {sl}<br>TP: Estructura</div>', unsafe_allow_html=True)
            else:
                st.error("NO OPERAR")

    # === 2. REGISTRO ===
    with t_reg:
        st.subheader("📝 Registrar Trade")
        with st.form("reg"):
            c1,c2 = st.columns(2)
            dt = c1.date_input("Fecha", datetime.now())
            pr = c1.text_input("Par", "XAUUSD").upper()
            tp = c1.selectbox("Tipo", ["BUY", "SELL"])
            rs = c2.selectbox("Resultado", ["WIN", "LOSS", "BE"])
            mn = c2.number_input("P/L ($)", step=10.0, help="Negativo si pierdes")
            rt = c2.number_input("Ratio", value=2.5)
            nt = st.text_area("Notas")
            if st.form_submit_button("Guardar"):
                save_trade(user, sel_acc, {"Fecha":dt,"Par":pr,"Tipo":tp,"Resultado":rs,"Dinero":mn,"Ratio":rt,"Notas":nt})
                st.success("Guardado!"); st.rerun()

    # === 3. DASHBOARD ===
    with t_dash:
        st.subheader("📊 Métricas")
        df = load_trades(user, sel_acc)
        if not df.empty:
            k1,k2,k3,k4 = st.columns(4)
            wins = len(df[df["Resultado"]=="WIN"])
            k1.metric("Neto", f"${df['Dinero'].sum():,.2f}")
            k2.metric("WinRate", f"{(wins/len(df)*100):.1f}%")
            k3.metric("Trades", len(df))
            k4.metric("Saldo", f"${act:,.2f}")
            
            df["Eq"] = ini + df["Dinero"].cumsum()
            fig = go.Figure(go.Scatter(x=df["Fecha"], y=df["Eq"], line=dict(color='#00ff00', width=3)))
            fig.update_layout(title="Equity Curve", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
            st.plotly_chart(fig, use_container_width=True)
        else: st.info("Sin trades registrados")

    # === 4. CALENDARIO ===
    with t_cal:
        st.subheader(f"📅 Calendario: {sel_acc}")
        c_p, c_t, c_n = st.columns([1,5,1])
        with c_p: 
            if st.button("⬅️"): change_month(-1); st.rerun()
        with c_n: 
            if st.button("➡️"): change_month(1); st.rerun()
            
        df = load_trades(user, sel_acc)
        html, y, m = render_cal_html(df)
        with c_t: st.markdown(f"<h3 style='text-align:center; color:#ff9900'>{calendar.month_name[m]} {y}</h3>", unsafe_allow_html=True)
        st.markdown(html, unsafe_allow_html=True)

# --- EXEC ---
if 'user' not in st.session_state: st.session_state.user = None
if st.session_state.user: main_app()
else: login_screen()
