
import os, random, time
import cloudinary
import cloudinary.api
from cloudinary.search import Search
from cloudinary.utils import cloudinary_url

DEFAULT_ROOT = os.environ.get("CLOUD_TONGUE_ROOT", "home")
IMAGE_EXTS = {"jpg", "jpeg", "png", "webp", "gif", "bmp"}

def _norm_root(root: str) -> str:
    root = (root or "").strip().strip("/")
    return root or "home"

def _search_under_root(root_folder: str, max_results: int = 500):
    # Don't limit by resource_type to allow raw images too
    expr = f'folder="{root_folder}/*"'
    return Search().expression(expr).max_results(max_results).execute()

def _infer_category(root: str, public_id: str) -> str:
    # public_id like "home/白苔/img123" -> "白苔"
    root = _norm_root(root)
    prefix = f"{root}/"
    if public_id.startswith(prefix):
        tail = public_id[len(prefix):]
        return tail.split("/", 1)[0]
    return ""

def _is_visual_resource(r: dict) -> bool:
    rt = (r.get("resource_type") or "image").lower()
    fmt = (r.get("format") or "").lower()
    if rt == "image":
        return True
    if rt == "raw" and fmt in IMAGE_EXTS:
        return True
    return False

def _build_url(r: dict) -> str | None:
    public_id = r.get("public_id")
    if not public_id:
        return None
    rt = (r.get("resource_type") or "image").lower()
    typ = (r.get("type") or "upload").lower()
    # If asset is authenticated-token based, skip (not viewable without token/cookie)
    if typ == "authenticated":
        return None
    params = dict(secure=True)
    if typ == "private":
        params["sign_url"] = True
        params["expires_at"] = int(time.time()) + 3600  # 1h temp URL

    if rt == "image":
        url, _ = cloudinary_url(public_id, type=typ, **params)
    else:
        url, _ = cloudinary_url(public_id, resource_type=rt, type=typ, **params)
    return url

def get_random_cloudinary_question(root_folder: str = DEFAULT_ROOT, fallback_categories=None):
    root = _norm_root(root_folder)
    if fallback_categories is None:
        fallback_categories = ["白苔", "黃苔", "灰黑苔", "紅紫舌無苔"]

    result = _search_under_root(root)
    resources = result.get("resources", []) or []
    # group by category
    by_cat = {}
    for r in resources:
        if not _is_visual_resource(r):
            continue
        cat = _infer_category(root, r.get("public_id", ""))
        if not cat:
            continue
        by_cat.setdefault(cat, []).append(r)

    cats = list(by_cat.keys()) or list(fallback_categories)
    # Select a category that actually has at least one usable URL
    random.shuffle(cats)
    chosen_cat = None
    chosen_res = None
    for cat in cats:
        random.shuffle(by_cat.get(cat, []))
        for r in by_cat.get(cat, []):
            url = _build_url(r)
            if url:
                chosen_cat = cat
                chosen_res = r | {"_url": url}
                break
        if chosen_res:
            break

    if not chosen_res:
        # Fallback: no assets yielded a URL
        return {
            "image_url": "",
            "public_id": "",
            "category": random.choice(cats) if cats else "白苔",
            "choices": (cats[:4] if len(cats) >= 4 else (cats + [c for c in fallback_categories if c not in cats])[:4]) or fallback_categories,
            "explanation": "Cloudinary 中找不到可顯示的圖片（可能是 access_mode=authenticated 或上傳為 raw 且副檔名非圖片）。",
        }

    # Build choices and explanation
    all_cats = list(dict.fromkeys(cats))  # unique preserve order
    random.shuffle(all_cats)
    if len(all_cats) < 4:
        pool = [c for c in fallback_categories if c not in all_cats]
        random.shuffle(pool)
        choices = (all_cats + pool)[:4]
    else:
        choices = all_cats[:4]
    if chosen_cat not in choices:
        choices[random.randrange(len(choices))] = chosen_cat
        random.shuffle(choices)

    explanation = f"此題由 Cloudinary 資料夾「{root}/{chosen_cat}」隨機抽取。"
    return {
        "image_url": chosen_res.get("_url", ""),
        "public_id": chosen_res.get("public_id", ""),
        "category": chosen_cat,
        "choices": choices,
        "explanation": explanation,
    }
