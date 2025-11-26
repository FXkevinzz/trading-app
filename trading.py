import google.generativeai as genai
import streamlit as st

# Configura tu clave aquí directamente SOLO PARA ESTA PRUEBA
# (O usa st.secrets si ya lo tienes configurado)
api_key = st.secrets["GEMINI_KEY"] 

genai.configure(api_key=api_key)

st.write("## 🤖 Diagnóstico de Modelos Gemini")

try:
    st.write("Consultando a Google...")
    models = genai.list_models()
    found = False
    for m in models:
        if 'generateContent' in m.supported_generation_methods:
            st.success(f"✅ Modelo disponible: **{m.name}**")
            found = True
    
    if not found:
        st.error("❌ No se encontraron modelos. Tu API KEY podría no tener permisos o estar mal copiada.")
except Exception as e:
    st.error(f"❌ Error fatal: {str(e)}")
    st.info("Intenta actualizar la librería: pip install -U google-generativeai")
