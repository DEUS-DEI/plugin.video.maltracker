def get_all_history():
    conn = connect()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM history')
    rows = cursor.fetchall()
    conn.close()
    return rows
import xbmc
import xbmcvfs
import xbmcgui
import xbmcplugin
import xbmcaddon
import sqlite3
import os
import sys

# Addon handle
_HANDLE = int(sys.argv[1])

# Addon base URL
_URL = sys.argv[0]

# Get addon directory
_ADDON_PATH = xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('path'))

# Database file path
_DB_FILE = os.path.join(xbmcvfs.translatePath('special://userdata/addon_data/plugin.video.maltracker'), 'maltracker.db')

def connect():
    # Ensure directory exists
    db_dir = os.path.dirname(_DB_FILE)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)

    # Connect to database
    conn = sqlite3.connect(_DB_FILE)
    return conn

_tables_created = False

def create_tables():
    global _tables_created
    if _tables_created:
        return

    conn = connect()
    cursor = conn.cursor()

    # Create anime table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS anime (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mal_id INTEGER,
            title TEXT,
            status TEXT,
            episodes_watched INTEGER
        )
    ''')

    # Create history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            anime_id INTEGER,
            episode INTEGER,
            date TEXT,
            addon_id TEXT,
            FOREIGN KEY (anime_id) REFERENCES anime (id)
        )
    ''')

    conn.commit()
    conn.close()
    _tables_created = True

def get_anime(anime_id):
    conn = connect()
    cursor = conn.cursor()

    # Get anime from database
    cursor.execute('''
        SELECT * FROM anime WHERE id = ?
    ''', (anime_id,))

    anime = cursor.fetchone()
    conn.close()
    return anime

def add_anime(mal_id, title, status, episodes_watched=0):
    conn = connect()
    cursor = conn.cursor()

    # Add anime to database
    cursor.execute('''
        INSERT INTO anime (mal_id, title, status, episodes_watched) VALUES (?, ?, ?, ?)
    ''', (mal_id, title, status, episodes_watched))

    conn.commit()
    conn.close()

def update_anime(anime_id, status, episodes_watched):
    conn = connect()
    cursor = conn.cursor()

    # Update anime in database
    cursor.execute('''
        UPDATE anime SET status = ?, episodes_watched = ? WHERE id = ?
    ''', (status, episodes_watched, anime_id))

    conn.commit()
    conn.close()

def add_history(anime_id, episode, date, addon_id):
    conn = connect()
    cursor = conn.cursor()

    # Add history to database
    cursor.execute('''
        INSERT INTO history (anime_id, episode, date, addon_id) VALUES (?, ?, ?, ?)
    ''', (anime_id, episode, date, addon_id))

    conn.commit()
    conn.close()

def log_playback(title, episode, addon_id):
    conn = connect()
    cursor = conn.cursor()

    # Get anime from database by title
    cursor.execute('''
        SELECT id, mal_id FROM anime WHERE title = ?
    ''', (title,))
    result = cursor.fetchone()

    if result:
        anime_id = result[0]
        mal_id = result[1]
    else:
        # Add anime to database if it doesn't exist
        # Need to get mal_id first
        import resources.lib.mal_api as mal_api
        mal_id = mal_api.search_anime(title)
        if mal_id is None:
            mal_id = 0
        add_anime(mal_id, title, 'watching')
        cursor.execute('''
            SELECT id FROM anime WHERE title = ?
        ''', (title,))
        result = cursor.fetchone()
        if result:
            anime_id = result[0]
        else:
            anime_id = None

    # Add history to database
    import datetime
    date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        INSERT INTO history (anime_id, episode, date, addon_id) VALUES (?, ?, ?, ?)
    ''', (anime_id, episode, date, addon_id))

    conn.commit()

    # Update episode on MAL
    import resources.lib.mal_api as mal_api
    if mal_id is not None and mal_id != 0:
        if mal_api.update_episode(mal_id, episode):
            xbmc.executebuiltin('Notification(MAL Tracker, Episodio actualizado en MAL)')
        else:
            xbmc.executebuiltin('Notification(MAL Tracker, Error al actualizar episodio en MAL)')

    conn.close()

# Create tables on import
create_tables()
