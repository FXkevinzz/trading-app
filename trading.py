import streamlit as st
import os
from datetime import datetime
import pytz
import google.generativeai as genai

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Set & Forget Ultimate", layout="wide", page_icon="🦁")

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .stApp {background-color: #0E1117; color: white;}
    [data-testid="stSidebar"] {background-color: #262730 !important;}
    div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] > div[data-testid="stVerticalBlock"] {
        background-color: #161B22; padding: 15px; border-radius: 8px; border: 1px solid #30363D;
    }
    h1, h2, h3, p, span, label {color: white !important;}
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div>div {
        background-color: #0E1117 !important; color: white !important; border: 1px solid #464b5c;
    }
    .open-session {background-color: #1f7a1f; color: white !important; padding: 10px; border-radius: 5px; text-align: center; font-weight: bold;}
    .closed-session {background-color: #5c0000; color: white !important; padding: 10px; border-radius: 5px; text-align: center; font-weight: bold;}
    .plan-box {border-left: 5px solid #4CAF50; padding: 15px; background-color: rgba(76, 175, 80, 0.1); border-radius: 5px; margin-top: 10px;}
    img { border-radius: 5px; margin-bottom: 10px; }
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
    ruta_local = f"fotos/{nombre_archivo}"
    if os.path.exists(ruta_local): st.image(ruta_local, caption=caption)
    elif nombre_archivo in links: st.image(links[nombre_archivo], caption=caption)
    else: st.warning(f"⚠️ Falta foto")

# --- BARRA LATERAL ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/7210/7210633.png", width=80)
    
    # SELECTOR DE MODO (NUEVO)
    modo = st.radio("Modo de Operativa", ["Swing / Day (W-D-4H)", "Scalping (4H-2H-1H)"])
    
    st.info("**Recuerda:** Sin *Shift of Structure* ni *Vela Envolvente*, NO HAY TRADE.")
    
    # CHATBOT GEMINI
    st.markdown("---")
    st.header("Coach IA 🧠")
    api_key = st.text_input("API Key (Opcional)", type="password")
    if api_key:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-pro')
            if "messages" not in st.session_state: st.session_state.messages = []
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]): st.markdown(msg["content"])
            if prompt := st.chat_input("Consulta..."):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"): st.markdown(prompt)
                # Contexto según modo
                contexto = "Scalping (4H/2H/1H)" if "Scalping" in modo else "Swing (W/D/4H)"
                resp = model.generate_content(f"Eres experto en Set&Forget ({contexto}). Reglas PDF: SL 5-7 pips, No BE, No Parciales. Usuario: {prompt}")
                st.session_state.messages.append({"role": "assistant", "content": resp.text})
                with st.chat_message("assistant"): st.markdown(resp.text)
        except: st.error("Error API Key")

    st.markdown("---")
    if st.button("🔄 Limpiar Todo"): 
        st.session_state.messages = []
        st.rerun()

# --- SESIONES ---
tz_ec = pytz.timezone('America/Guayaquil')
hora_ec = datetime.now(tz_ec).hour
if 15 <= hora_ec < 19:
    estado_mercado = "❌ MERCADO CERRADO (Hueco Tarde)"
    clase_css = "closed-session"
else:
    estado_mercado = "✅ MERCADO ACTIVO (Asia/Londres/NY)"
    clase_css = "open-session"

st.title(f"🦁 Set & Forget: {modo.split('(')[0]}")
st.markdown(f'<div class="{clase_css}">{estado_mercado}</div>', unsafe_allow_html=True)
st.markdown("---")

col_guia, col_checklist, col_resultados = st.columns([1, 2, 1.2], gap="medium")

# 🔴 GUÍA
with col_guia:
    st.header("📖 Chuleta")
    with st.expander("🐂 Alcistas", expanded=True):
        st.markdown("### Bullish Engulfing"); mostrar_imagen("bullish_engulfing.png", "Verde envuelve roja")
        st.markdown("### Morning Star"); mostrar_imagen("morning_star.png", "Giro 3 velas")
        st.markdown("### Hammer"); mostrar_imagen("hammer.png", "Rechazo abajo")
    with st.expander("🐻 Bajistas"):
        st.markdown("### Bearish Engulfing"); mostrar_imagen("bearish_engulfing.png", "Roja envuelve verde")
        st.markdown("### Shooting Star"); mostrar_imagen("shooting_star.png", "Rechazo arriba")

# 🟠 CHECKLIST (DINÁMICO SEGÚN MODO)
with col_checklist:
    
    # --- LÓGICA SWING / DAY (Original) ---
    if "Swing" in modo:
        with st.container():
            st.subheader("🔗 Tendencias (W / D / 4H)")
            c1, c2, c3 = st.columns(3)
            with c1: tw = st.selectbox("Weekly", ["Alcista", "Bajista"], key="tw")
            with c2: td = st.selectbox("Daily", ["Alcista", "Bajista"], key="td")
            with c3: t4 = st.selectbox("4 Hour", ["Alcista", "Bajista"], key="t4")
            if tw == td == t4: st.success("💎 TRIPLE SYNC")
            elif tw == td: st.info("✅ SWING SYNC")
            elif td == t4: st.info("✅ DAY SYNC")
            else: st.warning("⚠️ MIXTO")
        
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("1. Weekly")
            w_score = sum([
                st.checkbox("At/Rejected AOI (+10%)", key="w1")*10,
                st.checkbox("Rej. Previous Structure (+10%)", key="w2")*10,
                st.checkbox("Patterns (+10%)", key="w3")*10,
                st.checkbox("Rejecting 50 EMA (+5%)", key="w4")*5,
                st.checkbox("Round Psych Level (+5%)", key="w5")*5
            ])
        with c2:
            st.subheader("2. Daily")
            d_score = sum([
                st.checkbox("At/Rejected AOI (+10%)", key="d1")*10,
                st.checkbox("Rej. Previous Structure (+10%)", key="d2")*10,
                st.checkbox("Candlestick Rejection (+10%)", key="d3")*10,
                st.checkbox("Patterns (+10%)", key="d4")*10,
                st.checkbox("Rejecting 50 EMA (+5%)", key="d5")*5
            ])
        st.divider()
        c3, c4 = st.columns(2)
        with c3:
            st.subheader("3. Execution (4H)")
            h4_score = sum([
                st.checkbox("Candlestick Rejection (+10%)", key="h1")*10,
                st.checkbox("Patterns (+10%)", key="h2")*10,
                st.checkbox("At/Rejected AOI (+5%)", key="h3")*5,
                st.checkbox("Rej. Previous Structure (+5%)", key="h4")*5,
                st.checkbox("Rejecting 50 EMA (+5%)", key="h5")*5
            ])
        with c4:
            st.subheader("4. ENTRY SIGNAL")
            st.caption("Must Have")
            entry_sos = st.checkbox("⚡ Shift of Structure", key="e1")
            entry_eng = st.checkbox("🕯️ Engulfing Candlestick", key="e2")
            entry_rr = st.checkbox("💰 1:2.5 RR Minimum", key="e3")
            entry_score = sum([entry_sos*10, entry_eng*10])
            
        total = w_score + d_score + h4_score + entry_score

    # --- LÓGICA SCALPING (Nuevo PDF Pag 33) ---
    else:
        with st.container():
            st.subheader("🔗 Tendencias (4H / 2H / 1H)")
            c1, c2, c3 = st.columns(3)
            with c1: t4 = st.selectbox("4 Hour", ["Alcista", "Bajista"], key="st4")
            with c2: t2 = st.selectbox("2 Hour", ["Alcista", "Bajista"], key="st2")
            with c3: t1 = st.selectbox("1 Hour", ["Alcista", "Bajista"], key="st1")
            if t4 == t2 == t1: st.success("💎 TRIPLE SYNC")
            elif t4 == t2: st.info("✅ 4H-2H SYNC")
            elif t2 == t1: st.info("✅ 2H-1H SYNC")
            else: st.warning("⚠️ MIXTO")

        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("1. 4H Context")
            # Pesos reducidos al 5% para Scalp [cite: 582-592]
            w_score = sum([
                st.checkbox("At/Rejected 4H AOI (+5%)", key="sc1")*5,
                st.checkbox("Rej. Prev Structure (+5%)", key="sc2")*5,
                st.checkbox("Patterns (+5%)", key="sc3")*5,
                st.checkbox("Rejecting 50 EMA (+5%)", key="sc4")*5,
                st.checkbox("Round Psych Level (+5%)", key="sc5")*5
            ])
        with c2:
            st.subheader("2. 2H Context")
            d_score = sum([
                st.checkbox("At/Rejected 2H AOI (+5%)", key="sc6")*5,
                st.checkbox("Rej. Prev Structure (+5%)", key="sc7")*5,
                st.checkbox("Candlestick Rej 2H (+5%)", key="sc8")*5,
                st.checkbox("Patterns 2H (+5%)", key="sc9")*5,
                st.checkbox("Rejecting 2H EMA (+5%)", key="sc10")*5
            ])
        st.divider()
        c3, c4 = st.columns(2)
        with c3:
            st.subheader("3. Execution (1H)")
            # Reglas 1HR Checklist [cite: 594-597]
            h4_score = sum([
                st.checkbox("Candlestick Rej 1H (+5%)", key="sc11")*5,
                st.checkbox("Patterns 1H (+5%)", key="sc12")*5,
                st.checkbox("Rej. Prev Structure (+5%)", key="sc13")*5,
                st.checkbox("Rejecting 1H EMA (+5%)", key="sc14")*5
            ])
        with c4:
            st.subheader("4. ENTRY (15m/30m)")
            st.caption("Must Have")
            # Entry Checklist [cite: 612-614]
            entry_sos = st.checkbox("⚡ Shift of Structure (15m)", key="se1")
            entry_eng = st.checkbox("🕯️ Engulfing (15m/30m)", key="se2")
            entry_rr = st.checkbox("💰 1:2.5 RR Minimum", key="se3")
            entry_score = sum([entry_sos*10, entry_eng*10])
            
        # Ajuste de total para que 100% sea posible con los nuevos pesos
        # Total Scalp items = 25 (Context) + 25 (Context) + 20 (Exec) + 20 (Entry) = ~90% max raw
        # Sumamos un bono base de 10% por ser Scalp para ajustar la escala visual
        total = w_score + d_score + h4_score + entry_score + 10

# 🔵 RESULTADOS
with col_resultados:
    is_valid = entry_sos and entry_eng and entry_rr
    
    def get_advice():
        if not entry_sos: return "⛔ STOP: Falta Estructura"
        if not entry_eng: return "⚠️ CUIDADO: Falta Vela"
        if not entry_rr: return "💸 RIESGO: Mal Ratio"
        if total >= 90: return "💎 SNIPER: Ejecuta"
        return "💤 ESPERA"
    
    msg = get_advice()
    st.header("🤖 IA")
    if "STOP" in msg: st.error(msg)
    elif "CUIDADO" in msg: st.warning(msg)
    elif "SNIPER" in msg: st.success(msg)
    else: st.info(msg)
    
    st.divider()
    st.metric("Probabilidad", f"{min(total, 100)}%")
    st.progress(min(total, 100))
    
    if is_valid and total >= 60:
        st.success("### ✅ EJECUTAR")
        st.balloons()
        
        # Plan específico según modo
        if "Scalp" in modo:
            plan = """
            <b>Plan Scalping:</b><br>
            • Entrada: Cierre M15/M30<br>
            • SL: 3-5 pips del AOI<br>
            • TP: Estructura 1H/2H<br>
            • Gestión: Rápida pero sin BE
            """
        else:
            plan = """
            <b>Plan Swing:</b><br>
            • Entrada: Cierre 4H<br>
            • SL: 5-7 pips del AOI<br>
            • TP: Estructura Daily<br>
            • Gestión: Set & Forget
            """
            
        st.markdown(f'<div class="plan-box">{plan}</div>', unsafe_allow_html=True)
    else:
        st.error("### ❌ NO OPERAR")

