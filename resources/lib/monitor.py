import xbmc
import xbmcgui
import xbmcplugin
import sys
import os
import xbmcaddon
from . import db  # Import the db module

class MyMonitor(xbmc.Monitor):
    def __init__(self):
        xbmc.Monitor.__init__(self)

    def onPlayBackStarted(self):
        # Sincronización automática al iniciar reproducción
        try:
            import resources.lib.db as db
            import resources.lib.mal_api as mal_api
            db.create_tables()
            mal_api.get_anime_list()  # Refresca lista local
        except Exception as e:
            xbmc.log(f"Error en sincronización automática: {e}", xbmc.LOGERROR)
        # Get the currently playing item
        player = xbmc.Player()
        playing_file = player.getPlayingFile()

        # Get the title and episode number from the playing file
        # This will likely need to be adjusted based on the naming convention
        # of the files being played.
        try:
            title, episode, addon_id = self.extract_title_episode(playing_file)
        except:
            title = playing_file
            episode = None
            addon_id = "local"

        # Log the playback to the database
        db.log_playback(title, episode, addon_id)

        xbmc.log(f"Playback started: Title: {title}, Episode: {episode}, File: {playing_file}", xbmc.LOGINFO)

    def extract_title_episode(self, filename):
        # Try to extract addon identifier from filename
        if "plugin.video.animeflv" in filename:
            addon_id = "animeflv"
        elif "plugin.video.elementum" in filename:
            addon_id = "elementum"
        else:
            addon_id = "local"

        # This is a placeholder.  Implement your logic to extract the title and episode
        # from the filename.  This will depend on the naming convention of your files.
        # Example: "Anime Title - Episode 01.mp4"
        parts = filename.split(" - ")
        title = parts[0]
        episode_str = None
        if len(parts) > 1 and "." in parts[1]:
            episode_str = parts[1].split(".")[0]
        try:
            episode = int(episode_str)
        except:
            episode = None
        return title, episode, addon_id

    def onPlayBackStopped(self):
        # Sincronización automática al detener reproducción
        try:
            import resources.lib.db as db
            import resources.lib.mal_api as mal_api
            db.create_tables()
            mal_api.get_anime_list()  # Refresca lista local
        except Exception as e:
            xbmc.log(f"Error en sincronización automática: {e}", xbmc.LOGERROR)

    def onPlayBackEnded(self):
        pass
