import streamlit as st
import pandas as pd
from datetime import datetime
from modules.styles import inject_theme
from modules.data import (
    init_filesystem, verify_user, register_user, get_user_accounts, 
    get_balance_data, OFFICIAL_PAIRS
)
from modules.ui import modal_new_trade, modal_update_trade
from modules.utils import get_market_status

# 1. CONFIGURACIÓN
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
        # Selector de Modo basado en el PDF
        mode = st.radio("Estrategia (Cheat Sheet)", ["Swing (W + D + 4H)", "Intraday (D + 4H)", "Scalping (4H + 2H + 1H)"])
        
        if st.button("Cerrar Sesión"): st.session_state.user = None; st.rerun()

    # DASHBOARD SUPERIOR
    st.markdown("### 📊 Dashboard Ejecutivo")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    win_rate = 0
    if not df.empty:
        closed = df[df['Status'] == 'CLOSED']
        wins = len(closed[closed['Resultado'] == 'WIN'])
        if len(closed) > 0: win_rate = (wins / len(closed)) * 100
        with kpi1: st.metric("Win Rate", f"{win_rate:.1f}%")
        with kpi2: st.metric("Trades Totales", len(df))
        with kpi3: st.metric("Mejor Trade", f"${df['Dinero'].max():,.0f}" if not df.empty else "$0")
        with kpi4: st.metric("Peor Trade", f"${df['Dinero'].min():,.0f}" if not df.empty else "$0")

    tab_op, tab_hist = st.tabs(["🚀 OPERATIVA (CHECKLIST OFICIAL)", "📜 HISTORIAL"])

    # --- PESTAÑA OPERATIVA: CHECKLIST DEL PDF ---
    with tab_op:
        # 1. Configuración Inicial
        c_sel, c_info = st.columns([1, 2])
        with c_sel:
            curr_pair = st.selectbox("ACTIVO", OFFICIAL_PAIRS)
        with c_info:
            time_str, sess, status, col_st = get_market_status()
            st.markdown(f"""
            <div style="margin-top: 10px;">
                <b>Sesión:</b> {sess} | <b>Estado:</b> <span style='color:{col_st}'><b>{status}</b></span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<div class="strategy-box">', unsafe_allow_html=True)
        st.markdown(f"<h4 style='color:var(--accent); border-bottom:1px solid var(--border-color); padding-bottom:5px;'>📋 CONFLUENCIAS: {mode.upper()}</h4>", unsafe_allow_html=True)
        
        total_score = 0
        
        # === LÓGICA SWING (W + D + 4H) - Páginas 31-32 del PDF ===
        if "Swing" in mode:
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                st.markdown("**1. CONTEXTO MACRO (W/D)**")
                # Semanal / Diario Mix
                s_w_aoi = st.checkbox("Rechazo W AOI (+10%)") 
                s_d_aoi = st.checkbox("Rechazo D AOI (+10%)")
                s_w_ema = st.checkbox("Rechazo W 50 EMA (+5%)")
                s_d_ema = st.checkbox("Rechazo D 50 EMA (+5%)")
                s_psych = st.checkbox("Nivel Psicológico Redondo (+5%)")
                
                score_a = (10 if s_w_aoi else 0) + (10 if s_d_aoi else 0) + \
                          (5 if s_w_ema else 0) + (5 if s_d_ema else 0) + (5 if s_psych else 0)

            with col_b:
                st.markdown("**2. ESTRUCTURA & PATRONES**")
                s_w_str = st.checkbox("Rechazo Estructura Previa W (+10%)")
                s_d_str = st.checkbox("Rechazo Estructura Previa D (+10%)")
                s_w_cnd = st.checkbox("Rechazo Vela W (+10%)")
                s_d_cnd = st.checkbox("Rechazo Vela D (+10%)")
                s_pat = st.checkbox("Patrón (H&S, Doble Suelo/Techo) (+10%)")
                
                score_b = (10 if s_w_str else 0) + (10 if s_d_str else 0) + \
                          (10 if s_w_cnd else 0) + (10 if s_d_cnd else 0) + (10 if s_pat else 0)

            with col_c:
                st.markdown("**3. EJECUCIÓN (4H)**")
                s_4h_ema = st.checkbox("4H 50 EMA (+5%)")
                s_4h_cnd = st.checkbox("4H Rechazo Vela (+10%)")
                s_4h_str = st.checkbox("4H Rechazo Estructura (+5%)")
                s_4h_pat = st.checkbox("4H Patrón (+10%)")
                
                score_c = (5 if s_4h_ema else 0) + (10 if s_4h_cnd else 0) + \
                          (5 if s_4h_str else 0) + (10 if s_4h_pat else 0)
            
            total_score = score_a + score_b + score_c

        # === LÓGICA INTRADAY (D + 4H) - Página 32 del PDF ===
        elif "Intraday" in mode:
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("**1. CONTEXTO DIARIO (D)**")
                i_d_aoi = st.checkbox("Rechazo D AOI (+10%)")
                i_d_ema = st.checkbox("Rechazo D 50 EMA (+5%)")
                i_psych = st.checkbox("Nivel Psicológico (+5%)")
                i_d_str = st.checkbox("Rechazo Estructura Previa D (+10%)")
                i_d_cnd = st.checkbox("Rechazo Vela D (+10%)")
                i_d_pat = st.checkbox("Patrón D (+10%)")
                
                score_a = (10 if i_d_aoi else 0) + (5 if i_d_ema else 0) + (5 if i_psych else 0) + \
                          (10 if i_d_str else 0) + (10 if i_d_cnd else 0) + (10 if i_d_pat else 0)

            with col_b:
                st.markdown("**2. CONTEXTO 4H**")
                i_4_aoi = st.checkbox("Rechazo 4H AOI (+5%)")
                i_4_ema = st.checkbox("Rechazo 4H 50 EMA (+5%)")
                i_4_str = st.checkbox("Rechazo Estructura Previa 4H (+5%)")
                i_4_cnd = st.checkbox("Rechazo Vela 4H (+10%)")
                i_4_pat = st.checkbox("Patrón 4H (+10%)")
                
                score_b = (5 if i_4_aoi else 0) + (5 if i_4_ema else 0) + (5 if i_4_str else 0) + \
                          (10 if i_4_cnd else 0) + (10 if i_4_pat else 0)
            
            total_score = score_a + score_b

        # === LÓGICA SCALPING (4H + 2H + 1H) - Página 33 del PDF ===
        else:
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.markdown("**1. CONTEXTO 4H**")
                sc_4_aoi = st.checkbox("4H AOI (+5%)")
                sc_4_ema = st.checkbox("4H 50 EMA (+5%)")
                sc_psy = st.checkbox("Psicológico (+5%)")
                sc_4_str = st.checkbox("4H Estructura (+5%)")
                sc_4_cnd = st.checkbox("4H Vela (+5%)")
                
                score_a = (5 if sc_4_aoi else 0) + (5 if sc_4_ema else 0) + (5 if sc_psy else 0) + \
                          (5 if sc_4_str else 0) + (5 if sc_4_cnd else 0)

            with col_b:
                st.markdown("**2. CONTEXTO 2H**")
                sc_2_aoi = st.checkbox("2H AOI (+5%)")
                sc_2_ema = st.checkbox("2H 50 EMA (+5%)")
                sc_2_str = st.checkbox("2H Estructura (+5%)")
                sc_2_cnd = st.checkbox("2H Vela (+5%)")
                
                score_b = (5 if sc_2_aoi else 0) + (5 if sc_2_ema else 0) + \
                          (5 if sc_2_str else 0) + (5 if sc_2_cnd else 0)

            with col_c:
                st.markdown("**3. CONTEXTO 1H**")
                sc_1_aoi = st.checkbox("1H AOI (+5%)")
                sc_1_ema = st.checkbox("1H 50 EMA (+5%)")
                sc_1_str = st.checkbox("1H Estructura (+5%)")
                sc_1_cnd = st.checkbox("1H Vela (+5%)")
                
                score_c = (5 if sc_1_aoi else 0) + (5 if sc_1_ema else 0) + \
                          (5 if sc_1_str else 0) + (5 if sc_1_cnd else 0)
            
            total_score = score_a + score_b + score_c

        st.markdown("---")
        
        # === GATILLO DE ENTRADA (MANDATORIOS DEL PDF) ===
        st.markdown("##### 🔫 GATILLO DE ENTRADA (Obligatorios)")
        c_trig1, c_trig2, c_trig3 = st.columns(3)
        with c_trig1: 
            trig_sos = st.checkbox("⚡ Cambio de Estructura (SOS) (+10%)")
        with c_trig2: 
            trig_eng = st.checkbox("🕯️ Vela Envolvente (+10%)")
        with c_trig3:
            trig_rr = st.checkbox("💰 Ratio Riesgo/Beneficio > 1:2.5")
            
        trig_pat = st.checkbox("Patrón de Entrada (+5%)")
        
        entry_score = (10 if trig_sos else 0) + (10 if trig_eng else 0) + (5 if trig_pat else 0)
        final_total = total_score + entry_score
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # --- VISUALIZACIÓN DEL PUNTAJE Y BOTÓN ---
        st.markdown("<br>", unsafe_allow_html=True)
        col_bar, col_btn = st.columns([3, 1])
        
        # Validaciones del PDF
        is_valid = trig_sos and trig_eng and trig_rr
        
        with col_bar:
            # Lógica de Calificación del PDF (Página 37)
            grade = "F"
            if final_total >= 90: grade = "A (90%+)"
            elif final_total >= 80: grade = "B (80%+)"
            elif final_total >= 70: grade = "C (70%+)"
            elif final_total >= 60: grade = "D (60%+)"
            
            msg_cls = "status-stop"
            if final_total >= 60 and is_valid: msg_cls = "status-warning"
            if final_total >= 80 and is_valid: msg_cls = "status-sniper"
            
            # Si faltan los obligatorios, mostramos error aunque el puntaje sea alto
            if not is_valid:
                msg_txt = "⛔ FALTAN REGLAS DE ORO (SOS/VELA/RR)"
                msg_cls = "status-stop"
            else:
                msg_txt = f"CALIFICACIÓN: {grade}"

            st.markdown(f"""
            <div style="display:flex; align-items:center; gap:15px;">
                <div style="font-size:2.5rem; font-weight:900; color:var(--text-main);">{final_total}%</div>
                <div class="{msg_cls}" style="flex-grow:1; text-align:center; font-size:1.1rem;">{msg_txt}</div>
            </div>
            """, unsafe_allow_html=True)
            st.progress(min(final_total, 100))

        with col_btn:
            # BOTÓN DE EJECUCIÓN
            # Se permite hacer click siempre, pero visualmente te avisa
            btn_type = "primary" if (is_valid and final_total >= 60) else "secondary"
            if st.button("🚀 EJECUTAR TRADE", type=btn_type, use_container_width=True):
                modal_new_trade(user, sel_acc, mode, curr_pair, final_total)

    # --- PESTAÑA HISTORIAL ---
    with tab_hist:
        if not df.empty:
            # Filtros básicos
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
            # Selector de Edición
            tr_idx = st.selectbox("Seleccionar Trade para Gestionar:", df_view.index, format_func=lambda x: f"#{x} {df_view.loc[x,'Par']} ({df_view.loc[x,'Status']})")
            if st.button("📂 GESTIONAR TRADE SELECCIONADO"):
                modal_update_trade(user, sel_acc, tr_idx, df.loc[tr_idx])
        else:
            st.info("Historial vacío.")

if 'user' not in st.session_state: st.session_state.user = None
if st.session_state.user: main_app()
else: login_screen()
