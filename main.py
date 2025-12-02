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
        
        # Balance
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

    # DASHBOARD
    st.markdown("### 📊 Dashboard Ejecutivo")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    win_rate = 0
    if not df.empty:
        closed = df[df['Status'] == 'CLOSED']
        wins = len(closed[closed['Resultado'] == 'WIN'])
        if len(closed) > 0: win_rate = (wins / len(closed)) * 100
        with kpi1: st.metric("Win Rate", f"{win_rate:.1f}%")
        with kpi2: st.metric("Trades", len(df))
        with kpi3: st.metric("Mejor Trade", f"${df['Dinero'].max():,.0f}" if not df.empty else "$0")
        with kpi4: st.metric("Peor Trade", f"${df['Dinero'].min():,.0f}" if not df.empty else "$0")

    # --- PESTAÑAS PRINCIPALES ---
    tab_op, tab_hist = st.tabs(["🚀 OPERATIVA (TU ESTRATEGIA)", "📜 HISTORIAL"])

    # 1. PESTAÑA OPERATIVA (RECUPERADA AL 100%)
    with tab_op:
        # Configuración Superior
        c_mod = st.columns([1,2,1])
        with c_mod[1]: 
            # Selector de Modo Original
            global_mode = st.radio("", ["Swing (W-D-4H)", "Scalping (4H-2H-1H)"], horizontal=True, label_visibility="collapsed")
        
        c_sel, c_info = st.columns([1, 2])
        with c_sel:
            curr_pair = st.selectbox("ACTIVO", OFFICIAL_PAIRS)
        with c_info:
            time_str, sess, status, col_st = get_market_status()
            st.markdown(f"<div style='margin-top:10px;'><b>Sesión:</b> {sess} | <b>Estado:</b> <span style='color:{col_st}'><b>{status}</b></span></div>", unsafe_allow_html=True)

        st.markdown("---")

        # --- AQUÍ ESTÁ TU LÓGICA ORIGINAL RECUPERADA ---
        r1_c1, r1_c2 = st.columns(2)
        r2_c1, r2_c2 = st.columns(2)
        total = 0
        sos, eng, rr = False, False, False

        def header(t): return f"<div class='strategy-header'>{t}</div>"

        # LÓGICA SWING ORIGINAL
        if "Swing" in global_mode:
            # SEMANAL
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
            
            # DIARIO
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

            # 4 HORAS
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
            
            # GATILLO
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

        # LÓGICA SCALPING ORIGINAL
        else: 
            with r1_c1:
                st.markdown('<div class="strategy-box">', unsafe_allow_html=True)
                st.markdown(header("1. CONTEXTO (4H)"), unsafe_allow_html=True)
                t4 = st.selectbox("Trend 4H", ["Alcista", "Bajista"], key="s4")
                w_sc = sum([
                    st.checkbox("AOI (+5%)", key="sc1")*5, st.checkbox("Rechazo Estructura (+5%)", key="sc2")*5,
                    st.checkbox("Patrón (+5%)", key="sc3")*5, st.checkbox("EMA 50 (+5%)", key="sc4")*5,
                    st.checkbox("Psicológico (+5%)", key="sc5")*5
                ])
                st.markdown('</div>', unsafe_allow_html=True)
            with r1_c2:
                st.markdown('<div class="strategy-box">', unsafe_allow_html=True)
                st.markdown(header("2. CONTEXTO (2H)"), unsafe_allow_html=True)
                t2 = st.selectbox("Trend 2H", ["Alcista", "Bajista"], key="s2t")
                d_sc = sum([
                    st.checkbox("AOI (+5%)", key="s21")*5, st.checkbox("Rechazo Estructura (+5%)", key="s22")*5,
                    st.checkbox("Vela (+5%)", key="s23")*5, st.checkbox("Patrón (+5%)", key="s24")*5,
                    st.checkbox("EMA 50 (+5%)", key="s25")*5
                ])
                st.markdown('</div>', unsafe_allow_html=True)
            with r2_c1:
                st.markdown('<div class="strategy-box" style="margin-top:20px">', unsafe_allow_html=True)
                st.markdown(header("3. EJECUCIÓN (1H)"), unsafe_allow_html=True)
                t1 = st.selectbox("Trend 1H", ["Alcista", "Bajista"], key="s1t")
                h4_sc = sum([
                    st.checkbox("Vela (+5%)", key="s31")*5, st.checkbox("Patrón (+5%)", key="s32")*5,
                    st.checkbox("Rechazo Estructura (+5%)", key="s33")*5, st.checkbox("EMA 50 (+5%)", key="s34")*5
                ])
                st.markdown('</div>', unsafe_allow_html=True)
            with r2_c2:
                st.markdown('<div class="strategy-box" style="margin-top:20px">', unsafe_allow_html=True)
                st.markdown(header("4. GATILLO (M15)"), unsafe_allow_html=True)
                if t4==t2==t1: st.success("💎 TRIPLE ALINEACIÓN")
                sos = st.checkbox("⚡ SOS"); eng = st.checkbox("🕯️ Vela Entrada")
                pat_ent = st.checkbox("Patrón Entrada (+5%)"); rr = st.checkbox("💰 Ratio")
                entry_score = sum([sos*10, eng*10, pat_ent*5])
                total = w_sc + d_sc + h4_sc + entry_score + 15

        # --- BARRA DE PUNTAJE Y BOTÓN DE EJECUCIÓN ---
        st.markdown("<br>", unsafe_allow_html=True)
        valid = sos and eng and rr
        msg, css_cl = "💤 ESPERAR", "status-warning"
        
        # Lógica de Estado Original
        if not sos: msg, css_cl = "⛔ FALTA SOS", "status-stop"
        elif not eng: msg, css_cl = "⚠️ FALTA VELA", "status-warning"
        elif total >= 90: msg, css_cl = "💎 SNIPER ENTRY", "status-sniper"
        elif total >= 60 and valid: msg, css_cl = "✅ VÁLIDO", "status-sniper"
        
        # HUD DE PUNTAJE
        st.markdown(f"""
        <div class="hud-container">
            <div class="hud-stat"><div class="hud-label">PUNTAJE</div><div class="hud-value-large">{total}%</div></div>
            <div style="flex-grow:1; text-align:center; margin:0 20px;"><span class="{css_cl}">{msg}</span></div>
        </div>
        """, unsafe_allow_html=True)
        st.progress(min(total, 100))

        # BOTÓN PARA ABRIR EL MODAL DE REGISTRO
        # Solo sugerimos ejecutar si el puntaje es decente, pero dejamos el botón activo
        if st.button("🚀 EJECUTAR TRADE", type="primary" if total >= 60 else "secondary", use_container_width=True):
            modal_new_trade(user, sel_acc, global_mode, curr_pair, total)

    # --- PESTAÑA HISTORIAL ---
    with tab_hist:
        if not df.empty:
            # Filtros
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
