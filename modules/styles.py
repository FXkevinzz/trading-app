import streamlit as st

def inject_theme(theme_mode):
    """Inyecta el CSS dinámico basado en el tema seleccionado."""
    if theme_mode == "Claro (Swiss Design)":
        # Modo Claro (Buen contraste por defecto)
        css_vars = """
            --bg-app: #f0f2f6; /* Fondo general un poco más gris */
            --bg-card: #ffffff; /* Cajas blancas puras */
            --bg-sidebar: #ffffff;
            --text-main: #1e293b; 
            --text-muted: #64748b; 
            --border-color: #e2e8f0;
            --input-bg: #ffffff; 
            --accent: #2563eb; --accent-green: #16a34a; --accent-red: #dc2626;
            --button-text: #ffffff;
            --shadow: 0 2px 5px rgba(0,0,0,0.05);
        """
    else:
        # Modo Oscuro (Cyber Navy) - ¡COLORES ACTUALIZADOS PARA MÁS CONTRASTE!
        css_vars = """
            --bg-app: #050a14; /* Fondo principal MÁS oscuro (casi negro azulado) */
            --bg-card: #1a2540; /* Cajas MÁS claras (azul marino visible) */
            --bg-sidebar: #0a1020;
            --text-main: #e2e8f0; 
            --text-muted: #94a3b8; 
            --border-color: #304368; /* Borde más claro y definido */
            --input-bg: #131c33; 
            --accent: #3b82f6; --accent-green: #10b981; --accent-red: #ef4444;
            --button-text: #ffffff;
            --shadow: 0 4px 20px rgba(0,0,0,0.4); /* Sombra más fuerte para dar profundidad */
        """

    st.markdown(f"""
    <style>
    :root {{ {css_vars} }}
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
    .stApp {{ background-color: var(--bg-app); color: var(--text-main); }}
    h1, h2, h3, h4, h5, p, label, span, div {{ color: var(--text-main) !important; }}
    
    /* Sidebar */
    [data-testid="stSidebar"] {{ background-color: var(--bg-sidebar); border-right: 1px solid var(--border-color); }}
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2 {{ color: var(--text-main) !important; }}
    
    /* Inputs */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {{
        background-color: var(--input-bg) !important; color: var(--text-main) !important;
        border: 1px solid var(--border-color) !important; border-radius: 8px;
    }}
    
    /* Tabs Redondas */
    .stTabs [data-baseweb="tab"] {{
        background-color: var(--bg-card) !important; color: var(--text-muted) !important;
        border: 1px solid var(--border-color); border-radius: 50px !important;
        padding: 0 25px !important; height: 45px; box-shadow: var(--shadow); margin-right: 10px;
    }}
    .stTabs [data-baseweb="tab"][aria-selected="true"] {{
        background-color: var(--accent) !important; color: white !important; border: none !important;
    }}
    
    /* Cards & HUD (ESTRATEGIA BOX) */
    .strategy-box {{ 
        background-color: var(--bg-card); 
        border: 1px solid var(--border-color); 
        padding: 20px; 
        border-radius: 16px; /* Bordes más redondeados */
        box-shadow: var(--shadow);
        height: 100%; /* Para que los cuadrantes tengan la misma altura */
    }}
    .strategy-header {{ color: var(--accent); font-weight: 800; text-transform: uppercase; letter-spacing: 1px; border-bottom: 2px solid var(--border-color); margin-bottom: 15px; padding-bottom: 10px; }}
    
    /* HUD Puntuación */
    .hud-container {{ background: linear-gradient(145deg, var(--bg-card), var(--bg-app)); border: 1px solid var(--accent); border-radius: 16px; padding: 20px; margin-top: 20px; display: flex; align-items: center; justify-content: space-between; box-shadow: var(--shadow); }}
    .hud-value-large {{ font-size: 3rem; font-weight: 900; color: var(--text-main); line-height: 1; }}
    
    /* Status Labels */
    .status-sniper {{ background: rgba(16,185,129,0.2); color: var(--accent-green); border: 2px solid var(--accent-green); padding: 8px 20px; border-radius: 50px; font-weight: 800; letter-spacing: 1px; }}
    .status-warning {{ background: rgba(250,204,21,0.2); color: #fbbf24; border: 2px solid #fbbf24; padding: 8px 20px; border-radius: 50px; font-weight: 800; letter-spacing: 1px; }}
    .status-stop {{ background: rgba(239,68,68,0.2); color: var(--accent-red); border: 2px solid var(--accent-red); padding: 8px 20px; border-radius: 50px; font-weight: 800; letter-spacing: 1px; }}
    </style>
    """, unsafe_allow_html=True)
