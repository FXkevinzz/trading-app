import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import os
import json
import calendar
import shutil
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
import pytz
from PIL import Image
import google.generativeai as genai
import io

# ==========================================
# 1. CONFIGURACIÓN OPTIMIZADA
# ==========================================
st.set_page_config(
    page_title="Trading Pro Suite AI Ultra", 
    layout="wide", 
    page_icon="🦁",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. GESTIÓN DE DIRECTORIOS
# ==========================================
DATA_DIR = "user_data"
IMG_DIR = os.path.join(DATA_DIR, "brain_images") # Carpeta específica para imágenes de la IA
BRAIN_FILE = os.path.join(DATA_DIR, "brain_data.json")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
ACCOUNTS_FILE = os.path.join(DATA_DIR, "accounts_config.json")

# Crear directorios necesarios
for d in [DATA_DIR, IMG_DIR]:
    if not os.path.exists(d): os.makedirs(d)

# ==========================================
# 3. INTELIGENCIA ARTIFICIAL Y LÓGICA
# ==========================================
def init_ai():
    if "GEMINI_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_KEY"])
        return True
    return False

@st.cache_data(ttl=60) # Cache para no leer disco a cada segundo
def load_brain():
    if not os.path.exists(BRAIN_FILE): return []
    try:
        with open(BRAIN_FILE, "r") as f: return json.load(f)
    except: return []

def save_image_locally(image_data, filename):
    """Guarda la imagen analizada en el disco local para el Playbook."""
    path = os.path.join(IMG_DIR, filename)
    try:
        # image_data viene como PIL Image
        image_data.save(path)
        return path
    except Exception as e:
        st.error(f"Error guardando imagen: {e}")
        return None

def save_to_brain(analysis_text, pair, result, mode, image_obj=None):
    memory = load_brain()
    
    # Guardar imagen física si existe
    img_path = None
    if image_obj:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        img_filename = f"{pair}_{result}_{timestamp}.png"
        img_path = save_image_locally(image_obj, img_filename)

    new_mem = {
        "date": str(datetime.now()),
        "pair": pair,
        "mode": mode,
        "result": result,
        "analysis": analysis_text,
        "image_path": img_path # Guardamos la referencia
    }
    memory.append(new_mem)
    try:
        with open(BRAIN_FILE, "w") as f: json.dump(memory, f, indent=4)
        load_brain.clear() # Limpiar cache para recargar datos nuevos
    except: pass

def analyze_chart(image, mode, pair, tf):
    brain = load_brain()
    context = ""
    if brain:
        wins = [x for x in brain if x.get('result') == 'WIN']
        examples = wins[-2:] if len(wins) >= 2 else wins
        context = f"TUS MEJORES TRADES PREVIOS:\n{str(examples)}\n\n"
    
    prompt = f"""
    Eres un Mentor 'Set & Forget'. Analiza este gráfico ({pair} - {tf}).
    ESTRATEGIA: {mode}
    {context}
    VALIDA: 1. Sincronización/Tendencia 2. AOI 3. Patrón de Entrada.
    
    Responde:
    🎯 VEREDICTO: [APROBADO/DUDOSO/DENEGADO]
    📊 PROBABILIDAD: 0-100%
    📝 ANÁLISIS: (Técnico)
    💡 CONSEJO: (Gestión)
    """
    modelos = ['gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-1.5-pro']
    for m in modelos:
        try:
            model = genai.GenerativeModel(m)
            return model.generate_content([prompt, image]).text
        except: continue
    return "Error conexión IA."

@st.cache_data
def generate_audit_report(df):
    # Versión optimizada que recibe un DataFrame pandas
    if df.empty: return "Sin datos."
    csv_txt = df.to_string()
    prompt = f"Audita estos trades como un experto en riesgo:\n{csv_txt}\nDetecta: Fugas, Zonas de Poder y da un consejo."
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        return model.generate_content(prompt).text
    except: return "Error Auditoría."

