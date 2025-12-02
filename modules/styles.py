import streamlit as st

def inject_theme(theme_mode):
    """Inyecta el CSS dinámico basado en el tema seleccionado."""
    # Colores base (Inspirados en la imagen que mandaste)
    bg_app = "#0b1121"       # Fondo muy oscuro
    bg_card = "#151e32"      # Fondo de las tarjetas (Azul grisáceo)
    text_main = "#f8fafc"
    text_muted = "#94a3b8"
    border_color = "#2a3655"
    accent_green = "#10b981" # Verde TradeZella
    accent_red = "#ef4444"   # Rojo TradeZella

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
    
    /* COLORES DE TEXTO */
    .text-green {{ color: {accent_green} !important; }}
    .text-red {{ color: {accent_red} !important; }}
    .text-white {{ color: {text_main} !important; }}
    
    /* CALENDARIO ESTILO GRID */
    .cal-grid {{ display: grid; grid-template-columns: repeat(7, 1fr); gap: 8px; }}
    .cal-day-box {{
        background-color: {bg_card};
        border: 1px solid {border_color};
        border-radius: 8px;
        min-height: 80px;
        padding: 8px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: transform 0.2s;
    }}
    .cal-day-box:hover {{ border-color: {text_muted}; }}
    
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
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
