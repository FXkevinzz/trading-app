import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import os

# Módulos Propios
from modules.styles import inject_theme
from modules.data import (
    init_filesystem, verify_user, register_user, get_user_accounts, 
    create_account, get_balance_data, create_backup_zip, DATA_DIR
)
from modules.ui import modal_new_trade, modal_update_trade
from modules.utils import get_market_status, render_heatmap

# 1. CONFIG
st.set_page_config(page_title="Trading Pro Suite", layout="wide", page_icon="🦁")
init_filesystem()

# 2. LOGIN (Mismo de antes)
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

# 3. APP PRINCIPAL (NUEVA ESTRUCTURA)
def main_app():
    user = st.session_state.user
    inject_theme("Oscuro (Cyber Navy)")
    
    # Sidebar Minimalista
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
            <div style="color:var(--text-muted); font-size:0.8rem;">BALANCE ACTUAL</div>
            <div style="color:#fff; font-size:1.8rem; font-weight:bold">${act:,.2f}</div>
            <div style="color:{color_pnl}; font-size:1rem;">{'+' if pnl_total>0 else ''}{pnl_total:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        mode = st.radio("Estrategia", ["Swing (W-D-4H)", "Scalping (1H-15m)"])
        
        if st.button("Cerrar Sesión"): st.session_state.user = None; st.rerun()

    # --- DASHBOARD SUPERIOR ---
    st.markdown("### 📊 Dashboard Ejecutivo")
    
    # Métricas Rápidas
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    
    win_rate = 0
    if not df.empty:
        closed_trades = df[df['Status'] == 'CLOSED']
        wins = len(closed_trades[closed_trades['Resultado'] == 'WIN'])
        total_closed = len(closed_trades)
        win_rate = (wins / total_closed * 100) if total_closed > 0 else 0
        
        with kpi1: st.metric("Win Rate", f"{win_rate:.1f}%")
        with kpi2: st.metric("Trades Totales", len(df))
        with kpi3: st.metric("Mejor Trade", f"${df['Dinero'].max():,.0f}" if not df.empty else "$0")
        with kpi4: st.metric("Peor Trade", f"${df['Dinero'].min():,.0f}" if not df.empty else "$0")

    # --- PESTAÑAS SIMPLIFICADAS ---
    tab_op, tab_hist, tab_news = st.tabs(["🚀 OPERATIVA", "📜 HISTORY / JOURNAL", "📰 NOTICIAS"])

    # 1. PESTAÑA OPERATIVA (CENTRO DE MANDO)
    with tab_op:
        # Botón Gigante de Entrada
        col_btn, col_info = st.columns([1, 2])
        with col_btn:
            if st.button("➕ REGISTRAR NUEVO TRADE", type="primary", use_container_width=True, help="Abre el modal de entrada"):
                modal_new_trade(user, sel_acc, mode)
        
        with col_info:
            time_str, sess, status, col_st = get_market_status()
            st.markdown(f"**Mercado:** <span style='color:{col_st}'>{status}</span> | **Sesión:** {sess}", unsafe_allow_html=True)

        st.markdown("##### 🟢 Trades Abiertos (En Curso)")
        if not df.empty:
            open_trades = df[df['Status'] == 'OPEN']
            if not open_trades.empty:
                for i, row in open_trades.iterrows():
                    # Tarjeta de Trade Abierto
                    with st.container():
                        c1, c2, c3, c4 = st.columns([1, 2, 2, 1])
                        c1.markdown(f"**{row['Par']}**")
                        c2.caption(f"{row['Direccion']} | {row['Fecha']}")
                        c3.info("⏳ EN PROCESO")
                        if c4.button("✏️ GESTIONAR", key=f"btn_open_{i}"):
                            modal_update_trade(user, sel_acc, i, row)
                        st.divider()
            else:
                st.info("No tienes operaciones abiertas. ¡A cazar! 🦁")
        else:
            st.info("Bitácora vacía.")

    # 2. PESTAÑA HISTORY (JOURNAL COMPACTO)
    with tab_hist:
        if not df.empty:
            # Filtros
            f_col1, f_col2 = st.columns(2)
            with f_col1: search = st.text_input("🔍 Buscar activo...", placeholder="Ej: XAUUSD")
            with f_col2: filter_res = st.multiselect("Filtrar Resultado", ["WIN", "LOSS", "BE"])
            
            # Filtrado
            df_show = df.copy()
            if search: df_show = df_show[df_show['Par'].str.contains(search.upper())]
            if filter_res: df_show = df_show[df_show['Resultado'].isin(filter_res)]
            
            # Tabla Visual
            st.dataframe(
                df_show[['Fecha', 'Par', 'Direccion', 'Status', 'Resultado', 'Dinero', 'Ratio']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Dinero": st.column_config.NumberColumn(format="$%.2f"),
                    "Resultado": st.column_config.TextColumn()
                }
            )
            
            st.markdown("### 📝 Edición Rápida")
            # Selector para editar cualquier trade
            trade_to_edit = st.selectbox("Selecciona un trade para ver detalles o editar:", df_show.index, format_func=lambda x: f"Trade #{x} - {df_show.loc[x, 'Par']} ({df_show.loc[x, 'Resultado']})")
            
            if st.button("📂 ABRIR DETALLES DEL TRADE"):
                modal_update_trade(user, sel_acc, trade_to_edit, df.loc[trade_to_edit])
                
        else:
            st.write("Historial vacío.")

    # 3. PESTAÑA NOTICIAS
    with tab_news:
         html = f"""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-events.js" async>{{"colorTheme": "dark","isTransparent": true,"width": "100%","height": "600","locale": "es","importanceFilter": "-1,0","currencyFilter": "USD,EUR,GBP"}}</script></div>"""
         st.components.v1.html(html, height=600)

if 'user' not in st.session_state: st.session_state.user = None
if st.session_state.user: main_app()
else: login_screen()
