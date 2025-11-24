import streamlit as st
import os
from datetime import datetime
import pytz

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Set & Forget Adaptive", layout="wide", page_icon="🦁")

# --- ESTILOS CSS INTELIGENTES (ADAPTATIVOS) ---
st.markdown("""
    <style>
    /* 1. CONTENEDORES (Cajas de Checklist) */
    /* Usamos 'secondary-background-color' que cambia solo según el tema */
    div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] > div[data-testid="stVerticalBlock"] {
        background-color: var(--secondary-background-color);
        padding: 15px;
        border-radius: 10px;
        border: 1px solid rgba(128, 128, 128, 0.2); /* Borde sutil adaptable */
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    /* 2. MÉTRICAS (Cuadros de números) */
    div[data-testid="stMetric"] { 
        background-color: var(--background-color); /* Fondo base */
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 8px; 
        padding: 10px; 
    }

    /* 3. IMÁGENES */
    img { border-radius: 8px; margin-bottom: 10px; transition: transform 0.2s; }
    img:hover { transform: scale(1.02); }

    /* 4. ALERTAS DE ESTADO (Colores fijos para asegurar lectura) */
    .open-session { 
        background-color: #dcfce7; /* Verde muy claro */
        color: #14532d; /* Texto verde oscuro */
        padding: 10px; 
        border-radius: 8px; 
        text-align: center; 
        font-weight: bold; 
        font-size: 18px;
        border: 1px solid #22c55e;
    }
    .closed-session { 
        background-color: #fee2e2; /* Rojo muy claro */
        color: #7f1d1d; /* Texto rojo oscuro */
        padding: 10px; 
        border-radius: 8px; 
        text-align: center; 
        font-weight: bold; 
        font-size: 18px;
        border: 1px solid #ef4444;
    }
    
    /* 5. PLAN DE ACCIÓN (Caja de éxito) */
    .plan-box { 
        border-left: 5px solid #4CAF50; 
        padding: 15px; 
        background-color: var(--secondary-background-color);
        border-radius: 5px; 
        margin-top: 10px;
    }
    
    /* Ajuste para que los inputs se vean bien en ambos modos */
    .stTextInput > div > div > input { color: var(--text-color); }
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
    if os.path.exists(ruta_local):
        st.image(ruta_local, caption=caption)
    elif nombre_archivo in links:
        st.image(links[nombre_archivo], caption=caption)
    else:
        st.warning(f"⚠️ Falta foto: {nombre_archivo}")

# --- BARRA LATERAL ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/7210/7210633.png", width=80)
    st.info("**Recuerda:** Sin *Shift of Structure* ni *Vela Envolvente*, NO HAY TRADE.")
    st.markdown("---")
    st.header("📝 Notas")
    par = st.text_input("Par (ej: XAUUSD)")
    notas = st.text_area("Plan", height=150, placeholder="Ej: Esperar retest en 1.0500...")
    st.markdown("---")
    if st.button("🔄 Limpiar Todo"): st.rerun()

# --- SESIONES ---
tz_ec = pytz.timezone('America/Guayaquil')
hora_ec = datetime.now(tz_ec).hour

# Lógica visual para el header de sesión (Compatible con Light/Dark)
if 15 <= hora_ec < 19:
    estado_mercado = "❌ MERCADO CERRADO (Hueco Tarde)"
    html_alert = f'<div class="closed-session">{estado_mercado}</div>'
else:
    estado_mercado = "✅ MERCADO ACTIVO (Asia/Londres/NY)"
    html_alert = f'<div class="open-session">{estado_mercado}</div>'

st.title("🦁 Set & Forget: Adaptive")
st.markdown(html_alert, unsafe_allow_html=True)
st.markdown("---")

# --- LAYOUT ---
col_guia, col_checklist, col_resultados = st.columns([1, 2, 1.2], gap="medium")

# 🔴 GUÍA VISUAL
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
    with st.container():
        st.subheader("🔗 Tendencias")
        c1, c2, c3 = st.columns(3)
        with c1: tw = st.selectbox("W", ["Alcista", "Bajista"], key="tw")
        with c2: td = st.selectbox("D", ["Alcista", "Bajista"], key="td")
        with c3: t4 = st.selectbox("4H", ["Alcista", "Bajista"], key="t4")
        if tw == td == t4: st.success("💎 TRIPLE SYNC")
        elif tw == td: st.info("✅ SWING SYNC")
        elif td == t4: st.info("✅ DAY SYNC")
        else: st.warning("⚠️ MIXTO")
    
    st.divider()
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("1. Weekly")
        w_score = sum([st.checkbox("AOI (+10%)", key="w1")*10, st.checkbox("Estruc. Previa (+10%)", key="w2")*10, st.checkbox("Patrón (+10%)", key="w3")*10, st.checkbox("EMA 50 (+5%)", key="w4")*5, st.checkbox("Psicológico (+5%)", key="w5")*5])
    with c2:
        st.subheader("2. Daily")
        d_score = sum([st.checkbox("AOI (+10%)", key="d1")*10, st.checkbox("Estruc. Previa (+10%)", key="d2")*10, st.checkbox("Vela (+10%)", key="d3")*10, st.checkbox("Patrón (+10%)", key="d4")*10, st.checkbox("EMA 50 (+5%)", key="d5")*5])
    
    st.divider()
    
    c3, c4 = st.columns(2)
    with c3:
        st.subheader("3. Ejecución (4H)")
        h4_score = sum([st.checkbox("Vela (+10%)", key="h1")*10, st.checkbox("Patrón (+10%)", key="h2")*10, st.checkbox("AOI (+5%)", key="h3")*5, st.checkbox("Estructura (+5%)", key="h4")*5, st.checkbox("EMA 50 (+5%)", key="h5")*5])
    with c4:
        st.subheader("4. GATILLO")
        entry_sos = st.checkbox("⚡ Shift of Structure", key="e1")
        entry_eng = st.checkbox("🕯️ Vela Envolvente", key="e2")
        entry_rr = st.checkbox("💰 RR Mínimo 1:2.5", key="e3")
        entry_score = sum([entry_sos*10, entry_eng*10])

# 🔵 RESULTADOS
with col_resultados:
    total = w_score + d_score + h4_score + entry_score
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
    st.metric("Probabilidad", f"{total}%")
    st.progress(min(total, 100))
    
    if is_valid and total >= 60:
        st.success("### ✅ EJECUTAR")
        st.balloons()
        st.markdown("""
        <div class="plan-box">
        <b>Plan de Acción:</b><br>
        • Entrada: Cierre de vela<br>
        • SL: 5-7 pips del AOI<br>
        • TP: Próx. Estructura<br>
        • Gestión: Set & Forget
        </div>
        """, unsafe_allow_html=True)
    else:
        st.error("### ❌ NO OPERAR")
