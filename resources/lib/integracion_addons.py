import os
import sqlite3
import xbmcaddon

# Rutas estándar de Alfa y Balandro
ALFA_DB_DEFAULT = os.path.expanduser(os.path.join('~', 'AppData', 'Roaming', 'Kodi', 'userdata', 'addon_data', 'plugin.video.alfa', 'alfa.db'))
BALANDRO_DB_DEFAULT = os.path.expanduser(os.path.join('~', 'AppData', 'Roaming', 'Kodi', 'userdata', 'addon_data', 'plugin.video.balandro', 'balandro.db'))

addon = xbmcaddon.Addon()
def get_alfa_db_path():
    custom = addon.getSetting('alfa_db_path')
    return custom if custom else ALFA_DB_DEFAULT

def get_balandro_db_path():
    custom = addon.getSetting('balandro_db_path')
    return custom if custom else BALANDRO_DB_DEFAULT

# Ejemplo: importar biblioteca de Alfa

def importar_biblioteca_alfa():
    db_path = get_alfa_db_path()
    if not os.path.exists(db_path):
        return []
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT titulo, temporada, episodio, visto FROM biblioteca')
        items = cursor.fetchall()
    except Exception:
        items = []
    conn.close()
    return items

# Ejemplo: importar biblioteca de Balandro

def importar_biblioteca_balandro():
    db_path = get_balandro_db_path()
    if not os.path.exists(db_path):
        return []
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT titulo, temporada, episodio, visto FROM biblioteca')
        items = cursor.fetchall()
    except Exception:
        items = []
    conn.close()
    return items

# Puedes agregar aquí funciones para marcar como visto, sincronizar, etc.
