import streamlit as st
import pandas as pd
import os
from datetime import datetime
import pytz
import google.generativeai as genai

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Set & Forget Ultimate Pro", layout="wide", page_icon="🦁")

# --- GESTIÓN DE DATOS (PERSISTENCIA) ---
FILE_NAME = "journal.csv"

def cargar_datos():
    if not os.path.exists(FILE_NAME):
        return pd.DataFrame(columns=["Fecha", "Par", "Tipo", "Resultado", "Ratio", "Notas"])
    return pd.read_csv(FILE_NAME)

def guardar_trade(fecha, par, tipo, resultado, ratio, notas):
    df = cargar_datos()
    nuevo_registro = pd.DataFrame({
        "Fecha": [fecha],
        "Par": [par],
        "Tipo": [tipo],
        "Resultado": [resultado],
        "Ratio": [ratio],
        "Notas": [notas]
    })
    df = pd.concat([df, nuevo_registro], ignore_index=True)
    df.to_csv(FILE_NAME, index=False)

# --- ESTILOS CSS (BLOOMBERG DARK) ---
st.markdown("""
    <style>
    /* Estilos Generales */
    .stApp {background-color: #0E1117; color: white;}
    [data-testid="stSidebar"] {background-color: #000000 !important; border-right: 1px solid #333;}
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #161B22; border-radius: 4px 4px 0px 0px; gap: 1px; padding-top: 10px; padding-bottom: 10px; }
    .stTabs [aria-selected="true"] { background-color: #238636 !important; color: white !important; }

    /* Inputs Dark Mode */
    .stTextInput>div>div>input, .stSelectbox>div>div>div, .stNumberInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: #0E1117 !important; 
        color: #00ff00 !important; /* Texto verde terminal */
        border: 1px solid #333;
    }

    /* Métricas Dashboard */
    div[data-testid="metric-container"] {
        background-color: #161B22;
        padding: 15px;
        border-radius: 5px;
        border: 1px solid #333;
    }
    
    /* Alertas */
    .open-session {background-color: #1f7a1f; color: white !important; padding: 10px; border-radius: 5px; text-align: center; font-weight: bold;}
    .closed-session {background-color: #5c0000; color: white !important; padding: 10px; border-radius: 5px; text-align: center; font-weight: bold;}
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIÓN IMAGEN ---
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

# --- BARRA LATERAL (GLOBAL) ---
with st.sidebar:
    st.title("🦁 TRADING PRO")
    
    # 1. ESTADO DEL MERCADO
    tz_ec = pytz.timezone('America/Guayaquil')
    hora_ec = datetime.now(tz_ec).hour
    if 15 <= hora_ec < 19:
        st.markdown('<div class="closed-session">❌ MERCADO CERRADO</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="open-session">✅ MERCADO ACTIVO</div>', unsafe_allow_html=True)
    
    st.divider()

    # 2. IA COACH
    st.subheader("🧠 AI Coach")
    api_key = st.text_input("Gemini API Key", type="password")
    if api_key:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        if "messages" not in st.session_state: st.session_state.messages = []
        
        if prompt := st.chat_input("Pregunta al Coach..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            try:
                resp = model.generate_content(f"Eres un mentor de trading institucional estricto. Responde breve y directo: {prompt}")
                st.session_state.messages.append({"role": "assistant", "content": resp.text})
            except:
                st.error("Error API")

        with st.expander("Ver Chat Reciente"):
            for msg in st.session_state.messages[-4:]: # Mostrar solo últimos 4
                st.caption(f"{msg['role']}: {msg['content']}")

# --- ESTRUCTURA DE PESTAÑAS ---
tab1, tab2, tab3 = st.tabs(["🦁 OPERATIVA (Checklist)", "📝 REGISTRAR TRADE", "📊 DASHBOARD & HISTORIAL"])

# ==========================================
# TAB 1: OPERATIVA (TU CÓDIGO ORIGINAL)
# ==========================================
with tab1:
    col_config, col_main = st.columns([1, 4])
    
    with col_config:
        st.info("Configuración")
        modo = st.radio("Modo", ["Swing (W-D-4H)", "Scalping (4H-2H-1H)"])
        
    with col_main:
        col_guia, col_checklist, col_res = st.columns([1, 2, 1.2])

        # GUÍA VISUAL
        with col_guia:
            with st.expander("📖 Patrones", expanded=False):
                st.caption("Alcistas")
                mostrar_imagen("bullish_engulfing.png", "B. Engulfing")
                st.caption("Bajistas")
                mostrar_imagen("bearish_engulfing.png", "B. Engulfing")

        # CHECKLIST LÓGICA
        with col_checklist:
            if "Swing" in modo:
                st.subheader("🔗 Tendencias (W / D / 4H)")
                c1, c2, c3 = st.columns(3)
                tw = c1.selectbox("Weekly", ["Alcista", "Bajista"], key="tw")
                td = c2.selectbox("Daily", ["Alcista", "Bajista"], key="td")
                t4 = c3.selectbox("4H", ["Alcista", "Bajista"], key="t4")
                
                st.markdown("---")
                st.caption("Checklist Rápido")
                
                # Simplificado para UX
                ch1 = st.checkbox("Rechazo AOI (Daily/Weekly)")
                ch2 = st.checkbox("Estructura a favor")
                ch3 = st.checkbox("Patrón de Vela (4H)")
                ch4 = st.checkbox("Gatillo: Shift of Structure")
                ch5 = st.checkbox("Gatillo: Ratio min 1:2.5")
                
                total_score = sum([ch1, ch2, ch3, ch4, ch5]) * 20
            
            else: # Scalping
                st.subheader("🔗 Tendencias (4H / 2H / 1H)")
                c1, c2, c3 = st.columns(3)
                t4 = c1.selectbox("4H", ["Alcista", "Bajista"], key="st4")
                t2 = c2.selectbox("2H", ["Alcista", "Bajista"], key="st2")
                t1 = c3.selectbox("1H", ["Alcista", "Bajista"], key="st1")
                
                st.markdown("---")
                st.caption("Checklist Scalping")
                ch1 = st.checkbox("Rechazo AOI (4H/2H)")
                ch2 = st.checkbox("Patrón Vela (1H)")
                ch3 = st.checkbox("Ruptura M15/M30")
                ch4 = st.checkbox("Ratio 1:2.5")
                
                total_score = sum([ch1, ch2, ch3, ch4]) * 25

        # RESULTADOS EN VIVO
        with col_res:
            st.metric("Probabilidad del Setup", f"{total_score}%")
            st.progress(total_score)
            
            if total_score >= 80:
                st.success("💎 EJECUTAR TRADE")
                st.markdown("""
                    <div style="background:#1f7a1f; padding:10px; border-radius:5px;">
                    <b>PLAN:</b><br>SL: Estructural + Spread<br>TP: Siguiente Liquidez
                    </div>
                """, unsafe_allow_html=True)
            elif total_score >= 60:
                st.warning("⚠️ CUIDADO: Faltan confirmaciones")
            else:
                st.error("💤 NO OPERAR")

# ==========================================
# TAB 2: REGISTRO DE TRADES (BITÁCORA)
# ==========================================
with tab2:
    st.header("📝 Registrar Nueva Operación")
    
    with st.form("trade_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            fecha_reg = st.date_input("Fecha", datetime.now())
            par_reg = st.text_input("Par (ej: XAUUSD)", "EURUSD").upper()
        with c2:
            tipo_reg = st.selectbox("Tipo", ["COMPRA", "VENTA"])
            res_reg = st.selectbox("Resultado", ["WIN ✅", "LOSS ❌", "BE 🛡️"])
        with c3:
            ratio_reg = st.number_input("Ratio RR (Ej: 2.5)", min_value=0.0, step=0.1)
            notas_reg = st.text_area("Notas / Emociones", placeholder="Me sentí ansioso, entré tarde...")
            
        submitted = st.form_submit_button("💾 GUARDAR TRADE EN BITÁCORA")
        
        if submitted:
            guardar_trade(fecha_reg, par_reg, tipo_reg, res_reg, ratio_reg, notas_reg)
            st.success("Trade registrado correctamente.")

# ==========================================
# TAB 3: DASHBOARD & HISTORIAL
# ==========================================
with tab3:
    st.header("📊 Tu Rendimiento")
    
    df = cargar_datos()
    
    if not df.empty:
        # CÁLCULO DE MÉTRICAS
        total_trades = len(df)
        wins = len(df[df["Resultado"].str.contains("WIN")])
        losses = len(df[df["Resultado"].str.contains("LOSS")])
        win_rate = round((wins / total_trades) * 100, 1) if total_trades > 0 else 0
        
        # MUESTRA DE MÉTRICAS
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Trades", total_trades)
        m2.metric("Win Rate", f"{win_rate}%", delta_color="normal")
        m3.metric("Ganadas", wins)
        m4.metric("Perdidas", losses, delta_color="inverse")
        
        st.markdown("---")
        
        # HISTORIAL (Estilo Calendario/Lista)
        st.subheader("📜 Historial Reciente")
        
        # Colorear la tabla según Win/Loss
        def color_result(val):
            color = '#1f7a1f' if 'WIN' in val else '#5c0000' if 'LOSS' in val else '#333'
            return f'background-color: {color}'

        st.dataframe(
            df.sort_values(by="Fecha", ascending=False).style.map(color_result, subset=['Resultado']),
            use_container_width=True,
            height=400
        )
        
        # Botón para descargar CSV
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Descargar Backup (CSV)", csv, "journal_backup.csv", "text/csv")
        
    else:
        st.info("Aún no hay trades registrados. Ve a la pestaña 'Registrar Trade' para comenzar.")
