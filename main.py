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
        mode = st.radio("Estrategia", ["Swing (W-D-4H)", "Scalping (4H-1H-15m)"])
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

    tab_op, tab_hist = st.tabs(["🚀 OPERATIVA (CHECKLIST)", "📜 HISTORY / JOURNAL"])

    # --- PESTAÑA OPERATIVA CON CHECKLIST RESTAURADO ---
    with tab_op:
        # Selector de activo
        curr_pair = st.selectbox("ACTIVO A OPERAR", OFFICIAL_PAIRS)
        
        st.markdown('<div class="strategy-box">', unsafe_allow_html=True)
        
        # --- LÓGICA DEL CHECKLIST (Adaptada al modo) ---
        c1, c2 = st.columns(2)
        total_score = 0
        
        if "Swing" in mode:
            with c1:
                st.caption("CONTEXTO MACRO (Semanal/Diario)")
                s1 = sum([st.checkbox("Tendencia W/D Alineada", key="sw1")*20,
                          st.checkbox("Rechazo Zona AOI", key="sw2")*20,
                          st.checkbox("Patrón de Vela Macro", key="sw3")*10])
            with c2:
                st.caption("GATILLO (4H)")
                s2 = sum([st.checkbox("SOS (Quiebre Estructura)", key="sw4")*20,
                          st.checkbox("Vela Envolvente / Pinbar", key="sw5")*20,
                          st.checkbox("Ratio > 1:2.5", key="sw6")*10])
            total_score = s1 + s2
        else: # Scalping
            with c1:
                st.caption("CONTEXTO (4H / 1H)")
                s1 = sum([st.checkbox("Tendencia 4H/1H", key="sc1")*20,
                          st.checkbox("Zona de Demanda/Oferta", key="sc2")*20,
                          st.checkbox("Liquidez Previa Tomada", key="sc3")*10])
            with c2:
                st.caption("GATILLO (15m)")
                s2 = sum([st.checkbox("Change of Character (ChoCH)", key="sc4")*20,
                          st.checkbox("Order Block Valido", key="sc5")*20,
                          st.checkbox("Entrada por Confirmación", key="sc6")*10])
            total_score = s1 + s2

        st.markdown('</div>', unsafe_allow_html=True)
        
        # VISUALIZACIÓN DEL PUNTAJE
        st.markdown("<br>", unsafe_allow_html=True)
        col_bar, col_btn = st.columns([3, 1])
        
        with col_bar:
            # HUD Visual
            msg_cls = "status-stop" if total_score < 60 else "status-warning" if total_score < 80 else "status-sniper"
            msg_txt = "⛔ NO OPERAR" if total_score < 60 else "⚠️ RIESGO MEDIO" if total_score < 80 else "💎 SNIPER ENTRY"
            st.markdown(f"""
            <div style="display:flex; align-items:center; gap:15px;">
                <div style="font-size:2rem; font-weight:900;">{total_score}%</div>
                <div class="{msg_cls}" style="flex-grow:1; text-align:center;">{msg_txt}</div>
            </div>
            """, unsafe_allow_html=True)
            st.progress(total_score)

        with col_btn:
            # EL BOTÓN MÁGICO
            # Solo se habilita (visualmente sugerido) si hay puntaje, pero dejamos hacer click siempre por libertad
            btn_label = "🚀 EJECUTAR" if total_score >= 60 else "Forzar Entrada"
            btn_type = "primary" if total_score >= 60 else "secondary"
            
            if st.button(btn_label, type=btn_type, use_container_width=True):
                # AQUÍ CONECTAMOS: Lanza el modal y le pasa el puntaje calculado
                modal_new_trade(user, sel_acc, mode, curr_pair, total_score)

    # --- PESTAÑA HISTORIAL ---
    with tab_hist:
        if not df.empty:
            st.dataframe(
                df[['Fecha', 'Par', 'Direccion', 'Status', 'Resultado', 'Dinero', 'Confluencia']],
                use_container_width=True, hide_index=True,
                column_config={"Dinero": st.column_config.NumberColumn(format="$%.2f"), "Confluencia": st.column_config.ProgressColumn(format="%d%%", min_value=0, max_value=100)}
            )
            # Selector de Edición
            tr_idx = st.selectbox("Seleccionar Trade para Gestionar:", df.index, format_func=lambda x: f"#{x} {df.loc[x,'Par']} ({df.loc[x,'Status']})")
            if st.button("📂 GESTIONAR TRADE"):
                modal_update_trade(user, sel_acc, tr_idx, df.loc[tr_idx])
        else:
            st.info("Historial vacío.")

if 'user' not in st.session_state: st.session_state.user = None
if st.session_state.user: main_app()
else: login_screen()
