
import xbmc
import xbmcvfs
import xbmcgui
import xbmcplugin
import xbmcaddon
import sys
import os
from resources.lib import monitor

# Addon handle
HANDLE = int(sys.argv[1])

# Addon base URL
BASE_URL = sys.argv[0]

# Get addon directory
ADDON_PATH = xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('path'))

# Get the settings path
settings_file = os.path.join(ADDON_PATH, 'resources', 'settings.xml')

def get_url(params):
    url = BASE_URL
    if params:
        url += '?' + '&'.join([f'{key}={value}' for key, value in params.items()])
    return url

def main_menu():
    add_directory_item('Importar Alfa', {'action': 'import_alfa'})
    add_directory_item('Importar Balandro', {'action': 'import_balandro'})
    # Create main menu items
    add_directory_item('Watching', {'action': 'my_list', 'status': 'watching'})
    add_directory_item('Completed', {'action': 'my_list', 'status': 'completed'})
    add_directory_item('On Hold', {'action': 'my_list', 'status': 'on_hold'})
    add_directory_item('Dropped', {'action': 'my_list', 'status': 'dropped'})
    add_directory_item('Plan to Watch', {'action': 'my_list', 'status': 'plan_to_watch'})
    add_directory_item('Estadísticas', {'action': 'stats'})
    add_directory_item('Calendario', {'action': 'calendar'})
    add_directory_item('Export Data', {'action': 'export_data'})
    add_directory_item('Import Data', {'action': 'import_data'})
    add_directory_item('Search Anime', {'action': 'search'})
    add_directory_item('Ayuda / Cómo configurar', {'action': 'help'})
    add_directory_item('Importar configuración API', {'action': 'import_api_config'})

    # End of directory
    xbmcplugin.endOfDirectory(HANDLE)

import resources.lib.mal_api as mal_api

def my_list():
    # Get the status from the parameters
    from urllib.parse import parse_qs
    params = dict(parse_qs(sys.argv[2][1:]))
    status = params.get('status', ['watching'])[0]
    # Filtros avanzados
    keyboard = xbmc.Keyboard('', 'Buscar título (opcional)')
    keyboard.doModal()
    search_term = keyboard.getText() if keyboard.isConfirmed() else None
    genre = xbmcgui.Dialog().input('Filtrar por género (opcional)')
    year = xbmcgui.Dialog().input('Filtrar por año (opcional)')
    min_score = xbmcgui.Dialog().numeric(0, 'Puntaje mínimo (opcional)')
    min_score = int(min_score) if min_score else 0
    anime_list = mal_api.get_anime_list()
    if anime_list:
        for anime in anime_list:
            title = anime['node']['title']
            anime_id = anime['node']['id']
            list_status = anime['list_status']['status']
            score = anime['list_status'].get('score', 0)
            episodes_watched = anime['list_status'].get('num_episodes_watched', 0)
            genres = ','.join(anime['node'].get('genres', [])) if 'genres' in anime['node'] else ''
            aired_year = str(anime['node'].get('start_date', '')[:4]) if anime['node'].get('start_date') else ''
            if (
                list_status == status and
                (not search_term or search_term.lower() in title.lower()) and
                (not genre or genre.lower() in genres.lower()) and
                (not year or year == aired_year) and
                score >= min_score
            ):
                list_item = xbmcgui.ListItem(title)
                context_menu = [
                    ("Registrar episodio manualmente", f"RunPlugin({get_url({'action': 'manual_log', 'anime_id': anime_id})})"),
                    ("Ver detalles", f"RunPlugin({get_url({'action': 'details', 'anime_id': anime_id})})"),
                    ("Marcar episodio como visto", f"RunPlugin({get_url({'action': 'mark_watched', 'anime_id': anime_id})})"),
                    ("Cambiar estado", f"RunPlugin({get_url({'action': 'change_status', 'anime_id': anime_id})})")
                ]
                list_item.addContextMenuItems(context_menu)
                url = get_url({'action': 'play', 'anime_id': anime_id})
                xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=list_item, isFolder=False)
        xbmcplugin.endOfDirectory(HANDLE)
    else:
        dialog = xbmcgui.Dialog()
        dialog.ok("MAL Tracker", "Failed to get your anime list from MAL.")
        xbmcplugin.endOfDirectory(HANDLE)

import sqlite3
import json
import csv

