import streamlit as st
import os
from datetime import datetime
import pytz

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Set & Forget Pro", layout="wide", page_icon="🦁")

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .stApp {background-color: #0E1117;}
    div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] > div[data-testid="stVerticalBlock"] {
        background-color: #161B22; padding: 15px; border-radius: 8px; border: 1px solid #30363D;
    }
    h3 { border-bottom: 2px solid #30363D; padding-bottom: 10px; }
    div[data-testid="stMetric"] { background-color: #0D1117; border: 1px solid #30363D; border-radius: 8px; padding: 10px; }
    img { border-radius: 5px; margin-bottom: 10px; }
    .open-session { background-color: #1f7a1f; color: white; padding: 10px; border-radius: 5px; text-align: center; font-weight: bold; font-size: 18px;}
    .closed-session { background-color: #990000; color: white; padding: 10px; border-radius: 5px; text-align: center; font-weight: bold; font-size: 18px;}
    
    /* Estilo para el Plan de Acción */
    .plan-box { background-color: #0d1117; border-left: 5px solid #28a745; padding: 15px; border-radius: 5px; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIÓN IMAGEN ---
def mostrar_imagen(nombre_archivo, caption):
    ruta = f"fotos/{nombre_archivo}"
    if os.path.exists(ruta):
        st.image(ruta, caption=caption)
    else:
        st.warning(f"⚠️ Falta foto: {nombre_archivo}")

# --- BARRA LATERAL: NOTAS + RECUERDA ---
with st.sidebar:
    # 1. EL MENSAJE "RECUERDA" (Agregado)
    st.info("""
    **Recuerda:** Si no hay *Shift of Structure* ni *Vela Envolvente*, el trade no es válido aunque tengas 100%.
    """)
    
    st.markdown("---")
    
    st.header("📝 Notas de Análisis")
    par = st.text_input("Par (ej: GBPJPY)")
    notas = st.text_area("Plan (ej: Esperar pullback...)", height=150)
    
    st.markdown("---")
    if st.button("🔄 Limpiar Todo"): st.rerun()

# --- LOGICA DE SESIONES ---
tz_ec = pytz.timezone('America/Guayaquil')
hora_ec = datetime.now(tz_ec).hour

# Regla: Cierre operativo 15:00 (3 PM). Apertura Tokio 19:00 (7 PM).
if 15 <= hora_ec < 19:
    estado_mercado = "❌ MERCADO CERRADO (Hueco de Tarde)"
    clase_css = "closed-session"
else:
    estado_mercado = "✅ MERCADO ACTIVO (Londres / NY / Tokio)"
    clase_css = "open-session"

# --- INTERFAZ SUPERIOR ---
st.title("🦁 Set & Forget: Pro Edition")
st.markdown(f'<div class="{clase_css}">{estado_mercado}</div>', unsafe_allow_html=True)
st.markdown("---")

# --- LAYOUT PRINCIPAL ---
col_guia, col_checklist, col_resultados = st.columns([1, 2, 1.2], gap="medium")

# 🔴 COLUMNA IZQUIERDA: GUÍA
with col_guia:
    st.header("📖 Chuleta")
    with st.expander("🐂 Alcistas", expanded=True):
        st.markdown("### Bullish Engulfing"); mostrar_imagen("bullish_engulfing.png", "Verde envuelve roja")
        st.markdown("### Morning Star"); mostrar_imagen("morning_star.png", "Giro 3 velas")
        st.markdown("### Hammer"); mostrar_imagen("hammer.png", "Rechazo abajo")
    with st.expander("🐻 Bajistas"):
        st.markdown("### Bearish Engulfing"); mostrar_imagen("bearish_engulfing.png", "Roja envuelve verde")
        st.markdown("### Shooting Star"); mostrar_imagen("shooting_star.png", "Rechazo arriba")

# 🟠 COLUMNA CENTRAL: TRABAJO
with col_checklist:
    with st.container():
        st.subheader("🔗 Tendencias")
        ct1, ct2, ct3 = st.columns(3)
        with ct1: t_w = st.selectbox("Semanal", ["Alcista", "Bajista"], key="tw")
        with ct2: t_d = st.selectbox("Diario", ["Alcista", "Bajista"], key="td")
        with ct3: t_4h = st.selectbox("4 Horas", ["Alcista", "Bajista"], key="t4h")
        
        if t_w == t_d == t_4h: st.success("💎 TRIPLE SYNC")
        elif t_w == t_d: st.info("✅ SWING SYNC (W+D)")
        elif t_d == t_4h: st.info("✅ DAY SYNC (D+4H)")
        else: st.warning("⚠️ MIXTO")

    st.divider()
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("1. Weekly")
        w_score = sum([
            st.checkbox("En/Rechazo W AOI (+10%)", key="w1")*10,
            st.checkbox("Rechazo Estruc. Previa (+10%)", key="w2")*10,
            st.checkbox("Patrón W (+10%)", key="w3")*10,
            st.checkbox("Rechazo W EMA 50 (+5%)", key="w4")*5,
            st.checkbox("Nivel Psicológico (+5%)", key="w5")*5
        ])
    with c2:
        st.subheader("2. Daily")
        d_score = sum([
            st.checkbox("En/Rechazo D AOI (+10%)", key="d1")*10,
            st.checkbox("Rechazo Estruc. Previa (+10%)", key="d2")*10,
            st.checkbox("Rechazo Vela D (+10%)", key="d3")*10,
            st.checkbox("Patrón D (+10%)", key="d4")*10,
            st.checkbox("Rechazo D EMA 50 (+5%)", key="d5")*5
        ])
    
    st.divider()
    c3, c4 = st.columns(2)
    with c3:
        st.subheader("3. Ejecución (4H)")
        h4_score = sum([
            st.checkbox("Rechazo Vela 4H (+10%)", key="h1")*10,
            st.checkbox("Patrón 4H (+10%)", key="h2")*10,
            st.checkbox("En/Rechazo 4H AOI (+5%)", key="h3")*5,
            st.checkbox("Rechazo Estruc. 4H (+5%)", key="h4")*5,
            st.checkbox("Rechazo 4H EMA 50 (+5%)", key="h5")*5
        ])
    with c4:
        st.subheader("4. GATILLO")
        st.caption("Obligatorio")
        entry_sos = st.checkbox("⚡ Shift of Structure (+10%)", key="e1")
        entry_eng = st.checkbox("🕯️ Vela Envolvente (+10%)", key="e2")
        entry_rr = st.checkbox("💰 RR Mínimo 1:2.5 (Manual)", key="e3")
        entry_score = sum([entry_sos*10, entry_eng*10])

# 🔵 COLUMNA DERECHA: RESULTADOS
with col_resultados:
    total_score = w_score + d_score + h4_score + entry_score
    is_valid = entry_sos and entry_eng and entry_rr

    # Determinar Grado (A, B, C)
    grade_text = "F"
    if total_score >= 90: grade_text = "A+ (Excellent)"
    elif total_score >= 80: grade_text = "B (Good)"
    elif total_score >= 70: grade_text = "C (Moderate)"

    # Consejero IA Simplificado
    def get_advice():
        if not entry_sos: return "⛔ STOP: Falta Cambio de Estructura."
        if not entry_eng: return "⚠️ CUIDADO: Falta Vela Envolvente."
        if not entry_rr: return "💸 RIESGO: Ratio < 1:2.5 no vale la pena."
        if total_score >= 90: return "💎 SNIPER: Configura tu orden."
        return "💤 ESPERA: Mercado no claro."

    msg = get_advice()
    st.header("🤖 Consejero")
    if "STOP" in msg: st.error(msg)
    elif "CUIDADO" in msg: st.warning(msg)
    elif "SNIPER" in msg: st.success(msg)
    else: st.info(msg)
    
    st.divider()
    
    st.header("🏆 Veredicto")
    st.metric("Probabilidad", f"{total_score}%")
    st.progress(min(total_score, 100))
    
    if is_valid and total_score >= 60:
        # 2. EL PLAN DE ACCIÓN (Agregado)
        st.success(f"### ✅ EJECUTAR TRADE - {grade_text}")
        st.balloons()
        
        st.markdown("""
        **Plan de Acción:**
        * **Entrada:** Al cierre de la vela envolvente.
        * **Stop Loss:** 5-7 pips por debajo/arriba del AOI.
        * **Take Profit:** Siguiente estructura limpia (Min 1:2.5).
        * **Gestión:** Set & Forget (No mover a Breakeven).
        """)
    else:
        st.error("### ❌ NO OPERAR")
        st.caption("Faltan reglas obligatorias.")