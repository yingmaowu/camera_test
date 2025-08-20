import os, random
import cloudinary
import cloudinary.api

# Configure is expected to be done elsewhere (e.g., in app.py via env vars)
# Required envs: CLOUD_NAME, CLOUD_API_KEY, CLOUD_API_SECRET
# Optional: CLOUD_TONGUE_ROOT (default "home")

DEFAULT_ROOT = os.environ.get("CLOUD_TONGUE_ROOT", "home")

def _norm_root(root: str) -> str:
    # normalize: strip spaces, remove leading '/', no trailing '/'
    root = (root or "").strip().strip("/")
    return root or "home"

def _list_categories_via_subfolders(root_folder: str):
    """Try Cloudinary 'subfolders' API."""
    try:
        resp = cloudinary.api.subfolders(root_folder)
        names = []
        for sf in resp.get("folders", []):
            name = sf.get("name") or ""
            # name often looks like "home/白苔"; convert to leaf after the root
            parts = name.split("/", 1)
            leaf = parts[1] if len(parts) == 2 else parts[0]
            if leaf and leaf not in names:
                names.append(leaf)
        return names
    except Exception:
        return []

def _list_categories_via_resources(root_folder: str, max_results: int = 500):
    """Fallback: list resources under root and infer first-level subfolders."""
    try:
        prefix = f"{root_folder}/"
        resp = cloudinary.api.resources(
            type="upload",
            prefix=prefix,
            resource_type="image",
            max_results=max_results,
            context=False
        )
        cats = set()
        for r in resp.get("resources", []):
            public_id = r.get("public_id", "")
            # public_id can look like "home/白苔/img123" or "home/白苔/sub/img"
            if public_id.startswith(prefix):
                tail = public_id[len(prefix):]  # "白苔/img123"
                parts = tail.split("/", 1)
                if parts and parts[0]:
                    cats.add(parts[0])
        return list(cats)
    except Exception:
        return []

def _list_categories(root_folder: str):
    root_folder = _norm_root(root_folder)
    cats = _list_categories_via_subfolders(root_folder)
    if cats:
        return cats
    return _list_categories_via_resources(root_folder)

def _random_resource_from_category(cat: str, root_folder: str, max_results: int = 100):
    root_folder = _norm_root(root_folder)
    prefix = f"{root_folder}/{cat}/"
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
    root_folder = _norm_root(root_folder)
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
            "choices": cats[:4] if len(cats) >= 4 else (cats + [c for c in fallback_categories if c not in cats])[:4],
            "explanation": "Cloudinary 中找不到任何圖片，請確認資料夾與權限。"
        }

    image_url = res.get("secure_url") or res.get("url", "")
    public_id = res.get("public_id", "")
    # Build choices (shuffle; ensure correct answer inside)
    choices = list(dict.fromkeys(cats))  # keep order/unique
    random.shuffle(choices)

    # Keep top 4 options; if fewer, pad from fallback pool
    if len(choices) < 4:
        pool = [c for c in fallback_categories if c not in choices]
        random.shuffle(pool)
        choices = (choices + pool)[:4]
    else:
        choices = choices[:4]

    if cat not in choices and choices:
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
