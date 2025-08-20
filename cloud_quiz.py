import os, random
import cloudinary
import cloudinary.api

# Ensure Cloudinary is configured via env vars:
# CLOUD_NAME, CLOUD_API_KEY, CLOUD_API_SECRET

DEFAULT_ROOT = os.environ.get("CLOUD_TONGUE_ROOT", "home")

def _list_categories(root_folder: str = DEFAULT_ROOT):
    # returns list of subfolder names under root (category names)
    resp = cloudinary.api.subfolders(root_folder)
    subs = [sf["name"] for sf in resp.get("folders", [])]
    # The API returns only direct children; names are like f"{root_folder}/{name}"
    # Normalize to just the leaf name.
    clean = []
    for full in subs:
        # full looks like '<root>/<leaf>'
        parts = full.split("/", 1)
        if len(parts) == 2:
            clean.append(parts[1])
        else:
            clean.append(full)
    return clean

def _random_resource_from_category(cat: str, root_folder: str = DEFAULT_ROOT, max_results: int = 100):
    prefix = f"{root_folder}/{cat}/"
    # list images under the category prefix
    resp = cloudinary.api.resources(
        type="upload",
        prefix=prefix,
        resource_type="image",
        max_results=max_results,
        context=True
    )
    resources = resp.get("resources", [])
    if not resources:
        return None
    return random.choice(resources)

def get_random_cloudinary_question(root_folder: str = DEFAULT_ROOT, fallback_categories=None):
    """Return a question dict using a random image from Cloudinary.

    The dict format:
    {
      "image_url": <str>,
      "public_id": <str>,
      "category": <str>,  # answer
      "choices": [<str>, <str>, ...],
      "explanation": <str>,
    }
    """
    if fallback_categories is None:
        fallback_categories = ["白苔", "黃苔", "灰黑苔", "紅紫舌無苔"]

    cats = _list_categories(root_folder)
    if not cats:
        cats = list(fallback_categories)

    # Pick a category first (uniform over categories)
    cat = random.choice(cats)

    res = _random_resource_from_category(cat, root_folder=root_folder)
    # If this category is empty, try other categories
    tried = {cat}
    while (res is None) and len(tried) < len(cats):
        cat2 = random.choice([c for c in cats if c not in tried])
        res = _random_resource_from_category(cat2, root_folder=root_folder)
        tried.add(cat2)

    if res is None:
        # total fallback – synth question with no image
        return {
            "image_url": "",
            "public_id": "",
            "category": random.choice(cats),
            "choices": cats[:],
            "explanation": "從 Cloudinary 無法列出圖片，請確認資料夾或 API 權限。"
        }

    image_url = res.get("secure_url") or res.get("url")
    public_id = res.get("public_id", "")
    # Build choices (shuffle; ensure correct answer inside)
    choices = list(set(cats))  # unique
    random.shuffle(choices)

    # Keep top 4 options; if fewer, pad from fallback pool
    if len(choices) < 4:
        pool = list(set(fallback_categories) - set(choices))
        random.shuffle(pool)
        choices = (choices + pool)[:4]
    else:
        choices = choices[:4]

    if cat not in choices:
        # ensure correct answer present by replacing a random slot
        idx = random.randrange(len(choices))
        choices[idx] = cat
        random.shuffle(choices)

    explanation = f"此題由 Cloudinary 資料夾「{root_folder}/{cat}」隨機抽取。"

    return {
        "image_url": image_url,
        "public_id": public_id,
        "category": cat,
        "choices": choices,
        "explanation": explanation,
    }