# ==========================================
# 4. SISTEMA DE TEMAS (CSS FINAL)
# ==========================================
def inject_theme(theme_mode):
    if theme_mode == "Claro (Swiss Design)":
        css_vars = """--bg-app:#f8fafc; --bg-card:#ffffff; --bg-sidebar:#1e293b; --text-main:#0f172a; --text-muted:#475569; --border-color:#e2e8f0; --input-bg:#ffffff; --accent:#2563eb; --accent-green:#16a34a; --accent-red:#dc2626; --button-text:#ffffff; --shadow:0 4px 6px -1px rgba(0,0,0,0.1); --chart-text:#0f172a; --chart-grid:#e2e8f0;"""
    else:
        css_vars = """--bg-app:#0b1121; --bg-card:#151e32; --bg-sidebar:#020617; --text-main:#f1f5f9; --text-muted:#94a3b8; --border-color:#2a3655; --input-bg:#1e293b; --accent:#3b82f6; --accent-green:#00e676; --accent-red:#ff1744; --button-text:#ffffff; --shadow:0 10px 15px -3px rgba(0,0,0,0.5); --chart-text:#94a3b8; --chart-grid:#1e293b;"""
    
    st.markdown(f"""<style>:root {{ {css_vars} }} 
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    .stApp {{ background-color: var(--bg-app); color: var(--text-main); font-family: 'Inter'; }}
    [data-testid="stSidebar"] {{ background-color: var(--bg-sidebar); border-right: 1px solid var(--border-color); }}
    h1,h2,h3,p,label,span,div {{ color: var(--text-main) !important; }}
    .strategy-box {{ background: var(--bg-card); border: 1px solid var(--border-color); padding: 20px; border-radius: 12px; box-shadow: var(--shadow); }}
    .stTextInput input, .stSelectbox div[data-baseweb="select"]>div {{ background: var(--input-bg) !important; color: var(--text-main) !important; border: 1px solid var(--border-color) !important; }}
    .stButton button {{ background: var(--accent) !important; color: var(--button-text) !important; border: none; font-weight: bold; }}
    .stTabs [data-baseweb="tab"][aria-selected="true"] {{ background: var(--accent) !important; color: white !important; }}
    .hud-container {{ background: linear-gradient(135deg, var(--bg-card), var(--bg-app)); border: 1px solid var(--accent); border-radius: 12px; padding: 20px; display: flex; align-items: center; justify-content: space-between; }}
    .status-sniper {{ background: rgba(16,185,129,0.15); color: var(--accent-green); border: 1px solid var(--accent-green); padding: 10px 20px; border-radius: 50px; font-weight: bold; }}
    .status-warning {{ background: rgba(250,204,21,0.15); color: #d97706; border: 1px solid #facc15; padding: 10px 20px; border-radius: 50px; font-weight: bold; }}
    .status-stop {{ background: rgba(239,68,68,0.15); color: var(--accent-red); border: 1px solid var(--accent-red); padding: 10px 20px; border-radius: 50px; font-weight: bold; }}
    </style>""", unsafe_allow_html=True)

# ==========================================
# 5. FUNCIONES BACKEND (OPTIMIZADAS)
# ==========================================
def load_json(fp): return json.load(open(fp)) if os.path.exists(fp) else {}
def save_json(fp, data): 
    try: json.dump(data, open(fp, "w")) 
    except: pass

def verify_user(u, p):
    if u == "admin" and p == "1234": return True
    d = load_json(USERS_FILE)
    return u in d and d[u] == p

def register_user(u, p): d = load_json(USERS_FILE); d[u] = p; save_json(USERS_FILE, d)
def get_user_accounts(u): d = load_json(ACCOUNTS_FILE); return list(d.get(u, {}).keys()) if u in d else ["Principal"]

def create_account(u, name, bal): 
    d = load_json(ACCOUNTS_FILE); d.setdefault(u, {})[name] = bal; save_json(ACCOUNTS_FILE, d)
    save_trade(u, name, None, init=True)

def create_backup_zip():
    """Crea un ZIP de toda la carpeta user_data"""
    shutil.make_archive("backup_trading", 'zip', DATA_DIR)
    return "backup_trading.zip"

@st.cache_data(ttl=10) # Cache corto para datos de balance
def get_balance_data(u, acc):
    d = load_json(ACCOUNTS_FILE); ini = d.get(u, {}).get(acc, 0.0)
    fp = os.path.join(DATA_DIR, u, f"{acc}.csv".replace(" ", "_"))
    df = pd.read_csv(fp) if os.path.exists(fp) else pd.DataFrame()
    pnl = df["Dinero"].sum() if not df.empty else 0
    return ini, ini + pnl, df

