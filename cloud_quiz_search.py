
import os, random, time
from typing import List, Dict, Any
import cloudinary
import cloudinary.api
from cloudinary.search import Search
from cloudinary.utils import cloudinary_url

# ------------------------------------------------------------------
# Root configuration
# ------------------------------------------------------------------
# We support multiple roots via CLOUD_TONGUE_ROOTS, e.g. "home,",
# which means: search under "home/*" AND also root-level ("白苔/*", etc.).
# Backwards-compat: if not set, we default to searching BOTH ["home", ""].
#
# You can still pass root_folder to get_random_cloudinary_question(),
# but the env var CLOUD_TONGUE_ROOTS (if present) takes precedence.
# ------------------------------------------------------------------

def _parse_roots(default_roots: List[str]) -> List[str]:
    roots_env = os.environ.get("CLOUD_TONGUE_ROOTS")
    if roots_env is not None:
        roots = [r.strip().strip('/') for r in roots_env.split(',')]
        # Normalize empty => root-level
        roots = [r for r in (r if r != None else '' for r in roots)]
        # Ensure '' is a single entry if present
        uniq = []
        for r in roots:
            if r not in uniq:
                uniq.append(r)
        return uniq or default_roots

    # Legacy single-root support
    single = os.environ.get("CLOUD_TONGUE_ROOT")
    if single is not None:
        single = single.strip().strip('/')
        if single == '':
            return ['']
        return [single]

    return default_roots

# Allowed file extensions that we treat as displayable images even for raw assets
_IMG_EXTS = {"jpg", "jpeg", "png", "webp", "gif", "bmp"}

def _is_displayable(r: Dict[str, Any]) -> bool:
    rt = (r.get("resource_type") or "image").lower()
    typ = (r.get("type") or "upload").lower()
    fmt = (r.get("format") or "").lower()
    if rt == "image":
        # For authenticated images, we skip (browser needs token). Private we can sign.
        return typ in {"upload", "private"}
    if rt == "raw":
        return fmt in _IMG_EXTS and typ in {"upload", "private"}
    return False

def _build_secure_url(public_id: str, rt: str, typ: str) -> str:
    params = dict(secure=True)
    # private assets require a signed URL; set a reasonable expiry
    if typ == "private":
        params["sign_url"] = True
        params["expires_at"] = int(time.time()) + 3600  # 1 hour
    if rt == "image":
        url, _ = cloudinary_url(public_id, type=typ, **params)
    else:
        url, _ = cloudinary_url(public_id, resource_type=rt, type=typ, **params)
    return url

def _folder_for(cat: str, root: str) -> str:
    root = (root or "").strip().strip("/")
    return f"{cat}" if root == "" else f"{root}/{cat}"

def _search_category(cat: str, root: str, max_results: int = 200) -> List[Dict[str, Any]]:
    """Search resources for a specific category under a given root."""
    folder = _folder_for(cat, root)
    # Search API: folder="白苔" or folder="home/白苔"
    res = Search().expression(f'folder="{folder}"').max_results(max_results).execute()
    items = res.get("resources", []) or []
    # keep only displayable
    items = [r for r in items if _is_displayable(r)]
    return items

def _pick_item(items: List[Dict[str, Any]]):
    if not items:
        return None
    # random choice; if first fails to build URL, try others
    order = list(range(len(items)))
    random.shuffle(order)
    for i in order:
        r = items[i]
        pid = r.get("public_id", "")
        rt = (r.get("resource_type") or "image").lower()
        typ = (r.get("type") or "upload").lower()
        try:
            url = _build_secure_url(pid, rt, typ)
            if url:
                return r, url
        except Exception:
            continue
    return None

def get_random_cloudinary_question(root_folder: str = None, fallback_categories=None):
    """Return a question dict using a random image from Cloudinary.

    The dict format:
    {
      "image_url": <str>,
      "public_id": <str>,
      "category": <str>,  # correct answer
      "choices": [<str>, <str>, ...],
      "explanation": <str>,
    }
    """
    # Categories (Chinese labels)
    if fallback_categories is None:
        fallback_categories = ["白苔", "黃苔", "灰黑苔", "紅紫舌無苔"]

    # Determine roots to search. Default: BOTH 'home' and root-level.
    roots = _parse_roots(default_roots=["home", ""])

    # Aggregate available items per category across roots
    per_cat: Dict[str, List[Dict[str, Any]]] = {c: [] for c in fallback_categories}
    for root in roots:
        for cat in fallback_categories:
            try:
                items = _search_category(cat, root)
                if items:
                    per_cat[cat].extend(items)
            except Exception:
                # ignore root that doesn't exist or lacks permission
                continue

    # Choose a category that actually has items
    non_empty = [cat for cat, items in per_cat.items() if items]
    if not non_empty:
        # Nothing found anywhere — build a safe fallback question
        choices = list(fallback_categories)
        random.shuffle(choices)
        choices = choices[:4]
        return {
            "image_url": "",
            "public_id": "",
            "category": choices[0],
            "choices": choices,
            "explanation": "Cloudinary 找不到可用的圖片，請確認資料夾位置與權限（建議使用 Public image/upload）。",
        }

    cat = random.choice(non_empty)
    picked = _pick_item(per_cat[cat])
    if not picked:
        # Extremely unlikely: had items but all failed URL build
        choices = list(fallback_categories)
        random.shuffle(choices)
        choices = choices[:4]
        return {
            "image_url": "",
            "public_id": "",
            "category": choices[0],
            "choices": choices,
            "explanation": f"無法產生 {cat} 的可用圖片網址，請檢查資產的 resource_type/type 設定。",
        }

    r, url = picked
    public_id = r.get("public_id", "")
    # Build choices (ensure correct answer present)
    choices = list(dict.fromkeys(fallback_categories))  # keep order unique
    random.shuffle(choices)
    choices = choices[:4] if len(choices) >= 4 else choices
    if cat not in choices:
        idx = random.randrange(len(choices))
        choices[idx] = cat
        random.shuffle(choices)

    explanation = "此題由 Cloudinary 隨機抽取（支援根目錄與 home/ 資料夾）。"

    return {
        "image_url": url,
        "public_id": public_id,
        "category": cat,
        "choices": choices,
        "explanation": explanation,
    }
