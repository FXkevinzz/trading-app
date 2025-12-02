import pandas as pd
import calendar
import pytz
import streamlit as st
from datetime import datetime, time
import requests # LIBRERÍA NUEVA PARA TELEGRAM

# --- FUNCIÓN TELEGRAM (NUEVA) ---
def send_telegram_alert(trade_data, image_path=None):
    """Envía una alerta rica en formato al bot de Telegram."""
    try:
        # 1. Obtener credenciales de los secretos
        if "TELEGRAM_TOKEN" not in st.secrets or "TELEGRAM_CHAT_ID" not in st.secrets:
            return False # No configurado, no hacemos nada

        token = st.secrets["TELEGRAM_TOKEN"]
        chat_id = st.secrets["TELEGRAM_CHAT_ID"]
        
        # 2. Construir el mensaje con Emojis
        # Formato HTML simple soportado por Telegram
        msg = f"""
🦁 <b>NUEVO TRADE REGISTRADO</b>
-----------------------------
<b>Activo:</b> {trade_data['Par']}
<b>Dirección:</b> {trade_data['Direccion']}
<b>Precio Entrada:</b> {trade_data.get('Entry', 'N/A')}
<b>Stop Loss:</b> {trade_data.get('SL', 'N/A')}
<b>Take Profit:</b> {trade_data.get('TP', 'N/A')}
-----------------------------
<b>Riesgo:</b> {trade_data.get('Risk', '1%')}
<b>Lotaje Sugerido:</b> {trade_data.get('Lots', 'N/A')}
-----------------------------
<i>"{trade_data.get('Notes', '')}"</i>
        """

        # 3. Enviar Imagen (si existe) o solo Texto
        if image_path:
            url = f"https://api.telegram.org/bot{token}/sendPhoto"
            with open(image_path, "rb") as img:
                payload = {"chat_id": chat_id, "caption": msg, "parse_mode": "HTML"}
                files = {"photo": img}
                requests.post(url, data=payload, files=files)
        else:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {"chat_id": chat_id, "text": msg, "parse_mode": "HTML"}
            requests.post(url, data=payload)
            
        return True
    except Exception as e:
        print(f"Error Telegram: {e}")
        return False

# --- LÓGICA DE HORARIO (ALEX G) ---
def get_market_status():
    try:
        tz_ny = pytz.timezone('America/New_York')
        now_ny = datetime.now(tz_ny)
        curr_t = now_ny.time()
        
        # Ventana 11 PM - 11 AM
        in_zone = (curr_t >= time(23, 0)) or (curr_t <= time(11, 0))
        wd = now_ny.weekday()
        
        # Nombres de Sesiones
        session_display = "ASIA 🇯🇵"
        if time(3, 0) <= curr_t < time(8, 0): session_display = "LONDRES 🇬🇧"
        elif time(8, 0) <= curr_t < time(12, 0): session_display = "NY / LONDRES 🇺🇸🇬🇧"
        elif time(12, 0) <= curr_t < time(17, 0): session_display = "NUEVA YORK 🇺🇸"
        
        status = "ESPERAR 💤"; color = "#94a3b8"
        
        if wd >= 5: 
            status = "CERRADO ❌"; color = "#ef4444"
        elif wd == 4:
            if curr_t < time(11, 0): status = "⚠️ VIERNES"; color = "#fbbf24"
            else: status = "CERRADO"; color = "#ef4444"
        elif in_zone:
            status = "✅ ZONA DE TRADING"; color = "#10b981"
        else:
            status = "⛔ FUERA DE SESIÓN"; color = "#ef4444"

        return now_ny.strftime("%I:%M %p"), session_display, status, color
    except: return "--:--", "Error", "Error", "#333"

# --- COMPONENTE RELOJ VIVO (JS) ---
def get_live_clock_html():
    return """
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
        body { margin: 0; padding: 0; background-color: transparent; font-family: 'Inter', sans-serif; }
        .clock-container {
            background-color: #1a2540; border: 1px solid #304368;
            border-radius: 12px; padding: 15px; text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2); color: white;
        }
        .label { color: #94a3b8; font-size: 12px; font-weight: 700; margin-bottom: 5px; }
        .time { font-size: 32px; font-weight: 900; line-height: 1; margin-bottom: 8px; }
        .status-badge { display: inline-block; padding: 6px 12px; border-radius: 50px; font-size: 12px; font-weight: 800; }
        .go { background-color: rgba(16, 185, 129, 0.2); color: #10b981; }
        .stop { background-color: rgba(239, 68, 68, 0.2); color: #ef4444; }
        .warn { background-color: rgba(251, 191, 36, 0.2); color: #fbbf24; }
    </style>
    </head>
    <body>
        <div class="clock-container"><div class="label">HORA NY (EST)</div><div class="time" id="time">--:--:--</div><div class="status-badge stop" id="status">...</div></div>
        <script>
            function updateClock() {
                const now = new Date();
                const options = { timeZone: 'America/New_York', hour12: true, hour: 'numeric', minute: '2-digit', second: '2-digit' };
                document.getElementById('time').innerText = now.toLocaleTimeString('en-US', options);
                
                const nyDate = new Date(now.toLocaleString('en-US', { timeZone: 'America/New_York' }));
                const h = nyDate.getHours(); const d = nyDate.getDay();
                const inZone = (h >= 23) || (h < 11);
                
                let s = "FUERA DE SESIÓN", c = "stop";
                if (d===0||d===6) { s="CERRADO ❌"; }
                else if (d===5) { s = h<11 ? "⚠️ VIERNES" : "CERRADO"; c = h<11 ? "warn" : "stop"; }
                else if (inZone) { s="✅ ZONA PRIME"; c="go"; }
                
                const el = document.getElementById('status');
                el.innerText = s; el.className = "status-badge " + c;
            }
            setInterval(updateClock, 1000); updateClock();
        </script>
    </body>
    </html>
    """

def render_cal_html(df, is_dark):
    d = st.session_state.get('cal_date', datetime.now())
    y, m = d.year, d.month
    data = {}
    if not df.empty:
        try:
            df['Fecha'] = pd.to_datetime(df['Fecha'])
            data = df[(df['Fecha'].dt.year==y) & (df['Fecha'].dt.month==m)].groupby(df['Fecha'].dt.day)['Dinero'].sum().to_dict()
        except: pass
    cal = calendar.Calendar(firstweekday=0)
    html = '<div style="display:grid; grid-template-columns:repeat(7, 1fr); gap:5px; margin-top:10px;">'
    for h in ["L","M","M","J","V","S","D"]: html += f'<div style="text-align:center; color:#64748b; font-size:0.65rem;">{h}</div>'
    for week in cal.monthdayscalendar(y, m):
        for day in week:
            if day==0: html+='<div></div>'
            else:
                val=data.get(day,0)
                col="#10b981" if val>0 else "#ef4444" if val<0 else "#64748b"
                bg="rgba(16,185,129,0.1)" if val>0 else "rgba(239,68,68,0.1)" if val<0 else "#1e293b"
                html+=f'<div style="background:{bg}; border:1px solid {col if val!=0 else "#2a3655"}; border-radius:4px; height:40px; font-size:0.7rem; padding:2px;">{day}</div>'
    return html+'</div>', y, m

def mostrar_imagen(n, c): return None