def save_trade(u, acc, data, init=False):
    folder = os.path.join(DATA_DIR, u); os.makedirs(folder, exist_ok=True)
    fp = os.path.join(folder, f"{acc}.csv".replace(" ", "_"))
    cols = ["Fecha","Par","Tipo","Resultado","Dinero","Ratio","Notas"]
    if init and not os.path.exists(fp): pd.DataFrame(columns=cols).to_csv(fp, index=False); return
    df = pd.read_csv(fp) if os.path.exists(fp) else pd.DataFrame(columns=cols)
    if data: df = pd.concat([df, pd.DataFrame([data])], ignore_index=True); df.to_csv(fp, index=False)
    get_balance_data.clear() # Limpiar cache al guardar

def load_trades(u, acc):
    fp = os.path.join(DATA_DIR, u, f"{acc}.csv".replace(" ", "_"))
    return pd.read_csv(fp) if os.path.exists(fp) else pd.DataFrame(columns=["Fecha","Par","Tipo","Resultado","Dinero","Ratio","Notas"])

# ==========================================
# 6. FUNCIONES VISUALES
# ==========================================
def mostrar_imagen(nombre, caption):
    local = os.path.join(IMG_DIR, nombre)
    if os.path.exists(local): st.image(local, caption=caption, use_container_width=True)

def render_heatmap(df, is_dark):
    # Preprocesamiento para Heatmap
    if df.empty: return None
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    df['Dia'] = df['Fecha'].dt.day_name()
    # Simulamos hora si no existe (en el futuro deberías guardar la hora)
    df['Hora'] = "10 AM" # Placeholder si no guardas hora exacta
    
    # Agrupación simple por día (Heatmap real requiere hora exacta de entrada)
    grouped = df.groupby('Dia')['Dinero'].sum().reset_index()
    
    fig = px.bar(grouped, x='Dia', y='Dinero', color='Dinero', 
                 color_continuous_scale=['red', 'green'], title="Rendimiento por Día")
    
    bg = 'rgba(0,0,0,0)'
    text_col = '#94a3b8' if is_dark else '#0f172a'
    fig.update_layout(paper_bgcolor=bg, plot_bgcolor=bg, font=dict(color=text_col))
    return fig

def render_cal_html(df, is_dark):
    # (Lógica de calendario optimizada)
    d = st.session_state.get('cal_date', datetime.now())
    y, m = d.year, d.month
    data = {}
    if not df.empty:
        try:
            df['Fecha'] = pd.to_datetime(df['Fecha'])
            df_m = df[(df['Fecha'].dt.year==y) & (df['Fecha'].dt.month==m)]
            data = df_m.groupby(df['Fecha'].dt.day)['Dinero'].sum().to_dict()
        except: pass

    cal = calendar.Calendar(firstweekday=0)
    day_col = "#94a3b8" if is_dark else "#64748b"
    html = '<div style="display:grid; grid-template-columns:repeat(7, 1fr); gap:8px; margin-top:15px;">'
    for h in ["LUN","MAR","MIÉ","JUE","VIE","SÁB","DOM"]: html += f'<div style="text-align:center; color:{day_col}; font-size:0.8rem; font-weight:bold;">{h}</div>'
    
    for week in cal.monthdayscalendar(y, m):
        for day in week:
            if day == 0: html += '<div style="opacity:0;"></div>'
            else:
                val = data.get(day, 0); txt = f"${val:,.0f}" if val != 0 else ""
                bg = "var(--bg-card)"; border = "var(--border-color)"; col = "var(--text-main)"
                if val > 0: bg="rgba(16,185,129,0.15)"; border="var(--accent-green)"; col="var(--accent-green)"
                elif val < 0: bg="rgba(239,68,68,0.15)"; border="var(--accent-red)"; col="var(--accent-red)"
                html += f'<div style="background:{bg}; border:1px solid {border}; border-radius:8px; min-height:80px; padding:5px; display:flex; flex-direction:column; justify-content:space-between;"><div style="color:var(--text-muted); font-size:0.8rem;">{day}</div><div style="color:{col}; font-weight:bold; text-align:right;">{txt}</div></div>'
    html += '</div>'
    return html, y, m

