"""
Core mood model shared across all media adapters (movies, music, books...).

Every piece of content gets scored on the same two axes so we can compare
apples to oranges (a song vs. a movie vs. a book) using one distance formula.

Axes:
    valence: 0.0 (dark/negative) -> 1.0 (bright/positive)
    energy:  0.0 (calm/slow)     -> 1.0 (intense/fast)
"""

from dataclasses import dataclass
from math import sqrt


@dataclass
class MoodPoint:
    valence: float  # 0.0 - 1.0
    energy: float   # 0.0 - 1.0

    def distance_to(self, other: "MoodPoint") -> float:
        return sqrt((self.valence - other.valence) ** 2 + (self.energy - other.energy) ** 2)


@dataclass
class ContentItem:
    """A single recommendable item, already normalized to our mood space."""
    id: str
    title: str
    media_type: str  # "movie" | "music" | "book"
    image_url: str | None
    mood: MoodPoint
    source_url: str | None = None

    def score_against(self, target: MoodPoint) -> float:
        distance = self.mood.distance_to(target)
        return 1 - distance


MOOD_PRESETS = {
    "happy":     MoodPoint(valence=0.85, energy=0.65),
    "sad":       MoodPoint(valence=0.15, energy=0.25),
    "angry":     MoodPoint(valence=0.2,  energy=0.85),
    "anxious":   MoodPoint(valence=0.25, energy=0.75),
    "relaxed":   MoodPoint(valence=0.65, energy=0.15),
    "excited":   MoodPoint(valence=0.9,  energy=0.9),
    "nostalgic": MoodPoint(valence=0.55, energy=0.3),
    "bored":     MoodPoint(valence=0.4,  energy=0.15),
    "romantic":  MoodPoint(valence=0.75, energy=0.4),
    "lonely":    MoodPoint(valence=0.2,  energy=0.2),
    "confident": MoodPoint(valence=0.8,  energy=0.75),
    "calm":      MoodPoint(valence=0.6,  energy=0.1),
}