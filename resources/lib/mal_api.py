def get_anime_details(anime_id):
    token = auth.authenticate()
    if not token:
        return None
    url = f'{_API_BASE_URL}/anime/{anime_id}?fields=id,title,num_episodes,synopsis,my_list_status'
    headers = {'Authorization': f'Bearer {token["access_token"]}'}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return None
    return response.json()

def search_anime_full(query):
    token = auth.authenticate()
    if not token:
        return []
    url = f'{_API_BASE_URL}/anime?q={query}&limit=10&fields=id,title,synopsis,num_episodes'
    headers = {'Authorization': f'Bearer {token["access_token"]}'}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return []
    data = response.json()
    return [item['node'] for item in data.get('data', [])]

def add_to_list(anime_id):
    token = auth.authenticate()
    if not token:
        return False
    url = f'{_API_BASE_URL}/anime/{anime_id}/my_list_status'
    headers = {'Authorization': f'Bearer {token["access_token"]}'}
    data = {'status': 'watching'}
    response = requests.put(url, headers=headers, data=data)
    return response.status_code == 200

def get_airing_calendar():
    # Integración real con AniList para calendario de emisión
    import requests
    query = '''
    query ($userName: String) {
      MediaListCollection(userName: $userName, type: ANIME, status_in: [CURRENT, PLANNING]) {
        lists {
          entries {
            media {
              id
              title { romaji }
              nextAiringEpisode { airingAt episode }
            }
          }
        }
      }
    }
    '''
    import xbmcaddon
    addon = xbmcaddon.Addon()
    anilist_username = addon.getSetting('anilist_username')
    variables = {"userName": anilist_username}
    url = "https://graphql.anilist.co"
    response = requests.post(url, json={"query": query, "variables": variables})
    if response.status_code != 200:
        return []
    data = response.json()
    result = []
    for l in data.get('data', {}).get('MediaListCollection', {}).get('lists', []):
        for entry in l.get('entries', []):
            media = entry.get('media', {})
            next_ep = media.get('nextAiringEpisode')
            if next_ep:
                from datetime import datetime
                airing_time = datetime.fromtimestamp(next_ep['airingAt']).strftime('%Y-%m-%d %H:%M')
                result.append({
                    'title': media['title']['romaji'],
                    'next_airing': f"Episodio {next_ep['episode']} - {airing_time}"
                })
    return result
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import requests
import json
import os
import sys

from resources.lib import auth

# Addon handle
_HANDLE = int(sys.argv[1])

# Addon base URL
_URL = sys.argv[0]

# Get addon directory
import xbmcvfs
_ADDON_PATH = xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('path'))

# Get settings
_ADDON = xbmcaddon.Addon()
_CLIENT_ID = _ADDON.getSetting('client_id')
_CLIENT_SECRET = _ADDON.getSetting('client_secret')

_API_BASE_URL = 'https://api.myanimelist.net/v2'

def get_anime_list():
    # Authenticate
    token = auth.authenticate()
    if not token:
        xbmcgui.Dialog().ok("MAL Tracker", "Authentication failed.")
        return None

    # Build request URL
    url = f'{_API_BASE_URL}/users/@me/animelist?limit=1000'

    # Make request
    headers = {
        'Authorization': f'Bearer {token["access_token"]}'
    }
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        xbmcgui.Dialog().ok("MAL Tracker", f"Failed to get anime list: {response.status_code} - {response.text}")
        return None

    # Parse response
    data = response.json()
    return data['data']

def update_episode(anime_id, episode):
    # Authenticate
    token = auth.authenticate()
    if not token:
        xbmcgui.Dialog().ok("MAL Tracker", "Authentication failed.")
        return False

    # Build request URL
    url = f'{_API_BASE_URL}/anime/{anime_id}/my_list_status'

    # Build request data
    data = {
        'num_watched_episodes': int(episode)
    }

    # Make request
    headers = {
        'Authorization': f'Bearer {token["access_token"]}'
    }
    response = requests.patch(url, headers=headers, data=data)

    if response.status_code != 200:
        xbmcgui.Dialog().ok("MAL Tracker", f"Failed to update episode: {response.status_code} - {response.text}")
        xbmc.executebuiltin('Notification(MAL Tracker, Error al actualizar episodio en MAL)')
        return False

    xbmc.executebuiltin('Notification(MAL Tracker, Episodio actualizado en MAL)')
    return True

def update_status(anime_id, status):
    # Authenticate
    token = auth.authenticate()
    if not token:
        xbmcgui.Dialog().ok("MAL Tracker", "Authentication failed.")
        return False

    # Build request URL
    url = f'{_API_BASE_URL}/anime/{anime_id}/my_list_status'

    # Build request data
    data = {
        'status': status
    }

    # Make request
    headers = {
        'Authorization': f'Bearer {token["access_token"]}'
    }
    response = requests.patch(url, headers=headers, data=data)

    if response.status_code != 200:
        xbmcgui.Dialog().ok("MAL Tracker", f"Failed to update status: {response.status_code} - {response.text}")
        xbmc.executebuiltin('Notification(MAL Tracker, Error al actualizar estado en MAL)')
        return False

    xbmc.executebuiltin('Notification(MAL Tracker, Estado actualizado en MAL)')
    return True

def search_anime(title):
    # Authenticate
    token = auth.authenticate()
    if not token:
        xbmcgui.Dialog().ok("MAL Tracker", "Authentication failed.")
        return None

    # Build request URL
    url = f'{_API_BASE_URL}/anime?q={title}'

    # Make request
    headers = {
        'Authorization': f'Bearer {token["access_token"]}'
    }
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        xbmcgui.Dialog().ok("MAL Tracker", f"Failed to search anime: {response.status_code} - {response.text}")
        return None

    # Parse response
    data = response.json()
    if data.get('data') and len(data['data']) > 0:
        return data['data'][0]['node']['id']
    else:
        return None
