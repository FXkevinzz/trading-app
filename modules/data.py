import os
import json
import shutil
import pandas as pd
import streamlit as st
import zipfile

# Constantes de Directorio
DATA_DIR = "user_data"
IMG_DIR = os.path.join(DATA_DIR, "brain_images")
BRAIN_FILE = os.path.join(DATA_DIR, "brain_data.json")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
ACCOUNTS_FILE = os.path.join(DATA_DIR, "accounts_config.json")

def init_filesystem():
    """Garantiza que las carpetas existan."""
    for d in [DATA_DIR, IMG_DIR]:
        if not os.path.exists(d): os.makedirs(d)

# --- Funciones JSON Genéricas ---
def load_json(fp):
    if not os.path.exists(fp): return {}
    try:
        with open(fp, "r") as f: return json.load(f)
    except: return {}

def save_json(fp, data):
    try:
        with open(fp, "w") as f: json.dump(data, f)
    except: pass

# --- Gestión de Usuarios (Auth) ---
def verify_user(u, p):
    if u == "admin" and p == "1234": return True
    d = load_json(USERS_FILE)
    return u in d and d[u] == p

def register_user(u, p):
    d = load_json(USERS_FILE)
    d[u] = p
    save_json(USERS_FILE, d)

# --- Gestión de Cuentas y Trades ---
def get_user_accounts(u):
    d = load_json(ACCOUNTS_FILE)
    return list(d.get(u, {}).keys()) if u in d else ["Principal"]

def create_account(u, name, bal):
    d = load_json(ACCOUNTS_FILE)
    d.setdefault(u, {})[name] = bal
    save_json(ACCOUNTS_FILE, d)
    # Inicializa el CSV vacío
    save_trade(u, name, None, init=True)

@st.cache_data(ttl=5)
def get_balance_data(u, acc):
    d = load_json(ACCOUNTS_FILE)
    ini = d.get(u, {}).get(acc, 0.0)
    fp = os.path.join(DATA_DIR, u, f"{acc}.csv".replace(" ", "_"))
    
    if os.path.exists(fp):
        try:
            df = pd.read_csv(fp)
            pnl = df["Dinero"].sum() if not df.empty else 0
        except:
            df = pd.DataFrame()
            pnl = 0
    else:
        df = pd.DataFrame()
        pnl = 0
    return ini, ini + pnl, df

def save_trade(u, acc, data, init=False):
    folder = os.path.join(DATA_DIR, u)
    if not os.path.exists(folder): os.makedirs(folder)
    fp = os.path.join(folder, f"{acc}.csv".replace(" ", "_"))
    cols = ["Fecha","Par","Tipo","Resultado","Dinero","Ratio","Notas"]
    
    if init:
        if not os.path.exists(fp): pd.DataFrame(columns=cols).to_csv(fp, index=False)
        return

    try:
        df = pd.read_csv(fp) if os.path.exists(fp) else pd.DataFrame(columns=cols)
    except:
        df = pd.DataFrame(columns=cols)
        
    if data:
        df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
        df.to_csv(fp, index=False)
        get_balance_data.clear()

def delete_trade(u, acc, index):
    fp = os.path.join(DATA_DIR, u, f"{acc}.csv".replace(" ", "_"))
    try:
        df = pd.read_csv(fp)
        df = df.drop(index)
        df.to_csv(fp, index=False)
        get_balance_data.clear()
        return True
    except: return False

def load_trades(u, acc):
    fp = os.path.join(DATA_DIR, u, f"{acc}.csv".replace(" ", "_"))
    if os.path.exists(fp):
        try: return pd.read_csv(fp)
        except: pass
    return pd.DataFrame(columns=["Fecha","Par","Tipo","Resultado","Dinero","Ratio","Notas"])

# --- Backup ---
def create_backup_zip():
    shutil.make_archive("backup_trading", 'zip', DATA_DIR)
    return "backup_trading.zip"
