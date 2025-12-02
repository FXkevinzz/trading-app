import streamlit as st
import google.generativeai as genai
import os
import json
from datetime import datetime
from modules.data import BRAIN_FILE, IMG_DIR 

def init_ai():
    """Inicializa la API."""
    if "GEMINI_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_KEY"])
        return True
    return False

@st.cache_data(ttl=60)
def load_brain():
    if not os.path.exists(BRAIN_FILE): return []
    try:
        with open(BRAIN_FILE, "r") as f: return json.load(f)
    except: return []

def save_image_locally(image_obj, filename):
    try:
        path = os.path.join(IMG_DIR, filename)
        image_obj.save(path)
        return path
    except: return None

# --- FUNCIÓN DE ANÁLISIS DE IMÁGENES (PARA EL MODAL) ---
def analyze_multiframe(images_data, mode, pair):
    # (Esta función se mantiene igual que antes para el análisis visual)
    brain = load_brain()
    context = ""
    if brain:
        wins = [x for x in brain if x.get('result') == 'WIN']
        examples = wins[-2:] if len(wins) >= 2 else wins
        context = f"REFERENCIA (TUS MEJORES TRADES PREVIOS):\n{str(examples)}\n\n"
    
    img_desc = ""
    for i, data in enumerate(images_data):
        img_desc += f"IMAGEN {i+1}: Temporalidad {data['tf']}.\n"

    prompt = f"""
    Eres un Mentor de Trading Institucional experto en la estrategia 'Set & Forget'.
    ESTRATEGIA: {mode} del activo {pair}.
    {context}
    IMÁGENES SUMINISTRADAS: {img_desc}
    
    TU MISIÓN ES VALIDAR LA SINCRONIZACIÓN (TRIPLE SYNC):
    1. TENDENCIA: ¿Alineación macro?
    2. ZONA (AOI): ¿Reacción en zona válida?
    3. GATILLO: ¿Shift of Structure (SOS) + Vela Envolvente?
    
    Responde formato exacto:
    🎯 SINCRONÍA: [PERFECTA / DUDOSA / DESALINEADA]
    📊 PROBABILIDAD: 0-100%
    📝 ANÁLISIS TÉCNICO: (Relación temporalidades)
    💡 CONSEJO DE EJECUCIÓN: (SL/TP sugeridos)
    """
    
    content = [prompt]
    for data in images_data: content.append(data['img'])

    modelos = ['gemini-2.0-flash', 'gemini-1.5-flash']
    for m in modelos:
        try:
            model = genai.GenerativeModel(m)
            return model.generate_content(content).text
        except: continue
            
    return "Error de conexión IA. Verifica API Key."

# --- NUEVA FUNCIÓN: CHAT MENTOR ---
def chat_with_mentor(user_input, trade_history_df):
    """
    Función de chat que recibe el mensaje del usuario y el historial de trades (DataFrame).
    """
    # 1. Convertir historial a texto para que la IA lo entienda
    history_context = "HISTORIAL DE TRADES DEL USUARIO (CSV):\n"
    if not trade_history_df.empty:
        # Pasamos las últimas 20 operaciones para no saturar
        history_context += trade_history_df.tail(20).to_string()
    else:
        history_context += "El usuario aún no tiene trades registrados."

    # 2. El Prompt del Mentor (Personalidad Alex G / Cheat Sheet)
    system_prompt = f"""
    Eres el MENTOR DE TRADING personal de este usuario. Te basas estrictamente en la estrategia "Set & Forget" y la "Cheat Sheet" de Alex G.
    
    TUS REGLAS DE ORO:
    1. Solo operamos Lunes-Jueves (Viernes es riesgo).
    2. Solo operamos Londres y NY (11pm - 11am EST).
    3. Buscamos SIEMPRE confluencia de 3 temporalidades (W+D+4H o D+4H+1H).
    4. Psicología: Eres firme pero empático. Si el usuario pierde por romper reglas, regáñalo constructivamente. Si gana siguiendo el plan, felicítalo.
    
    CONTEXTO ACTUAL DEL USUARIO:
    {history_context}
    
    INSTRUCCIONES:
    - Analiza sus datos si te pregunta sobre su rendimiento.
    - Si te dice que se siente mal/ansioso, dale consejos de psicología de trading (Mark Douglas/Trading in the Zone).
    - Sé conciso, directo y profesional. Usa emojis ocasionalmente.
    - Si detectas que está operando contra tendencia en su historial, házselo saber.
    
    PREGUNTA DEL USUARIO: {user_input}
    """

    # 3. Llamada a Gemini
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(system_prompt)
        return response.text
    except Exception as e:
        return f"Error conectando con el Mentor IA: {str(e)}"
