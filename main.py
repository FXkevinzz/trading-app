import streamlit as st
import pandas as pd
from datetime import datetime
from modules.styles import inject_theme
from modules.data import (
    init_filesystem, verify_user, register_user, get_user_accounts, 
    get_balance_data, OFFICIAL_PAIRS
)
from modules.ui import modal_new_trade, modal_update_trade
from modules.utils import get_market_status, render_cal_html
from modules.ai import init_ai, chat_with_mentor # Importamos el chat

# 1. CONFIG
st.set_page_config(page_title="Trading Pro Suite", layout="wide", page_icon="🦁")
init_filesystem()

# 2. LOGIN
def login_screen():
    inject_theme("Oscuro (Cyber Navy)")
    c1,c2,c3 = st.columns([1,1,1])
    with c2:
        st.markdown("<h1 style='text-align:center; color:var(--accent);'>🦁 Trading Suite AI</h1>", unsafe_allow_html=True)
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
    inject_theme("Oscuro (Cyber Navy)")
    
    # Inicializar historial de chat si no existe
    if "messages" not in st.session_state:
        st.session_state.messages = []
        # Mensaje de bienvenida del mentor
        st.session_state.messages.append({"role": "assistant", "content": "Hola, trader. Soy tu Mentor IA. He revisado tu bitácora. ¿En qué te puedo ayudar hoy? ¿Psicología, análisis o revisión de trades?"})

    with st.sidebar:
        st.title(f"👤 {user.upper()}")
        accs = get_user_accounts(user)
        sel_acc = st.selectbox("Cuenta", accs)
        ini, act, df = get_balance_data(user, sel_acc)
        
        # Balance Card
        pnl_total = act - ini
        color_pnl = "#10b981" if pnl_total >= 0 else "#ef4444"
        st.markdown(f"""
        <div style="background:var(--bg-card); padding:15px; border-radius:12px; border:1px solid var(--border-color); text-align:center;">
            <div style="color:var(--text-muted); font-size:0.8rem;">BALANCE</div>
            <div style="color:#fff; font-size:1.8rem; font-weight:bold">${act:,.2f}</div>
            <div style="color:{color_pnl}; font-size:1rem;">{'+' if pnl_total>0 else ''}{pnl_total:,.2f}</div>
        </div>""", unsafe_allow_html=True)
        
        st.markdown("---")
        if st.button("Cerrar Sesión"): st.session_state.user = None; st.rerun()

    # --- DEFINICIÓN DE LAS 4 PESTAÑAS (ORDEN NUEVO) ---
    tab_op, tab_hist, tab_dash, tab_ai = st.tabs(["🚀 OPERATIVA", "📜 HISTORIAL", "📊 DASHBOARD", "🧠 MENTOR IA"])

    # ==========================================
    # PESTAÑA 1: OPERATIVA (TU CHECKLIST ORIGINAL)
    # ==========================================
    with tab_op:
        # Configuración Superior
        c_mod = st.columns([1,2,1])
        with c_mod[1]: 
            global_mode = st.radio("", ["Swing (W-D-4H)", "Scalping (4H-2H-1H)"], horizontal=True, label_visibility="collapsed")
        
        c_sel, c_info = st.columns([1, 2])
        with c_sel:
            curr_pair = st.selectbox("ACTIVO", OFFICIAL_PAIRS)
        with c_info:
            time_str, sess, status, col_st = get_market_status()
            st.markdown(f"<div style='margin-top:10px;'><b>Sesión:</b> {sess} | <b>Estado:</b> <span style='color:{col_st}'><b>{status}</b></span></div>", unsafe_allow_html=True)

        st.markdown("---")

        r1_c1, r1_c2 = st.columns(2)
        r2_c1, r2_c2 = st.columns(2)
        total = 0
        sos, eng, rr = False, False, False

        def header(t): return f"<div class='strategy-header'>{t}</div>"

        # LÓGICA ORIGINAL RESTAURADA
        if "Swing" in global_mode:
            with r1_c1:
                st.markdown('<div class="strategy-box">', unsafe_allow_html=True)
                st.markdown(header("1. CONTEXTO SEMANAL (W)"), unsafe_allow_html=True)
                tw = st.selectbox("Tendencia W", ["Alcista", "Bajista"], key="tw")
                w_sc = sum([
                    st.checkbox("Rechazo AOI (+10%)", key="w1")*10,
                    st.checkbox("Rechazo Estructura Previa (+10%)", key="w2")*10,
                    st.checkbox("Patrón de Vela Rechazo (+10%)", key="w3")*10,
                    st.checkbox("Patrón Mercado (+10%)", key="w4")*10,
                    st.checkbox("EMA 50 (+5%)", key="w5")*5,
                    st.checkbox("Nivel Psicológico (+5%)", key="w6")*5
                ])
                st.markdown('</div>', unsafe_allow_html=True)
            with r1_c2:
                st.markdown('<div class="strategy-box">', unsafe_allow_html=True)
                st.markdown(header("2. CONTEXTO DIARIO (D)"), unsafe_allow_html=True)
                td = st.selectbox("Tendencia D", ["Alcista", "Bajista"], key="td")
                d_sc = sum([
                    st.checkbox("Rechazo AOI (+10%)", key="d1")*10,
                    st.checkbox("Rechazo Estructura Previa (+10%)", key="d2")*10,
                    st.checkbox("Patrón de Vela Rechazo (+10%)", key="d3")*10,
                    st.checkbox("Patrón Mercado (+10%)", key="d4")*10,
                    st.checkbox("EMA 50 (+5%)", key="d5")*5
                ])
                st.markdown('</div>', unsafe_allow_html=True)
            with r2_c1:
                st.markdown('<div class="strategy-box" style="margin-top:20px">', unsafe_allow_html=True)
                st.markdown(header("3. EJECUCIÓN (4H)"), unsafe_allow_html=True)
                t4 = st.selectbox("Tendencia 4H", ["Alcista", "Bajista"], key="t4")
                h4_sc = sum([
                    st.checkbox("Rechazo Vela (+10%)", key="h1")*10,
                    st.checkbox("Patrón Mercado (+10%)", key="h2")*10,
                    st.checkbox("Rechazo Estructura Previa (+5%)", key="h3")*5,
                    st.checkbox("EMA 50 (+5%)", key="h4")*5
                ])
                st.markdown('</div>', unsafe_allow_html=True)
            with r2_c2:
                st.markdown('<div class="strategy-box" style="margin-top:20px">', unsafe_allow_html=True)
                st.markdown(header("4. GATILLO FINAL"), unsafe_allow_html=True)
                if tw==td==t4: st.success("💎 TRIPLE ALINEACIÓN")
                sos = st.checkbox("⚡ SOS (Obligatorio)")
                eng = st.checkbox("🕯️ Envolvente (Obligatorio)")
                pat_ent = st.checkbox("Patrón en Entrada (+5%)")
                rr = st.checkbox("💰 Ratio > 1:2.5")
                entry_score = (10 if sos else 0) + (10 if eng else 0) + (5 if pat_ent else 0)
                total = w_sc + d_sc + h4_sc + entry_score

        else: # SCALPING
            with r1_c1:
                st.markdown('<div class="strategy-box">', unsafe_allow_html=True)
                st.markdown(header("1. CONTEXTO (4H)"), unsafe_allow_html=True)
                t4 = st.selectbox("Trend 4H", ["Alcista", "Bajista"], key="s4")
                w_sc = sum([st.checkbox("AOI", key="s1")*10, st.checkbox("Estructura", key="s2")*10]) 
                st.markdown('</div>', unsafe_allow_html=True)
            total = w_sc 

        st.markdown("<br>", unsafe_allow_html=True)
        valid = sos and eng and rr
        msg, css_cl = "💤 ESPERAR", "status-warning"
        
        if total >= 90: msg, css_cl = "💎 SNIPER ENTRY", "status-sniper"
        elif total >= 60: msg, css_cl = "✅ VÁLIDO", "status-sniper"
        
        st.markdown(f"""
        <div class="hud-container">
            <div class="hud-stat"><div class="hud-label">PUNTAJE</div><div class="hud-value-large">{total}%</div></div>
            <div style="flex-grow:1; text-align:center; margin:0 20px;"><span class="{css_cl}">{msg}</span></div>
        </div>
        """, unsafe_allow_html=True)
        st.progress(min(total, 100))

        if st.button("🚀 EJECUTAR TRADE", type="primary" if total >= 60 else "secondary", use_container_width=True):
            modal_new_trade(user, sel_acc, global_mode, curr_pair, total)

    # ==========================================
    # PESTAÑA 2: HISTORIAL
    # ==========================================
    with tab_hist:
        if not df.empty:
            f1, f2 = st.columns([2, 1])
            with f1: f_pair = st.text_input("Buscar Activo", placeholder="EURUSD...")
            with f2: f_res = st.multiselect("Resultado", ["WIN", "LOSS", "BE", "PENDING"])
            
            df_view = df.copy()
            if f_pair: df_view = df_view[df_view['Par'].str.contains(f_pair.upper())]
            if f_res: df_view = df_view[df_view['Resultado'].isin(f_res)]
            
            st.dataframe(
                df_view[['Fecha', 'Par', 'Direccion', 'Status', 'Resultado', 'Dinero', 'Confluencia']],
                use_container_width=True, hide_index=True,
                column_config={
                    "Dinero": st.column_config.NumberColumn(format="$%.2f"),
                    "Confluencia": st.column_config.ProgressColumn(format="%d%%", min_value=0, max_value=100)
                }
            )
            tr_idx = st.selectbox("Seleccionar Trade:", df_view.index, format_func=lambda x: f"#{x} {df_view.loc[x,'Par']}")
            if st.button("📂 GESTIONAR TRADE"):
                modal_update_trade(user, sel_acc, tr_idx, df.loc[tr_idx])
        else:
            st.info("Historial vacío.")

    # ==========================================
    # PESTAÑA 3: DASHBOARD (MOVIDO AQUÍ)
    # ==========================================
    with tab_dash:
        st.markdown("### 📈 Rendimiento General")
        
        # Cálculos (Iguales que antes)
        net_pnl = 0; total_wins = 0; total_loss = 0; win_rate = 0; profit_factor = 0; gross_profit = 0; gross_loss = 0
        if not df.empty:
            net_pnl = df['Dinero'].sum()
            wins = df[df['Resultado'] == 'WIN']; losses = df[df['Resultado'] == 'LOSS']
            gross_profit = wins['Dinero'].sum(); gross_loss = abs(losses['Dinero'].sum())
            total_wins = len(wins); total_loss = len(losses)
            total_closed = len(df[df['Status'] == 'CLOSED'])
            if total_closed > 0: win_rate = (total_wins / total_closed) * 100
            if gross_loss > 0: profit_factor = gross_profit / gross_loss
            else: profit_factor = gross_profit

        # Tarjetas Dashboard
        col_main, col_side = st.columns([2, 1])
        with col_main:
            bg_color = "rgba(16, 185, 129, 0.1)" if net_pnl >= 0 else "rgba(239, 68, 68, 0.1)"
            text_color = "#10b981" if net_pnl >= 0 else "#ef4444"
            st.markdown(f"""
            <div style="background:var(--bg-card); border:1px solid var(--border-color); border-radius:12px; padding:20px; display:flex; justify-content:space-between; align-items:center;">
                <div><div style="color:var(--text-muted); font-size:0.9rem;">Net PnL</div><div style="font-size:2.5rem; font-weight:900; color:{text_color};">${net_pnl:,.2f}</div></div>
                <div><div style="background:{bg_color}; color:{text_color}; padding:5px 15px; border-radius:20px; font-weight:bold;">{profit_factor:.2f} PF</div></div>
            </div>""", unsafe_allow_html=True)
            
            c1, c2, c3 = st.columns(3)
            with c1: st.markdown(f"<div style='background:var(--bg-card); padding:10px; border-radius:10px; margin-top:10px; text-align:center;'>Win Rate<br><b>{win_rate:.1f}%</b></div>", unsafe_allow_html=True)
            with c2: st.markdown(f"<div style='background:var(--bg-card); padding:10px; border-radius:10px; margin-top:10px; text-align:center;'>Trades<br><b>{len(df)}</b></div>", unsafe_allow_html=True)
            with c3: st.markdown(f"<div style='background:var(--bg-card); padding:10px; border-radius:10px; margin-top:10px; text-align:center;'>Wins<br><b>{total_wins}</b></div>", unsafe_allow_html=True)

        with col_side:
            st.markdown(f"""
            <div style="background:var(--bg-card); border:1px solid var(--border-color); border-radius:12px; padding:15px; margin-bottom:10px;">
                <div style="color:#10b981;">Total Profit: <b>${gross_profit:,.2f}</b></div>
            </div>
            <div style="background:var(--bg-card); border:1px solid var(--border-color); border-radius:12px; padding:15px;">
                <div style="color:#ef4444;">Total Loss: <b>-${gross_loss:,.2f}</b></div>
            </div>""", unsafe_allow_html=True)

        # Calendario
        st.markdown("#### 📅 Calendario de PnL")
        dc1, dc2, dc3 = st.columns([1, 4, 1])
        d = st.session_state.get('cal_date', datetime.now())
        with dc1: 
            if st.button("◀"): st.session_state['cal_date'] = d.replace(month=d.month-1) if d.month>1 else d.replace(year=d.year-1, month=12); st.rerun()
        with dc2: st.markdown(f"<h5 style='text-align:center; margin:0;'>{d.strftime('%B %Y')}</h5>", unsafe_allow_html=True)
        with dc3: 
            if st.button("▶"): st.session_state['cal_date'] = d.replace(month=d.month+1) if d.month<12 else d.replace(year=d.year+1, month=1); st.rerun()
        html_cal, _, _ = render_cal_html(df, True)
        st.markdown(html_cal, unsafe_allow_html=True)

    # ==========================================
    # PESTAÑA 4: MENTOR IA (CHAT EN VIVO)
    # ==========================================
    with tab_ai:
        st.markdown("### 🧠 Mentor IA (Set & Forget)")
        st.caption("Pregúntame sobre tus trades, psicología o si estás siguiendo las reglas.")
        
        # Verificar API Key
        if not init_ai():
            st.error("⚠️ Falta configurar la API Key de Gemini en Secrets.")
        else:
            # Contenedor del chat
            chat_container = st.container(height=400)
            
            # Mostrar historial
            with chat_container:
                for msg in st.session_state.messages:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])

            # Input del usuario
            if prompt := st.chat_input("Escribe tu pregunta al Mentor..."):
                # 1. Guardar y mostrar mensaje usuario
                st.session_state.messages.append({"role": "user", "content": prompt})
                with chat_container:
                    with st.chat_message("user"):
                        st.markdown(prompt)

                # 2. Generar respuesta IA
                with chat_container:
                    with st.chat_message("assistant"):
                        with st.spinner("El Mentor está analizando tu diario..."):
                            # Llamamos a la función del módulo AI pasando el historial de trades
                            response_text = chat_with_mentor(prompt, df)
                            st.markdown(response_text)
                
                # 3. Guardar respuesta IA
                st.session_state.messages.append({"role": "assistant", "content": response_text})

if 'user' not in st.session_state: st.session_state.user = None
if st.session_state.user: main_app()
else: login_screen()
