"""
Spotify adapter: fetches tracks and maps audio features -> mood point.

Spotify gives us REAL mood data directly:
    valence: 0.0 (sad) - 1.0 (happy)
    energy:  0.0 (calm) - 1.0 (intense)
"""

import os
import time
import httpx
from app.models.mood import MoodPoint, ContentItem

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "")

_token_cache = {"access_token": None, "expires_at": 0}


async def _get_access_token(client: httpx.AsyncClient) -> str:
    if _token_cache["access_token"] and time.time() < _token_cache["expires_at"]:
        return _token_cache["access_token"]

    resp = await client.post(
        "https://accounts.spotify.com/api/token",
        data={"grant_type": "client_credentials"},
        auth=(CLIENT_ID, CLIENT_SECRET),
    )
    resp.raise_for_status()
    data = resp.json()
    _token_cache["access_token"] = data["access_token"]
    _token_cache["expires_at"] = time.time() + data["expires_in"] - 60
    return _token_cache["access_token"]


async def get_tracks_by_playlist(playlist_id: str, limit: int = 20) -> list[ContentItem]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        token = await _get_access_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        tracks_resp = await client.get(
            f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks",
            headers=headers,
            params={"limit": limit},
        )
        tracks_resp.raise_for_status()
        track_data = tracks_resp.json().get("items", [])
        track_ids = [t["track"]["id"] for t in track_data if t.get("track")]

        features_resp = await client.get(
            "https://api.spotify.com/v1/audio-features",
            headers=headers,
            params={"ids": ",".join(track_ids)},
        )
        features_resp.raise_for_status()
        features_list = features_resp.json().get("audio_features", [])
        features_by_id = {f["id"]: f for f in features_list if f}

        items = []
        for t in track_data:
            track = t.get("track")
            if not track:
                continue
            feat = features_by_id.get(track["id"])
            if not feat:
                continue
            mood = MoodPoint(valence=feat["valence"], energy=feat["energy"])
            images = track.get("album", {}).get("images", [])
            items.append(ContentItem(
                id=track["id"],
                title=f"{track['name']} — {track['artists'][0]['name']}",
                media_type="music",
                image_url=images[0]["url"] if images else None,
                mood=mood,
                source_url=track.get("external_urls", {}).get("spotify"),
            ))
        return items