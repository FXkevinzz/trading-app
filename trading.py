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

# --- 2. ESTILOS CSS PROFESIONALES (ADAPTABLES) ---
st.markdown("""
    <style>
    /* VARIABLES CSS PARA ADAPTARSE A TEMA CLARO/OSCURO AUTOMÁTICAMENTE */
    :root {
        --card-bg: rgba(255, 255, 255, 0.05);
        --border-color: rgba(128, 128, 128, 0.2);
        --shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        --accent-gold: #D4AF37;
        --accent-green: #00C853;
        --accent-red: #D50000;
    }

    /* TARJETAS (CARDS) ESTILO GLASSMORPHISM */
    .st-emotion-cache-1r6slb0, .css-1r6slb0 { /* Contenedores nativos */
        border: 1px solid var(--border-color);
        border-radius: 10px;
        padding: 20px;
        box-shadow: var(--shadow);
    }
    
    /* CLASE PERSONALIZADA PARA CAJAS */
    .custom-card {
        background-color: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        transition: transform 0.2s;
    }
    .custom-card:hover {
        transform: translateY(-2px);
        border-color: var(--accent-gold);
    }

    /* TITULOS DE SECCIÓN */
    .section-title {
        font-size: 1.1rem;
        font-weight: 700;
        margin-bottom: 15px;
        text-transform: uppercase;
        letter-spacing: 1px;
        border-bottom: 2px solid var(--border-color);
        padding-bottom: 5px;
    }

    /* INPUTS MAS ELEGANTES */
    .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] {
        border-radius: 8px !important;
    }

    /* BOTONES */
    .stButton button {
        border-radius: 8px !important;
        font-weight: bold !important;
        width: 100%;
    }
    
    /* CALENDARIO MEJORADO */
    .calendar-container { 
        display: grid; 
        grid-template-columns: repeat(7, 1fr); 
        gap: 8px; 
        margin-top: 15px; 
    }
    .calendar-header { 
        text-align: center; 
        font-weight: 700; 
        opacity: 0.7; 
        font-size: 0.85rem;
    }
    .calendar-day { 
        min-height: 80px; 
        border-radius: 8px; 
        padding: 8px; 
        display: flex; 
        flex-direction: column; 
        justify-content: space-between; 
        font-size: 0.9rem;
        border: 1px solid var(--border-color);
        background-color: var(--card-bg);
    }
    
    /* KPI CARDS */
    .kpi-card {
        text-align: center;
        padding: 15px;
        border-radius: 10px;
        background: var(--card-bg);
        border: 1px solid var(--border-color);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. GESTIÓN DE DATOS ---
DATA_DIR = "user_data"
IMG_DIR = "fotos"
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
USERS_FILE = os.path.join(DATA_DIR, "users.json")
ACCOUNTS_FILE = os.path.join(DATA_DIR, "accounts_config.json")

def load_json(fp): return json.load(open(fp)) if os.path.exists(fp) else {}
def save_json(fp, data): json.dump(data, open(fp, "w"))
def verify_user(u, p): d = load_json(USERS_FILE); return u in d and d[u] == p
def register_user(u, p): d = load_json(USERS_FILE); d[u] = p; save_json(USERS_FILE, d)

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
            if day == 0: html += '<div class="calendar-day" style="opacity:0; border:none;"></div>'
            else:
                val = data.get(day, 0)
                txt = f"${val:,.0f}" if val != 0 else ""
                
                # Colores adaptables (usando variables CSS nativas cuando sea posible o colores hardcodeados que sirvan en ambos)
                color_text = "#00C853" if val > 0 else "#D50000" if val < 0 else "inherit"
                bg_color = "rgba(0, 200, 83, 0.1)" if val > 0 else "rgba(213, 0, 0, 0.1)" if val < 0 else "var(--card-bg)"
                border_color = "#00C853" if val > 0 else "#D50000" if val < 0 else "var(--border-color)"
                
                html += f'''
                <div class="calendar-day" style="background:{bg_color}; border:1px solid {border_color}">
                    <div style="opacity:0.6; font-size:0.8em; font-weight:bold;">{day}</div>
                    <div style="color:{color_text}; font-weight:bold; margin-top:auto; text-align:right;">{txt}</div>
                </div>'''
    html += '</div>'
    return html, y, m

# --- 5. LOGIN ---
def login_screen():
    c1,c2,c3 = st.columns([1,1,1])
    with c2:
        st.markdown("<h1 style='text-align:center;'>🦁 Trading Suite</h1>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["Ingresar", "Registrarse"])
        with t1:
            u = st.text_input("Usuario")
            p = st.text_input("Password", type="password")
            if st.button("Ingresar", type="primary"):
                if verify_user(u, p): st.session_state.user = u; st.rerun()
                else: st.error("Error de credenciales")
        with t2:
            nu = st.text_input("Nuevo Usuario")
            np = st.text_input("Nueva Password", type="password")
            if st.button("Crear Cuenta"):
                if nu and np: register_user(nu, np); st.success("Creado!"); st.rerun()

# --- 6. APP PRINCIPAL ---
def main_app():
    user = st.session_state.user
    if 'cal_date' not in st.session_state: st.session_state['cal_date'] = datetime.now()

    # --- SIDEBAR PROFESIONAL ---
    with st.sidebar:
        st.title(f"👤 {user}")
        if st.button("Cerrar Sesión"): st.session_state.user = None; st.rerun()
        st.markdown("---")
        
        accs = get_user_accounts(user)
        sel_acc = st.selectbox("📂 Cuenta Activa", accs)
        ini, act = get_balance(user, sel_acc)
        
        # Tarjeta de Saldo Sidebar
        col_s = "#00C853" if act >= ini else "#D50000"
        st.markdown(f"""
        <div class="custom-card" style="text-align:center;">
            <div style="font-size:0.8rem; opacity:0.7; text-transform:uppercase;">Saldo Actual</div>
            <div style="font-size:1.8rem; font-weight:bold; color:{col_s};">${act:,.2f}</div>
            <div style="font-size:0.8rem; opacity:0.5; margin-top:5px;">Inicial: ${ini:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        with st.expander("➕ Nueva Cuenta"):
            na = st.text_input("Nombre")
            nb = st.number_input("Saldo", value=10000.0)
            if st.button("Crear"):
                if na: create_account(user, na, nb); st.rerun()

    # --- CUERPO PRINCIPAL ---
    t_op, t_reg, t_dash, t_cal = st.tabs(["🦁 OPERATIVA", "📝 REGISTRO", "📊 DASHBOARD", "📅 CALENDARIO"])

    # === 1. OPERATIVA (REDISENADA) ===
    with t_op:
        col_guia, col_check, col_res = st.columns([1, 2, 1.2], gap="large")

        # GUÍA VISUAL
        with col_guia:
            st.markdown("<div class='section-title'>📖 Patrones</div>", unsafe_allow_html=True)
            with st.expander("🐂 Alcistas", expanded=True):
                st.caption("Bullish Engulfing"); mostrar_imagen("bullish_engulfing.png", "B. Engulfing")
                st.caption("Morning Star"); mostrar_imagen("morning_star.png", "Morning Star")
                st.caption("Hammer"); mostrar_imagen("hammer.png", "Hammer")
            with st.expander("🐻 Bajistas"):
                st.caption("Bearish Engulfing"); mostrar_imagen("bearish_engulfing.png", "B. Engulfing")
                st.caption("Shooting Star"); mostrar_imagen("shooting_star.png", "Shooting Star")

        # CHECKLIST OPERATIVO (DINÁMICO)
        with col_check:
            # Selector de Modo en una tarjeta destacada
            with st.container(border=True):
                modo = st.radio("Modo de Operativa", ["Swing (W-D-4H)", "Scalping (4H-2H-1H)"], horizontal=True)

            if "Swing" in modo:
                st.markdown("<div class='section-title'>1. Alineación de Tendencia</div>", unsafe_allow_html=True)
                with st.container(border=True):
                    c1,c2,c3 = st.columns(3)
                    tw = c1.selectbox("Semanal (W)", ["Alcista", "Bajista"], key="tw")
                    td = c2.selectbox("Diario (D)", ["Alcista", "Bajista"], key="td")
                    t4 = c3.selectbox("4 Horas (4H)", ["Alcista", "Bajista"], key="t4")
                    
                    if tw==td==t4: st.success("💎 TRIPLE ALINEACIÓN")
                    elif tw==td: st.info("✅ SWING SYNC")
                    elif td==t4: st.info("✅ DAY SYNC")
                    else: st.warning("⚠️ MIXTO")
                
                st.markdown("<div class='section-title'>2. Confirmaciones</div>", unsafe_allow_html=True)
                
                with st.container(border=True):
                    st.markdown("**Semanal (W)**")
                    w_sc = sum([st.checkbox("Rechazo AOI (+10%)", key="w1")*10, st.checkbox("Estructura (+10%)", key="w2")*10, st.checkbox("Patrón (+10%)", key="w3")*10, st.checkbox("EMA 50 (+5%)", key="w4")*5, st.checkbox("Psicológico (+5%)", key="w5")*5])
                
                with st.container(border=True):
                    st.markdown("**Diario (D)**")
                    d_sc = sum([st.checkbox("Rechazo AOI (+10%)", key="d1")*10, st.checkbox("Estructura (+10%)", key="d2")*10, st.checkbox("Vela (+10%)", key="d3")*10, st.checkbox("Patrón (+10%)", key="d4")*10, st.checkbox("EMA 50 (+5%)", key="d5")*5])
                
                with st.container(border=True):
                    st.markdown("**Ejecución (4H)**")
                    h4_sc = sum([st.checkbox("Vela (+10%)", key="h1")*10, st.checkbox("Patrón (+10%)", key="h2")*10, st.checkbox("AOI (+5%)", key="h3")*5, st.checkbox("Estructura (+5%)", key="h4")*5, st.checkbox("EMA 50 (+5%)", key="h5")*5])
                
                st.markdown("<div class='section-title'>3. Gatillo Final</div>", unsafe_allow_html=True)
                with st.container(border=True):
                    sos = st.checkbox("⚡ Shift of Structure")
                    eng = st.checkbox("🕯️ Vela Envolvente")
                    rr = st.checkbox("💰 Ratio > 1:2.5")
                    entry_score = sum([sos*10, eng*10])
                
                total = w_sc + d_sc + h4_sc + entry_score

            else: # Scalping
                st.markdown("<div class='section-title'>1. Alineación (4H-2H-1H)</div>", unsafe_allow_html=True)
                with st.container(border=True):
                    c1,c2,c3 = st.columns(3)
                    t4 = c1.selectbox("4H", ["Alcista", "Bajista"], key="st4")
                    t2 = c2.selectbox("2H", ["Alcista", "Bajista"], key="st2")
                    t1 = c3.selectbox("1H", ["Alcista", "Bajista"], key="st1")
                    
                    if t4==t2==t1: st.success("💎 TRIPLE SYNC")
                    elif t4==t2: st.info("✅ 4H-2H SYNC")
                    elif t2==t1: st.info("✅ 2H-1H SYNC")
                    else: st.warning("⚠️ MIXTO")
                
                st.markdown("<div class='section-title'>2. Confirmaciones</div>", unsafe_allow_html=True)
                with st.container(border=True):
                    st.markdown("**Contexto 4H**")
                    w_sc = sum([st.checkbox("AOI (+5%)", key="sc1")*5, st.checkbox("Estructura (+5%)", key="sc2")*5, st.checkbox("Patrón (+5%)", key="sc3")*5, st.checkbox("EMA 50 (+5%)", key="sc4")*5, st.checkbox("Psicológico (+5%)", key="sc5")*5])
                
                with st.container(border=True):
                    st.markdown("**Contexto 2H**")
                    d_sc = sum([st.checkbox("AOI (+5%)", key="sc6")*5, st.checkbox("Estructura (+5%)", key="sc7")*5, st.checkbox("Vela (+5%)", key="sc8")*5, st.checkbox("Patrón (+5%)", key="sc9")*5, st.checkbox("EMA 50 (+5%)", key="sc10")*5])
                
                with st.container(border=True):
                    st.markdown("**Ejecución (1H)**")
                    h4_sc = sum([st.checkbox("Vela (+5%)", key="sc11")*5, st.checkbox("Patrón (+5%)", key="sc12")*5, st.checkbox("Estructura (+5%)", key="sc13")*5, st.checkbox("EMA 50 (+5%)", key="sc14")*5])
                
                st.markdown("<div class='section-title'>3. Gatillo (M15/M30)</div>", unsafe_allow_html=True)
                with st.container(border=True):
                    sos = st.checkbox("⚡ SOS", key="se1")
                    eng = st.checkbox("🕯️ Entrada", key="se2")
                    rr = st.checkbox("💰 Ratio > 1:2.5", key="se3")
                    entry_score = sum([sos*10, eng*10])
                total = w_sc + d_sc + h4_sc + entry_score + 10

        # PANEL DE RESULTADOS
        with col_res:
            st.markdown("<div class='section-title'>🎯 Veredicto</div>", unsafe_allow_html=True)
            valid = sos and eng and rr
            
            # Gauge simulado con progress bar
            score_color = "red"
            if total >= 60: score_color = "orange"
            if total >= 80: score_color = "green"
            
            st.metric("Score Total", f"{min(total, 100)}/100")
            st.progress(min(total, 100))
            
            if valid and total >= 60:
                st.success("✅ EJECUTAR TRADE")
                sl = "5-7 pips" if "Swing" in modo else "3-5 pips"
                st.markdown(f"""
                <div style="background:rgba(0, 200, 83, 0.1); border:1px solid #00C853; padding:15px; border-radius:10px;">
                    <strong style="color:#00C853">PLAN DE ACCIÓN:</strong><br>
                    🛡️ Stop Loss: {sl}<br>
                    🎯 Take Profit: Liquidez Próxima
                </div>
                """, unsafe_allow_html=True)
            elif not valid:
                st.error("⛔ GATILLOS INCOMPLETOS")
                st.caption("Requieres SOS, Vela Envolvente y Ratio.")
            else:
                st.warning("💤 ESPERAR MEJOR SETUP")

    # === 2. REGISTRO ===
    with t_reg:
        col_form, col_last = st.columns([2, 1])
        with col_form:
            st.markdown("<div class='section-title'>📝 Registrar Nuevo Trade</div>", unsafe_allow_html=True)
            with st.form("reg"):
                c1,c2 = st.columns(2)
                dt = c1.date_input("Fecha", datetime.now())
                pr = c1.text_input("Par", "XAUUSD").upper()
                tp = c1.selectbox("Tipo", ["BUY", "SELL"])
                
                rs = c2.selectbox("Resultado", ["WIN", "LOSS", "BE"])
                mn = c2.number_input("Monto ($)", min_value=0.0, step=10.0, help="Pon el valor positivo, el sistema ajustará.")
                rt = c2.number_input("Ratio", value=2.5)
                nt = st.text_area("Notas / Emociones")
                
                if st.form_submit_button("Guardar Trade"):
                    final_mn = mn if rs == "WIN" else -mn if rs == "LOSS" else 0
                    save_trade(user, sel_acc, {"Fecha":dt,"Par":pr,"Tipo":tp,"Resultado":rs,"Dinero":final_mn,"Ratio":rt,"Notas":nt})
                    st.success("Guardado!"); st.rerun()

    # === 3. DASHBOARD ===
    with t_dash:
        df = load_trades(user, sel_acc)
        if not df.empty:
            st.markdown(f"<div class='section-title'>📊 Rendimiento: {sel_acc}</div>", unsafe_allow_html=True)
            
            # KPIs Cards
            k1,k2,k3,k4 = st.columns(4)
            wins = len(df[df["Resultado"]=="WIN"])
            neto = df['Dinero'].sum()
            
            k1.markdown(f"<div class='kpi-card'><div style='font-size:0.9em; opacity:0.7'>Beneficio Neto</div><div style='font-size:1.5em; font-weight:bold; color:{'#00C853' if neto>=0 else '#D50000'}'>${neto:,.2f}</div></div>", unsafe_allow_html=True)
            k2.markdown(f"<div class='kpi-card'><div style='font-size:0.9em; opacity:0.7'>Win Rate</div><div style='font-size:1.5em; font-weight:bold'>{(wins/len(df)*100):.1f}%</div></div>", unsafe_allow_html=True)
            k3.markdown(f"<div class='kpi-card'><div style='font-size:0.9em; opacity:0.7'>Total Trades</div><div style='font-size:1.5em; font-weight:bold'>{len(df)}</div></div>", unsafe_allow_html=True)
            k4.markdown(f"<div class='kpi-card'><div style='font-size:0.9em; opacity:0.7'>Saldo Final</div><div style='font-size:1.5em; font-weight:bold'>${act:,.2f}</div></div>", unsafe_allow_html=True)
            
            st.write("") # Espacio
            
            # Gráfico Equity
            df["Eq"] = ini + df["Dinero"].cumsum()
            fig = go.Figure(go.Scatter(x=df["Fecha"], y=df["Eq"], 
                                       line=dict(color='#00C853', width=3), 
                                       fill='tozeroy', fillcolor='rgba(0, 200, 83, 0.1)'))
            fig.update_layout(title="Curva de Crecimiento", 
                              paper_bgcolor='rgba(0,0,0,0)', 
                              plot_bgcolor='rgba(0,0,0,0)', 
                              font=dict(color='gray'),
                              xaxis=dict(showgrid=False),
                              yaxis=dict(gridcolor='rgba(128,128,128,0.1)'))
            st.plotly_chart(fig, use_container_width=True)
        else: st.info("No hay trades registrados en esta cuenta.")

    # === 4. CALENDARIO ===
    with t_cal:
        c_p, c_t, c_n = st.columns([1,5,1])
        with c_p: 
            if st.button("⬅️ Mes Anterior"): change_month(-1); st.rerun()
        with c_n: 
            if st.button("Mes Siguiente ➡️"): change_month(1); st.rerun()
            
        df = load_trades(user, sel_acc)
        html, y, m = render_cal_html(df)
        with c_t: 
            st.markdown(f"<h3 style='text-align:center; margin:0;'>{calendar.month_name[m]} {y}</h3>", unsafe_allow_html=True)
        
        st.markdown(html, unsafe_allow_html=True)

# --- EXEC ---
if 'user' not in st.session_state: st.session_state.user = None
if st.session_state.user: main_app()
else: login_screen()
