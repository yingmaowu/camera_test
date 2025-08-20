import os, random
import cloudinary
from cloudinary.search import Search
from typing import List, Dict

DEFAULT_ROOT = os.environ.get("CLOUD_TONGUE_ROOT", "home")

IMAGE_FORMATS = {"jpg", "jpeg", "png", "webp", "gif"}

def _norm_root(root: str) -> str:
    return (root or "home").strip().strip("/") or "home"

def _search_under_root(root: str) -> Dict:
    root = _norm_root(root)
    # Do NOT restrict resource_type here; some uploads may be 'raw' by mistake.
    return Search() \
        .expression(f'folder:"{root}/*"') \
        .with_field("public_id") \
        .with_field("resource_type") \
        .with_field("format") \
        .max_results(500) \
        .execute()

def _group_by_category(resources: List[Dict], root: str) -> Dict[str, List[Dict]]:
    root = _norm_root(root)
    cats = {}
    prefix = root + "/"
    for r in resources:
        pid = r.get("public_id","")
        if not pid.startswith(prefix):
            continue
        tail = pid[len(prefix):]  # e.g. '白苔/img123'
        cat = tail.split("/", 1)[0] if tail else ""
        if not cat:
            continue
        cats.setdefault(cat, []).append(r)
    return cats

def _pick_random_image_resource(resources: List[Dict]) -> Dict:
    # First try true image resources
    imgs = [r for r in resources if r.get("resource_type") == "image"]
    if not imgs:
        # If none, try those with image-like formats (some may have been uploaded as raw)
        imgs = [r for r in resources if (r.get("format") or "").lower() in IMAGE_FORMATS]
    if not imgs:
        return {}
    return random.choice(imgs)

def get_random_cloudinary_question(root_folder: str = DEFAULT_ROOT, fallback_categories=None):
    root_folder = _norm_root(root_folder)
    if fallback_categories is None:
        fallback_categories = ["白苔", "黃苔", "灰黑苔", "紅紫舌無苔"]

    result = _search_under_root(root_folder)
    resources = result.get("resources", [])
    cats = _group_by_category(resources, root_folder)
    if not cats:
        # Nothing under the root
        return {
            "image_url": "",
            "public_id": "",
            "category": random.choice(fallback_categories),
            "choices": fallback_categories,
            "explanation": "Cloudinary 的資料夾下沒有可用的圖片（可能是沒有資源或權限不足）。"
        }

    # Randomly pick a category that actually has at least one usable resource
    viable = [(cat, lst) for cat, lst in cats.items() if lst]
    if not viable:
        return {
            "image_url": "",
            "public_id": "",
            "category": random.choice(list(cats.keys()) or fallback_categories),
            "choices": fallback_categories,
            "explanation": "找到資料夾，但裡面沒有可用的圖片（可能是被當成 raw 上傳）。"
        }

    cat, lst = random.choice(viable)
    res = _pick_random_image_resource(lst)
    if not res:
        return {
            "image_url": "",
            "public_id": "",
            "category": cat,
            "choices": fallback_categories,
            "explanation": f"「{root_folder}/{cat}」沒有可用的 image 資源（可能是 raw 上傳）。"
        }

    # Build delivery URL (works for images)
    # Prefer secure URL from delivery, else construct with CloudinaryImage
    try:
        from cloudinary.utils import cloudinary_url
        url, _ = cloudinary_url(res["public_id"], secure=True, resource_type=res.get("resource_type","image"))
    except Exception:
        url = ""

    choices = list({*cats.keys(), *fallback_categories})
    random.shuffle(choices)
    choices = choices[:4] if len(choices) >= 4 else (choices + [c for c in fallback_categories if c not in choices])[:4]
    if cat not in choices and choices:
        choices[random.randrange(len(choices))] = cat
        random.shuffle(choices)

    explanation = f"此題由 Cloudinary 資料夾「{root_folder}/{cat}」隨機抽取。"
    return {
        "image_url": url,
        "public_id": res.get("public_id",""),
        "category": cat,
        "choices": choices,
        "explanation": explanation,
    }
