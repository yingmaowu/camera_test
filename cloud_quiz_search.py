
import os, random
import cloudinary
from cloudinary.search import Search
from cloudinary.utils import cloudinary_url

DEFAULT_ROOT = os.environ.get("CLOUD_TONGUE_ROOT", "home")
ALLOWED_EXT = {"jpg", "jpeg", "png", "webp", "gif"}

def _norm_root(root: str) -> str:
    root = (root or "").strip().strip("/")
    return root or "home"

def _search_images_under_root(root_folder: str, max_results: int = 500):
    """Return list of resources under root_folder using Cloudinary Search API.
    We don't request with_field extras (to avoid 400). We filter client-side.
    """
    root_folder = _norm_root(root_folder)
    expr = f'folder:"{root_folder}/*"'
    result = Search().expression(expr).max_results(min(max_results, 500)).execute()
    resources = result.get("resources", []) or []
    # Prefer images; some may be uploaded as other resource_types.
    images = []
    for r in resources:
        rt = r.get("resource_type")
        fmt = (r.get("format") or "").lower()
        if rt == "image" or fmt in ALLOWED_EXT:
            images.append(r)
    return images

def _extract_category(public_id: str, root_folder: str):
    # 'home/白苔/xxx' -> '白苔'
    root_prefix = f"{_norm_root(root_folder)}/"
    if public_id.startswith(root_prefix):
        tail = public_id[len(root_prefix):]
        return tail.split("/", 1)[0]
    return None

def _build_secure_url(res: dict):
    pid = res.get("public_id", "")
    fmt = res.get("format")  # can be None
    rt = res.get("resource_type", "image") or "image"
    typ = res.get("type", "upload") or "upload"
    url, _ = cloudinary_url(pid, format=fmt, resource_type=rt, type=typ, secure=True)
    return url

def get_random_cloudinary_question(root_folder: str = DEFAULT_ROOT, fallback_categories=None):
    root_folder = _norm_root(root_folder)
    if fallback_categories is None:
        fallback_categories = ["白苔", "黃苔", "灰黑苔", "紅紫舌無苔"]

    resources = _search_images_under_root(root_folder)
    # Group by category
    by_cat = {}
    for r in resources:
        pid = r.get("public_id") or ""
        cat = _extract_category(pid, root_folder)
        if not cat:
            continue
        by_cat.setdefault(cat, []).append(r)

    categories = list(by_cat.keys())
    if not categories:
        categories = list(fallback_categories)
        # Still return a question without image if no images found
        choices = categories[:]
        random.shuffle(choices)
        choices = (choices + [c for c in fallback_categories if c not in choices])[:4]
        return {
            "image_url": "",
            "public_id": "",
            "category": random.choice(categories),
            "choices": choices,
            "explanation": "Cloudinary 中找不到任何圖片，請確認資料夾與權限。",
        }

    cat = random.choice(categories)
    chosen = random.choice(by_cat[cat])
    image_url = _build_secure_url(chosen)

    # Build choices
    choices = list(dict.fromkeys(categories))
    random.shuffle(choices)
    if len(choices) < 4:
        pool = [c for c in (fallback_categories or []) if c not in choices]
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
        "public_id": chosen.get("public_id", ""),
        "category": cat,
        "choices": choices,
        "explanation": explanation,
    }
