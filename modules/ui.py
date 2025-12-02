import streamlit as st
from datetime import datetime
from PIL import Image
from modules.data import save_trade, OFFICIAL_PAIRS, delete_trade
from modules.ai import analyze_multiframe, save_image_locally
import pandas as pd

# --- MODAL: NUEVO TRADE (CON CALCULADORA PRO) ---
@st.dialog("➕ REGISTRAR TRADE & CALCULADORA")
def modal_new_trade(user, account, global_mode, prefilled_pair, confluence_score):
    # 1. HEADER CON PUNTAJE
    st.markdown(f"""
    <div style="background:rgba(16, 185, 129, 0.1); border:1px solid #10b981; border-radius:8px; padding:10px; text-align:center; margin-bottom:15px;">
        <span style="color:#10b981; font-weight:bold;">✨ Confluence Score: {confluence_score}%</span>
    </div>
    """, unsafe_allow_html=True)
    
    # 2. SELECCIÓN DE ACTIVO Y DIRECCIÓN
    c1, c2 = st.columns(2)
    with c1:
        # Intentar pre-seleccionar el par
        try: idx = OFFICIAL_PAIRS.index(prefilled_pair)
        except: idx = 0
        par = st.selectbox("Currency Pair *", OFFICIAL_PAIRS, index=idx)
    with c2:
        direction = st.radio("Direction *", ["LONG 🟢", "SHORT 🔴"], horizontal=True)

    st.markdown("---")

    # 3. CALCULADORA DE RIESGO (ESTILO IMAGEN)
    st.markdown("#### 🧮 Calculadora de Posición")
    
    # Fila 1: Balance
    bal = st.number_input("Account Balance ($) *", value=1000.0, step=100.0, help="Tu capital actual")
    
    # Fila 2: Precios (SL y TP)
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        sl_price = st.number_input("Stop Loss Price *", format="%.5f", value=0.00000)
    with col_p2:
        tp_price = st.number_input("Take Profit Price *", format="%.5f", value=0.00000)
        
    # Fila 3: Entrada y Riesgo
    col_p3, col_p4 = st.columns(2)
    with col_p3:
        entry_price = st.number_input("Entry Price *", format="%.5f", value=0.00000)
    with col_p4:
        risk_pct = st.number_input("Risk Percentage (%) *", value=1.0, step=0.1)

    # --- LÓGICA DE CÁLCULO AUTOMÁTICO ---
    lot_size = 0.0
    risk_usd = bal * (risk_pct / 100)
    pips_sl = 0.0
    
    if entry_price > 0 and sl_price > 0:
        # Detectar si es JPY o XAU (Gold) para calcular pips correctamente
        is_jpy = "JPY" in par
        is_xau = "XAU" in par
        
        raw_diff = abs(entry_price - sl_price)
        
        if is_jpy:
            multiplier = 100
        elif is_xau:
            multiplier = 10 # El oro suele moverse en centavos/dólares
        else:
            multiplier = 10000 # Pares normales (EURUSD, etc)
            
        pips_sl = raw_diff * multiplier
        
        # Fórmula Standard: Lotes = Riesgo / (Pips * 10)
        # Nota: Esto es aproximado para pares USD. 
        if pips_sl > 0:
            lot_size = risk_usd / (pips_sl * 10)
            if is_xau: lot_size = risk_usd / (pips_sl * 100) # Ajuste fino para Oro según broker
            if is_jpy: lot_size = risk_usd / (pips_sl * 9) # Ajuste aproximado valor pip JPY

    # 4. RESULTADO (CAJA VERDE)
    st.markdown(f"""
    <div style="background-color:#0f172a; border:1px solid #1e293b; border-radius:10px; padding:15px; margin-top:10px;">
        <div style="color:#94a3b8; font-size:0.9rem; margin-bottom:5px;">📠 Calculated Lot Size</div>
        <div style="font-size:2rem; font-weight:bold; color:#10b981;">{lot_size:.2f} Lots</div>
        <div style="font-size:0.8rem; color:#64748b;">Riesgo: ${risk_usd:.2f} ({pips_sl:.1f} pips)</div>
    </div>
    <br>
    """, unsafe_allow_html=True)

    # 5. IA Y NOTAS
    st.markdown("#### 📝 Notas & IA")
    notes = st.text_area("Notes *", placeholder="Escribe tus confluencias aquí...", height=100)
    
    img_file = st.file_uploader("Chart Image (Before Trade) *", type=['png', 'jpg'])
    
    if img_file:
        with st.expander("🦁 Consultar a Gemini (IA)", expanded=False):
            st.image(img_file, width=150)
            if st.button("Analizar con IA"):
                with st.spinner("Analizando estructura..."):
                    img_obj = Image.open(img_file)
                    # Llamada a la IA
                    analisis = analyze_multiframe([{'img': img_obj, 'tf': 'Setup'}], global_mode, par)
                    st.info(analisis)
                    st.session_state['temp_ai_note'] = analisis

    # BOTÓN FINAL DE GUARDAR
    if st.button("💾 SAVE TRADE", type="primary", use_container_width=True):
        img_path = None
        if img_file:
            img_obj = Image.open(img_file)
            fname = f"{par}_{datetime.now().strftime('%Y%m%d%H%M%S')}_before.png"
            img_path = save_image_locally(img_obj, fname)

        # Si la IA analizó algo, lo agregamos a las notas
        final_notes = notes
        if 'temp_ai_note' in st.session_state:
            final_notes += f"\n\n[IA ANALYSIS]: {st.session_state['temp_ai_note']}"
            del st.session_state['temp_ai_note']

        # Guardamos en la base de datos
        # Nota: Guardamos Entry/SL/TP dentro de las notas para referencia futura
        calc_info = f"Entry: {entry_price} | SL: {sl_price} | TP: {tp_price} | Risk: {risk_pct}%"
        full_notes = f"{calc_info}\n{final_notes}"

        trade_data = {
            "Fecha": str(datetime.now().date()), 
            "Par": par, 
            "Direccion": direction, 
            "Status": "OPEN", 
            "Resultado": "PENDING", 
            "Dinero": 0.0, 
            "Ratio": 0.0, 
            "Notas": full_notes,
            "Img_Antes": img_path, 
            "Img_Despues": None,
            "Confluencia": confluence_score
        }
        
        save_trade(user, account, trade_data)
        st.rerun()

# --- MODAL: ACTUALIZAR TRADE (IGUAL QUE ANTES) ---
@st.dialog("📝 UPDATE TRADE")
def modal_update_trade(user, account, trade_idx, current_data):
    st.markdown(f"**{current_data['Par']}** | {current_data['Direccion']}")
    
    uc1, uc2 = st.columns(2)
    with uc1: new_result = st.selectbox("Outcome", ["WIN", "LOSS", "BE"], index=0)
    with uc2: new_pnl = st.number_input("Realized PnL ($)", value=0.0)
    
    new_ratio = st.number_input("Risk/Reward Ratio Achieved", value=0.0)
    
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
            
            # Lógica automática de signo
            final_pnl = abs(new_pnl) if new_result == "WIN" else -abs(new_pnl) if new_result == "LOSS" else 0.0

            update_data = {
                "Status": "CLOSED", "Resultado": new_result,
                "Dinero": final_pnl, "Ratio": new_ratio,
                "Img_Despues": img_path_after
            }
            save_trade(user, account, update_data, index=trade_idx)
            st.rerun()
