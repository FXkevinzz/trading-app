# --- BLOQUE DE DIAGNÓSTICO TEMPORAL (Pégalo al final de main.py) ---
def debug_available_models():
    import google.generativeai as genai
    
    st.markdown("---")
    st.header("🛠️ Diagnóstico de Modelos (ListModels)")
    
    # 1. Autenticación
    try:
        api_key = st.secrets["GEMINI_KEY"]
        genai.configure(api_key=api_key)
    except Exception as e:
        st.error(f"Error de API Key: {e}")
        return

    # 2. Llamada a ListModels
    try:
        st.write("Consultando API de Google...")
        # Iteramos sobre todos los modelos disponibles
        valid_models = []
        
        for m in genai.list_models():
            # Filtramos solo los que sirven para 'generateContent' (Chat/Texto)
            if 'generateContent' in m.supported_generation_methods:
                valid_models.append({
                    "Model ID (Lo que debes poner en código)": m.name,
                    "Nombre": m.display_name,
                    "Límite Tokens": m.input_token_limit
                })
        
        if valid_models:
            st.success(f"¡Conexión Exitosa! Se encontraron {len(valid_models)} modelos compatibles.")
            st.table(valid_models)
        else:
            st.warning("La API respondió, pero no devolvió modelos compatibles con generateContent.")

    except Exception as e:
        st.error(f"❌ Error fatal conectando a Google: {e}")

# Ejecutar diagnóstico
if st.button("🔍 VER LISTA DE MODELOS DISPONIBLES"):
    debug_available_models()
# ------------------------------------------------------------------
