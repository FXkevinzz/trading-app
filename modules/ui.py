import streamlit as st
from datetime import datetime
from PIL import Image
from modules.data import save_trade, OFFICIAL_PAIRS, delete_trade
from modules.ai import analyze_multiframe, save_image_locally
from modules.utils import send_telegram_alert # IMPORTANTE
import pandas as pd

# --- MODAL NUEVO TRADE ---
@st.dialog("➕ REGISTRAR TRADE & CALCULADORA")
def modal_new_trade(user, account, global_mode, prefilled_pair, confluence_score):
    st.markdown(f"""<div style="background:rgba(16, 185, 129, 0.1); border-left: 4px solid #10b981; padding:10px; margin-bottom:15px;"><strong style="color:#10b981;">💎 Score: {confluence_score}%</strong></div>""", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        try: idx = OFFICIAL_PAIRS.index(prefilled_pair)
        except: idx = 0
        par = st.selectbox("Activo", OFFICIAL_PAIRS, index=idx)
    with c2: direction = st.radio("Dirección", ["LONG 🟢", "SHORT 🔴"], horizontal=True)

    st.markdown("#### 🧮 Parámetros")
    r1, r2 = st.columns(2)
    with r1: bal = st.number_input("Balance ($)", value=10000.0, step=100.0)
    with r2: risk_pct = st.number_input("Riesgo (%)", value=1.0, step=0.1)

    p1, p2, p3 = st.columns(3)
    with p1: entry_price = st.number_input("Entrada", format="%.5f")
    with p2: sl_price = st.number_input("Stop Loss", format="%.5f")
    with p3: tp_price = st.number_input("Take Profit", format="%.5f")

    lot_size = 0.0; risk_usd = bal*(risk_pct/100); pips = 0.0
    if entry_price > 0 and sl_price > 0:
        if "JPY" in par: mult=100
        elif "XAU" in par: mult=10 
        else: mult=10000
        pips = abs(entry_price-sl_price)*mult
        if pips>0: lot_size = risk_usd/(pips*(9 if "JPY" in par else 100 if "XAU" in par else 10))

    st.markdown(f"""<div style="background-color:#0f172a; border:1px solid #334155; border-radius:10px; padding:15px; margin-top:10px; display:flex; justify-content:space-between;"><div><div style="color:#94a3b8; font-size:0.8rem;">LOTAJE SUGERIDO</div><div style="font-size:2rem; font-weight:900; color:#10b981;">{lot_size:.2f}</div></div><div style="text-align:right;"><div style="color:#e2e8f0;">Riesgo: ${risk_usd:.0f}</div><div style="color:#64748b; font-size:0.8rem;">{pips:.1f} pips</div></div></div><br>""", unsafe_allow_html=True)

    notes = st.text_area("Notas", placeholder="Plan...", height=100)
    img_file = st.file_uploader("Gráfico (Antes)", type=['png', 'jpg'])
    
    if img_file and st.button("🦁 Análisis IA"):
        with st.spinner("Analizando..."):
            img_obj = Image.open(img_file)
            an = analyze_multiframe([{'img': img_obj, 'tf': 'Setup'}], global_mode, par)
            st.info(an); st.session_state['temp_ai'] = an

    if st.button("💾 GUARDAR Y ENVIAR ALERTA", type="primary", use_container_width=True):
        img_path = None
        if img_file:
            img_obj = Image.open(img_file)
            fname = f"{par}_{datetime.now().strftime('%Y%m%d%H%M%S')}_before.png"
            img_path = save_image_locally(img_obj, fname)

        full_notes = f"Entry: {entry_price} | SL: {sl_price} | TP: {tp_price}\n{notes}"
        if 'temp_ai' in st.session_state: full_notes += f"\n\n[IA]: {st.session_state['temp_ai']}"

        trade_data = {
            "Fecha": str(datetime.now().date()), "Par": par, "Direccion": direction, 
            "Status": "OPEN", "Resultado": "PENDING", "Dinero": 0.0, 
            "Ratio": 0.0, "Notas": full_notes, "Img_Antes": img_path, "Img_Despues": None,
            "Confluencia": confluence_score
        }
        
        save_trade(user, account, trade_data)
        
        # --- ENVÍO A TELEGRAM ---
        # Preparamos datos bonitos para el mensaje
        tg_data = {
            "Par": par, "Direccion": direction, "Entry": entry_price, 
            "SL": sl_price, "TP": tp_price, "Risk": f"{risk_pct}% (${risk_usd:.0f})",
            "Lots": f"{lot_size:.2f}", "Notes": notes
        }
        with st.spinner("Enviando alerta a Telegram... 📲"):
            ok = send_telegram_alert(tg_data, img_path)
            if ok: st.toast("¡Alerta enviada a Telegram!", icon="✈️")
            else: st.toast("Guardado, pero faltan credenciales de Telegram.", icon="⚠️")
        
        st.rerun()

# --- MODAL UPDATE (IGUAL) ---
@st.dialog("📝 GESTIONAR")
def modal_update_trade(user, account, idx, data):
    st.markdown(f"**{data['Par']}** | {data['Direccion']}")
    c1, c2 = st.columns(2)
    with c1: res = st.selectbox("Resultado", ["WIN", "LOSS", "BE"], index=0)
    with c2: pnl = st.number_input("PnL ($)", value=0.0)
    img = st.file_uploader("Foto Cierre", type=['png', 'jpg'])
    if st.button("🗑️ Borrar"): delete_trade(user, account, idx); st.rerun()
    if st.button("✅ Actualizar", type="primary"):
        path = data.get('Img_Despues')
        if img:
            io = Image.open(img); fn = f"{data['Par']}_after.png"
            path = save_image_locally(io, fn)
        fpnl = abs(pnl) if res=="WIN" else -abs(pnl) if res=="LOSS" else 0.0
        save_trade(user, account, {"Status": "CLOSED", "Resultado": res, "Dinero": fpnl, "Img_Despues": path}, index=idx)
        st.rerun()
