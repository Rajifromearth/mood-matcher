"""
Last.fm adapter: fetches tracks matching a mood tag and maps tags -> mood point.
"""

import os
import random
import httpx
from app.models.mood import MoodPoint, ContentItem

API_KEY = os.getenv("LASTFM_API_KEY", "")
BASE_URL = "https://ws.audioscrobbler.com/2.0/"

TAG_MOOD_MAP = {
    "happy":       MoodPoint(0.9, 0.6),
    "fun":         MoodPoint(0.85, 0.65),
    "party":       MoodPoint(0.8, 0.9),
    "dance":       MoodPoint(0.75, 0.85),
    "upbeat":      MoodPoint(0.8, 0.7),
    "chill":       MoodPoint(0.6, 0.25),
    "chillout":    MoodPoint(0.6, 0.25),
    "relax":       MoodPoint(0.65, 0.2),
    "mellow":      MoodPoint(0.55, 0.25),
    "acoustic":    MoodPoint(0.6, 0.3),
    "sad":         MoodPoint(0.15, 0.3),
    "melancholy":  MoodPoint(0.2, 0.3),
    "melancholic": MoodPoint(0.2, 0.3),
    "dark":        MoodPoint(0.15, 0.6),
    "angry":       MoodPoint(0.2, 0.85),
    "aggressive":  MoodPoint(0.25, 0.9),
    "energetic":   MoodPoint(0.75, 0.9),
    "rock":        MoodPoint(0.55, 0.8),
    "metal":       MoodPoint(0.3, 0.9),
    "pop":         MoodPoint(0.8, 0.65),
    "romantic":    MoodPoint(0.75, 0.35),
    "love":        MoodPoint(0.8, 0.4),
    "calm":        MoodPoint(0.6, 0.15),
    "ambient":     MoodPoint(0.5, 0.15),
    "instrumental": MoodPoint(0.5, 0.35),
}
DEFAULT_MOOD = MoodPoint(0.5, 0.5)


def _mood_for_tags(tags: list[str]) -> MoodPoint:
    points = [TAG_MOOD_MAP[t.lower()] for t in tags if t.lower() in TAG_MOOD_MAP]
    if not points:
        return DEFAULT_MOOD
    avg_valence = sum(p.valence for p in points) / len(points)
    avg_energy = sum(p.energy for p in points) / len(points)
    return MoodPoint(avg_valence, avg_energy)


def _best_tags_for_mood(target: MoodPoint, top_n: int = 3) -> list[str]:
    """Find the tag names whose mood is closest to the target mood."""
    scored = []
    for name, mood in TAG_MOOD_MAP.items():
        distance = ((mood.valence - target.valence) ** 2 + (mood.energy - target.energy) ** 2) ** 0.5
        scored.append((distance, name))
    scored.sort(key=lambda x: x[0])
    return [name for _, name in scored[:top_n]]


async def _get_top_tags(client: httpx.AsyncClient, artist: str, track: str) -> list[str]:
    resp = await client.get(BASE_URL, params={
        "method": "track.getTopTags",
        "artist": artist,
        "track": track,
        "api_key": API_KEY,
        "format": "json",
    })
    if resp.status_code != 200:
        return []
    data = resp.json()
    tags = data.get("toptags", {}).get("tag", [])
    return [t["name"] for t in tags[:5]]


async def get_top_tracks(limit: int = 20, target_mood: MoodPoint | None = None) -> list[ContentItem]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        if target_mood:
            candidate_tags = _best_tags_for_mood(target_mood, top_n=3)
            chosen_tag = random.choice(candidate_tags)
            resp = await client.get(BASE_URL, params={
                "method": "tag.getTopTracks",
                "tag": chosen_tag,
                "api_key": API_KEY,
                "format": "json",
                "limit": limit,
                "page": random.randint(1, 3),
            })
            resp.raise_for_status()
            data = resp.json()
            tracks = data.get("tracks", {}).get("track", [])
        else:
            resp = await client.get(BASE_URL, params={
                "method": "chart.getTopTracks",
                "api_key": API_KEY,
                "format": "json",
                "limit": limit,
            })
            resp.raise_for_status()
            data = resp.json()
            tracks = data.get("tracks", {}).get("track", [])

        items = []
        for track in tracks:
            artist_name = track["artist"]["name"] if isinstance(track["artist"], dict) else track["artist"]
            track_name = track["name"]
            tags = await _get_top_tags(client, artist_name, track_name)
            mood = _mood_for_tags(tags)
            images = track.get("image", [])
            image_url = images[-1]["#text"] if images and images[-1].get("#text") else None
            items.append(ContentItem(
                id=track.get("mbid") or f"{artist_name}-{track_name}",
                title=f"{track_name} — {artist_name}",
                media_type="music",
                image_url=image_url,
                mood=mood,
                source_url=track.get("url"),
            ))
        return items


async def search_tracks(query: str, limit: int = 15) -> list[ContentItem]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(BASE_URL, params={
            "method": "track.search",
            "track": query,
            "api_key": API_KEY,
            "format": "json",
            "limit": limit,
        })
        resp.raise_for_status()
        data = resp.json()
        tracks = data.get("results", {}).get("trackmatches", {}).get("track", [])

        items = []
        for track in tracks:
            artist_name = track["artist"]
            track_name = track["name"]
            tags = await _get_top_tags(client, artist_name, track_name)
            mood = _mood_for_tags(tags)
            images = track.get("image", [])
            image_url = images[-1]["#text"] if images and images[-1].get("#text") else None
            items.append(ContentItem(
                id=track.get("mbid") or f"{artist_name}-{track_name}",
                title=f"{track_name} — {artist_name}",
                media_type="music",
                image_url=image_url,
                mood=mood,
                source_url=track.get("url"),
            ))
        return items