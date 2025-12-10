# pages/diagnostico.py
import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="Diagnóstico IA", page_icon="🛠️")

st.title("🛠️ Diagnóstico de Conexión Google Gemini")

# 1. VERIFICACIÓN DE API KEY
st.subheader("1. Verificación de Credenciales")
try:
    api_key = st.secrets["GEMINI_KEY"]
    # Mostramos solo los primeros y últimos caracteres por seguridad
    masked_key = f"{api_key[:5]}...{api_key[-5:]}" if api_key else "None"
    st.info(f"API Key detectada: `{masked_key}`")
    
    # Configuramos la librería
    genai.configure(api_key=api_key)
    st.success("✅ Librería configurada correctamente.")
    
except Exception as e:
    st.error(f"❌ Error leyendo GEMINI_KEY de secrets: {e}")
    st.stop()

# 2. CONSULTA DE MODELOS
st.subheader("2. Modelos Disponibles")
st.write("Haz clic para conectar con Google y listar qué modelos permite tu cuenta:")

if st.button("🔍 ESCANEAR MODELOS"):
    try:
        with st.spinner("Conectando con servidores de Google..."):
            all_models = list(genai.list_models())
            
            # Filtramos solo los que sirven para chat (generateContent)
            chat_models = []
            for m in all_models:
                if 'generateContent' in m.supported_generation_methods:
                    chat_models.append({
                        "ID del Modelo (Usar en código)": m.name,
                        "Nombre Visible": m.display_name,
                        "Versión": m.version
                    })
            
            if chat_models:
                st.success(f"¡Conexión Exitosa! Tienes acceso a {len(chat_models)} modelos de texto.")
                st.table(chat_models)
                st.markdown("---")
                st.markdown("### 👉 Recomendación:")
                
                # Análisis automático
                ids = [m["ID del Modelo (Usar en código)"] for m in chat_models]
                if "models/gemini-1.5-flash" in ids:
                    st.success("✅ Tienes **gemini-1.5-flash**. Este es el MEJOR para tu app (rápido y gratis).")
                    st.code('model = genai.GenerativeModel("gemini-1.5-flash")', language="python")
                elif "models/gemini-pro" in ids:
                     st.warning("⚠️ Tienes gemini-pro. Es bueno, pero 1.5-flash es mejor.")
                else:
                    st.error("No veo los modelos estándar. Usa el ID exacto que aparezca en la tabla de arriba.")
            else:
                st.warning("Se conectó, pero no se encontraron modelos compatibles con chat.")
                
    except Exception as e:
        st.error(f"❌ Error conectando a la API: {e}")
        st.write("Posibles causas: API Key inválida, bloqueo regional, o librería desactualizada.")
