import io
import logging
from typing import Dict, Any, Optional, List
from PIL import Image
import requests
import torch
from app.core.exceptions import ImageProcessingError

logger = logging.getLogger(__name__)

ROAD_SCORES: Dict[str, int] = {
    # Excellent
    "a newly paved road": 100,
    "a clean road": 100,
    "an excellent highway": 100,
    "a smooth asphalt road": 98,
    "a well maintained road": 97,
    "a dry road": 95,
    "a clear road": 95,
    "a road with clear lane markings": 95,

    # Good
    "a road with slight wear": 90,
    "a slightly cracked road": 88,
    "a patched road": 85,
    "a road with faded lane markings": 82,

    # Moderate
    "a rough road": 75,
    "a road with small potholes": 72,
    "a road with minor potholes": 70,
    "an uneven road surface": 68,
    "a road with loose gravel": 65,
    "a gravel road": 60,
    "a dusty road": 60,
    "a road with standing water": 58,
    "a road with light traffic": 60,

    # Poor
    "a road with large potholes": 45,
    "a road with major potholes": 40,
    "a muddy road": 35,
    "a waterlogged road": 30,
    "a road under construction": 30,
    "a damaged road": 28,
    "a road with broken pavement": 25,
    "a road with missing pavement": 20,
    "a road with heavy traffic": 20,

    # Dangerous
    "a blocked road": 15,
    "a road accident": 10,
    "a flooded road": 10,
    "a road with fallen trees": 10,
    "a damaged bridge": 5,
    "a collapsed road": 0,
    "a severely damaged road": 0
}

ROAD_LABELS: List[str] = list(ROAD_SCORES.keys())

def get_category_for_score(score: int) -> str:
    if score >= 95:
        return "Excellent"
    elif score >= 80:
        return "Good"
    elif score >= 60:
        return "Moderate"
    elif score >= 20:
        return "Poor"
    else:
        return "Dangerous"

class RoadModelService:
    def __init__(self):
        self.model = None
        self.processor = None
        self.device = None
        self.is_loaded = False

    def load_model(self):
        """Lazy load CLIP model on first inference."""
        if not self.is_loaded:
            try:
                from transformers import CLIPModel, CLIPProcessor

                self.device = "cuda" if torch.cuda.is_available() else "cpu"
                logger.info(f"Loading CLIP model on device: {self.device}...")
                self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(self.device)
                self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
                self.is_loaded = True
                logger.info("CLIP model loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load HuggingFace CLIP model: {e}")
                raise ImageProcessingError(
                    message="Vision AI model failed to initialize on the server.",
                    details=str(e)
                )

    def analyze_image(self, image: Image.Image) -> Dict[str, Any]:
        """Analyze a PIL Image using CLIP zero-shot classification against road labels."""
        self.load_model()
        if not self.is_loaded or not (self.model and self.processor):
            raise ImageProcessingError(
                message="CLIP vision model is not loaded. Please ensure the app has fully started."
            )

        try:
            inputs = self.processor(
                text=ROAD_LABELS,
                images=image,
                return_tensors="pt",
                padding=True
            )
            if self.device == "cuda":
                inputs = {k: v.to("cuda") for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.model(**inputs)

            logits = outputs.logits_per_image
            probs = logits.softmax(dim=1).cpu()[0]

            top_probs, top_indices = torch.topk(probs, k=min(3, len(ROAD_LABELS)))

            best_index = top_indices[0].item()
            best_label = ROAD_LABELS[best_index]
            score = ROAD_SCORES[best_label]
            confidence = round(top_probs[0].item() * 100, 2)

            top_candidates = [
                {"label": ROAD_LABELS[idx.item()], "probability": round(prob.item() * 100, 2)}
                for prob, idx in zip(top_probs, top_indices)
            ]

            return {
                "condition_label": best_label,
                "road_score": score,
                "confidence_percent": confidence,
                "category": get_category_for_score(score),
                "top_candidates": top_candidates
            }
        except Exception as e:
            logger.error(f"Inference error with CLIP: {e}")
            raise ImageProcessingError(
                message=f"Failed to run vision inference on road image: {str(e)}",
                details=str(e)
            )

    def analyze_from_url(self, image_url: str) -> Dict[str, Any]:
        """Fetch image from URL and analyze road condition."""
        if not image_url or not image_url.startswith(("http://", "https://")):
            raise ImageProcessingError(
                message="Invalid image URL provided. Must start with http:// or https://",
                details={"provided_url": image_url}
            )

        try:
            response = requests.get(image_url, timeout=12)
        except requests.exceptions.Timeout:
            raise ImageProcessingError(
                message="Timeout while downloading road image from the specified URL.",
                details={"url": image_url}
            )
        except requests.exceptions.RequestException as e:
            raise ImageProcessingError(
                message=f"Network error downloading image from URL: {str(e)}",
                details={"url": image_url, "error": str(e)}
            )

        if response.status_code != 200:
            raise ImageProcessingError(
                message=f"Remote image server returned HTTP {response.status_code}",
                details={"url": image_url, "status_code": response.status_code}
            )

        try:
            image = Image.open(io.BytesIO(response.content)).convert("RGB")
        except Exception as e:
            raise ImageProcessingError(
                message="Downloaded content is not a valid or readable image file.",
                details={"url": image_url, "error": str(e)}
            )

        return self.analyze_image(image)

    def analyze_from_bytes(self, image_bytes: bytes) -> Dict[str, Any]:
        """Analyze image from raw byte stream (e.g. uploaded file)."""
        if not image_bytes:
            raise ImageProcessingError(
                message="Uploaded image file is empty."
            )

        try:
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except Exception as e:
            raise ImageProcessingError(
                message="Uploaded file is not a recognized or valid image format.",
                details=str(e)
            )

        return self.analyze_image(image)

    def estimate_default_road_condition(
        self,
        weather_safety: float = 90.0,
        congestion_ratio: float = 1.0
    ) -> Dict[str, Any]:
        """Estimate road condition heuristically based on weather severity and traffic."""
        if weather_safety < 60:
            label = "a road with standing water"
            score = 58
            cat = "Moderate"
        elif congestion_ratio > 1.6:
            label = "a road with heavy traffic"
            score = 70
            cat = "Moderate"
        else:
            label = "a clear road"
            score = 95
            cat = "Excellent"

        return {
            "condition_label": label,
            "road_score": score,
            "confidence_percent": 80.0,
            "category": cat,
            "top_candidates": []
        }

road_model_service = RoadModelService()
