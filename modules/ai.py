import streamlit as st
import google.generativeai as genai
import os
import json
from datetime import datetime
from modules.data import BRAIN_FILE, IMG_DIR 
from PIL import Image

def init_ai():
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

# --- ANÁLISIS DE IMÁGENES (MODAL) ---
def analyze_multiframe(images_data, mode, pair):
    # (Misma lógica de siempre para el modal de registro)
    brain = load_brain()
    context = ""
    if brain:
        wins = [x for x in brain if x.get('result') == 'WIN']
        examples = wins[-2:] if len(wins) >= 2 else wins
        context = f"REFERENCIA (MEJORES TRADES):\n{str(examples)}\n"
    
    img_desc = ""
    for i, data in enumerate(images_data):
        img_desc += f"IMAGEN {i+1}: {data['tf']}.\n"

    prompt = f"""
    Eres un Mentor Institucional (Estrategia Set & Forget).
    Activo: {pair} | Modo: {mode}
    {context}
    IMÁGENES: {img_desc}
    
    VALIDA LA SINCRONÍA (TRIPLE SYNC):
    1. Tendencia W/D/4H alineada?
    2. Reacción en AOI válido?
    3. Gatillo (SOS + Vela) claro?
    
    Responde:
    🎯 SINCRONÍA: [PERFECTA / DUDOSA / NO]
    📊 PROBABILIDAD: 0-100%
    📝 ANÁLISIS: Breve y directo.
    💡 CONSEJO: SL/TP sugerido.
    """
    
    content = [prompt]
    for data in images_data: content.append(data['img'])

    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        return model.generate_content(content).text
    except: return "Error IA."

# --- NUEVO: CHAT MENTOR CON VISIÓN ---
def chat_with_mentor(user_input, trade_history_df, image_file=None):
    """
    Chat avanzado que acepta texto, historial de datos e IMÁGENES.
    """
    # 1. Contexto de Datos
    history_txt = "SIN HISTORIAL"
    if not trade_history_df.empty:
        history_txt = trade_history_df.tail(15).to_string()

    # 2. Prompt del Sistema
    system_prompt = f"""
    Eres el MENTOR DE TRADING (Estrategia 'Set & Forget' de Alex G).
    
    TUS DATOS:
    - Historial del alumno (últimos 15 trades):
    {history_txt}
    
    TU PERSONALIDAD:
    - Eres un trader institucional veterano. Directo, analítico y disciplinado.
    - Si el usuario sube un gráfico, analízalo buscando: Tendencia, AOI, Estructura y Patrones de Vela.
    - Si el usuario pregunta por psicología, cita a Mark Douglas.
    - Si sus trades recientes son malos (LOSS), sé duro pero constructivo.
    - Si son buenos (WIN), felicítalo y recuérdale no sobreoperar.
    
    PREGUNTA DEL ALUMNO: {user_input}
    """

    content = [system_prompt]
    
    # 3. Si hay imagen, la añadimos al paquete
    if image_file:
        img = Image.open(image_file)
        content.append(img)
        content.append("Analiza este gráfico adjunto basándote en la estrategia.")

    # 4. Generar Respuesta
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(content)
        return response.text
    except Exception as e:
        return f"⚠️ Error conectando con el Mentor: {str(e)}"
