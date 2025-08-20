// === 舌象分類教學 ===
// 來自 rrrrr-main 的資料表（20 組）：把「部位_顏色」對應到判讀/方劑/典籍
const data = {
  "腎_white":{"message":"腎白：腎陽不足或寒象偏重，舌苔偏白。","herb":"六味地黃丸（視症加減）","classic":"腎陽虛多見白苔，畏寒肢冷。"},
  "腎_gold":{"message":"腎黃：多見濕熱或虛熱上蒸，舌苔偏黃。","herb":"知柏地黃丸（視症加減）","classic":"陰虛火旺或濕熱下注時，苔可見黃。"},
  "腎_black":{"message":"腎黑：多屬寒極或瘀象，色黑多見於舌根。","herb":"附子理中湯、活血化瘀法（依症）","classic":"寒盛則黑，或久病入絡見瘀滯。"},
  "腎_red":{"message":"腎紅：陰虛內熱，舌質紅或偏紅，苔少。","herb":"六味地黃丸、知柏地黃丸（依症）","classic":"腎陰虛則潮熱盜汗，舌紅少苔。"},
  "肝_white":{"message":"肝白：多偏寒或氣滯，苔白薄。","herb":"柴胡疏肝散（依症）","classic":"寒主收引，色白；肝鬱亦可見白苔。"},
  "肝_gold":{"message":"肝黃：多見肝膽濕熱，苔黃膩。","herb":"龍膽瀉肝湯","classic":"濕熱下注或肝膽鬱熱，苔黃而膩。"},
  "肝_black":{"message":"肝黑：多屬瘀血內阻或寒凝，見色黑暗。","herb":"血府逐瘀湯（依症）","classic":"久瘀則色暗或近黑，痛有定處。"},
  "肝_red":{"message":"肝紅：肝火偏旺或陰虛火亢，舌紅少苔。","herb":"龍膽瀉肝湯、滋陰降火（依症）","classic":"肝火上炎，目赤易怒；或陰虛火旺舌紅。"},
  "膽_white":{"message":"膽白：偏寒或膽氣不舒，苔白薄。","herb":"小柴胡湯（依症）","classic":"少陽不和，寒熱往來，苔可見白。"},
  "膽_gold":{"message":"膽黃：膽經濕熱，苔黃膩。","herb":"龍膽瀉肝湯","classic":"肝膽濕熱，口苦目眩，苔黃膩。"},
  "膽_black":{"message":"膽黑：多為寒濕重或瘀阻，色黑。","herb":"溫陽化濕、活血化瘀法（依症）","classic":"寒濕凝滯，色黑暗而舌苔厚。"},
  "膽_red":{"message":"膽紅：少陽鬱熱或陰虛內熱，舌紅少苔。","herb":"小柴胡湯合滋陰藥（依症）","classic":"少陽熱鬱，口苦胸脅苦滿。"},
  "脾胃_white":{"message":"脾胃白：多見寒濕或陽虛，苔白厚或白膩。","herb":"理中湯、平胃散（依症）","classic":"脾陽不振，運化失常，白苔或膩苔。"},
  "脾胃_gold":{"message":"脾胃黃：濕熱困脾，苔黃膩。","herb":"黃連溫膽湯、平胃散加味（依症）","classic":"濕熱內蘊，納呆腹脹，苔黃膩。"},
  "脾胃_black":{"message":"脾胃黑：多為寒極或久病入絡，舌苔黯黑。","herb":"溫陽散寒、活血之品（依症）","classic":"寒盛則黑，或瘀阻日久。"},
  "脾胃_red":{"message":"脾胃紅：胃陰不足或虛熱，舌紅少苔。","herb":"養陰清熱品（依症）","classic":"陰傷少津，苔少或無苔。"},
  "心肺_white":{"message":"心肺白：多見外感初起或寒象，苔白薄。","herb":"荊防敗毒散等（依症）","classic":"風寒束表或陽氣不足，苔白薄。"},
  "心肺_gold":{"message":"心肺黃：熱象或痰熱，苔黃。","herb":"清熱化痰或瀉心之劑（依症）","classic":"熱盛則黃，痰熱壅阻咳嗽。"},
  "心肺_black":{"message":"心肺黑：寒凝血瘀或久病，色黑暗。","herb":"溫陽化瘀法（依症）","classic":"寒凝血瘀，脈澀舌黯。"},
  "心肺_red":{"message":"心肺紅：多屬熱盛或陰虛火旺，舌紅少苔。","herb":"清心瀉火或滋陰降火（依症）","classic":"心火亢或陰虛火旺，口舌生瘡。"}
};

const regions = ["腎", "肝", "膽", "脾胃", "心肺"];
const colors = [
  { key: "white", label: "白" },
  { key: "gold", label: "黃" },
  { key: "black", label: "黑" },
  { key: "red", label: "紅" }
];

let selectedRegion = null;
let selectedColor = null;

function renderButtons() {
  const rbox = document.getElementById('region-btns');
  rbox.innerHTML = '';
  regions.forEach(r => {
    const b = document.createElement('button');
    b.className = 'btn' + (selectedRegion === r ? ' active' : '');
    b.textContent = r;
    b.onclick = () => { selectedRegion = r; renderButtons(); renderResult(); };
    rbox.appendChild(b);
  });

  const cbox = document.getElementById('color-btns');
  cbox.innerHTML = '';
  colors.forEach(c => {
    const b = document.createElement('button');
    b.className = 'btn' + (selectedColor === c.key ? ' active' : '');
    b.textContent = c.label;
    b.onclick = () => { selectedColor = c.key; renderButtons(); renderResult(); };
    cbox.appendChild(b);
  });
}

function keyFor(region, colorKey) {
  // 使用格式：腎_white / 肝_gold / ...
  return region + '_' + colorKey;
}

function renderResult() {
  const box = document.getElementById('result');
  if (!selectedRegion || !selectedColor) {
    box.innerHTML = '<span class="muted">請先選擇部位與顏色</span>';
    return;
  }
  const key = keyFor(selectedRegion, selectedColor);
  const item = data[key];
  if (!item) {
    box.innerHTML = '<span class="muted">找不到此組合的教學資料（' + key + '）</span>';
    return;
  }
  const msg = item.message || '';
  const herb = item.herb || '';
  const classic = item.classic || '';
  const colorLabel = (colors.find(c=>c.key===selectedColor)||{}).label || selectedColor;

  box.innerHTML = ''
    + '<div><strong>部位：</strong>' + selectedRegion + '　<strong>顏色：</strong>' + colorLabel + '</div>'
    + (msg ? '<div style="margin-top:8px;"><strong>判讀：</strong>' + msg + '</div>' : '')
    + (herb ? '<div style="margin-top:8px;"><strong>常見方劑：</strong>' + herb + '</div>' : '')
    + (classic ? '<div style="margin-top:8px;"><strong>典籍：</strong>' + classic + '</div>' : '');
}

document.getElementById('reset').onclick = () => { selectedRegion = null; selectedColor = null; renderButtons(); renderResult(); };

renderButtons();
renderResult();
