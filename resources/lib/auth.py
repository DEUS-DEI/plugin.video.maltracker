import xbmc
import xbmcvfs
import xbmcgui
import xbmcplugin
import xbmcaddon
import requests
import json
import os
import sys

# Addon handle
_HANDLE = int(sys.argv[1])

# Addon base URL
_URL = sys.argv[0]

# Get addon directory
_ADDON_PATH = xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('path'))

# Get settings
_ADDON = xbmcaddon.Addon()
_CLIENT_ID = _ADDON.getSetting('client_id')
_CLIENT_SECRET = _ADDON.getSetting('client_secret')


# OAuth2 URLs
_AUTH_URL = 'https://myanimelist.net/v1/oauth2/authorize'
_TOKEN_URL = 'https://myanimelist.net/v1/oauth2/token'

# Redirect URI registrado en MyAnimeList (debe coincidir con el panel de la app)
# Si solo permite localhost, usa exactamente este valor:
_REDIRECT_URI = 'http://localhost'

# Token file path
_TOKEN_FILE = os.path.join(xbmcvfs.translatePath('special://userdata/addon_data/plugin.video.maltracker'), 'token.json')

def authenticate():
    # Check if token exists
    if os.path.exists(_TOKEN_FILE):
        with open(_TOKEN_FILE, 'r') as f:
            token = json.load(f)
        # Check if token is valid
        if is_token_valid(token):
            return token
        else:
            # Refresh token
            token = refresh_token(token['refresh_token'])
            if not token:
                # Authentication failed, start from scratch
                return authenticate_new()
            return token
    else:
        # Authenticate new
        return authenticate_new()

def authenticate_new():
    # Generate code verifier and challenge

    import secrets
    import hashlib
    import base64
    code_verifier = secrets.token_urlsafe(64)[:128]
    code_challenge = hashlib.sha256(code_verifier.encode('ascii')).digest()
    code_challenge = base64.urlsafe_b64encode(code_challenge).decode('ascii').replace('=', '')


    # Build authorization URL (incluye redirect_uri)
    auth_url = (
        f'{_AUTH_URL}?response_type=code'
        f'&client_id={_CLIENT_ID}'
        f'&code_challenge={code_challenge}'
        f'&code_challenge_method=S256'
        f'&redirect_uri={_REDIRECT_URI}'
    )

    # Intentar abrir el navegador automáticamente
    try:
        import webbrowser
        webbrowser.open(auth_url)
        xbmcgui.Dialog().ok('Autenticación MAL', 'Se ha intentado abrir el navegador con la URL de autorización. Si no se abre, copia la URL manualmente.')
    except Exception:
        xbmcgui.Dialog().ok('Autenticación MAL', 'No se pudo abrir el navegador automáticamente. Copia la URL manualmente.')

    # Mostrar la URL y permitir copiarla
    ok = xbmcgui.Dialog().yesno('Autenticación MAL', f'Abre la siguiente URL en tu navegador para autorizar el addon:\n\n{auth_url}\n\n¿Copiar la URL al portapapeles?', yeslabel='Copiar', nolabel='No copiar')
    if ok:
        try:
            import pyperclip
            pyperclip.copy(auth_url)
            xbmcgui.Dialog().ok('Autenticación MAL', 'URL copiada al portapapeles.')
        except Exception:
            xbmcgui.Dialog().ok('Autenticación MAL', 'No se pudo copiar al portapapeles. Copia la URL manualmente.')

    # Get authorization code from user
    dialog = xbmcgui.Dialog()
    auth_code = dialog.input('Pega el código de autorización de MyAnimeList', type=xbmcgui.INPUT_ALPHANUM)

    if not auth_code:
        return None

    # Get token
    token = get_token(auth_code, code_verifier)

    return token

def get_token(auth_code, code_verifier):

    # Build token request data (incluye redirect_uri)
    data = {
        'grant_type': 'authorization_code',
        'code': auth_code,
        'client_id': _CLIENT_ID,
        'client_secret': _CLIENT_SECRET,
        'code_verifier': code_verifier,
        'redirect_uri': _REDIRECT_URI
    }

    # Make token request
    response = requests.post(_TOKEN_URL, data=data)

    if response.status_code != 200:
        xbmcgui.Dialog().ok("MAL Tracker", f"Failed to get token: {response.status_code} - {response.text}")
        return None

    # Save token to file
    token = response.json()
    save_token(token)

    return token

def refresh_token(refresh_token):

    # Build refresh token request data (incluye redirect_uri)
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': _CLIENT_ID,
        'client_secret': _CLIENT_SECRET,
        'redirect_uri': _REDIRECT_URI
    }

    # Make refresh token request
    response = requests.post(_TOKEN_URL, data=data)

    if response.status_code != 200:
        xbmcgui.Dialog().ok("MAL Tracker", f"Failed to refresh token: {response.status_code} - {response.text}")
        return None

    # Save token to file
    token = response.json()
    save_token(token)

    return token

def is_token_valid(token):
    # Check if token is expired
    # Implementación básica: asume que el token es un dict con 'expires_at' (timestamp)
    import time
    expires_at = token.get('expires_at')
    if expires_at is None:
        return False
    return time.time() < expires_at

def save_token(token):
    # Ensure directory exists
    token_dir = os.path.dirname(_TOKEN_FILE)
    if not os.path.exists(token_dir):
        os.makedirs(token_dir)

    # Save token to file
    with open(_TOKEN_FILE, 'w') as f:
        json.dump(token, f)

import hashlib
import base64