def change_month(delta):
    d = st.session_state.get('cal_date', datetime.now())
    m, y = d.month + delta, d.year
    if m > 12: m, y = 1, y+1
    elif m < 1: m, y = 12, y-1
    st.session_state['cal_date'] = d.replace(year=y, month=m, day=1)

# ==========================================
# 7. LOGIN
# ==========================================
def login_screen():
    inject_theme("Oscuro (Cyber Navy)")
    c1,c2,c3 = st.columns([1,1,1])
    with c2:
        st.markdown("<h1 style='text-align:center; color:var(--accent);'>🦁 Trading Suite Ultra</h1>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["INGRESAR", "REGISTRARSE"])
        with t1:
            u = st.text_input("Usuario", key="l_u"); p = st.text_input("Password", type="password", key="l_p")
            if st.button("ACCEDER", use_container_width=True, key="b_l"):
                if verify_user(u, p): st.session_state.user = u; st.rerun()
                else: st.error("Error (Prueba: admin/1234)")
        with t2:
            nu = st.text_input("Nuevo Usuario", key="r_u"); np = st.text_input("Nueva Password", type="password", key="r_p")
            if st.button("CREAR CUENTA", use_container_width=True, key="b_r"): register_user(nu, np); st.success("Creado!"); st.rerun()

# ==========================================
# 8. APP PRINCIPAL
# ==========================================
def main_app():
    user = st.session_state.user
    # Inicialización de estado
    if 'cal_date' not in st.session_state: st.session_state['cal_date'] = datetime.now()
    if 'global_pair' not in st.session_state: st.session_state.global_pair = "XAUUSD"
    if 'global_mode' not in st.session_state: st.session_state.global_mode = "Swing (W-D-4H)"
    if 'ai_temp_result' not in st.session_state: st.session_state.ai_temp_result = None
    if 'ai_temp_image' not in st.session_state: st.session_state.ai_temp_image = None # Para persistencia de imagen

    # --- SIDEBAR ---
    with st.sidebar:
        st.title(f"👤 {user.upper()}")
        tema = st.radio("🎨 TEMA", ["Oscuro (Cyber Navy)", "Claro (Swiss Design)"], index=0)
        inject_theme(tema)
        is_dark = True if tema == "Oscuro (Cyber Navy)" else False
        
        st.markdown("---")
        # CALCULADORA RIESGO
        with st.expander("🧮 CALCULADORA RIESGO"):
            calc_bal = st.number_input("Balance", value=10000.0)
            calc_risk = st.number_input("Riesgo %", value=1.0)
            calc_sl = st.number_input("Stop Loss (Pips)", value=5.0)
            if calc_sl > 0:
                risk_usd = calc_bal * (calc_risk/100)
                lots = risk_usd / (calc_sl * 10) # Aproximado estándar
                st.markdown(f"**Riesgo:** ${risk_usd:.2f}")
                st.success(f"**LOTES:** {lots:.2f}")

        st.markdown("---")
        
        accs = get_user_accounts(user)
        sel_acc = st.selectbox("📂 CUENTA ACTIVA", accs)
        ini, act, df_bal = get_balance_data(user, sel_acc)
        
        st.markdown(f"""<div style="background:rgba(255,255,255,0.05); padding:15px; border-radius:10px; border:1px solid rgba(255,255,255,0.1); text-align:center;"><div style="color:#94a3b8; font-size:0.8rem;">BALANCE</div><div style="color:{'#10b981' if act>=ini else '#ef4444'}; font-size:1.8rem; font-weight:bold">${act:,.2f}</div></div>""", unsafe_allow_html=True)
        
        c_new, c_back = st.columns(2)
        with c_new:
            with st.popover("➕ CUENTA"):
                na = st.text_input("Nombre"); nb = st.number_input("Capital", 100.0)
                if st.button("Crear"): create_account(user, na, nb); st.rerun()
        with c_back:
            # BOTÓN DE BACKUP
            zip_file = create_backup_zip()
            with open(zip_file, "rb") as f:
                st.download_button("💾 BACKUP", f, file_name="backup.zip", mime="application/zip")
        
        if st.button("CERRAR SESIÓN", use_container_width=True): st.session_state.user = None; st.rerun()

    # --- TABS ---
    tabs = st.tabs(["🦁 OPERATIVA", "🧠 IA VISION", "📝 BITÁCORA", "📊 ANALYTICS", "📅 CALENDARIO", "📰 NOTICIAS"])

    # TAB 1: OPERATIVA
    with tabs[0]:
        st.markdown('<div class="strategy-box">', unsafe_allow_html=True)
        c_mod = st.columns([1,2,1])
        with c_mod[1]: st.session_state.global_mode = st.radio("", ["Swing (W-D-4H)", "Scalping (4H-2H-1H)"], horizontal=True, label_visibility="collapsed")
        st.markdown("---"); st.session_state.global_pair = st.text_input("ACTIVO GLOBAL", st.session_state.global_pair).upper()
        st.markdown('</div><br>', unsafe_allow_html=True)

        # Checklist completo (Resumido en visualización, expandido en lógica interna)
        r1, r2 = st.columns(2)
        total = 0; sos, eng = False, False
        with r1:
            st.markdown('<div class="strategy-box"><h5>1. CONTEXTO</h5>', unsafe_allow_html=True)
            w1 = st.checkbox("Rechazo AOI (+10%)")
            w2 = st.checkbox("Estructura (+10%)")
            w3 = st.checkbox("Patrón (+10%)")
            st.markdown('</div>', unsafe_allow_html=True)
        with r2:
            st.markdown('<div class="strategy-box"><h5>2. GATILLO</h5>', unsafe_allow_html=True)
            sos = st.checkbox("⚡ SOS (Obligatorio)")
            eng = st.checkbox("🕯️ Envolvente (Obligatorio)")
            rr = st.checkbox("💰 Ratio > 1:2.5")
            st.markdown('</div>', unsafe_allow_html=True)
        
        total = (w1+w2+w3)*10 + (sos+eng)*10
        valid = sos and eng and rr
        msg, css = "ESPERAR", "status-warning"
        if valid and total>=50: msg, css = "VALIDO", "status-sniper"
        
        st.markdown(f"""<br><div class="hud-container"><div class="hud-stat"><div class="hud-label">TOTAL</div><div class="hud-value-large">{total}%</div></div><div style="flex-grow:1; text-align:center; margin:0 20px;"><span class="{css}">{msg}</span></div></div>""", unsafe_allow_html=True)

    # TAB 2: IA VISION (PLAYBOOK + ANALISIS)
    with tabs[1]:
        sub_ia = st.tabs(["👁️ ANÁLISIS", "📘 GALERÍA (PLAYBOOK)"])
        
        with sub_ia[0]:
            st.markdown(f"<h3 style='color:var(--accent)'>🧠 Mentor IA</h3>", unsafe_allow_html=True)
            if not init_ai(): st.error("Falta API KEY")
            else:
                c_img, c_res = st.columns([1, 1.5])
                with c_img:
                    uploaded_file = st.file_uploader("Sube tu gráfico", type=["jpg", "png"])
                    if uploaded_file:
                        image = Image.open(uploaded_file)
                        st.image(image, caption="Gráfico", use_container_width=True)
                        st.session_state.ai_temp_image = image # Guardar en sesión
                        
                        if st.button("🦁 ANALIZAR", type="primary", use_container_width=True):
                            with st.spinner("Analizando..."):
                                res = analyze_chart(image, st.session_state.global_mode, st.session_state.global_pair, "Multi")
                                st.session_state.ai_temp_result = res
                with c_res:
                    if st.session_state.ai_temp_result:
                        st.markdown('<div class="strategy-box">', unsafe_allow_html=True)
                        st.markdown(st.session_state.ai_temp_result)
                        st.markdown('</div>', unsafe_allow_html=True)
                        st.info("Registra el trade como 'WIN' en Bitácora para guardar este análisis y la foto.")

        with sub_ia[1]:
            st.markdown("### 📘 Tu Playbook de Éxito")
            brain_data = load_brain()
            wins = [x for x in brain_data if x.get('result') == 'WIN' and x.get('image_path')]
            if wins:
                cols = st.columns(3)
                for i, trade in enumerate(wins):
                    with cols[i % 3]:
                        if os.path.exists(trade['image_path']):
                            st.image(trade['image_path'], caption=f"{trade['pair']} - {trade['date'][:10]}")
                            with st.popover("Ver Análisis"):
                                st.write(trade['analysis'])
            else:
                st.info("Aún no hay trades ganadores con imagen guardados.")

    # TAB 3: BITÁCORA
    with tabs[2]:
        c_form, c_hist = st.columns([1, 1.5])
        with c_form:
            st.markdown(f"<h3 style='color:var(--accent)'>📝 Nuevo Registro</h3>", unsafe_allow_html=True)
            st.markdown('<div class="strategy-box">', unsafe_allow_html=True)
            with st.form("reg_trade"):
                dt = st.date_input("Fecha", datetime.now())
                pr = st.text_input("Par", st.session_state.global_pair)
                tp = st.selectbox("Tipo", ["BUY","SELL"]); rs = st.selectbox("Resultado", ["WIN", "LOSS", "BE"])
                mn = st.number_input("Monto PnL", step=10.0); rt = st.number_input("Ratio", 2.5)
                nt = st.text_area("Notas")
                if st.form_submit_button("GUARDAR"):
                    rm = mn if rs=="WIN" else -abs(mn) if rs=="LOSS" else 0
                    save_trade(user, sel_acc, {"Fecha":dt,"Par":pr,"Tipo":tp,"Resultado":rs,"Dinero":rm,"Ratio":rt,"Notas":nt})
                    
                    # Guardar en Cerebro CON IMAGEN
                    if st.session_state.ai_temp_result and st.session_state.ai_temp_image:
                        save_to_brain(st.session_state.ai_temp_result, pr, rs, st.session_state.global_mode, st.session_state.ai_temp_image)
                        st.toast("🧠 IA Aprendió + Imagen Guardada", icon="📸")
                        st.session_state.ai_temp_result = None # Reset
                        st.session_state.ai_temp_image = None
                        
                    st.success("Guardado"); st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        
        with c_hist:
            st.markdown(f"<h3 style='color:var(--accent)'>📜 Historial</h3>", unsafe_allow_html=True)
            df_h = load_trades(user, sel_acc)
            if not df_h.empty:
                df_h['Fecha'] = pd.to_datetime(df_h['Fecha'])
                df_h = df_h.sort_values("Fecha", ascending=False)
                for d in df_h['Fecha'].dt.date.unique():
                    dd = df_h[df_h['Fecha'].dt.date == d]
                    pnl = dd['Dinero'].sum(); icon = "🟢" if pnl >= 0 else "🔴"
                    with st.expander(f"{icon} {d} | PnL: ${pnl:,.2f}"): st.dataframe(dd)

    # TAB 4: ANALYTICS
    with tabs[3]:
        if not df_bal.empty:
            st.markdown("#### 📈 Equity Curve")
            fig = go.Figure(go.Scatter(x=df_bal["Fecha"], y=df_bal["Dinero"].cumsum() + ini, mode='lines+markers'))
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='gray'))
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("#### 🔥 Heatmap de Rendimiento")
            fig_heat = render_heatmap(df_bal, is_dark)
            if fig_heat: st.plotly_chart(fig_heat, use_container_width=True)
            
            if st.button("AUDITAR RENDIMIENTO"):
                if init_ai(): st.info(generate_audit_report(df_bal))

    # TAB 5: CALENDARIO
    with tabs[4]:
        c_p, c_t, c_n = st.columns([1,5,1])
        with c_p: 
            if st.button("⬅️"): change_month(-1); st.rerun()
        with c_n: 
            if st.button("➡️"): change_month(1); st.rerun()
        html, y, m = render_cal_html(df_bal, is_dark)
        with c_t: st.markdown(f"<h3 style='text-align:center; color:var(--text-main); margin:0'>{calendar.month_name[m]} {y}</h3>", unsafe_allow_html=True)
        st.markdown(html, unsafe_allow_html=True)

    # TAB 6: NOTICIAS
    with tabs[5]:
        tv = "dark" if is_dark else "light"
        html = f"""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-events.js" async>{{"colorTheme": "{tv}","isTransparent": true,"width": "100%","height": "800","locale": "es","importanceFilter": "-1,0","currencyFilter": "USD,EUR,GBP,JPY,AUD,CAD,CHF,NZD"}}</script></div>"""
        components.html(html, height=800)

if 'user' not in st.session_state: st.session_state.user = None
if st.session_state.user: main_app()
else: login_screen()

