import logging
from typing import Dict, Any, List
from app.core.config import settings

logger = logging.getLogger(__name__)

class ScoringService:
    def __init__(self):
        self.w_duration = settings.WEIGHT_DURATION
        self.w_congestion = settings.WEIGHT_CONGESTION
        self.w_road = settings.WEIGHT_ROAD_SCORE
        self.w_weather = settings.WEIGHT_WEATHER

    def compute_composite_score(
        self,
        duration_minutes: float,
        congestion_ratio: float,
        road_condition_score: float,
        weather_safety_score: float,
        max_duration_in_group: float = 30.0
    ) -> Dict[str, float]:
        """
        Compute an integrated suitability score for an emergency hospital route.
        Each component is normalized on a 0-100 scale:
        - duration_score: Shorter ETA yields higher score (crucial for emergencies)
        - congestion_score: Lower traffic congestion ratio gives higher score
        - road_condition_score: Smoother, safer road surfaces give higher score
        - weather_safety_score: Clearer skies, dry roads, good visibility give higher score
        """
        # Duration score: 100 for immediate, scaled downwards as travel time increases
        # Using a benchmark where <= 5 mins = 100, and scales down smoothly
        ref_duration = max(max_duration_in_group, 15.0)
        duration_factor = min(1.0, duration_minutes / ref_duration)
        duration_score = max(0.0, round((1.0 - duration_factor * 0.85) * 100.0, 1))

        # Congestion score: 1.0 (free flow) = 100; 2.0 (double duration) = 40; >=2.5 = 10
        if congestion_ratio <= 1.0:
            congestion_score = 100.0
        elif congestion_ratio <= 1.5:
            congestion_score = round(100.0 - (congestion_ratio - 1.0) * 80.0, 1) # 100 -> 60
        elif congestion_ratio <= 2.0:
            congestion_score = round(60.0 - (congestion_ratio - 1.5) * 60.0, 1)  # 60 -> 30
        else:
            congestion_score = max(5.0, round(30.0 - (congestion_ratio - 2.0) * 20.0, 1))

        # Composite weighted sum
        composite = (
            (duration_score * self.w_duration) +
            (congestion_score * self.w_congestion) +
            (road_condition_score * self.w_road) +
            (weather_safety_score * self.w_weather)
        )
        composite_score = max(0.0, min(100.0, round(composite, 2)))

        return {
            "duration_score": duration_score,
            "congestion_score": congestion_score,
            "road_condition_score": round(float(road_condition_score), 1),
            "weather_safety_score": round(float(weather_safety_score), 1),
            "final_composite_score": composite_score
        }

    def generate_recommendation_notes(
        self,
        scores: Dict[str, float],
        duration_minutes: float,
        congestion_ratio: float,
        weather_main: str,
        road_label: str
    ) -> str:
        """Construct human-readable notes detailing why this route is scored as such."""
        notes = []
        notes.append(f"Estimated arrival: {duration_minutes:.1f} mins.")

        if congestion_ratio > 1.3:
            notes.append(f"Moderate/heavy traffic delay detected (congestion index {congestion_ratio:.2f}).")
        else:
            notes.append("Smooth traffic flow along the path.")

        notes.append(f"Road surface assessed as '{road_label}' (Quality score: {scores['road_condition_score']}/100).")

        if scores["weather_safety_score"] < 80:
            notes.append(f"Weather warning: {weather_main} condition presents caution.")
        else:
            notes.append(f"Weather conditions favorable ({weather_main}).")

        return " ".join(notes)

scoring_service = ScoringService()
