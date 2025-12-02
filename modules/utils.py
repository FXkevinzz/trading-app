import pandas as pd
import calendar
import pytz
import streamlit as st
from datetime import datetime, time
import os

# --- LÓGICA DE HORARIO (PDF ALEX G) ---
def get_market_status():
    try:
        # 1. Definir Zona Horaria NY (EST)
        tz_ny = pytz.timezone('America/New_York')
        now_ny = datetime.now(tz_ny)
        
        # 2. Definir Ventana de Trading (23:00 - 11:00)
        # La lógica es: Si es más tarde de las 23:00 O más temprano de las 11:00
        curr_t = now_ny.time()
        start_t = time(23, 0) # 11 PM
        end_t = time(11, 0)   # 11 AM
        
        # ¿Estamos en la ventana de Alex G?
        in_zone = (curr_t >= start_t) or (curr_t <= end_t)
        
        # 3. Definir Días (0=Lun, ... 4=Vie, 5=Sab, 6=Dom)
        wd = now_ny.weekday()
        
        # Nombres de Sesiones para mostrar
        session_display = "ASIA 🇯🇵"
        if time(3, 0) <= curr_t < time(8, 0): session_display = "LONDRES 🇬🇧"
        elif time(8, 0) <= curr_t < time(12, 0): session_display = "NY / LONDRES 🇺🇸🇬🇧"
        elif time(12, 0) <= curr_t < time(17, 0): session_display = "NUEVA YORK 🇺🇸"
        
        # 4. Semáforo de Estrategia
        status = "ESPERAR 💤"
        color = "#94a3b8" # Gris
        
        if wd >= 5: # Finde
            status = "CERRADO ❌"
            color = "#ef4444"
        elif wd == 4: # Viernes
            if curr_t < time(11, 0):
                status = "⚠️ VIERNES (Riesgo)"
                color = "#fbbf24" # Amarillo
            else:
                status = "CERRADO (Fin de Semana)"
                color = "#ef4444"
        elif in_zone: # Lunes a Jueves dentro de horario
            status = "✅ ZONA DE TRADING"
            color = "#10b981" # Verde Neon
        else: # Lunes a Jueves pero fuera de horario (ej: 3 PM)
            status = "⛔ FUERA DE SESIÓN"
            color = "#ef4444" # Rojo

        return now_ny.strftime("%I:%M %p"), session_display, status, color
        
    except Exception as e:
        return "--:--", "Error", "Error", "#333"

# --- UTILIDADES VISUALES (MANTENER) ---
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
    html = '<div style="display:grid; grid-template-columns:repeat(7, 1fr); gap:5px; margin-top:10px;">'
    day_col = "#94a3b8" if is_dark else "#64748b"
    for h in ["LUN","MAR","MIÉ","JUE","VIE","SÁB","DOM"]: 
        html += f'<div style="text-align:center; color:{day_col}; font-size:0.65rem; font-weight:bold;">{h}</div>'
    
    for week in cal.monthdayscalendar(y, m):
        for day in week:
            if day == 0: html += '<div></div>'
            else:
                val = data.get(day, 0)
                bg = "var(--bg-card)"; border = "var(--border-color)"; col = "var(--text-muted)"
                if val > 0: bg="rgba(16,185,129,0.15)"; border="#10b981"; col="#10b981"
                elif val < 0: bg="rgba(239,68,68,0.15)"; border="#ef4444"; col="#ef4444"
                
                html += f'''<div style="background:{bg}; border:1px solid {border}; border-radius:4px; height:50px; padding:4px; font-size:0.7rem; display:flex; flex-direction:column; justify-content:space-between;">
                    <span>{day}</span><span style="color:{col}; font-weight:bold; align-self:flex-end;">{f"${val:,.0f}" if val!=0 else ""}</span>
                </div>'''
    return html + '</div>', y, m

def mostrar_imagen(nombre, caption): return None
