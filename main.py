import streamlit as st
import pandas as pd
from datetime import datetime
import calendar
from modules.styles import inject_theme
from modules.data import (
    init_filesystem, verify_user, register_user, get_user_accounts, 
    get_balance_data, OFFICIAL_PAIRS
)
from modules.ui import modal_new_trade, modal_update_trade
from modules.utils import get_live_clock_html, render_cal_html
from modules.ai import init_ai, chat_with_mentor
import streamlit.components.v1 as components

# 1. CONFIG
st.set_page_config(page_title="Trading Pro Suite", layout="wide", page_icon="🦁")
init_filesystem()

# 2. LOGIN
def login_screen():
    inject_theme("Oscuro")
    c1,c2,c3 = st.columns([1,1,1])
    with c2:
        st.markdown("<h1 style='text-align:center; color:#10b981;'>🦁 Trading Pro Suite</h1>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["INGRESAR", "REGISTRARSE"])
        with t1:
            u = st.text_input("Usuario", key="l_u"); p = st.text_input("Password", type="password", key="l_p")
            if st.button("ENTRAR", use_container_width=True):
                if verify_user(u, p): st.session_state.user = u; st.rerun()
                else: st.error("Error")
        with t2:
            nu = st.text_input("Nuevo Usuario"); np = st.text_input("Nueva Password", type="password")
            if st.button("REGISTRAR", use_container_width=True):
                if nu and np: register_user(nu, np); st.success("Listo"); st.rerun()

# 3. APP PRINCIPAL
def main_app():
    user = st.session_state.user
    inject_theme("Oscuro")
    
    # Inicializar chat
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "🦁 **Mentor IA:** Hola. He analizado tu bitácora. Sube un gráfico si quieres que revise tu análisis o pregúntame sobre psicología.", "image": None}]

    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown(f"### 👤 {user.upper()}")
        components.html(get_live_clock_html(), height=160)
        
        accs = get_user_accounts(user)
        sel_acc = st.selectbox("Cuenta Seleccionada", accs)
        ini, act, df = get_balance_data(user, sel_acc)
        
        pnl_total = act - ini
        color_pnl = "#10b981" if pnl_total >= 0 else "#ef4444"
        st.markdown(f"""
        <div class="dashboard-card" style="text-align:center; padding:15px;">
            <div class="sub-stat-label">BALANCE ACTUAL</div>
            <div style="font-size:2rem; font-weight:bold; color:white;">${act:,.2f}</div>
            <div style="color:{color_pnl}; font-weight:bold;">{'+' if pnl_total>0 else ''}${pnl_total:,.2f}</div>
        </div>""", unsafe_allow_html=True)
        
        st.markdown("---")
        if st.button("Cerrar Sesión"): st.session_state.user = None; st.rerun()

    # --- PESTAÑAS ---
    tab_op, tab_hist, tab_dash, tab_ai = st.tabs(["🚀 OPERATIVA", "📜 HISTORIAL", "📊 DASHBOARD PRO", "🧠 MENTOR IA"])

    # 1. PESTAÑA OPERATIVA
    with tab_op:
        c_mod = st.columns([1,2,1])
        with c_mod[1]: 
            global_mode = st.radio("", ["Swing (W-D-4H)", "Scalping (4H-2H-1H)"], horizontal=True, label_visibility="collapsed")
        
        if 'pair_selector' not in st.session_state: st.session_state.pair_selector = OFFICIAL_PAIRS[0]
        st.session_state.pair_selector = st.selectbox("ACTIVO", OFFICIAL_PAIRS)
        st.markdown("---")
        
        r1_c1, r1_c2 = st.columns(2)
        r2_c1, r2_c2 = st.columns(2)
        total = 0; sos, eng, rr = False, False, False

        def header(t): return f"<div style='color:#10b981; font-weight:bold; margin-bottom:10px; border-bottom:1px solid #2a3655;'>{t}</div>"

        # Lógica Original
        with r1_c1:
            st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
            st.markdown(header("1. CONTEXTO MACRO"), unsafe_allow_html=True)
            s1 = sum([st.checkbox("Tendencia Alineada (+20%)")*20, st.checkbox("Rechazo AOI (+20%)")*20, st.checkbox("Patrón Vela (+10%)")*10])
            st.markdown('</div>', unsafe_allow_html=True)
        with r1_c2:
            st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
            st.markdown(header("2. GATILLO FINAL"), unsafe_allow_html=True)
            s2 = sum([st.checkbox("SOS / Quiebre (+20%)")*20, st.checkbox("Vela Envolvente (+20%)")*20, st.checkbox("Ratio > 1:2.5 (+10%)")*10])
            st.markdown('</div>', unsafe_allow_html=True)
        
        total = s1 + s2
        st.markdown("<br>", unsafe_allow_html=True)
        
        col_hud, col_btn = st.columns([3, 1])
        with col_hud:
            st.markdown(f"""
            <div class="dashboard-card" style="display:flex; align-items:center; justify-content:space-between; padding:15px;">
                <span class="sub-stat-label">CALIDAD DEL TRADE</span>
                <span style="font-size:2rem; font-weight:900; color:{'#10b981' if total>=60 else '#ef4444'}">{total}%</span>
            </div>""", unsafe_allow_html=True)
        with col_btn:
            if st.button("🚀 EJECUTAR", type="primary", use_container_width=True):
                modal_new_trade(user, sel_acc, global_mode, st.session_state.pair_selector, total)

    # 2. PESTAÑA HISTORIAL
    with tab_hist:
        if not df.empty:
            f1, f2 = st.columns([2, 1])
            with f1: f_pair = st.text_input("Buscar", placeholder="EURUSD...")
            with f2: f_res = st.multiselect("Filtro", ["WIN", "LOSS", "BE", "PENDING"])
            
            df_view = df.copy()
            if f_pair: df_view = df_view[df_view['Par'].str.contains(f_pair.upper())]
            if f_res: df_view = df_view[df_view['Resultado'].isin(f_res)]
            
            st.dataframe(df_view[['Fecha', 'Par', 'Direccion', 'Status', 'Resultado', 'Dinero', 'Confluencia']], use_container_width=True, hide_index=True)
            tr_idx = st.selectbox("Editar Trade:", df_view.index, format_func=lambda x: f"#{x} {df_view.loc[x,'Par']}")
            if st.button("📂 ABRIR"):
                modal_update_trade(user, sel_acc, tr_idx, df.loc[tr_idx])
        else:
            st.info("No hay trades registrados.")

    # 3. PESTAÑA DASHBOARD PRO
    with tab_dash:
        st.markdown("### 📊 Trading Dashboard")
        net_pnl = 0; win_rate = 0; pf = 0; best_streak = 0; largest_win = 0; largest_loss = 0
        total_trades = 0; wins_count = 0; loss_count = 0
        
        if not df.empty:
            net_pnl = df['Dinero'].sum()
            closed = df[df['Status'] == 'CLOSED']
            total_trades = len(closed)
            wins = closed[closed['Resultado'] == 'WIN']
            losses = closed[closed['Resultado'] == 'LOSS']
            wins_count = len(wins); loss_count = len(losses)
            if total_trades > 0: win_rate = (wins_count / total_trades) * 100
            gross_win = wins['Dinero'].sum(); gross_loss = abs(losses['Dinero'].sum())
            if gross_loss > 0: pf = gross_win / gross_loss
            else: pf = gross_win
            if not wins.empty: largest_win = wins['Dinero'].max()
            if not losses.empty: largest_loss = losses['Dinero'].min()
            current_streak = 0
            for res in closed['Resultado']:
                if res == 'WIN': current_streak += 1; best_streak = max(best_streak, current_streak)
                else: current_streak = 0

        top_c1, top_c2, top_c3 = st.columns([2, 1, 1])
        with top_c1:
            pnl_color = "text-green" if net_pnl >= 0 else "text-red"
            st.markdown(f"""<div class="dashboard-card"><div class="sub-stat-label">Net Profit & Loss</div><div class="big-pnl {pnl_color}">${net_pnl:,.2f}</div><div style="margin-top:10px; color:#94a3b8;">{total_trades} trades completados</div></div>""", unsafe_allow_html=True)
        with top_c2: st.markdown(f"""<div class="dashboard-card"><div class="sub-stat-label">Win Rate</div><div class="sub-stat-value">{win_rate:.1f}%</div><div style="font-size:0.8rem; color:#10b981;">{wins_count} Wins</div></div>""", unsafe_allow_html=True)
        with top_c3: st.markdown(f"""<div class="dashboard-card"><div class="sub-stat-label">Profit Factor</div><div class="sub-stat-value">{pf:.2f}</div><div style="font-size:0.8rem; color:#ef4444;">{loss_count} Losses</div></div>""", unsafe_allow_html=True)

        m1, m2, m3, m4 = st.columns(4)
        with m1: st.markdown(f"""<div class="dashboard-card"><div class="sub-stat-label">Largest Win</div><div class="sub-stat-value text-green">${largest_win:,.2f}</div></div>""", unsafe_allow_html=True)
        with m2: st.markdown(f"""<div class="dashboard-card"><div class="sub-stat-label">Largest Loss</div><div class="sub-stat-value text-red">${largest_loss:,.2f}</div></div>""", unsafe_allow_html=True)
        with m3: st.markdown(f"""<div class="dashboard-card"><div class="sub-stat-label">Best Streak</div><div class="sub-stat-value">🔥 {best_streak}</div></div>""", unsafe_allow_html=True)
        with m4: st.markdown(f"""<div class="dashboard-card"><div class="sub-stat-label">Avg Confluence</div><div class="sub-stat-value">{(df['Confluencia'].mean() if not df.empty else 0):.0f}%</div></div>""", unsafe_allow_html=True)

        st.markdown("#### 📅 Calendar")
        c_cal, c_week = st.columns([3, 1])
        d = st.session_state.get('cal_date', datetime.now())
        with c_cal:
            nc1, nc2, nc3 = st.columns([1, 6, 1])
            with nc1: 
                if st.button("◀"): st.session_state['cal_date'] = d.replace(month=d.month-1) if d.month>1 else d.replace(year=d.year-1, month=12); st.rerun()
            with nc2: st.markdown(f"<h3 style='text-align:center; margin:0;'>{d.strftime('%B %Y')}</h3>", unsafe_allow_html=True)
            with nc3: 
                if st.button("▶"): st.session_state['cal_date'] = d.replace(month=d.month+1) if d.month<12 else d.replace(year=d.year+1, month=1); st.rerun()
            html_cal, _, _ = render_cal_html(df, True)
            st.markdown(html_cal, unsafe_allow_html=True)
        with c_week:
            st.markdown("<div style='margin-top:40px;'></div>", unsafe_allow_html=True)
            st.markdown("##### Weekly Summary")
            for wk in ["Week 1", "Week 2", "Week 3", "Week 4"]:
                st.markdown(f"""<div class="dashboard-card" style="padding:10px; margin-bottom:8px; min-height:60px;"><div style="display:flex; justify-content:space-between;"><span style="color:#94a3b8; font-size:0.8rem;">{wk}</span><span style="color:#10b981; font-weight:bold;">$0.00</span></div></div>""", unsafe_allow_html=True)

    # ==========================================
    # PESTAÑA 4: MENTOR IA (REDSEÑADA)
    # ==========================================
    with tab_ai:
        if not init_ai():
            st.error("⚠️ Configura GEMINI_KEY en Secrets")
        else:
            # Layout de Chat Pro
            st.markdown("### 🧠 Mentor Inteligente")
            
            # 1. ÁREA DE CHAT (Scrollable)
            chat_container = st.container(height=500)
            
            # 2. MOSTRAR MENSAJES
            with chat_container:
                for msg in st.session_state.messages:
                    with st.chat_message(msg["role"], avatar="🦁" if msg["role"]=="assistant" else "👤"):
                        if msg.get("image"):
                            st.image(msg["image"], width=250)
                        st.markdown(msg["content"])

            # 3. ZONA DE INPUT (ESTILO COMANDO)
            st.markdown("---")
            col_upl, col_txt = st.columns([1, 4])
            
            # Uploader en un Expander para no ensuciar
            with col_upl:
                with st.popover("📸 Adjuntar", use_container_width=True):
                    img_upload = st.file_uploader("Subir Gráfico", type=['png', 'jpg'], key="chat_img")
            
            # Input de texto
            with col_txt:
                if prompt := st.chat_input("Escribe tu consulta al Mentor..."):
                    # a) Guardar mensaje usuario
                    user_msg = {"role": "user", "content": prompt, "image": img_upload}
                    st.session_state.messages.append(user_msg)
                    
                    # Mostrar inmediatamente en el chat
                    with chat_container:
                        with st.chat_message("user", avatar="👤"):
                            if img_upload: st.image(img_upload, width=250)
                            st.markdown(prompt)

                    # b) Pensar y Responder
                    with chat_container:
                        with st.chat_message("assistant", avatar="🦁"):
                            with st.spinner("Analizando gráfico y datos..."):
                                response = chat_with_mentor(prompt, df, img_upload)
                                st.markdown(response)
                    
                    # c) Guardar respuesta
                    st.session_state.messages.append({"role": "assistant", "content": response, "image": None})
                    st.rerun() # Refrescar para limpiar uploader si se usó

if 'user' not in st.session_state: st.session_state.user = None
if st.session_state.user: main_app()
else: login_screen()
