import streamlit as st
import calendar
import zipfile
from datetime import datetime
from PIL import Image
import streamlit.components.v1 as components
import plotly.graph_objects as go

# --- IMPORTACIÓN DE MÓDULOS PROPIOS ---
from modules.styles import inject_theme
from modules.data import (
    init_filesystem, verify_user, register_user, get_user_accounts, 
    create_account, get_balance_data, create_backup_zip, save_trade, 
    delete_trade, load_trades, DATA_DIR
)
from modules.ai import (
    init_ai, analyze_multiframe, load_brain, save_to_brain, generate_audit_report
)
from modules.utils import (
    get_market_status, render_cal_html, render_heatmap, mostrar_imagen
)

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Trading Pro Suite AI", layout="wide", page_icon="🦁")
init_filesystem()

# 2. LOGIN
def login_screen():
    inject_theme("Oscuro (Cyber Navy)")
    c1,c2,c3 = st.columns([1,1,1])
    with c2:
        st.markdown("<h1 style='text-align:center; color:var(--accent);'>🦁 Trading Suite AI</h1>", unsafe_allow_html=True)
        t1, t2, t3 = st.tabs(["INGRESAR", "REGISTRARSE", "RESTAURAR"])
        
        with t1:
            u = st.text_input("Usuario", key="l_u")
            p = st.text_input("Password", type="password", key="l_p")
            if st.button("ACCEDER", use_container_width=True, key="b_l"):
                if verify_user(u, p): 
                    st.session_state.user = u
                    st.rerun()
                else: st.error("Error (Prueba: admin/1234)")
        
        with t2:
            nu = st.text_input("Nuevo Usuario", key="r_u")
            np = st.text_input("Nueva Password", type="password", key="r_p")
            if st.button("CREAR CUENTA", use_container_width=True, key="b_r"):
                if nu and np: 
                    register_user(nu, np)
                    st.success("Creado!"); st.rerun()

        with t3:
            uploaded_zip = st.file_uploader("Subir backup.zip", type="zip")
            if uploaded_zip and st.button("RESTAURAR"):
                try:
                    with zipfile.ZipFile(uploaded_zip, 'r') as z:
                        z.extractall(DATA_DIR)
                    st.success("Restaurado.")
                except: st.error("Archivo inválido")

