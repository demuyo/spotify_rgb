# spotify_module.py
"""
Módulo de conexão com a API do Spotify via OAuth 2.0.
"""

import logging
from dataclasses import dataclass
from typing import Optional

import spotipy
from spotipy.oauth2 import SpotifyOAuth

import config

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class TrackInfo:
    track_id:    str
    name:        str
    artist:      str
    album:       str
    album_art:   str
    is_playing:  bool
    progress_ms: int
    duration_ms: int


def create_spotify_client() -> spotipy.Spotify:
    auth_manager = SpotifyOAuth(
        client_id=config.SPOTIFY_CLIENT_ID,
        client_secret=config.SPOTIFY_CLIENT_SECRET,
        redirect_uri=config.SPOTIFY_REDIRECT_URI,
        scope=config.SPOTIFY_SCOPE,
        open_browser=True,
        cache_path=".cache-spotify",
    )
    sp = spotipy.Spotify(auth_manager=auth_manager)
    logger.info("Cliente Spotify criado.")
    return sp


def get_current_track(sp: spotipy.Spotify) -> Optional[TrackInfo]:
    try:
        result = sp.current_user_playing_track()

        if result is None or result.get("item") is None:
            return None

        item = result["item"]
        images = item["album"]["images"]
        album_art_url = images[0]["url"] if images else ""
        artists = ", ".join(a["name"] for a in item["artists"])

        return TrackInfo(
            track_id=item["id"],
            name=item["name"],
            artist=artists,
            album=item["album"]["name"],
            album_art=album_art_url,
            is_playing=result.get("is_playing", False),
            progress_ms=result.get("progress_ms", 0) or 0,
            duration_ms=item.get("duration_ms", 0) or 0,
        )

    except spotipy.exceptions.SpotifyException as e:
        logger.error(f"Erro Spotify: {e}")
        return None
    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
        return None