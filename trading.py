import streamlit as st
import os
from datetime import datetime
import pytz
import google.generativeai as genai

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Set & Forget Clean", layout="wide", page_icon="🦁")

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    /* Estilos Generales */
    .stApp {background-color: #0E1117; color: white;}
    [data-testid="stSidebar"] {background-color: #262730 !important;}
    
    /* Contenedores */
    div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] > div[data-testid="stVerticalBlock"] {
        background-color: #161B22; 
        padding: 15px; 
        border-radius: 8px; 
        border: 1px solid #30363D;
    }
    
    /* Textos e Inputs */
    h1, h2, h3, p, span, label {color: white !important;}
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div>div {
        background-color: #0E1117 !important; 
        color: white !important; 
        border: 1px solid #464b5c;
    }
    
    /* Alertas */
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
    
    # SELECTOR DE MODO
    modo = st.radio("Modo de Operativa", ["Swing (W-D-4H)", "Scalping (4H-2H-1H)"])
    
    st.info("**Recuerda:** Sin *Shift of Structure* ni *Vela Envolvente*, NO HAY TRADE.")
    
    # CHATBOT GEMINI (CON MODELO FLASH)
    st.markdown("---")
    st.header("Coach IA 🧠")
    
    api_key = None
    if "GEMINI_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_KEY"]
    else:
        api_key = st.text_input("API Key", type="password")
    
    if api_key:
        try:
            genai.configure(api_key=api_key)
            # --- AQUÍ ESTÁ LA SOLUCIÓN: USAMOS FLASH ---
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            if "messages" not in st.session_state: st.session_state.messages = []
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]): st.markdown(msg["content"])
            
            if prompt := st.chat_input("Consulta..."):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"): st.markdown(prompt)
                
                contexto = "Scalping (4H/2H/1H)" if "Scalping" in modo else "Swing (W/D/4H)"
                prompt_sistema = f"""
                Eres experto en Set&Forget ({contexto}). 
                Reglas: SL 5-7 pips fuera de AOI, No BE, No Parciales. Ratio min 1:2.5.
                Usuario: {prompt}
                """
                
                resp = model.generate_content(prompt_sistema)
                st.session_state.messages.append({"role": "assistant", "content": resp.text})
                with st.chat_message("assistant"): st.markdown(resp.text)
        except Exception as e:
            st.error(f"Error de API: {e}")

    st.markdown("---")
    st.header("📝 Notas")
    par = st.text_input("Par (ej: XAUUSD)")
    notas = st.text_area("Plan", height=150, placeholder="Ej: Esperar retest...")
    
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