# 3. APP PRINCIPAL
def main_app():
    user = st.session_state.user
    # Variables de Sesión
    defaults = {
        'cal_date': datetime.now(), 'global_pair': "XAUUSD", 
        'global_mode': "Swing (W-D-4H)", 'ai_temp_result': None, 'ai_temp_images': None
    }
    for k, v in defaults.items():
        if k not in st.session_state: st.session_state[k] = v

    time_str, session, status_txt, status_color = get_market_status()

    # --- SIDEBAR ---
    with st.sidebar:
        st.title(f"👤 {user.upper()}")
        tema = st.radio("🎨 TEMA", ["Oscuro (Cyber Navy)", "Claro (Swiss Design)"], index=0)
        inject_theme(tema)
        is_dark = (tema == "Oscuro (Cyber Navy)")
        
        st.markdown("---")
        st.markdown(f"""
        <div style="background:var(--bg-card); border:1px solid {status_color}; border-radius:10px; padding:15px; text-align:center; margin-bottom:15px;">
            <div style="color:var(--text-muted); font-size:0.8rem; font-weight:bold;">HORA NY (EST)</div>
            <div style="color:var(--text-main); font-size:1.5rem; font-weight:900;">{time_str}</div>
            <div style="color:{status_color}; font-weight:bold; font-size:0.9rem; margin-top:5px;">{status_txt}</div>
            <div style="color:var(--text-muted); font-size:0.7rem;">Sesión: {session}</div>
        </div>""", unsafe_allow_html=True)

        with st.expander("🧮 CALCULADORA"):
            c_risk = st.number_input("Riesgo %", 1.0, 10.0, 1.0)
            c_sl = st.number_input("SL (Pips)", 1.0, 100.0, 5.0)
            accs = get_user_accounts(user)
            sel_acc = st.selectbox("Cuenta", accs)
            _, act_bal, _ = get_balance_data(user, sel_acc)
            if c_sl > 0:
                risk_usd = act_bal * (c_risk/100)
                lots = risk_usd / (c_sl * 10)
                st.success(f"Lotes: **{lots:.2f}** (${risk_usd:.0f})")

        st.markdown("---")
        if st.button("CERRAR SESIÓN", use_container_width=True): 
            st.session_state.user = None; st.rerun()
        
        ini, act, df_bal = get_balance_data(user, sel_acc)
        col_s = "#10b981" if act >= ini else "#ef4444"
        st.markdown(f"""<div style="background:rgba(255,255,255,0.05); padding:15px; border-radius:10px; border:1px solid rgba(255,255,255,0.1); text-align:center;"><div style="color:#94a3b8; font-size:0.8rem;">BALANCE</div><div style="color:{col_s}; font-size:1.8rem; font-weight:bold">${act:,.2f}</div></div>""", unsafe_allow_html=True)
        
        c_new, c_bkp = st.columns(2)
        with c_new:
            with st.popover("➕"):
                na = st.text_input("Nombre"); nb = st.number_input("Capital", 100.0)
                if st.button("Crear"): create_account(user, na, nb); st.rerun()
        with c_bkp:
            zip_path = create_backup_zip()
            with open(zip_path, "rb") as f: st.download_button("💾", f, "backup.zip", "application/zip")

    # --- PESTAÑAS PRINCIPALES ---
    tabs = st.tabs(["🦁 OPERATIVA", "🧠 IA VISION", "📝 BITÁCORA", "📊 ANALYTICS", "📅 CALENDARIO", "📰 NOTICIAS"])

    # TAB 1: OPERATIVA (CON LISTA COMPLETA OANDA)
    with tabs[0]:
        st.markdown('<div class="strategy-box">', unsafe_allow_html=True)
        c_mod = st.columns([1,2,1])
        with c_mod[1]: st.session_state.global_mode = st.radio("", ["Swing (W-D-4H)", "Scalping (4H-2H-1H)"], horizontal=True, label_visibility="collapsed")
        st.markdown("---")
        
        # --- LISTA EXTENDIDA OANDA/PROP FIRMS ---
        OFFICIAL_PAIRS = [
            # MAJORS
            "EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD", "NZDUSD", "USDCHF",
            # METALS & ENERGY
            "XAUUSD", "XAGUSD", "XPTUSD", "WTICOUSD", "BCOUSD", "NATGAS",
            # INDICES USA
            "US30", "US100", "US500", "US2000",
            # INDICES GLOBAL
            "DE40", "UK100", "FR40", "JP225", "HK50", "AU200", "EU50",
            # CROSSES (EUR/GBP/JPY/AUD)
            "EURGBP", "EURJPY", "EURAUD", "EURNZD", "EURCAD", "EURCHF",
            "GBPJPY", "GBPAUD", "GBPNZD", "GBPCAD", "GBPCHF",
            "AUDJPY", "AUDNZD", "AUDCAD", "AUDCHF",
            "NZDJPY", "NZDCAD", "NZDCHF", "CADJPY", "CADCHF", "CHFJPY",
            # EXOTICS
            "USDMXN", "USDSGD", "USDZAR", "USDTRY", "USDHKD", "USDCNH", "USDSEK", "USDNOK", "USDPLN",
            # CRYPTO
            "BTCUSD", "ETHUSD", "LTCUSD", "BCHUSD", "XRPUSD", "SOLUSD"
        ]
        
        # Lógica para mantener la selección
        curr_idx = 0
        if st.session_state.global_pair in OFFICIAL_PAIRS:
            curr_idx = OFFICIAL_PAIRS.index(st.session_state.global_pair)
        elif "XAU" in st.session_state.global_pair: # Fallback inteligente para Oro
             if "XAUUSD" in OFFICIAL_PAIRS: curr_idx = OFFICIAL_PAIRS.index("XAUUSD")

        # Selectbox con búsqueda
        st.session_state.global_pair = st.selectbox("ACTIVO GLOBAL", OFFICIAL_PAIRS, index=curr_idx)
        
        st.markdown('</div><br>', unsafe_allow_html=True)

        r1_c1, r1_c2 = st.columns(2)
        r2_c1, r2_c2 = st.columns(2)
        total = 0; sos, eng, rr = False, False, False
        modo = st.session_state.global_mode

        def header(t): return f"<div class='strategy-header'>{t}</div>"

        if "Swing" in modo:
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

        else: # SCALPING
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

        st.markdown("<br>", unsafe_allow_html=True)
        valid = sos and eng and rr
        msg, css_cl = "💤 ESPERAR", "status-warning"
        if not sos: msg, css_cl = "⛔ FALTA SOS", "status-stop"
        elif not eng: msg, css_cl = "⚠️ FALTA VELA", "status-warning"
        elif total >= 90: msg, css_cl = "💎 SNIPER ENTRY", "status-sniper"
        elif total >= 60 and valid: msg, css_cl = "✅ VÁLIDO", "status-sniper"
        
        st.markdown(f"""<div class="hud-container"><div class="hud-stat"><div class="hud-label">PUNTAJE</div><div class="hud-value-large">{total}%</div></div><div style="flex-grow:1; text-align:center; margin:0 20px;"><span class="{css_cl}">{msg}</span></div></div>""", unsafe_allow_html=True)
        st.progress(min(total, 100))

    # TAB 2: IA VISION
    with tabs[1]:
        sub_ia = st.tabs(["👁️ ANÁLISIS", "📘 PLAYBOOK"])
        with sub_ia[0]:
            if not init_ai(): st.error("Falta API KEY")
            else:
                c_img, c_res = st.columns([1, 1.5])
                with c_img:
                    col_up1, col_up2, col_up3 = st.columns(3)
                    with col_up1: img1 = st.file_uploader("1. MACRO", type=["jpg","png"], key="u1")
                    with col_up2: img2 = st.file_uploader("2. INTERMEDIO", type=["jpg","png"], key="u2")
                    with col_up3: img3 = st.file_uploader("3. GATILLO", type=["jpg","png"], key="u3")
                    
                    c_tf1, c_tf2, c_tf3 = st.columns(3)
                    with c_tf1: tf1 = st.selectbox("TF Macro", ["W", "D"], key="tf1")
                    with c_tf2: tf2 = st.selectbox("TF Intermedio", ["Daily", "4H", "1H"], key="tf2")
                    with c_tf3: tf3 = st.selectbox("TF Gatillo", ["4H", "1H", "15M", "5M"], key="tf3")

                    if st.button("🦁 ANALIZAR SINCRONÍA", type="primary", use_container_width=True):
                        images_data = []
                        if img1: images_data.append({'img': Image.open(img1), 'tf': tf1})
                        if img2: images_data.append({'img': Image.open(img2), 'tf': tf2})
                        if img3: images_data.append({'img': Image.open(img3), 'tf': tf3})
                        
                        if images_data:
                            with st.spinner("Analizando..."):
                                res = analyze_multiframe(images_data, st.session_state.global_mode, st.session_state.global_pair)
                                st.session_state.ai_temp_result = res
                                st.session_state.ai_temp_images = [x['img'] for x in images_data]
                with c_res:
                    if st.session_state.ai_temp_result:
                        st.markdown(f'<div class="strategy-box">{st.session_state.ai_temp_result}</div>', unsafe_allow_html=True)

        with sub_ia[1]:
            brain_data = load_brain()
            wins = [x for x in brain_data if x.get('result') == 'WIN']
            if wins:
                for trade in wins:
                    with st.expander(f"🏆 {trade['pair']} - {trade['date'][:16]}"):
                        cols = st.columns(len(trade['images']))
                        for idx, img_path in enumerate(trade['images']):
                            if os.path.exists(img_path): cols[idx].image(img_path)
                        st.write(trade['analysis'])
            else: st.info("Sin trades ganadores guardados.")

    # TAB 3: BITÁCORA
    with tabs[2]:
        c_form, c_hist = st.columns([1, 1.5])
        with c_form:
            st.markdown('<div class="strategy-box">', unsafe_allow_html=True)
            with st.form("reg_trade"):
                dt = st.date_input("Fecha", datetime.now())
                pr = st.text_input("Par", st.session_state.global_pair)
                tp = st.selectbox("Tipo", ["BUY","SELL"]); rs = st.selectbox("Resultado", ["WIN", "LOSS", "BE"])
                mn = st.number_input("PnL ($)", step=10.0); rt = st.number_input("Ratio", 2.5); nt = st.text_area("Notas")
                if st.form_submit_button("GUARDAR"):
                    rm = mn if rs=="WIN" else -abs(mn) if rs=="LOSS" else 0
                    save_trade(user, sel_acc, {"Fecha":dt,"Par":pr,"Tipo":tp,"Resultado":rs,"Dinero":rm,"Ratio":rt,"Notas":nt})
                    
                    if rs == "WIN" and st.session_state.ai_temp_result:
                        save_to_brain(st.session_state.ai_temp_result, pr, rs, st.session_state.global_mode, st.session_state.ai_temp_images)
                        st.session_state.ai_temp_result = None
                        st.session_state.ai_temp_images = None
                    st.success("Guardado"); st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        
        with c_hist:
            df_h = load_trades(user, sel_acc)
            if not df_h.empty:
                for idx, row in df_h.iterrows():
                    c1, c2 = st.columns([4, 1])
                    with c1: st.info(f"{row['Fecha']} | {row['Par']} | {row['Resultado']} | ${row['Dinero']}")
                    with c2: 
                        if st.button("🗑️", key=f"del_{idx}"):
                            delete_trade(user, sel_acc, idx); st.rerun()

    # TAB 4: ANALYTICS
    with tabs[3]:
        if not df_bal.empty:
            fig = go.Figure(go.Scatter(x=df_bal["Fecha"], y=df_bal["Dinero"].cumsum() + ini, mode='lines+markers'))
            st.plotly_chart(fig, use_container_width=True)
            fig_h = render_heatmap(df_bal, is_dark); st.plotly_chart(fig_h, use_container_width=True)
            if st.button("AUDITAR RENDIMIENTO"):
                if init_ai(): st.info(generate_audit_report(df_bal))

    # TAB 5: CALENDARIO
    with tabs[4]:
        c_p, c_t, c_n = st.columns([1,5,1])
        d = st.session_state.cal_date
        with c_p: 
            if st.button("⬅️"): 
                m, y = (d.month - 1, d.year) if d.month > 1 else (12, d.year - 1)
                st.session_state.cal_date = d.replace(month=m, year=y); st.rerun()
        with c_n: 
            if st.button("➡️"):
                m, y = (d.month + 1, d.year) if d.month < 12 else (1, d.year + 1)
                st.session_state.cal_date = d.replace(month=m, year=y); st.rerun()
        
        html, y, m = render_cal_html(df_bal, is_dark)
        with c_t: st.markdown(f"<h3 style='text-align:center;'>{calendar.month_name[m]} {y}</h3>", unsafe_allow_html=True)
        st.markdown(html, unsafe_allow_html=True)

    # TAB 6: NOTICIAS
    with tabs[5]:
        tv = "dark" if is_dark else "light"
        html = f"""<div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-events.js" async>{{"colorTheme": "{tv}","isTransparent": true,"width": "100%","height": "800","locale": "es","importanceFilter": "-1,0","currencyFilter": "USD,EUR,GBP,JPY,AUD,CAD,CHF,NZD"}}</script></div>"""
        components.html(html, height=800)

if 'user' not in st.session_state: st.session_state.user = None
if st.session_state.user: main_app()
else: login_screen()
