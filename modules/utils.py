import pandas as pd
import calendar
import streamlit as st
from datetime import datetime
import os

# --- COMPONENTE RELOJ VIVO (HTML/JS) ---
def get_live_clock_html():
    """
    Genera un widget HTML+JS que muestra la hora de NY en tiempo real
    y calcula el estado de la sesión según las reglas de Alex G.
    """
    return """
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
        body { margin: 0; padding: 0; background-color: transparent; font-family: 'Inter', sans-serif; }
        .clock-container {
            background-color: #1a2540; /* Color Fondo Card */
            border: 1px solid #304368;
            border-radius: 12px;
            padding: 15px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
            color: white;
        }
        .label { color: #94a3b8; font-size: 12px; letter-spacing: 1px; font-weight: 700; margin-bottom: 5px; }
        .time { font-size: 32px; font-weight: 900; line-height: 1; margin-bottom: 8px; }
        .status-badge {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 50px;
            font-size: 12px;
            font-weight: 800;
            border: 1px solid transparent;
        }
        .session { color: #64748b; font-size: 11px; margin-top: 10px; font-weight: 500; }
        
        /* Estados */
        .go { background-color: rgba(16, 185, 129, 0.2); color: #10b981; border-color: #10b981; }
        .stop { background-color: rgba(239, 68, 68, 0.2); color: #ef4444; border-color: #ef4444; }
        .warn { background-color: rgba(251, 191, 36, 0.2); color: #fbbf24; border-color: #fbbf24; }
    </style>
    </head>
    <body>
        <div class="clock-container" id="card">
            <div class="label">HORA NY (EST)</div>
            <div class="time" id="time">--:--:--</div>
            <div class="status-badge stop" id="status">CARGANDO...</div>
            <div class="session" id="session">--</div>
        </div>

        <script>
            function updateClock() {
                // 1. Obtener hora NY
                const now = new Date();
                const options = { timeZone: 'America/New_York', hour12: true, hour: 'numeric', minute: '2-digit', second: '2-digit' };
                const timeString = now.toLocaleTimeString('en-US', options);
                
                // 2. Obtener datos crudos para lógica
                const nyDateStr = now.toLocaleString('en-US', { timeZone: 'America/New_York' });
                const nyDate = new Date(nyDateStr);
                const day = nyDate.getDay(); // 0=Dom, 1=Lun, ..., 6=Sab
                const hour = nyDate.getHours();
                const minute = nyDate.getMinutes();

                // 3. Reglas Alex G (11 PM - 11 AM)
                // Rango: Hora >= 23 OR Hora < 11
                const inZone = (hour >= 23) || (hour < 11);
                
                let statusText = "FUERA DE SESIÓN";
                let statusClass = "stop";
                let sessionName = "ASIA 💤";

                // Definir Nombre Sesión
                if (hour >= 2 && hour < 8) sessionName = "LONDRES 🇬🇧";
                else if (hour >= 8 && hour < 12) sessionName = "NY / LONDRES 🇺🇸🇬🇧";
                else if (hour >= 12 && hour < 17) sessionName = "NUEVA YORK 🇺🇸";

                // Lógica Semáforo
                if (day === 6 || day === 0) { // Sábado o Domingo
                    statusText = "CERRADO ❌";
                    statusClass = "stop";
                } else if (day === 5) { // Viernes
                    if (hour < 11) {
                        statusText = "⚠️ VIERNES (Riesgo)";
                        statusClass = "warn";
                    } else {
                        statusText = "CERRADO (Fin de Semana)";
                        statusClass = "stop";
                    }
                } else { // Lunes a Jueves
                    if (inZone) {
                        statusText = "✅ ZONA PRIME (GO)";
                        statusClass = "go";
                        document.getElementById('card').style.borderColor = "#10b981";
                    } else {
                        statusText = "⛔ ESPERAR (Bajo Vol)";
                        statusClass = "stop";
                        document.getElementById('card').style.borderColor = "#ef4444";
                    }
                }

                // 4. Actualizar DOM
                document.getElementById('time').innerText = timeString;
                const statusEl = document.getElementById('status');
                statusEl.innerText = statusText;
                statusEl.className = "status-badge " + statusClass;
                document.getElementById('session').innerText = "Sesión: " + sessionName;
            }

            setInterval(updateClock, 1000); // Actualizar cada segundo
            updateClock(); // Ejecutar inmediatamente
        </script>
    </body>
    </html>
    """

# --- UTILIDADES DE CALENDARIO (PYTHON) ---
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
                txt = f"${val:,.0f}" if val != 0 else ""
                bg = "var(--bg-card)"
                border = "var(--border-color)"
                col = "var(--text-main)"
                
                if val > 0:
                    bg = "rgba(16, 185, 129, 0.15)"; border = "#10b981"; col = "#10b981"
                elif val < 0:
                    bg = "rgba(239, 68, 68, 0.15)"; border = "#ef4444"; col = "#ef4444"

                html += f'''
                <div style="background:{bg}; border:1px solid {border}; border-radius:4px; min-height:50px; padding:4px; display:flex; flex-direction:column; justify-content:space-between;">
                    <div style="color:var(--text-muted); font-size:0.7rem;">{day}</div>
                    <div style="color:{col}; font-weight:bold; font-size:0.75rem; text-align:right;">{txt}</div>
                </div>'''
    html += '</div>'
    return html, y, m

def get_market_status():
    # Placeholder para compatibilidad si alguna función vieja lo llama
    return "--:--", "--", "--", "#333"

def mostrar_imagen(nombre, caption): return None
