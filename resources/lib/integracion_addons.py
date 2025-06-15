
import os
import sqlite3
import xbmcaddon
import xbmcvfs

# Rutas estándar de Alfa y Balandro

# Usar rutas multiplataforma de Kodi
ALFA_DB_DEFAULT = 'special://userdata/addon_data/plugin.video.alfa/alfa.db'
BALANDRO_DB_DEFAULT = 'special://userdata/addon_data/plugin.video.balandro/balandro.db'

addon = xbmcaddon.Addon()

def get_alfa_db_path():
    custom = addon.getSetting('alfa_db_path')
    if custom:
        return xbmcvfs.translatePath(custom)
    return xbmcvfs.translatePath(ALFA_DB_DEFAULT)


def get_balandro_db_path():
    custom = addon.getSetting('balandro_db_path')
    if custom:
        return xbmcvfs.translatePath(custom)
    return xbmcvfs.translatePath(BALANDRO_DB_DEFAULT)

# Ejemplo: importar biblioteca de Alfa


def importar_biblioteca_alfa():
    db_path = get_alfa_db_path()
    if not xbmcvfs.exists(db_path):
        return []
    # Copiar a ruta temporal para acceso seguro multiplataforma
    import tempfile
    temp_db = tempfile.NamedTemporaryFile(delete=False)
    temp_db.close()
    xbmcvfs.copy(db_path, temp_db.name)
    conn = sqlite3.connect(temp_db.name)
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT titulo, temporada, episodio, visto FROM biblioteca')
        items = cursor.fetchall()
    except Exception:
        items = []
    conn.close()
    os.unlink(temp_db.name)
    return items

# Ejemplo: importar biblioteca de Balandro


def importar_biblioteca_balandro():
    db_path = get_balandro_db_path()
    if not xbmcvfs.exists(db_path):
        return []
    import tempfile
    temp_db = tempfile.NamedTemporaryFile(delete=False)
    temp_db.close()
    xbmcvfs.copy(db_path, temp_db.name)
    conn = sqlite3.connect(temp_db.name)
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT titulo, temporada, episodio, visto FROM biblioteca')
        items = cursor.fetchall()
    except Exception:
        items = []
    conn.close()
    os.unlink(temp_db.name)
    return items

# Puedes agregar aquí funciones para marcar como visto, sincronizar, etc.