def export_data():
    # Ask the user what they want to export
    dialog = xbmcgui.Dialog()
    options = ['Anime List', 'History']
    choice = dialog.select('Export Data', options)

    if choice == 0:
        # Export anime list
        export_anime_list()
    elif choice == 1:
        # Export history
        export_history()
    else:
        return

def export_anime_list():
    # Ask the user what format they want to export to
    dialog = xbmcgui.Dialog()
    options = ['CSV', 'JSON']
    choice = dialog.select('Export Format', options)

    if choice == 0:
        # Export to CSV
        export_anime_list_csv()
    elif choice == 1:
        # Export to JSON
        export_anime_list_json()
    else:
        return

def export_history():
    # Ask the user what format they want to export to
    dialog = xbmcgui.Dialog()
    options = ['CSV', 'JSON']
    choice = dialog.select('Export Format', options)

    if choice == 0:
        # Export to CSV
        export_history_csv()
    elif choice == 1:
        # Export to JSON
        export_history_json()
    else:
        return

def export_anime_list_csv():
    # Get the database connection
    conn = sqlite3.connect(os.path.join(xbmcvfs.translatePath('special://userdata/addon_data/plugin.video.maltracker'), 'maltracker.db'))
    cursor = conn.cursor()

    # Get the anime list
    cursor.execute('SELECT * FROM anime')
    anime_list = cursor.fetchall()

    # Ask the user where they want to save the file
    dialog = xbmcgui.Dialog()
    file_path = dialog.browse(0, 'Export Anime List', 'files', '.csv')

    if file_path:
        # Write the anime list to the CSV file
        with open(file_path, 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            csvwriter.writerow(['id', 'mal_id', 'title', 'status', 'episodes_watched'])
            for anime in anime_list:
                csvwriter.writerow(anime)

        # Show a notification
        xbmc.executebuiltin('Notification(MAL Tracker, Anime list exported to CSV)')

    # Close the database connection
    conn.close()

def export_anime_list_json():
    # Get the database connection
    conn = sqlite3.connect(os.path.join(xbmcvfs.translatePath('special://userdata/addon_data/plugin.video.maltracker'), 'maltracker.db'))
    cursor = conn.cursor()

    # Get the anime list
    cursor.execute('SELECT * FROM anime')
    anime_list = cursor.fetchall()

    # Ask the user where they want to save the file
    dialog = xbmcgui.Dialog()
    file_path = dialog.browse(0, 'Export Anime List', 'files', '.json')

    if file_path:
        # Write the anime list to the JSON file
        with open(file_path, 'w') as jsonfile:
            json.dump(anime_list, jsonfile)

        # Show a notification
        xbmc.executebuiltin('Notification(MAL Tracker, Anime list exported to JSON)')

    # Close the database connection
    conn.close()

def export_history_csv():
    # Get the database connection
    conn = sqlite3.connect(os.path.join(xbmcvfs.translatePath('special://userdata/addon_data/plugin.video.maltracker'), 'maltracker.db'))
    cursor = conn.cursor()

    # Get the history
    cursor.execute('SELECT * FROM history')
    history = cursor.fetchall()

    # Ask the user where they want to save the file
    dialog = xbmcgui.Dialog()
    file_path = dialog.browse(0, 'Export History', 'files', '.csv')

    if file_path:
        # Write the history to the CSV file
        with open(file_path, 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            csvwriter.writerow(['id', 'anime_id', 'episode', 'date', 'addon_id'])
            for item in history:
                csvwriter.writerow(item)

        # Show a notification
        xbmc.executebuiltin('Notification(MAL Tracker, History exported to CSV)')

    # Close the database connection
    conn.close()

def export_history_json():
    # Get the database connection
    conn = sqlite3.connect(os.path.join(xbmcvfs.translatePath('special://userdata/addon_data/plugin.video.maltracker'), 'maltracker.db'))
    cursor = conn.cursor()

    # Get the history
    cursor.execute('SELECT * FROM history')
    history = cursor.fetchall()

    # Ask the user where they want to save the file
    dialog = xbmcgui.Dialog()
    file_path = dialog.browse(0, 'Export History', 'files', '.json')

    if file_path:
        # Write the history to the JSON file
        with open(file_path, 'w') as jsonfile:
            json.dump(history, jsonfile)

        # Show a notification
        xbmc.executebuiltin('Notification(MAL Tracker, History exported to JSON)')

    # Close the database connection
    conn.close()

def import_data():
    # Ask the user what format they want to import from
    dialog = xbmcgui.Dialog()
    options = ['CSV', 'JSON']
    choice = dialog.select('Import Format', options)

    if choice == 0:
        # Import from CSV
        import_csv()
    elif choice == 1:
        # Import from JSON
        import_json()
    else:
        return

def import_csv():
    # Ask the user what file they want to import
    dialog = xbmcgui.Dialog()
    file_path = dialog.browse(1, 'Import CSV File', 'files', '.csv')

    if file_path:
        # Import the data from the CSV file
        try:
            with open(file_path, 'r', newline='') as csvfile:
                csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')
                header = next(csvreader)
                if header == ['id', 'mal_id', 'title', 'status', 'episodes_watched']:
                    # Import anime list
                    for row in csvreader:
                        try:
                            mal_id = int(row[1])
                            title = row[2]
                            status = row[3]
                            episodes_watched = int(row[4])
                            # Add the anime to the database
                            conn = sqlite3.connect(os.path.join(xbmcvfs.translatePath('special://userdata/addon_data/plugin.video.maltracker'), 'maltracker.db'))
                            cursor = conn.cursor()
                            cursor.execute('INSERT INTO anime (mal_id, title, status, episodes_watched) VALUES (?, ?, ?, ?)', (mal_id, title, status, episodes_watched))
                            conn.commit()
                            conn.close()
                        except Exception as e:
                            xbmcgui.Dialog().ok("MAL Tracker", f"Error importing row: {row}\n{e}")
                elif header == ['id', 'anime_id', 'episode', 'date', 'source']:
                    # Import history
                    for row in csvreader:
                        try:
                            anime_id = int(row[1])
                            episode = int(row[2])
                            date = row[3]
                            source = row[4]
                            # Add the history item to the database
                            conn = sqlite3.connect(os.path.join(xbmcvfs.translatePath('special://userdata/addon_data/plugin.video.maltracker'), 'maltracker.db'))
                            cursor = conn.cursor()
                            cursor.execute('INSERT INTO history (anime_id, episode, date, addon_id) VALUES (?, ?, ?, ?)', (anime_id, episode, date, source))
                            conn.commit()
                            conn.close()
                        except Exception as e:
                            xbmcgui.Dialog().ok("MAL Tracker", f"Error importing row: {row}\n{e}")
                else:
                    xbmcgui.Dialog().ok("MAL Tracker", "Invalid CSV file format.")
        except Exception as e:
            xbmcgui.Dialog().ok("MAL Tracker", f"Error importing CSV file:\n{e}")
        else:
            xbmc.executebuiltin('Notification(MAL Tracker, Data imported from CSV)')

def import_json():
    # Ask the user what file they want to import
    dialog = xbmcgui.Dialog()
    file_path = dialog.browse(1, 'Import JSON File', 'files', '.json')

    if file_path:
        # Import the data from the JSON file
        try:
            with open(file_path, 'r') as jsonfile:
                data = json.load(jsonfile)
                if isinstance(data, list):
                    # Import anime list
                    if len(data) > 0 and isinstance(data[0], list) and len(data[0]) == 5:
                        for row in data:
                            try:
                                mal_id = int(row[1])
                                title = row[2]
                                status = row[3]
                                episodes_watched = int(row[4])
                                # Add the anime to the database
                                conn = sqlite3.connect(os.path.join(xbmcvfs.translatePath('special://userdata/addon_data/plugin.video.maltracker'), 'maltracker.db'))
                                cursor = conn.cursor()
                                cursor.execute('INSERT INTO anime (mal_id, title, status, episodes_watched) VALUES (?, ?, ?, ?)', (mal_id, title, status, episodes_watched))
                                conn.commit()
                                conn.close()
                            except Exception as e:
                                xbmcgui.Dialog().ok("MAL Tracker", f"Error importing row: {row}\n{e}")
                    # Import history
                    elif len(data) > 0 and isinstance(data[0], list) and len(data[0]) == 5:
                        for row in data:
                            try:
                                anime_id = int(row[1])
                                episode = int(row[2])
                                date = row[3]
                                source = row[4]
                                # Add the history item to the database
                                conn = sqlite3.connect(os.path.join(xbmcvfs.translatePath('special://userdata/addon_data/plugin.video.maltracker'), 'maltracker.db'))
                                cursor = conn.cursor()
                                cursor.execute('INSERT INTO history (anime_id, episode, date, addon_id) VALUES (?, ?, ?, ?)', (anime_id, episode, date, source))
                                conn.commit()
                                conn.close()
                            except Exception as e:
                                xbmcgui.Dialog().ok("MAL Tracker", f"Error importing row: {row}\n{e}")
                    else:
                        xbmcgui.Dialog().ok("MAL Tracker", "Invalid JSON file format.")
                else:
                    xbmcgui.Dialog().ok("MAL Tracker", "Invalid JSON file format.")
        except Exception as e:
            xbmcgui.Dialog().ok("MAL Tracker", f"Error importing JSON file:\n{e}")
        else:
            xbmc.executebuiltin('Notification(MAL Tracker, Data imported from JSON)')

def add_directory_item(name, params):
    url = get_url(params)
    list_item = xbmcgui.ListItem(name)
    xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=list_item, isFolder=True)

def router(params):
    action = params.get('action')
    if action == 'my_list':
        my_list()
    elif action == 'export_data':
        export_data()
    elif action == 'import_data':
        import_data()
    elif action == 'search':
        search()
    elif action == 'manual_log':
        manual_log(params)
    elif action == 'details':
        show_details(params)
    elif action == 'mark_watched':
        mark_watched(params)
    elif action == 'change_status':
        change_status(params)
    elif action == 'sync_check':
        sync_check()
    elif action == 'calendar':
        show_calendar()
    elif action == 'import_alfa':
        importar_alfa()
    elif action == 'import_balandro':
        importar_balandro()
    elif action == 'stats':
        show_stats()
    elif action == 'help':
        show_help()
    elif action == 'import_api_config':
        import_api_config()
    else:
        main_menu()
# --- IMPORTAR CONFIGURACIÓN API ---
def import_api_config():
    dialog = xbmcgui.Dialog()
    file_path = dialog.browse(1, 'Selecciona archivo de configuración API', 'files', '.txt')
    if not file_path:
        return
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        if len(lines) < 2:
            xbmcgui.Dialog().ok('Importar configuración', 'El archivo debe tener al menos dos líneas: Client ID y Client Secret.')
            return
        client_id = lines[0].strip()
        client_secret = lines[1].strip()
        addon = xbmcaddon.Addon()
        addon.setSetting('client_id', client_id)
        addon.setSetting('client_secret', client_secret)
        xbmc.executebuiltin('Notification(MAL Tracker, Configuración importada correctamente)')
    except Exception as e:
        xbmcgui.Dialog().ok('Importar configuración', f'Error al importar configuración:\n{e}')
# --- MENÚ DE AYUDA ---
def show_help():
    ayuda = (
        "[B]Guía de configuración de MAL Tracker[/B]\n\n"
        "1. [B]Crea una cuenta en MyAnimeList:[/B]\n"
        "   - Ve a https://myanimelist.net/register\n\n"
        "2. [B]Obtén tu Client ID y Client Secret de la API de MAL:[/B] \n"
        "   - Ingresa a https://myanimelist.net/apiconfig\n"
        "   - Haz clic en 'Create ID' y sigue los pasos.\n"
        "   - Usa como URL de redirección: https://localhost/ o http://127.0.0.1/ (puedes dejarlo así para uso personal).\n"
        "   - Copia el Client ID y Client Secret generados.\n\n"
        "3. [B]Configura el addon en Kodi:[/B]\n"
        "   - Ve a los ajustes del addon (botón derecho > Ajustes o menú contextual).\n"
        "   - Ingresa tu usuario de MyAnimeList, Client ID y Client Secret.\n"
        "   - Si usas AniList para el calendario, ingresa también tu usuario de AniList.\n\n"
        "4. [B]Importar configuración de API desde archivo:[/B]\n"
        "   - Puedes importar el Client ID y el Client Secret desde un archivo de texto plano usando la opción 'Importar configuración API' en el menú principal.\n"
        "   - El archivo debe tener la primera línea con el Client ID y la segunda línea con el Client Secret.\n"
        "   - Ejemplo de archivo:\n"
        "     abcdefghijklmnopqrstuvwxyz123456\n"
        "     zyxwvutsrqponmlkjihgfedcba654321\n\n"
        "5. [B]Primer uso y autenticación:[/B]\n"
        "   - Al intentar sincronizar por primera vez, el addon intentará abrir automáticamente el navegador con la URL de autorización.\n"
        "   - Si no se abre el navegador, se mostrará la URL en pantalla y podrás copiarla al portapapeles.\n"
        "   - Abre la URL en tu navegador, inicia sesión y autoriza el acceso al addon.\n"
        "   - Si se solicita un código, pégalo en el addon para completar la autenticación.\n\n"
        "6. [B]Importar bibliotecas de Alfa/Balandro:[/B]\n"
        "   - Si tienes estos addons, puedes importar tu progreso desde el menú principal.\n"
        "   - Asegúrate de que las rutas de las bases de datos sean correctas en los ajustes si usas rutas personalizadas.\n\n"
        "7. [B]Buscar y añadir animes:[/B]\n"
        "   - Usa 'Buscar Anime' para encontrar títulos y añadirlos a tu lista de MAL.\n"
        "   - Puedes marcar episodios como vistos y cambiar el estado desde el menú contextual.\n\n"
        "8. [B]Exportar e importar datos:[/B]\n"
        "   - Puedes exportar tu historial y lista a archivos CSV o JSON para respaldo.\n"
        "   - Usa la opción de importar para restaurar datos si cambias de dispositivo.\n\n"
        "9. [B]Solución de problemas:[/B]\n"
        "   - Si el addon no sincroniza, revisa tu conexión a internet y que los datos de la API sean correctos.\n"
        "   - Si cambiaste tu contraseña de MAL, puede que debas volver a autorizar el addon.\n"
        "   - Consulta el log de Kodi para detalles de errores: https://kodi.wiki/view/Log_file\n\n"
        "10. [B]Soporte y documentación:[/B]\n"
        "   - Documentación oficial de la API de MAL: https://myanimelist.net/apiconfig/references/api/v2\n"
        "   - Ayuda de Kodi: https://kodi.wiki/\n"
        "   - Comunidad Kodi en español: https://mundokodi.com/\n"
        "   - Comunidad oficial: https://forum.kodi.tv/\n\n"
        "[I]Si tienes problemas de autenticación, revisa que el Client ID y Secret sean correctos, que tu cuenta esté activa y que hayas autorizado el acceso correctamente.[/I]\n"
        "[I]Recuerda que este addon no descarga ni reproduce anime, solo gestiona tu progreso y sincronización con MyAnimeList.[/I]"
    )
    xbmcgui.Dialog().textviewer('Ayuda y configuración', ayuda)


# --- PUNTO DE ENTRADA DEL ADDON ---
if __name__ == '__main__':
    import urllib.parse
    if len(sys.argv) > 2 and sys.argv[2]:
        params = dict(urllib.parse.parse_qsl(sys.argv[2][1:]))
    else:
        params = {}
    router(params)
def importar_alfa():
    from resources.lib.integracion_addons import importar_biblioteca_alfa
    import resources.lib.db as db
    import resources.lib.mal_api as mal_api
    items = importar_biblioteca_alfa()
    if not items:
        xbmcgui.Dialog().ok('Alfa', 'No se encontró biblioteca Alfa o está vacía.')
        return
    added = 0
    for titulo, temporada, episodio, visto in items:
        # Buscar en MAL
        mal_id = mal_api.search_anime(titulo)
        if mal_id:
            db.add_anime(mal_id, titulo, 'watching', episodio)
            mal_api.add_to_list(mal_id)
            if visto:
                mal_api.update_episode(mal_id, episodio)
            added += 1
    xbmcgui.Dialog().ok('Alfa', f'Se importaron y sincronizaron {added} animes con MAL y tu base local.')

# Importar biblioteca de Balandro
def importar_balandro():
    from resources.lib.integracion_addons import importar_biblioteca_balandro
    import resources.lib.db as db
    import resources.lib.mal_api as mal_api
    items = importar_biblioteca_balandro()
    if not items:
        xbmcgui.Dialog().ok('Balandro', 'No se encontró biblioteca Balandro o está vacía.')
        return
    added = 0
    for titulo, temporada, episodio, visto in items:
        mal_id = mal_api.search_anime(titulo)
        if mal_id:
            db.add_anime(mal_id, titulo, 'watching', episodio)
            mal_api.add_to_list(mal_id)
            if visto:
                mal_api.update_episode(mal_id, episodio)
            added += 1
    xbmcgui.Dialog().ok('Balandro', f'Se importaron y sincronizaron {added} animes con MAL y tu base local.')

def show_stats():
    import resources.lib.db as db
    history = db.get_all_history()
    total_episodios = len(history)
    animes = set([h[1] for h in history])
    horas = total_episodios * 0.5
    msg = f"Total episodios vistos: {total_episodios}\nTotal series: {len(animes)}\nHoras aproximadas: {horas}"
    xbmcgui.Dialog().ok('Estadísticas', msg)

# --- FUNCIONES FALTANTES ---
def search():
    keyboard = xbmcgui.Dialog().input('Buscar Anime', type=xbmcgui.INPUT_ALPHANUM)
    if keyboard:
        results = mal_api.search_anime_full(keyboard)
        if results:
            for anime in results:
                title = anime['title']
                anime_id = anime['id']
                list_item = xbmcgui.ListItem(title)
                context_menu = [
                    ("Añadir a mi lista", f"RunPlugin({get_url({'action': 'add_to_list', 'anime_id': anime_id})})"),
                    ("Ver detalles", f"RunPlugin({get_url({'action': 'details', 'anime_id': anime_id})})")
                ]
                list_item.addContextMenuItems(context_menu)
                xbmcplugin.addDirectoryItem(handle=HANDLE, url=get_url({'action': 'details', 'anime_id': anime_id}), listitem=list_item, isFolder=False)
            xbmcplugin.endOfDirectory(HANDLE)
        else:
            xbmcgui.Dialog().ok("MAL Tracker", "Anime no encontrado.")
    else:
        xbmcplugin.endOfDirectory(HANDLE)

def manual_log(params):
    anime_id = int(params.get('anime_id', [0])[0])
    episode = xbmcgui.Dialog().numeric(0, 'Número de episodio a registrar')
    if episode:
        from datetime import datetime
        import resources.lib.db as db
        db.add_history(anime_id, int(episode), datetime.now().isoformat(), 'manual')
        xbmc.executebuiltin('Notification(MAL Tracker, Episodio registrado manualmente)')

def show_details(params):
    anime_id = int(params.get('anime_id', [0])[0])
    details = mal_api.get_anime_details(anime_id)
    if details:
        msg = f"Título: {details.get('title')}\nEpisodios: {details.get('num_episodes')}\nSinopsis: {details.get('synopsis', 'N/A')}"
        xbmcgui.Dialog().ok('Detalles de Anime', msg)

def mark_watched(params):
    anime_id = int(params.get('anime_id', [0])[0])
    anime = mal_api.get_anime_details(anime_id)
    if anime:
        current = anime.get('my_list_status', {}).get('num_episodes_watched', 0)
        total = anime.get('num_episodes', 0)
        if current < total:
            mal_api.update_episode(anime_id, current + 1)
            xbmc.executebuiltin('Notification(MAL Tracker, Episodio marcado como visto)')
        else:
            xbmcgui.Dialog().ok('MAL Tracker', 'Ya has visto todos los episodios.')

def change_status(params):
    anime_id = int(params.get('anime_id', [0])[0])
    estados = ['watching', 'completed', 'on_hold', 'dropped', 'plan_to_watch']
    idx = xbmcgui.Dialog().select('Nuevo estado', estados)
    if idx >= 0:
        mal_api.update_status(anime_id, estados[idx])
        xbmc.executebuiltin(f'Notification(MAL Tracker, Estado cambiado a {estados[idx]})')

def sync_check():
    import resources.lib.db as db
    local = db.get_all_history()
    mal = mal_api.get_anime_list()
    pendientes = []
    for h in local:
        anime_id, episode = h[1], h[2]
        found = False
        for anime in mal:
            if anime['node']['id'] == anime_id and anime['list_status']['num_episodes_watched'] < episode:
                pendientes.append((anime_id, episode))
    if pendientes:
        msg = '\n'.join([f'Anime {aid} hasta ep {ep}' for aid, ep in pendientes])
        xbmcgui.Dialog().ok('Pendientes de sincronizar', msg)
    else:
        xbmcgui.Dialog().ok('Sincronización', 'Todo está sincronizado')

def show_calendar():
    airing = mal_api.get_airing_calendar()
    if airing:
        msg = '\n'.join([f"{a['title']}: {a['next_airing']}" for a in airing])
        xbmcgui.Dialog().ok('Calendario de emisión', msg)
    else:
        xbmcgui.Dialog().ok('Calendario de emisión', 'No hay datos disponibles')