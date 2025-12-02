import streamlit as st
import google.generativeai as genai
import os
import json
from datetime import datetime
from modules.data import BRAIN_FILE, IMG_DIR  # Importamos constantes

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

def save_to_brain(analysis_text, pair, result, mode, images_list=None):
    memory = load_brain()
    saved_paths = []
    
    if images_list:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        for idx, img in enumerate(images_list):
            fname = f"{pair}_{result}_{timestamp}_{idx}.png"
            path = save_image_locally(img, fname)
            if path: saved_paths.append(path)

    new_mem = {
        "date": str(datetime.now()), "pair": pair, "mode": mode,
        "result": result, "analysis": analysis_text, "images": saved_paths
    }
    memory.append(new_mem)
    
    try:
        with open(BRAIN_FILE, "w") as f: json.dump(memory, f, indent=4)
        load_brain.clear()
    except: pass

def analyze_multiframe(images_data, mode, pair):
    brain = load_brain()
    # Contexto (Few-Shot Learning)
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

    # Intento con modelos 2.0
    modelos = ['gemini-2.0-pro-exp', 'gemini-2.0-flash']
    for m in modelos:
        try:
            model = genai.GenerativeModel(m)
            return model.generate_content(content).text
        except: continue
            
    return "Error de conexión IA. Verifica API Key o cuotas."

def generate_audit_report(df):
    if df.empty: return "Sin datos para auditar."
    csv_txt = df.to_string()
    prompt = f"Audita estos trades (Riesgo Prop Firm):\n{csv_txt}\nDetecta: Fugas de Capital, Zonas de Poder, Consejo Psicológico."
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        return model.generate_content(prompt).text
    except: return "Error en Auditoría."
