import streamlit as st
from datetime import datetime
from PIL import Image
from modules.data import save_trade, OFFICIAL_PAIRS, delete_trade
from modules.ai import analyze_multiframe, save_image_locally

# --- MODAL: NUEVO TRADE (OPERATIVA) ---
@st.dialog("➕ NUEVO TRADE")
def modal_new_trade(user, account, global_mode):
    st.caption("Registra tu entrada y valida con IA antes de disparar.")
    
    # SECCIÓN 1: DATOS DEL TRADE
    c1, c2 = st.columns(2)
    with c1:
        par = st.selectbox("Activo", OFFICIAL_PAIRS, index=0)
        direction = st.radio("Dirección", ["LONG 🟢", "SHORT 🔴"], horizontal=True)
    with c2:
        date = st.date_input("Fecha", datetime.now())
        status = "PENDING" # Por defecto entra como pendiente/abierto
    
    st.divider()
    
    # SECCIÓN 2: GESTIÓN DE RIESGO (CALCULADORA)
    st.markdown("##### 🛡️ Gestión de Riesgo")
    rc1, rc2, rc3 = st.columns(3)
    with rc1: 
        balance = st.number_input("Balance ($)", value=10000.0, step=100.0)
    with rc2: 
        risk_pct = st.number_input("Riesgo %", value=1.0, step=0.1)
    with rc3: 
        sl_pips = st.number_input("SL (Pips)", value=10.0, step=1.0)
    
    # Cálculo automático
    risk_usd = balance * (risk_pct / 100)
    lot_size = risk_usd / (sl_pips * 10) if sl_pips > 0 else 0
    st.info(f"📊 LOTE CALCULADO: **{lot_size:.2f}** (Riesgo: ${risk_usd:.0f})")

    st.divider()

    # SECCIÓN 3: CEREBRO IA
    st.markdown("##### 🧠 Validación IA")
    img_file = st.file_uploader("Subir Gráfico (Setup)", type=['png', 'jpg'])
    
    ai_feedback = None
    if img_file:
        st.image(img_file, width=200)
        if st.button("🦁 ANALIZAR SETUP", use_container_width=True):
            with st.spinner("Gemini analizando estructura..."):
                # Preparamos la imagen para la IA
                img_obj = Image.open(img_file)
                # Llamada rápida a la IA
                ai_feedback = analyze_multiframe([{'img': img_obj, 'tf': 'Setup'}], global_mode, par)
                st.session_state['temp_ai_analysis'] = ai_feedback # Guardar temporalmente

    if 'temp_ai_analysis' in st.session_state:
        st.success("Análisis Completado")
        with st.expander("Ver Opinión IA", expanded=True):
            st.write(st.session_state['temp_ai_analysis'])

    st.divider()
    
    # BOTÓN GUARDAR
    notes = st.text_area("Notas / Plan")
    
    if st.button("💾 GUARDAR TRADE", type="primary", use_container_width=True):
        # Guardar imagen si existe
        img_path = None
        if img_file:
            img_obj = Image.open(img_file)
            fname = f"{par}_{datetime.now().strftime('%Y%m%d%H%M%S')}_before.png"
            img_path = save_image_locally(img_obj, fname)

        # Guardar datos
        trade_data = {
            "Fecha": date, "Par": par, "Direccion": direction, 
            "Status": "OPEN", "Resultado": "PENDING", 
            "Dinero": 0.0, "Ratio": 0.0, "Notas": notes,
            "Img_Antes": img_path, "Img_Despues": None
        }
        
        save_trade(user, account, trade_data)
        if 'temp_ai_analysis' in st.session_state: del st.session_state['temp_ai_analysis']
        st.rerun()

# --- MODAL: EDITAR TRADE (HISTORY) ---
@st.dialog("📝 ACTUALIZAR / CERRAR TRADE")
def modal_update_trade(user, account, trade_idx, current_data):
    st.markdown(f"**{current_data['Par']}** | {current_data['Direccion']}")
    
    # SECCIÓN RESULTADOS
    uc1, uc2 = st.columns(2)
    with uc1:
        new_result = st.selectbox("Resultado", ["WIN", "LOSS", "BE"], index=0)
    with uc2:
        new_pnl = st.number_input("PnL ($)", value=float(current_data['Dinero']))
    
    new_ratio = st.number_input("Ratio Obtenido (R:R)", value=float(current_data['Ratio'] if current_data['Ratio'] else 0.0))
    
    # FOTO DESPUES
    st.markdown("##### 📸 Resultado Visual")
    img_after = st.file_uploader("Foto Cierre (After)", type=['png', 'jpg'])
    
    new_notes = st.text_area("Bitácora de Cierre", value=str(current_data['Notas']))
    
    col_del, col_save = st.columns([1, 2])
    with col_del:
        if st.button("🗑️ Borrar", type="secondary"):
            delete_trade(user, account, trade_idx)
            st.rerun()
            
    with col_save:
        if st.button("✅ ACTUALIZAR", type="primary"):
             # Guardar imagen after si existe
            img_path_after = current_data.get('Img_Despues')
            if img_after:
                img_obj = Image.open(img_after)
                fname = f"{current_data['Par']}_{datetime.now().strftime('%Y%m%d%H%M%S')}_after.png"
                img_path_after = save_image_locally(img_obj, fname)
            
            # Lógica de PnL automático si es LOSS
            final_pnl = new_pnl
            if new_result == "LOSS" and new_pnl > 0: final_pnl = -new_pnl
            if new_result == "BE": final_pnl = 0

            update_data = {
                "Status": "CLOSED",
                "Resultado": new_result,
                "Dinero": final_pnl,
                "Ratio": new_ratio,
                "Notas": new_notes,
                "Img_Despues": img_path_after
            }
            save_trade(user, account, update_data, index=trade_idx)
            st.rerun()
