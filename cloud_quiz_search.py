import os, random
import cloudinary
from cloudinary.search import Search

# Root folder in Cloudinary that contains subfolders per category, e.g. 'home'
DEFAULT_ROOT = os.environ.get("CLOUD_TONGUE_ROOT", "home")

# Allowed image formats as a fallback filter (in case resource_type is missing)
ALLOWED_EXT = {"jpg", "jpeg", "png", "webp", "gif"}

def _norm_root(root: str) -> str:
    root = (root or "").strip().strip("/")
    return root or "home"

def _search_under_root(root_folder: str, max_results: int = 500):
    """Return list of resources under root_folder using Cloudinary Search API.

    IMPORTANT: Do NOT use with_field('public_id', ...) etc — not supported.
    We just request resources and filter client-side.
    """
    root_folder = _norm_root(root_folder)
    expr = f'folder:"{root_folder}/*" AND resource_type:image'
    # Execute search; returns dict with 'resources' and possibly 'next_cursor'
    result = Search().expression(expr).max_results(min(max_results, 500)).execute()
    return result.get("resources", [])

def _extract_category(public_id: str, root_folder: str):
    # public_id looks like 'home/白苔/xxx' -> return '白苔'
    root_prefix = f"{root_folder}/"
    if public_id.startswith(root_prefix):
        tail = public_id[len(root_prefix):]
        return tail.split("/", 1)[0]
    return None

def _is_image_resource(res: dict):
    # Cloudinary sets 'resource_type'=='image' and 'format' for images
    rt = res.get("resource_type")
    if rt and rt != "image":
        return False
    fmt = (res.get("format") or "").lower()
    if fmt and fmt not in ALLOWED_EXT:
        # if format exists and is not an image type, skip
        return False
    return True

def get_random_cloudinary_question(root_folder: str = DEFAULT_ROOT, fallback_categories=None):
    root_folder = _norm_root(root_folder)
    if fallback_categories is None:
        fallback_categories = ["白苔", "黃苔", "灰黑苔", "紅紫舌無苔"]

    resources = _search_under_root(root_folder)

    # Filter to images and group by category
    by_cat = {}
    for r in resources:
        if not _is_image_resource(r):
            continue
        pid = r.get("public_id") or ""
        cat = _extract_category(pid, root_folder)
        if not cat:
            continue
        by_cat.setdefault(cat, []).append(r)

    categories = list(by_cat.keys()) or list(fallback_categories)

    # Choose a category uniformly
    cat = random.choice(categories)

    # Pick a resource in that category (if available)
    chosen = None
    if by_cat.get(cat):
        chosen = random.choice(by_cat[cat])
    else:
        # Fallback: pick any resource
        flat = [r for lst in by_cat.values() for r in lst]
        if flat:
            chosen = random.choice(flat)

    if not chosen:
        # Total fallback (no resources found): synthetic question
        choices = categories[:]
        random.shuffle(choices)
        if len(choices) < 4:
            pad = [c for c in fallback_categories if c not in choices]
            random.shuffle(pad)
            choices = (choices + pad)[:4]
        else:
            choices = choices[:4]
        return {
            "image_url": "",
            "public_id": "",
            "category": random.choice(categories),
            "choices": choices,
            "explanation": "Cloudinary 中找不到任何圖片，請確認資料夾與權限。"
        }

    image_url = chosen.get("secure_url") or chosen.get("url") or ""
    # Build multiple-choice options
    choices = list(dict.fromkeys(categories))
    random.shuffle(choices)
    if len(choices) < 4:
        pad = [c for c in fallback_categories if c not in choices]
        random.shuffle(pad)
        choices = (choices + pad)[:4]
    else:
        choices = choices[:4]
    if cat not in choices:
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
