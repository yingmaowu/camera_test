# tongue_regions.py

# 五區對應 table
REGION_MAP = {
    "liver": "肝區",
    "kidney": "腎區",
    "heart": "心區",
    "spleen": "脾區",
    "lung": "肺區"
}

# 可回傳所有 key list
def get_region_ids():
    return list(REGION_MAP.keys())

# 取得中文名稱
def get_region_name(region_id):
    return REGION_MAP.get(region_id, "未知區域")