# 🟠 CHECKLIST
with col_checklist:
    if "Swing" in modo:
        with st.container():
            st.subheader("🔗 Tendencias (W / D / 4H)")
            c1, c2, c3 = st.columns(3)
            with c1: tw = st.selectbox("Semanal", ["Alcista", "Bajista"], key="tw")
            with c2: td = st.selectbox("Diario", ["Alcista", "Bajista"], key="td")
            with c3: t4 = st.selectbox("4 Horas", ["Alcista", "Bajista"], key="t4")
            if tw == td == t4: st.success("💎 TRIPLE SYNC")
            elif tw == td: st.info("✅ SWING SYNC")
            elif td == t4: st.info("✅ DAY SYNC")
            else: st.warning("⚠️ MIXTO")
        
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("1. Semanal (W)")
            w_score = sum([
                st.checkbox("En/Rechazo AOI (+10%)", key="w1")*10,
                st.checkbox("Rechazo Estruc. Previa (+10%)", key="w2")*10,
                st.checkbox("Patrones (+10%)", key="w3")*10,
                st.checkbox("Rechazo EMA 50 (+5%)", key="w4")*5,
                st.checkbox("Nivel Psicológico (+5%)", key="w5")*5
            ])
        with c2:
            st.subheader("2. Diario (D)")
            d_score = sum([
                st.checkbox("En/Rechazo AOI (+10%)", key="d1")*10,
                st.checkbox("Rechazo Estruc. Previa (+10%)", key="d2")*10,
                st.checkbox("Rechazo Vela (+10%)", key="d3")*10,
                st.checkbox("Patrones (+10%)", key="d4")*10,
                st.checkbox("Rechazo EMA 50 (+5%)", key="d5")*5
            ])
        st.divider()
        c3, c4 = st.columns(2)
        with c3:
            st.subheader("3. Ejecución (4H)")
            h4_score = sum([
                st.checkbox("Rechazo Vela (+10%)", key="h1")*10,
                st.checkbox("Patrones (+10%)", key="h2")*10,
                st.checkbox("En/Rechazo AOI (+5%)", key="h3")*5,
                st.checkbox("Rechazo Estructura (+5%)", key="h4")*5,
                st.checkbox("Rechazo EMA 50 (+5%)", key="h5")*5
            ])
        with c4:
            st.subheader("4. GATILLO")
            st.caption("Obligatorio")
            entry_sos = st.checkbox("⚡ Shift of Structure", key="e1")
            entry_eng = st.checkbox("🕯️ Vela Envolvente", key="e2")
            entry_rr = st.checkbox("💰 Ratio 1:2.5", key="e3")
            entry_score = sum([entry_sos*10, entry_eng*10])
            
        total = w_score + d_score + h4_score + entry_score

    else:
        # MODO SCALPING
        with st.container():
            st.subheader("🔗 Tendencias (4H / 2H / 1H)")
            c1, c2, c3 = st.columns(3)
            with c1: t4 = st.selectbox("4 Horas", ["Alcista", "Bajista"], key="st4")
            with c2: t2 = st.selectbox("2 Horas", ["Alcista", "Bajista"], key="st2")
            with c3: t1 = st.selectbox("1 Hora", ["Alcista", "Bajista"], key="st1")
            if t4 == t2 == t1: st.success("💎 TRIPLE SYNC")
            elif t4 == t2: st.info("✅ 4H-2H SYNC")
            elif t2 == t1: st.info("✅ 2H-1H SYNC")
            else: st.warning("⚠️ MIXTO")

        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("1. Contexto 4H")
            w_score = sum([
                st.checkbox("En/Rechazo AOI (+5%)", key="sc1")*5,
                st.checkbox("Rechazo Estruc. Previa (+5%)", key="sc2")*5,
                st.checkbox("Patrones (+5%)", key="sc3")*5,
                st.checkbox("Rechazo EMA 50 (+5%)", key="sc4")*5,
                st.checkbox("Nivel Psicológico (+5%)", key="sc5")*5
            ])
        with c2:
            st.subheader("2. Contexto 2H")
            d_score = sum([
                st.checkbox("En/Rechazo AOI (+5%)", key="sc6")*5,
                st.checkbox("Rechazo Estruc. Previa (+5%)", key="sc7")*5,
                st.checkbox("Rechazo Vela (+5%)", key="sc8")*5,
                st.checkbox("Patrones (+5%)", key="sc9")*5,
                st.checkbox("Rechazo EMA 50 (+5%)", key="sc10")*5
            ])
        st.divider()
        c3, c4 = st.columns(2)
        with c3:
            st.subheader("3. Ejecución (1H)")
            h4_score = sum([
                st.checkbox("Rechazo Vela (+5%)", key="sc11")*5,
                st.checkbox("Patrones (+5%)", key="sc12")*5,
                st.checkbox("Rechazo Estruc. Previa (+5%)", key="sc13")*5,
                st.checkbox("Rechazo EMA 50 (+5%)", key="sc14")*5
            ])
        with c4:
            st.subheader("4. GATILLO (15m/30m)")
            st.caption("Obligatorio")
            entry_sos = st.checkbox("⚡ Shift of Structure", key="se1")
            entry_eng = st.checkbox("🕯️ Vela Envolvente", key="se2")
            entry_rr = st.checkbox("💰 Ratio 1:2.5", key="se3")
            entry_score = sum([entry_sos*10, entry_eng*10])
            
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
        
        if "Scalp" in modo:
            plan = "<b>Plan Scalping:</b><br>• Entrada: Cierre M15/M30<br>• SL: 3-5 pips<br>• TP: Estructura 1H/2H"
        else:
            plan = "<b>Plan Swing:</b><br>• Entrada: Cierre 4H<br>• SL: 5-7 pips<br>• TP: Estructura Daily"
            
        st.markdown(f'<div class="plan-box">{plan}</div>', unsafe_allow_html=True)
    else:
        st.error("### ❌ NO OPERAR")

