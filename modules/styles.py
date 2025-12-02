import streamlit as st

def inject_theme(theme_mode):
    """Inyecta el CSS dinámico basado en el tema seleccionado."""
    if theme_mode == "Claro (Swiss Design)":
        css_vars = """
            --bg-app: #f8fafc; --bg-card: #ffffff; --bg-sidebar: #1e293b;
            --text-main: #0f172a; --text-muted: #475569; --border-color: #e2e8f0;
            --input-bg: #ffffff; --accent: #2563eb; --accent-green: #16a34a;
            --accent-red: #dc2626; --button-text: #ffffff;
            --shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        """
    else:
        # Modo Oscuro (Cyber Navy)
        css_vars = """
            --bg-app: #0b1121; --bg-card: #151e32; --bg-sidebar: #020617;
            --text-main: #f1f5f9; --text-muted: #94a3b8; --border-color: #2a3655;
            --input-bg: #1e293b; --accent: #3b82f6; --accent-green: #00e676;
            --accent-red: #ff1744; --button-text: #ffffff;
            --shadow: 0 10px 15px -3px rgba(0,0,0,0.5);
        """

    # He minificado un poco el CSS para que ocupe menos espacio visual aquí, 
    # pero mantiene toda tu lógica original de pestañas redondas y colores.
    st.markdown(f"""
    <style>
    :root {{ {css_vars} }}
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
    .stApp {{ background-color: var(--bg-app); color: var(--text-main); }}
    h1, h2, h3, h4, h5, p, label, span, div {{ color: var(--text-main) !important; }}
    
    /* Sidebar */
    [data-testid="stSidebar"] {{ background-color: var(--bg-sidebar); border-right: 1px solid var(--border-color); }}
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2 {{ color: #f8fafc !important; }}
    [data-testid="stSidebar"] p, span {{ color: #94a3b8 !important; }}

    /* Inputs */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {{
        background-color: var(--input-bg) !important; color: var(--text-main) !important;
        border: 1px solid var(--border-color) !important; border-radius: 8px;
    }}
    
    /* Tabs Redondas */
    .stTabs [data-baseweb="tab"] {{
        background-color: var(--bg-card) !important; color: var(--text-muted) !important;
        border: 1px solid var(--border-color); border-radius: 50px !important;
        padding: 0 25px !important; height: 45px; box-shadow: var(--shadow);
    }}
    .stTabs [data-baseweb="tab"][aria-selected="true"] {{
        background-color: var(--accent) !important; color: white !important; border: none !important;
    }}
    
    /* Cards & HUD */
    .strategy-box {{ background-color: var(--bg-card); border: 1px solid var(--border-color); padding: 20px; border-radius: 12px; box-shadow: var(--shadow); }}
    .strategy-header {{ color: var(--accent); font-weight: 800; text-transform: uppercase; letter-spacing: 1px; border-bottom: 1px solid var(--border-color); margin-bottom: 15px; }}
    .hud-container {{ background: linear-gradient(135deg, var(--bg-card), var(--bg-app)); border: 1px solid var(--accent); border-radius: 12px; padding: 20px; margin-top: 20px; display: flex; align-items: center; justify-content: space-between; box-shadow: var(--shadow); }}
    .hud-value-large {{ font-size: 3rem; font-weight: 900; color: var(--text-main); line-height: 1; }}
    
    /* Status Labels */
    .status-sniper {{ background: rgba(16,185,129,0.15); color: var(--accent-green); border: 1px solid var(--accent-green); padding: 5px 15px; border-radius: 50px; font-weight: bold; }}
    .status-warning {{ background: rgba(250,204,21,0.15); color: #d97706; border: 1px solid #facc15; padding: 5px 15px; border-radius: 50px; font-weight: bold; }}
    .status-stop {{ background: rgba(239,68,68,0.15); color: var(--accent-red); border: 1px solid var(--accent-red); padding: 5px 15px; border-radius: 50px; font-weight: bold; }}
    </style>
    """, unsafe_allow_html=True)
