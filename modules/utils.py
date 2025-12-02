import pandas as pd
import plotly.express as px
import calendar
import pytz
import streamlit as st
from datetime import datetime, time
from modules.data import IMG_DIR 
import os

def render_heatmap(df, is_dark):
    if df.empty: return None
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    df['Dia'] = df['Fecha'].dt.day_name()
    grouped = df.groupby('Dia')['Dinero'].sum().reset_index()
    fig = px.bar(grouped, x='Dia', y='Dinero', color='Dinero', color_continuous_scale=['red', 'green'])
    bg = 'rgba(0,0,0,0)'
    text_col = '#94a3b8' if is_dark else '#0f172a'
    fig.update_layout(paper_bgcolor=bg, plot_bgcolor=bg, font=dict(color=text_col), title="PnL por Día")
    return fig

def render_cal_html(df, is_dark):
    d = st.session_state.get('cal_date', datetime.now())
    y, m = d.year, d.month
    data = {}
    if not df.empty:
        try:
            df['Fecha'] = pd.to_datetime(df['Fecha'])
            df_m = df[(df['Fecha'].dt.year==y) & (df['Fecha'].dt.month==m)]
            data = df_m.groupby(df['Fecha'].dt.day)['Dinero'].sum().to_dict()
        except: pass

    cal = calendar.Calendar(firstweekday=0)
    html = '<div style="display:grid; grid-template-columns:repeat(7, 1fr); gap:8px; margin-top:15px;">'
    day_col = "#94a3b8" if is_dark else "#64748b"
    for h in ["LUN","MAR","MIÉ","JUE","VIE","SÁB","DOM"]: 
        html += f'<div style="text-align:center; color:{day_col}; font-size:0.8rem; font-weight:bold; padding:5px;">{h}</div>'
    
    for week in cal.monthdayscalendar(y, m):
        for day in week:
            if day == 0: html += '<div style="opacity:0;"></div>'
            else:
                val = data.get(day, 0)
                txt = f"${val:,.0f}" if val != 0 else ""
                bg, border, col = "var(--bg-card)", "var(--border-color)", "var(--text-main)"
                if val > 0: bg, border, col = "rgba(16, 185, 129, 0.15)", "var(--accent-green)", "var(--accent-green)"
                elif val < 0: bg, border, col = "rgba(239, 68, 68, 0.15)", "var(--accent-red)", "var(--accent-red)"

                html += f'''<div style="background:{bg}; border:1px solid {border}; border-radius:8px; min-height:80px; padding:10px; display:flex; flex-direction:column; justify-content:space-between;">
                            <div style="color:var(--text-muted); font-size:0.8rem; font-weight:bold;">{day}</div>
                            <div style="color:{col}; font-weight:bold; text-align:right;">{txt}</div></div>'''
    html += '</div>'
    return html, y, m

def get_market_status():
    try:
        tz_ny = pytz.timezone('America/New_York')
        now_ny = datetime.now(tz_ny)
        weekday, current_time = now_ny.weekday(), now_ny.time()
        
        session_name = "ASIA (TOKIO)"
        if time(3,0) <= current_time < time(8,0): session_name = "LONDRES 🇬🇧"
        elif time(8,0) <= current_time < time(12,0): session_name = "NY / LONDRES 🇺🇸🇬🇧"
        elif time(12,0) <= current_time < time(17,0): session_name = "NUEVA YORK 🇺🇸"
        
        status, color = "🔴 CERRADO", "#ff4444"
        is_open = current_time >= time(23,0) or current_time <= time(11,0) # Logica simplificada 24/5 forex
        
        # Logica rapida de ejemplo (ajustar segun necesidad exacta)
        if weekday < 4:
            status, color = ("🟢 ZONA PRIME", "#00e676") if (time(2,0) <= current_time <= time(11,0)) else ("💤 BAJO VOLUMEN", "#ffca28")
        elif weekday == 4 and current_time < time(16,0):
             status, color = ("⚠️ VIERNES", "#ffca28")
        elif weekday >= 5:
             status, color = ("❌ WEEKEND", "#ff4444")
             
        return now_ny.strftime("%I:%M %p"), session_name, status, color
    except: return "--:--", "--", "--", "#333"

def mostrar_imagen(nombre, caption):
    # Logica simplificada de imagenes locales vs web
    local = os.path.join(IMG_DIR, nombre)
    if os.path.exists(local): st.image(local, caption=caption, use_container_width=True)
