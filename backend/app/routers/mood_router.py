import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.mood import MoodPoint, MOOD_PRESETS
from app.services import tmdb_service, lastfm_service, books_service

router = APIRouter(prefix="/api/mood", tags=["mood"])


class MoodRequest(BaseModel):
    valence: float | None = None
    energy: float | None = None
    preset: str | None = None


@router.get("/presets")
def list_presets():
    return {name: {"valence": p.valence, "energy": p.energy} for name, p in MOOD_PRESETS.items()}


@router.post("/recommend")
async def recommend(req: MoodRequest):
    if req.preset:
        if req.preset not in MOOD_PRESETS:
            raise HTTPException(400, f"Unknown preset '{req.preset}'")
        target = MOOD_PRESETS[req.preset]
    elif req.valence is not None and req.energy is not None:
        target = MoodPoint(req.valence, req.energy)
    else:
        raise HTTPException(400, "Provide either a preset or both valence and energy")

    movies, tracks, books = await asyncio.gather(
        tmdb_service.get_popular_movies(limit=20, target_mood=target),
        lastfm_service.get_top_tracks(limit=20, target_mood=target),
        books_service.search_books(mood=target, limit=20),
        return_exceptions=True,
    )

    all_items = []
    for result in (movies, tracks, books):
        if isinstance(result, Exception):
            continue
        all_items.extend(result)

    scored = sorted(all_items, key=lambda item: item.score_against(target), reverse=True)

    return {
        "target_mood": {"valence": target.valence, "energy": target.energy},
        "results": [
            {
                "id": item.id,
                "title": item.title,
                "media_type": item.media_type,
                "image_url": item.image_url,
                "source_url": item.source_url,
                "match_score": round(item.score_against(target), 3),
            }
            for item in scored[:15]
        ],
    }
@router.get("/search")
async def search(q: str):
    if not q or not q.strip():
        raise HTTPException(400, "Query parameter 'q' is required")

    movies, tracks, books = await asyncio.gather(
        tmdb_service.search_movies(q, limit=15),
        lastfm_service.search_tracks(q, limit=15),
        books_service.search_books_by_title(q, limit=15),
        return_exceptions=True,
    )

    all_items = []
    for result in (movies, tracks, books):
        if isinstance(result, Exception):
            continue
        all_items.extend(result)

    return {
        "query": q,
        "results": [
            {
                "id": item.id,
                "title": item.title,
                "media_type": item.media_type,
                "image_url": item.image_url,
                "source_url": item.source_url,
            }
            for item in all_items
        ],
    }