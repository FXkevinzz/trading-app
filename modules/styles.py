import streamlit as st

def inject_theme(theme_mode):
    # Colores base (Inspirados en la imagen que mandaste)
    bg_app = "#0b1121"       # Fondo muy oscuro
    bg_card = "#151e32"      # Fondo de las tarjetas (Azul grisáceo)
    text_main = "#f8fafc"
    text_muted = "#94a3b8"
    border_color = "#2a3655"
    accent_green = "#10b981" # Verde TradeZella
    accent_red = "#ef4444"   # Rojo TradeZella
    accent = "#3b82f6"       # Azul de acento

    css = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;900&display=swap');
    
    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
        background-color: {bg_app};
        color: {text_main};
    }}

    .stApp {{ background-color: {bg_app}; }}

    /* ESTILOS DE TARJETAS (DASHBOARD) */
    .dashboard-card {{
        background-color: {bg_card};
        border: 1px solid {border_color};
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }}
    
    .big-pnl {{ font-size: 3.5rem; font-weight: 900; line-height: 1; }}
    .sub-stat-label {{ color: {text_muted}; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }}
    .sub-stat-value {{ font-size: 1.5rem; font-weight: 700; color: {text_main}; }}
    
    /* HUD PUNTAJE (CAJA DE LA OPERATIVA) */
    .hud-container {{ 
        background: {bg_card}; 
        border: 1px solid {border_color}; /* Bordes bien definidos */
        padding: 15px; 
        border-radius: 12px;
        display: flex; 
        align-items: center; 
    }}
    .status-sniper {{ background-color: rgba(16, 185, 129, 0.2); color: {accent_green}; border: 1px solid {accent_green}; padding: 5px 10px; border-radius: 50px; font-weight: bold; }}
    .status-warning {{ background-color: rgba(251, 191, 36, 0.2); color: #fbbf24; border: 1px solid #fbbf24; padding: 5px 10px; border-radius: 50px; font-weight: bold; }}
    .status-stop {{ background-color: rgba(239, 68, 68, 0.2); color: {accent_red}; border: 1px solid {accent_red}; padding: 5px 10px; border-radius: 50px; font-weight: bold; }}
    
    /* SIDEBAR */
    [data-testid="stSidebar"] {{ background-color: #020617; border-right: 1px solid {border_color}; }}
    
    /* BOTONES */
    .stButton button {{
        background-color: {accent_green};
        color: white;
        border-radius: 8px;
        font-weight: 600;
        border: none;
    }}
    
    /* Estilo de la cabecera de estrategia */
    .strategy-header {{ color: {accent_green}; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; border-bottom: 1px solid {border_color}; padding-bottom: 8px; }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
