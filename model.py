import torch
from transformers import CLIPProcessor
from transformers import CLIPModel
from PIL import Image
import requests
import io

device = "cuda" if torch.cuda.is_available() else "cpu"

clip_model = CLIPModel.from_pretrained(
    "openai/clip-vit-base-patch32"
).to(device)

clip_processor = CLIPProcessor.from_pretrained(
    "openai/clip-vit-base-patch32"
)

image_url = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRvARPm_CDTkek5nSs_mNQD6BA7SyPLDIqrKI--wXvicfoqebjgwiGSHeaE&s=10"
response = requests.get(image_url)
image = Image.open(io.BytesIO(response.content)).convert("RGB")

ROAD_SCORES = [{

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
]

ROAD_LABELS = list(ROAD_SCORES[0].keys())


inputs = clip_processor(
    text=ROAD_LABELS,
    images=image,
    return_tensors="pt",
    padding=True
)

with torch.no_grad():
    outputs = clip_model(**inputs)

logits = outputs.logits_per_image

probabilities = logits.softmax(dim=1)

best_index = probabilities.argmax().item()
print(best_index)
print(probabilities[0][best_index].item())

best_label = ROAD_LABELS[best_index]

road_score = ROAD_SCORES[0][best_label]

confidence = probabilities[0][best_index].item() * 100

print("Road Condition :", best_label)
print("Road Score     :", road_score)
print("Confidence     :", round(confidence,2),"%")