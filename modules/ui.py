import streamlit as st
from datetime import datetime
from PIL import Image
from modules.data import save_trade, OFFICIAL_PAIRS, delete_trade
from modules.ai import analyze_multiframe, save_image_locally
import pandas as pd

# --- MODAL: NUEVO TRADE (CON CALCULADORA DE PRECIOS) ---
@st.dialog("➕ REGISTRAR TRADE & CALCULADORA")
def modal_new_trade(user, account, global_mode, prefilled_pair, confluence_score):
    # HEADER ESTILO "PRO"
    st.markdown(f"""
    <div style="background:rgba(16, 185, 129, 0.1); border-left: 4px solid #10b981; padding:10px; margin-bottom:15px; border-radius:4px;">
        <strong style="color:#10b981;">💎 Confluence Score: {confluence_score}%</strong>
        <span style="font-size:0.8rem; color:#94a3b8; margin-left:10px;">(Estrategia: {global_mode})</span>
    </div>
    """, unsafe_allow_html=True)
    
    # 1. SELECCIÓN DE ACTIVO
    c1, c2 = st.columns(2)
    with c1:
        try: idx = OFFICIAL_PAIRS.index(prefilled_pair)
        except: idx = 0
        par = st.selectbox("Currency Pair *", OFFICIAL_PAIRS, index=idx)
    with c2:
        direction = st.radio("Direction *", ["LONG 🟢", "SHORT 🔴"], horizontal=True)

    st.markdown("---")

    # 2. CALCULADORA DE POSICIÓN (DISEÑO IMAGEN)
    st.markdown("#### 🧮 Trade Parameters")
    
    # Balance y Riesgo
    r1, r2 = st.columns(2)
    with r1:
        bal = st.number_input("Account Balance ($)", value=10000.0, step=100.0)
    with r2:
        risk_pct = st.number_input("Risk Percentage (%)", value=1.0, step=0.1)

    # Precios
    p1, p2, p3 = st.columns(3)
    with p1:
        entry_price = st.number_input("Entry Price", format="%.5f", value=0.00000)
    with p2:
        sl_price = st.number_input("Stop Loss Price", format="%.5f", value=0.00000)
    with p3:
        tp_price = st.number_input("Take Profit Price", format="%.5f", value=0.00000)

    # --- LÓGICA INTERNA DE CÁLCULO ---
    lot_size = 0.00
    risk_usd = bal * (risk_pct / 100)
    pips = 0.0
    
    if entry_price > 0 and sl_price > 0:
        # Detectar multiplicador (Japoneses vs Normales vs Oro)
        if "JPY" in par: multiplier = 100
        elif "XAU" in par or "BTC" in par: multiplier = 10 
        else: multiplier = 10000
        
        diff = abs(entry_price - sl_price)
        pips = diff * multiplier
        
        if pips > 0:
            # Fórmula estándar aproximada: (Riesgo) / (Pips * 10)
            # Ajuste fino para XAU/JPY puede variar según broker, esto es una referencia sólida.
            lot_divisor = 10 if "XAU" not in par else 100 
            if "JPY" in par: lot_divisor = 9 # Aproximación por tipo de cambio
            
            lot_size = risk_usd / (pips * lot_divisor)

    # 3. RESULTADO (CAJA VERDE DE LA IMAGEN)
    st.markdown(f"""
    <div style="background-color:#0f172a; border:1px solid #334155; border-radius:10px; padding:20px; margin-top:10px; display:flex; align-items:center; justify-content:space-between;">
        <div>
            <div style="color:#94a3b8; font-size:0.8rem; text-transform:uppercase; letter-spacing:1px;">Calculated Lot Size</div>
            <div style="font-size:2.2rem; font-weight:900; color:#10b981; line-height:1;">{lot_size:.2f}</div>
        </div>
        <div style="text-align:right;">
            <div style="color:#e2e8f0; font-weight:bold;">Risk: ${risk_usd:.2f}</div>
            <div style="color:#64748b; font-size:0.8rem;">Stop Loss: {pips:.1f} pips</div>
        </div>
    </div>
    <br>
    """, unsafe_allow_html=True)

    # 4. EVIDENCIA E IA
    st.markdown("#### 📸 Chart & Analysis")
    notes = st.text_area("Trade Notes", placeholder="Escribe tu plan...", height=100)
    img_file = st.file_uploader("Upload Chart (Before)", type=['png', 'jpg'])
    
    # Lógica de IA dentro del modal
    if img_file and st.button("🦁 Ask AI Analysis"):
        with st.spinner("Analizando estructura..."):
            img_obj = Image.open(img_file)
            analysis = analyze_multiframe([{'img': img_obj, 'tf': 'Setup'}], global_mode, par)
            st.info(analysis)
            st.session_state['temp_ai_note'] = analysis

    # BOTÓN FINAL
    if st.button("💾 SAVE TRADE", type="primary", use_container_width=True):
        # Guardar imagen
        img_path = None
        if img_file:
            img_obj = Image.open(img_file)
            fname = f"{par}_{datetime.now().strftime('%Y%m%d%H%M%S')}_before.png"
            img_path = save_image_locally(img_obj, fname)

        # Adjuntar análisis IA a las notas si existe
        full_notes = notes
        if 'temp_ai_note' in st.session_state:
            full_notes += f"\n\n[IA]: {st.session_state['temp_ai_note']}"
            del st.session_state['temp_ai_note']
            
        # Guardar datos técnicos en notas para referencia
        tech_data = f"Entry: {entry_price} | SL: {sl_price} | TP: {tp_price}"
        full_notes = f"{tech_data}\n{full_notes}"

        trade_data = {
            "Fecha": str(datetime.now().date()), "Par": par, "Direccion": direction, 
            "Status": "OPEN", "Resultado": "PENDING", "Dinero": 0.0, 
            "Ratio": 0.0, "Notas": full_notes, 
            "Img_Antes": img_path, "Img_Despues": None, "Confluencia": confluence_score
        }
        
        save_trade(user, account, trade_data)
        st.rerun()

# --- MODAL: ACTUALIZAR (SIN CAMBIOS) ---
@st.dialog("📝 UPDATE TRADE")
def modal_update_trade(user, account, trade_idx, current_data):
    st.markdown(f"**{current_data['Par']}** | {current_data['Direccion']}")
    uc1, uc2 = st.columns(2)
    with uc1: new_result = st.selectbox("Outcome", ["WIN", "LOSS", "BE"], index=0)
    with uc2: new_pnl = st.number_input("Realized PnL ($)", value=0.0)
    new_ratio = st.number_input("R:R Achieved", value=0.0)
    st.markdown("##### 📸 After Chart")
    img_after = st.file_uploader("Upload Image", type=['png', 'jpg'])
    
    c_del, c_sav = st.columns([1, 2])
    with c_del:
        if st.button("🗑️ Delete"):
            delete_trade(user, account, trade_idx); st.rerun()
    with c_sav:
        if st.button("✅ Update Trade", type="primary"):
            img_path_after = current_data.get('Img_Despues')
            if img_after:
                img_obj = Image.open(img_after)
                fname = f"{current_data['Par']}_after.png"
                img_path_after = save_image_locally(img_obj, fname)
            
            final_pnl = abs(new_pnl) if new_result == "WIN" else -abs(new_pnl) if new_result == "LOSS" else 0.0
            update_data = {
                "Status": "CLOSED", "Resultado": new_result,
                "Dinero": final_pnl, "Ratio": new_ratio, "Img_Despues": img_path_after
            }
            save_trade(user, account, update_data, index=trade_idx)
            st.rerun()
