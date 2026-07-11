"""
Open Library adapter: fetches books by subject and maps subject -> approximate mood point.

No API key required. Uses the Subjects API, which lets us pull books tied to
a specific topic (e.g. "romance", "horror") - similar to how we handle
movie genres and music tags.
"""

import random
import httpx
from app.models.mood import MoodPoint, ContentItem

BASE_URL = "https://openlibrary.org"
COVER_URL = "https://covers.openlibrary.org/b/id/{}-M.jpg"

SUBJECT_MOOD_MAP = {
    "humor":            MoodPoint(0.85, 0.55),
    "romance":          MoodPoint(0.75, 0.35),
    "fantasy":          MoodPoint(0.65, 0.65),
    "science_fiction":  MoodPoint(0.55, 0.7),
    "thriller":         MoodPoint(0.3, 0.85),
    "horror":           MoodPoint(0.15, 0.85),
    "mystery":          MoodPoint(0.35, 0.6),
    "adventure":        MoodPoint(0.7, 0.75),
    "biography":        MoodPoint(0.5, 0.4),
    "self_help":        MoodPoint(0.7, 0.5),
    "history":          MoodPoint(0.45, 0.35),
    "poetry":           MoodPoint(0.4, 0.3),
    "young_adult":      MoodPoint(0.7, 0.6),
    "classics":         MoodPoint(0.4, 0.4),
}
DEFAULT_MOOD = MoodPoint(0.5, 0.5)


def _best_subjects_for_mood(target: MoodPoint, top_n: int = 3) -> list[str]:
    scored = []
    for name, mood in SUBJECT_MOOD_MAP.items():
        distance = ((mood.valence - target.valence) ** 2 + (mood.energy - target.energy) ** 2) ** 0.5
        scored.append((distance, name))
    scored.sort(key=lambda x: x[0])
    return [name for _, name in scored[:top_n]]


async def search_books(mood: MoodPoint | None = None, limit: int = 20) -> list[ContentItem]:
    target = mood or DEFAULT_MOOD
    candidate_subjects = _best_subjects_for_mood(target, top_n=3)
    chosen_subject = random.choice(candidate_subjects)
    subject_mood = SUBJECT_MOOD_MAP.get(chosen_subject, DEFAULT_MOOD)

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f"{BASE_URL}/subjects/{chosen_subject}.json",
            params={"limit": limit, "offset": random.randint(0, 40)},
        )
        resp.raise_for_status()
        works = resp.json().get("works", [])

        items = []
        for work in works:
            cover_id = work.get("cover_id")
            authors = ", ".join(a.get("name", "Unknown") for a in work.get("authors", []))
            items.append(ContentItem(
                id=work.get("key", work.get("title", "")),
                title=f"{work.get('title', 'Untitled')} — {authors or 'Unknown'}",
                media_type="book",
                image_url=COVER_URL.format(cover_id) if cover_id else None,
                mood=subject_mood,
            ))
    return items
async def search_books_by_title(query: str, limit: int = 15) -> list[ContentItem]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f"{BASE_URL}/search.json",
            params={"q": query, "limit": limit},
        )
        resp.raise_for_status()
        docs = resp.json().get("docs", [])

        items = []
        for doc in docs:
            cover_id = doc.get("cover_i")
            authors = ", ".join(doc.get("author_name", []))
            subjects = [s.lower().replace(" ", "_") for s in doc.get("subject", [])[:5]]
            mood = _mood_for_subjects(subjects)
            work_key = doc.get("key")
            items.append(ContentItem(
                id=work_key or doc.get("title", ""),
                title=f"{doc.get('title', 'Untitled')} — {authors or 'Unknown'}",
                media_type="book",
                image_url=COVER_URL.format(cover_id) if cover_id else None,
                mood=mood,
                source_url=f"{BASE_URL}{work_key}" if work_key else None,
            ))
        return items


def _mood_for_subjects(subjects: list[str]) -> MoodPoint:
    points = [SUBJECT_MOOD_MAP[s] for s in subjects if s in SUBJECT_MOOD_MAP]
    if not points:
        return DEFAULT_MOOD
    avg_valence = sum(p.valence for p in points) / len(points)
    avg_energy = sum(p.energy for p in points) / len(points)
    return MoodPoint(avg_valence, avg_energy)