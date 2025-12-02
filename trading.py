import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
import google.generativeai as genai
from PIL import Image

# ==============================================================================
# 1. CONFIGURACIÓN INICIAL Y ESTILOS (THEME DARK NAVY)
# ==============================================================================
st.set_page_config(page_title="The Perfect Trade AI", layout="wide", page_icon="🦁")

def inject_custom_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        /* --- GLOBAL THEME --- */
        .stApp {
            background-color: #0f172a; /* Slate 900 - Fondo Principal */
            font-family: 'Inter', sans-serif;
            color: #f8fafc;
        }
        
        /* Ocultar elementos de Streamlit */
        #MainMenu, footer, header {visibility: hidden;}
        .stDeployButton {display:none;}

        /* --- NAVBAR --- */
        .nav-container {
            display: flex; justify-content: space-between; align-items: center;
            background-color: #0f172a; padding: 10px 0; border-bottom: 1px solid #1e293b; margin-bottom: 30px;
        }
        .nav-logo { font-weight: 800; font-size: 1.2rem; color: #fff; display: flex; align-items: center; gap: 10px; }
        .nav-user { color: #cbd5e1; font-weight: 600; font-size: 0.9rem; }
        .logout-btn { 
            background-color: rgba(239, 68, 68, 0.1); border: 1px solid #ef4444; 
            color: #ef4444; padding: 5px 15px; border-radius: 6px; font-size: 0.8rem; 
        }

        /* --- CARDS GENERALES --- */
        .card {
            background-color: #1e293b; /* Slate 800 */
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
        }

        /* --- CHECKLIST STYLES --- */
        .confluence-box { background: #1e293b; border-radius: 8px; padding: 15px; text-align: center; border: 1px solid #334155; }
        
        /* --- DASHBOARD STATS --- */
        .stat-card-big {
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border: 1px solid #334155; border-radius: 16px; padding: 25px; position: relative;
        }
        .stat-money { font-size: 3rem; font-weight: 800; color: #10b981; line-height: 1; }
        .kpi-card { background: #334155; border-radius: 8px; padding: 15px; text-align: center; }
        .kpi-label { color: #cbd5e1; font-size: 0.75rem; text-transform: uppercase; }
        .kpi-value { color: #fff; font-size: 1.2rem; font-weight: 700; }

        /* --- HISTORY LIST --- */
        .history-item { 
            background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 15px 20px; 
            display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;
        }
        .pair-badge { font-size: 1.1rem; font-weight: 700; color: white; display: flex; align-items: center; gap: 10px; }
        .dir-badge { font-size: 0.7rem; padding: 3px 8px; border-radius: 4px; font-weight: 700; text-transform: uppercase; }
        .dir-LONG { background: rgba(16, 185, 129, 0.2); color: #34d399; }
        .dir-SHORT { background: rgba(239, 68, 68, 0.2); color: #f87171; }

        /* --- BOTONES & INPUTS --- */
        .stButton button { background-color: #334155; color: white; border: none; border-radius: 8px; font-weight: 500; }
        .stButton button:hover { background-color: #475569; }
        div[data-testid="stForm"] { background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 20px; }
        .stTextInput input, .stNumberInput input, .stSelectbox div, .stTextArea textarea {
            background-color: #0f172a !important; color: white !important; border: 1px solid #334155 !important; border-radius: 6px;
        }
        </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# ==============================================================================
# 2. SISTEMA DE GESTIÓN DE ESTADO Y DATOS
# ==============================================================================

if 'page' not in st.session_state: st.session_state.page = 'checklist'
if 'checklist' not in st.session_state: st.session_state.checklist = {}
if 'chat_history' not in st.session_state: 
    st.session_state.chat_history = [{"role": "assistant", "content": "🦁 Hola. Soy tu Mentor 'Set & Forget'. Sube tu gráfico y analicemos la estructura."}]

# Datos de prueba iniciales
if 'trades' not in st.session_state: 
    st.session_state.trades = [
        {"id": "1", "pair": "EURUSD", "type": "LONG", "result": "WIN", "pnl": 1250.00, "date": "2025-12-02", "score": 95},
        {"id": "2", "pair": "GBPJPY", "type": "SHORT", "result": "LOSS", "pnl": -500.00, "date": "2025-12-03", "score": 80},
    ]

# Configuración de Estrategia
STRATEGY = {
    "WEEKLY": [("Trend", 10), ("At AOI / Rejected", 10), ("Touching EMA", 5), ("Round Psych Level", 5), ("Rejection Structure", 10)],
    "DAILY": [("Trend", 10), ("At AOI / Rejected", 10), ("Touching EMA", 5), ("Round Psych Level", 5), ("Rejection Structure", 10)],
    "4H": [("Trend", 5), ("At AOI / Rejected", 5), ("Touching EMA", 5), ("Round Psych Level", 5), ("Rejection Structure", 10)],
    "2H, 1H, 30m": [("Trend", 5), ("Touching EMA", 5), ("Break & Retest", 5)],
    "ENTRY SIGNAL": [("SOS (Shift of Structure)", 10), ("Engulfing candlestick", 10)]
}

# --- LÓGICA DE IA (GEMINI 2.0 FLASH) ---
def get_ai_mentor_response(messages, image=None, api_key=None):
    if not api_key: return "⚠️ Por favor ingresa tu API KEY en la barra lateral."
    
    try:
        genai.configure(api_key=api_key)
        
        system_instruction = """
        Eres el MENTOR SENIOR de la estrategia 'Set & Forget' (Alex G).
        Tu tono es profesional, institucional y estricto con el riesgo.
        
        REGLAS PARA VALIDAR GRÁFICOS (VISIÓN):
        1. 📅 DÍAS: ¿Es Lunes-Jueves? (Viernes/Domingo prohibido).
        2. ⏰ HORARIO: 11 PM - 11 AM EST (London/NY).
        3. 🎯 AOI: El precio DEBE reaccionar a una zona SEMANAL o DIARIA.
        4. ⚡ GATILLO: Busca 'Shift of Structure' + Vela Envolvente.
        
        SI VES EL GRÁFICO:
        - Identifica la tendencia.
        - Busca la EMA 50 y Niveles Psicológicos.
        - Da un veredicto: "✅ TRADE VÁLIDO" o "❌ DESCARTAR".
        """
        
        # Usamos gemini-2.0-flash-exp (o 1.5-flash si 2.0 no está disponible en tu región aun)
        model = genai.GenerativeModel(model_name="gemini-1.5-flash", system_instruction=system_instruction)
        
        prompt = messages[-1]["content"]
        inputs = [prompt, image] if image else [prompt]
        
        response = model.generate_content(inputs)
        return response.text
    except Exception as e:
        return f"Error IA: {str(e)}"

# --- LÓGICA DE PUNTUACIÓN ---
def calc_score():
    score = 0
    for sec, items in STRATEGY.items():
        for label, pts in items:
            if st.session_state.checklist.get(f"{sec}_{label}", False):
                score += pts
    return score

# --- MODAL DE GUARDADO ---
@st.dialog("Save Trade")
def save_trade_modal(score):
    st.markdown(f"<h3 style='color:#10b981'>Confluence Score: {score}%</h3>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1: pair = st.selectbox("Currency Pair *", ["EURUSD", "GBPUSD", "XAUUSD", "US30", "NAS100"])
    with c2: direction = st.selectbox("Direction *", ["LONG", "SHORT"])
    
    c3, c4 = st.columns(2)
    with c3: sl = st.number_input("Stop Loss", format="%.5f")
    with c4: tp = st.number_input("Take Profit", format="%.5f")
    
    entry = st.number_input("Entry Price", format="%.5f")
    risk = st.number_input("Risk %", value=1.0)
    
    # Calculadora simple de lotaje (Forex Standard aprox)
    lots = 0.0
    if entry > 0 and sl > 0:
        pips = abs(entry - sl) * 10000 if "JPY" not in pair else abs(entry - sl) * 100
        if pips > 0:
            risk_usd = 10000 * (risk/100) # Asumiendo cuenta 10k
            lots = risk_usd / (pips * 10)
    
    st.info(f"🔢 Lotaje Sugerido (Cuenta $10k): {lots:.2f} Lotes")
    notes = st.text_area("Notes *")
    
    if st.button("💾 Save Trade", use_container_width=True, type="primary"):
        new_trade = {
            "id": str(uuid.uuid4()),
            "pair": pair,
            "type": direction,
            "result": "PENDING",
            "pnl": 0.0,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "score": score,
            "entry": entry, "sl": sl, "tp": tp, "notes": notes
        }
        st.session_state.trades.insert(0, new_trade)
        st.session_state.checklist = {} 
        st.rerun()

# ==============================================================================
# 3. INTERFAZ: BARRA DE NAVEGACIÓN
# ==============================================================================

with st.sidebar:
    st.markdown("### 🔐 Configuración")
    api_key = st.text_input("Gemini API Key", type="password", placeholder="Pega tu Key aquí")
    st.caption("Obtén tu key gratis en Google AI Studio")
    st.divider()
    st.markdown("Developed for **The Perfect Trade**")

c_nav1, c_nav2 = st.columns([1, 4])
with c_nav1:
    st.markdown('<div class="nav-logo">🦁 THE PERFECT TRADE</div>', unsafe_allow_html=True)
with c_nav2:
    b1, b2, b3, b4, b_user = st.columns([1, 1, 1, 1, 2])
    with b1: 
        if st.button("📈 Checklist", use_container_width=True): st.session_state.page = 'checklist'; st.rerun()
    with b2: 
        if st.button("📖 History", use_container_width=True): st.session_state.page = 'history'; st.rerun()
    with b3: 
        if st.button("📊 Dashboard", use_container_width=True): st.session_state.page = 'dashboard'; st.rerun()
    with b4: 
        if st.button("🤖 AI Mentor", use_container_width=True): st.session_state.page = 'ai_mentor'; st.rerun()
    with b_user:
        st.markdown('<div style="text-align:right; padding-top:5px;"><span class="nav-user">kevin zambrano</span> <span class="logout-btn">Logout</span></div>', unsafe_allow_html=True)

st.divider()

# ==============================================================================
# PÁGINA 1: CHECKLIST
# ==============================================================================
if st.session_state.page == 'checklist':
    
    score = calc_score()
    score_color = "#ef4444"
    score_txt = "Weak Setup"
    if score > 60: score_color = "#facc15"; score_txt = "Moderate"
    if score > 90: score_color = "#10b981"; score_txt = "🔥 SNIPER ENTRY"

    # Dashboard Score
    st.markdown("<h3 style='text-align:center'>Confluence Summary</h3>", unsafe_allow_html=True)
    cols = st.columns(5)
    labels = ["WEEKLY", "DAILY", "4H", "2H/1H", "ENTRY"]
    for i, c in enumerate(cols):
        c.markdown(f"""<div class="confluence-box"><div style="color:#94a3b8; font-size:0.7rem;">{labels[i]}</div><div style="color:#2dd4bf; font-size:1.5rem; font-weight:bold">--%</div></div>""", unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style="background:#1e293b; border:2px solid {score_color}; border-radius:16px; padding:30px; text-align:center; margin:20px 0;">
        <div style="color:#cbd5e1; letter-spacing:1px; font-weight:600;">TOTAL OVERALL SCORE</div>
        <div style="font-size:4rem; font-weight:900; color:{score_color}; line-height:1.1;">{score}%</div>
        <div style="color:{score_color}; font-weight:bold;">{score_txt}</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("✅ SAVE TRADE", use_container_width=True, type="primary"):
        save_trade_modal(score)

    c_left, c_right = st.columns(2)
    for i, (sec, items) in enumerate(STRATEGY.items()):
        target_col = c_left if i % 2 == 0 else c_right
        with target_col:
            st.markdown(f'<div class="card"><h4>{sec}</h4>', unsafe_allow_html=True)
            for label, pts in items:
                key = f"{sec}_{label}"
                cl, cr = st.columns([4, 1])
                cl.markdown(f"<span style='font-size:0.9rem; color:#e2e8f0'>{label}</span>", unsafe_allow_html=True)
                toggle_val = cr.toggle(f"+{pts}", key=key, label_visibility="collapsed")
                st.session_state.checklist[key] = toggle_val
                if toggle_val: cr.markdown(f"<div style='text-align:right; color:#10b981; font-size:0.7rem;'>+{pts}%</div>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# PÁGINA 2: HISTORY
# ==============================================================================
elif st.session_state.page == 'history':
    st.title("Trading History")
    
    c_fil = st.columns([1,1,1,1,4])
    c_fil[0].button("ALL", type="primary")
    c_fil[1].button("WIN")
    c_fil[2].button("LOSS")
    
    st.markdown("<br>", unsafe_allow_html=True)

    for trade in st.session_state.trades:
        dir_cls = "dir-LONG" if trade['type'] == "LONG" else "dir-SHORT"
        score_col = "#10b981" if trade['score'] > 80 else "#facc15"
        pnl_col = '#10b981' if trade['pnl'] >= 0 else '#ef4444'
        
        st.markdown(f"""
        <div class="history-item">
            <div>
                <div class="pair-badge"><span style="background:#334155; padding:5px; border-radius:4px;">📈</span> {trade['pair']}</div>
                <div style="margin-top:5px;"><span class="{dir_cls}">{trade['type']}</span></div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:0.8rem; color:#94a3b8;">Confluence</div>
                <div style="color:{score_col}; font-weight:bold;">{trade['score']}%</div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:0.8rem; color:#94a3b8;">PnL</div>
                <div style="color:{pnl_col}; font-weight:bold;">${trade['pnl']}</div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:0.8rem; color:#94a3b8;">Date</div>
                <div style="color:white;">{trade['date']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ==============================================================================
# PÁGINA 3: DASHBOARD
# ==============================================================================
elif st.session_state.page == 'dashboard':
    trades = pd.DataFrame(st.session_state.trades)
    net_pnl = trades['pnl'].sum() if not trades.empty else 0
    wins = trades[trades['pnl'] > 0]
    
    c_main, c_side = st.columns([2, 1])
    with c_main:
        st.markdown(f"""
        <div class="stat-card-big">
            <div style="color:#cbd5e1; font-weight:600;">Net Profit & Loss</div>
            <div class="stat-money" style="color: {'#10b981' if net_pnl >= 0 else '#ef4444'}">${net_pnl:,.2f}</div>
            <div class="stat-sub">+ {len(trades)} trades completed</div>
            <div style="display:grid; grid-template-columns: repeat(3, 1fr); gap:10px; margin-top:20px;">
                <div class="kpi-card"><div class="kpi-label">Win Rate</div><div class="kpi-value">65%</div></div>
                <div class="kpi-card"><div class="kpi-label">Profit Factor</div><div class="kpi-value">2.4</div></div>
                <div class="kpi-card"><div class="kpi-label">Streak</div><div class="kpi-value">🔥 3</div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with c_side:
        st.markdown(f"""
        <div class="card"><div style="color:#94a3b8; font-size:0.8rem;">Total Profit</div><div style="font-size:1.5rem; color:#10b981; font-weight:bold">${wins['pnl'].sum():,.2f}</div></div>
        <div class="card"><div style="color:#94a3b8; font-size:0.8rem;">Total Loss</div><div style="font-size:1.5rem; color:#ef4444; font-weight:bold">$0.00</div></div>
        """, unsafe_allow_html=True)

# ==============================================================================
# PÁGINA 4: AI MENTOR (GEMINI 2.0 VISION)
# ==============================================================================
elif st.session_state.page == 'ai_mentor':
    st.markdown("## 🤖 AI Trading Mentor")
    
    c_chat, c_playbook = st.columns([3, 1])
    
    with c_chat:
        chat_container = st.container(height=500)
        for msg in st.session_state.chat_history:
            avatar = "🦁" if msg["role"] == "assistant" else "👤"
            with chat_container.chat_message(msg["role"], avatar=avatar):
                st.write(msg["content"])
                if "image" in msg: st.image(msg["image"], width=300)
        
        with st.form("chat_form", clear_on_submit=True):
            c_up, c_in = st.columns([1, 5])
            with c_up: uploaded_file = st.file_uploader("📷", type=["png", "jpg"], label_visibility="collapsed")
            with c_in: user_input = st.text_input("Mensaje...", label_visibility="collapsed")
            sent = st.form_submit_button("Enviar")
            
            if sent and (user_input or uploaded_file):
                img = Image.open(uploaded_file) if uploaded_file else None
                
                # 1. Guardar Usuario
                user_msg = {"role": "user", "content": user_input}
                if img: user_msg["image"] = img
                st.session_state.chat_history.append(user_msg)
                
                # 2. IA
                with st.spinner("🦁 Analizando..."):
                    reply = get_ai_mentor_response(st.session_state.chat_history, img, api_key)
                
                # 3. Guardar Bot
                st.session_state.chat_history.append({"role": "assistant", "content": reply})
                st.rerun()

    with c_playbook:
        st.markdown('<div class="card"><h4>📘 Quick Tips</h4><ul style="font-size:0.8rem; color:#cbd5e1;"><li>Sube una foto de tu gráfico 4H.</li><li>Pregunta si el AOI es válido.</li><li>Verifica la vela envolvente.</li></ul></div>', unsafe_allow_html=True)
