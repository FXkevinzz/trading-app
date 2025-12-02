import pandas as pd
import plotly.express as px
import calendar
import pytz
import streamlit as st
from datetime import datetime, time
from modules.data import IMG_DIR 
import os

# --- LÓGICA DE HORARIO (PDF ALEX G) ---
def get_market_status():
    try:
        # 1. Definir Zona Horaria NY (EST)
        tz_ny = pytz.timezone('America/New_York')
        now_ny = datetime.now(tz_ny)
        
        # 2. Definir Ventana de Trading (23:00 - 11:00)
        # Nota: Como cruza la medianoche, la lógica es:
        # O es tarde en la noche (> 23:00) O es temprano en la mañana (< 11:00)
        current_time = now_ny.time()
        start_time = time(23, 0) # 11 PM
        end_time = time(11, 0)   # 11 AM
        
        in_time_window = (current_time >= start_time) or (current_time <= end_time)
        
        # 3. Definir Días (0=Lun, 6=Dom)
        weekday = now_ny.weekday()
        is_weekend = weekday >= 5 # Sabado(5) o Domingo(6)
        is_friday = weekday == 4
        
        # 4. Determinar Sesión Actual
        session_name = "ASIA (Consolidación)"
        if time(2, 0) <= current_time < time(8, 0):
            session_name = "LONDRES 🇬🇧"
        elif time(8, 0) <= current_time < time(12, 0):
            session_name = "NY / LONDRES (Cruce) 🇺🇸🇬🇧"
        elif time(12, 0) <= current_time < time(17, 0):
            session_name = "NUEVA YORK 🇺🇸"
        
        # 5. Determinar ESTADO DE ESTRATEGIA (Semáforo)
        # Regla PDF: Lun-Jue (Mejor), Vie (Cuidado), Dom (No)
        # Regla PDF: 11pm - 11am EST
        
        status_text = "ESPERAR 💤"
        color = "#94a3b8" # Gris
        
        if is_weekend:
            status_text = "MERCADO CERRADO ❌"
            color = "#ef4444" # Rojo
        
        elif in_time_window:
            if weekday <= 3: # Lun, Mar, Mie, Jue
                status_text = "✅ ZONA DE TRADING (GO)"
                color = "#10b981" # Verde
            elif is_friday and current_time < time(11, 0):
                status_text = "⚠️ VIERNES (CUIDADO)"
                color = "#fbbf24" # Amarillo
        else:
            status_text = "⛔ FUERA DE SESIÓN"
            color = "#ef4444" # Rojo si no es hora
            
            # Excepción: Si es Lunes-Jueves pero fuera de hora (ej: 2pm), es "Bajo Volumen"
            if weekday <= 3 and not in_time_window:
                status_text = "💤 BAJO VOLUMEN"
                color = "#f59e0b" # Naranja

        return now_ny.strftime("%I:%M %p"), session_name, status_text, color
        
    except Exception as e:
        return "--:--", "Error", str(e), "#333"

# --- UTILIDADES VISUALES (MANTENER IGUAL) ---
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
        html += f'<div style="text-align:center; color:{day_col}; font-size:0.7rem; font-weight:bold; padding:5px;">{h}</div>'
    
    for week in cal.monthdayscalendar(y, m):
        for day in week:
            if day == 0: html += '<div style="opacity:0;"></div>'
            else:
                val = data.get(day, 0)
                txt = f"${val:,.0f}" if val != 0 else ""
                bg = "var(--bg-card)"
                border = "var(--border-color)"
                col = "var(--text-main)"
                
                if val > 0:
                    bg = "rgba(16, 185, 129, 0.15)"
                    border = "#10b981"
                    col = "#10b981"
                elif val < 0:
                    bg = "rgba(239, 68, 68, 0.15)"
                    border = "#ef4444"
                    col = "#ef4444"

                html += f'''
                <div style="background:{bg}; border:1px solid {border}; border-radius:6px; min-height:60px; padding:5px; display:flex; flex-direction:column; justify-content:space-between;">
                    <div style="color:var(--text-muted); font-size:0.7rem;">{day}</div>
                    <div style="color:{col}; font-weight:bold; font-size:0.8rem; text-align:right;">{txt}</div>
                </div>'''
    html += '</div>'
    return html, y, m

def render_heatmap(df, is_dark):
    return None # Placeholder si no se usa

def mostrar_imagen(nombre, caption):
    return None
