"""
TMDB adapter: fetches popular movies and maps genre -> approximate mood point.
"""

import os
import random
import httpx
from app.models.mood import MoodPoint, ContentItem

TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w342"

GENRE_MOOD_MAP = {
    "Comedy":          MoodPoint(0.85, 0.55),
    "Romance":         MoodPoint(0.75, 0.35),
    "Family":          MoodPoint(0.8, 0.4),
    "Animation":       MoodPoint(0.75, 0.55),
    "Adventure":       MoodPoint(0.7, 0.75),
    "Action":          MoodPoint(0.55, 0.9),
    "Thriller":        MoodPoint(0.3, 0.85),
    "Horror":          MoodPoint(0.15, 0.85),
    "Mystery":         MoodPoint(0.35, 0.6),
    "Crime":           MoodPoint(0.3, 0.7),
    "Drama":           MoodPoint(0.35, 0.4),
    "War":             MoodPoint(0.2, 0.75),
    "History":         MoodPoint(0.45, 0.35),
    "Documentary":     MoodPoint(0.5, 0.3),
    "Science Fiction": MoodPoint(0.55, 0.7),
    "Fantasy":         MoodPoint(0.65, 0.65),
    "Music":           MoodPoint(0.75, 0.6),
    "Western":         MoodPoint(0.4, 0.6),
}
DEFAULT_MOOD = MoodPoint(0.5, 0.5)


def _mood_for_genres(genre_ids: list[int], genre_lookup: dict[int, str]) -> MoodPoint:
    points = [GENRE_MOOD_MAP.get(genre_lookup.get(gid, ""), DEFAULT_MOOD) for gid in genre_ids]
    if not points:
        return DEFAULT_MOOD
    avg_valence = sum(p.valence for p in points) / len(points)
    avg_energy = sum(p.energy for p in points) / len(points)
    return MoodPoint(avg_valence, avg_energy)


def _genres_for_mood(target: MoodPoint, genre_lookup: dict[int, str], top_n: int = 4) -> list[int]:
    """Find the genre IDs whose mood is closest to the target mood."""
    name_to_id = {name: gid for gid, name in genre_lookup.items()}
    scored = []
    for name, mood in GENRE_MOOD_MAP.items():
        if name in name_to_id:
            distance = ((mood.valence - target.valence) ** 2 + (mood.energy - target.energy) ** 2) ** 0.5
            scored.append((distance, name_to_id[name]))
    scored.sort(key=lambda x: x[0])
    return [gid for _, gid in scored[:top_n]]


async def get_genre_lookup(client: httpx.AsyncClient) -> dict[int, str]:
    resp = await client.get(
        f"{TMDB_BASE_URL}/genre/movie/list",
        params={"api_key": TMDB_API_KEY},
    )
    resp.raise_for_status()
    data = resp.json()
    return {g["id"]: g["name"] for g in data.get("genres", [])}


async def get_popular_movies(limit: int = 20, target_mood: MoodPoint | None = None) -> list[ContentItem]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        genre_lookup = await get_genre_lookup(client)

        params = {
            "api_key": TMDB_API_KEY,
            "page": random.randint(1, 5),
            "sort_by": "popularity.desc",
        }

        if target_mood:
            genre_ids = _genres_for_mood(target_mood, genre_lookup)
            params["with_genres"] = "|".join(str(g) for g in genre_ids)
            resp = await client.get(f"{TMDB_BASE_URL}/discover/movie", params=params)
        else:
            resp = await client.get(f"{TMDB_BASE_URL}/movie/popular", params=params)

        resp.raise_for_status()
        results = resp.json().get("results", [])[:limit]

        items = []
        for movie in results:
            mood = _mood_for_genres(movie.get("genre_ids", []), genre_lookup)
            poster_path = movie.get("poster_path")
            items.append(ContentItem(
                id=str(movie["id"]),
                title=movie["title"],
                media_type="movie",
                image_url=f"{TMDB_IMAGE_BASE}{poster_path}" if poster_path else None,
                mood=mood,
                source_url=f"https://www.themoviedb.org/movie/{movie['id']}",
            ))
        return items


async def search_movies(query: str, limit: int = 15) -> list[ContentItem]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        genre_lookup = await get_genre_lookup(client)
        resp = await client.get(
            f"{TMDB_BASE_URL}/search/movie",
            params={"api_key": TMDB_API_KEY, "query": query},
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])[:limit]

        items = []
        for movie in results:
            mood = _mood_for_genres(movie.get("genre_ids", []), genre_lookup)
            poster_path = movie.get("poster_path")
            items.append(ContentItem(
                id=str(movie["id"]),
                title=movie["title"],
                media_type="movie",
                image_url=f"{TMDB_IMAGE_BASE}{poster_path}" if poster_path else None,
                mood=mood,
                source_url=f"https://www.themoviedb.org/movie/{movie['id']}",
            ))
        return items