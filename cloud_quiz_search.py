
import os, random
from typing import Dict, List, Tuple
import cloudinary
import cloudinary.api
from cloudinary.search import Search
from cloudinary.utils import cloudinary_url

DEFAULT_ROOT = os.environ.get("CLOUD_TONGUE_ROOT", "home")
IMAGE_EXTS = {"jpg","jpeg","png","webp","gif","bmp"}

def _norm_root(root: str) -> str:
    root = (root or "").strip().strip("/")
    return root or "home"

def _search_under_root(root_folder: str, max_results: int = 500) -> Dict:
    # Do NOT filter by resource_type to tolerate assets uploaded as 'raw'
    expr = f'folder:"{root_folder}/*"'
    return Search().expression(expr).max_results(max_results).execute()

def _collect_by_category(root_folder: str, results: Dict) -> Dict[str, List[Dict]]:
    """Group resources by first-level folder (category)."""
    prefix = f"{root_folder}/"
    groups: Dict[str, List[Dict]] = {}
    for r in results.get("resources", []):
        public_id = r.get("public_id","")
        if not public_id.startswith(prefix):
            continue
        tail = public_id[len(prefix):]  # e.g., '白苔/img123'
        cat = tail.split("/",1)[0]
        if not cat:
            continue
        groups.setdefault(cat, []).append(r)
    return groups

def _is_displayable(res: Dict) -> bool:
    """Whether we can reasonably show this as an <img>."""
    rtype = (res.get("resource_type") or "image").lower()
    fmt = (res.get("format") or "").lower()
    if rtype == "image":
        return True
    # Some were uploaded as raw but are actually image files
    if rtype == "raw" and fmt in IMAGE_EXTS:
        return True
    return False

def _build_url(res: Dict) -> str:
    """Build a secure delivery URL that matches the asset's type."""
    public_id = res.get("public_id","")
    rtype = (res.get("resource_type") or "image").lower()
    delivery_type = (res.get("type") or "upload")
    options = {"secure": True, "resource_type": rtype, "type": delivery_type}
    # Non-public delivery types (private/authenticated) usually need signing
    if delivery_type != "upload":
        options["sign_url"] = True
    url, _ = cloudinary_url(public_id, **options)
    return url or res.get("secure_url") or res.get("url") or ""

def get_random_cloudinary_question(root_folder: str = DEFAULT_ROOT, fallback_categories=None):
    """Return a question dict using a random image from Cloudinary.

    {
      "image_url": <str>,
      "public_id": <str>,
      "category": <str>,
      "choices": [<str>...],
      "explanation": <str>,
    }
    """
    root_folder = _norm_root(root_folder)
    if fallback_categories is None:
        fallback_categories = ["白苔", "黃苔", "灰黑苔", "紅紫舌無苔"]

    result = _search_under_root(root_folder)
    groups = _collect_by_category(root_folder, result)

    # categories: prefer detected groups; else fall back
    cats = list(groups.keys()) or list(fallback_categories)

    # pick a category that actually has displayable resources
    random.shuffle(cats)
    chosen_cat = None
    chosen_res = None
    for cat in cats:
        cand = [r for r in groups.get(cat, []) if _is_displayable(r)]
        if cand:
            chosen_cat = cat
            chosen_res = random.choice(cand)
            break

    if not chosen_res:
        # last resort: fall back with no image
        return {
            "image_url": "",
            "public_id": "",
            "category": cats[0] if cats else "",
            "choices": (cats[:4] or fallback_categories[:4]),
            "explanation": "Cloudinary 中找不到任何圖片，請確認資料夾與權限。"
        }

    image_url = _build_url(chosen_res)
    if not image_url:
        # try again within the same category
        cand = [r for r in groups.get(chosen_cat, []) if _is_displayable(r)]
        random.shuffle(cand)
        for r in cand:
            image_url = _build_url(r)
            if image_url:
                chosen_res = r
                break

    # Build choices (ensure correct inside, at most 4)
    choices = list(dict.fromkeys(cats))
    random.shuffle(choices)
    if len(choices) < 4:
        pool = [c for c in fallback_categories if c not in choices]
        random.shuffle(pool)
        choices = (choices + pool)[:4]
    else:
        choices = choices[:4]
    if chosen_cat not in choices and choices:
        i = random.randrange(len(choices))
        choices[i] = chosen_cat
        random.shuffle(choices)

    explanation = f"此題由 Cloudinary 資料夾「{root_folder}/{chosen_cat}」隨機抽取。"

    return {
        "image_url": image_url,
        "public_id": chosen_res.get("public_id",""),
        "category": chosen_cat,
        "choices": choices,
        "explanation": explanation,
    }
