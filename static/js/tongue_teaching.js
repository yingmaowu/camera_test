;(() => {
  // === 互動資料 ===
  const REGIONS = [
    { key: "tip",  label: "舌尖（心）" },
    { key: "side", label: "舌邊（肝膽）" },
    { key: "center", label: "舌中（脾胃）" },
    { key: "root", label: "舌根（腎）" },
  ];

  const COLORS = [
    { key: "white", label: "白苔" },
    { key: "yellow", label: "黃苔" },
    { key: "red", label: "紅舌" },
    { key: "pale", label: "淡舌" },
    { key: "thick", label: "厚苔" },
    { key: "thin", label: "薄苔" },
    { key: "black", label: "灰黑苔" },
    { key: "none", label: "紅紫舌無苔" },
  ];

  // === 說明對照（找不到部位專屬→退回顏色一般說明） ===
  const EXPLAINS = {
    // 顏色一般說明（fallback）
    _color: {
      white: [
        "多見表證或寒證；薄白而潤常為正常或外感初起。",
        "白厚而滑常見痰濕內盛。"
      ],
      yellow: [
        "主裡熱或濕熱，色越深熱勢越重。",
        "乾黃偏傷津；黏膩黃偏濕熱。"
      ],
      red: [
        "舌質偏紅，多見熱證或陰虛火旺。",
        "紅少苔偏陰虛；紅黃苔偏實熱。"
      ],
      pale: [
        "舌質淡白，多見氣血不足或陽虛。",
        "胖大齒痕多偏脾陽不足、痰濕。"
      ],
      thick: [
        "苔厚不易見舌質，多與痰濕、食積或實證相關。",
        "厚膩偏濕阻；厚乾偏熱盛傷津。"
      ],
      thin: [
        "苔薄可見舌質，常屬正常或外感初起。",
        "薄少而紅可能陰虛有熱。"
      ],
      black: [
        "灰黑苔多見病勢較重；黑乾偏熱盛傷津；黑濕偏寒濕或陽虛。"
      ],
      none: [
        "紅紫舌無苔多見陰津不足或陰虛有熱；偏紫可見瘀血徵象。"
      ]
    },

    // 舌尖（心）
    tip: {
      red: [
        "心火偏旺或心陰不足 → 舌尖偏紅。",
        "可伴煩躁、失眠、口瘡等。"
      ],
      white: [
        "外感初起或偏寒；薄白且潤通常無大礙。"
      ],
      yellow: [
        "心火上炎或裡熱上擾，注意失眠、心悸等伴隨症。"
      ]
    },
    // 舌邊（肝膽）
    side: {
      red: [
        "肝膽鬱火偏旺 → 舌邊偏紅。",
        "易伴口苦、易怒、頭痛。"
      ],
      yellow: [
        "肝膽濕熱偏重，黃苔支持此判斷。"
      ],
      pale: [
        "肝血不足或脾不生血，舌邊偏淡。"
      ]
    },
    // 舌中（脾胃）
    center: {
      yellow: [
        "脾胃濕熱或裡熱偏重。",
        "可伴口黏膩、口渴、便秘/黏滯感。"
      ],
      thick: [
        "食積或痰濕阻滯，苔厚常見。"
      ],
      white: [
        "薄白多正常；厚白滑 → 脾運失健、痰濕。"
      ],
      thin: [
        "苔薄可見舌質，若少苔且紅 → 陰虛內熱傾向。"
      ]
    },
    // 舌根（腎）
    root: {
      black: [
        "灰黑苔見於病勢較重；黑濕偏陽虛寒濕，黑乾偏熱盛傷津。"
      ],
      none: [
        "根部無苔且舌質紅紫 → 腎陰不足或陰虛火旺可能性增加。"
      ],
      pale: [
        "腎陽不足傾向可見根部偏淡，伴畏寒、四肢不溫。"
      ]
    }
  };

  // === 小工具 ===
  function createBtn(label, onClick) {
    const a = document.createElement("button");
    a.type = "button";
    a.className = "btn btn-outline";
    a.textContent = label;
    a.addEventListener("click", onClick);
    return a;
  }

  function renderList(items) {
    if (!items || !items.length) return "<p class='muted'>暫無說明</p>";
    return `<ul style="margin:6px 0 0 1rem">${ items.map(x => `<li style="margin:6px 0">${x}</li>`).join("") }</ul>`;
  }

  function unique(arr) {
    return Array.from(new Set(arr));
  }

  // === 初始化 ===
  const TongueTeaching = {
    init({ regionMount, colorMount, resultMount, resultContainer, resetBtn, onBtnStateChange }){
      let selectedRegion = null;
      let selectedColor = null;

      // 建立部位按鈕
      const regionBtns = REGIONS.map(r => {
        const btn = createBtn(r.label, () => {
          selectedRegion = (selectedRegion === r.key) ? null : r.key;
          regionBtns.forEach(b => onBtnStateChange?.(b, b === btn));
          showResult();
        });
        regionMount.appendChild(btn);
        return btn;
      });

      // 建立顏色按鈕
      const colorBtns = COLORS.map(c => {
        const btn = createBtn(c.label, () => {
          selectedColor = (selectedColor === c.key) ? null : c.key;
          colorBtns.forEach(b => onBtnStateChange?.(b, b === btn));
          showResult();
        });
        colorMount.appendChild(btn);
        return btn;
      });

      // 重設
      resetBtn?.addEventListener("click", () => {
        selectedRegion = null;
        selectedColor = null;
        regionBtns.forEach(b => onBtnStateChange?.(b, false));
        colorBtns.forEach(b => onBtnStateChange?.(b, false));
        resultMount.innerHTML = `<p class="muted">請先選擇部位與顏色。</p>`;
        resultContainer?.scrollIntoView({ behavior:'smooth', block:'nearest' });
      });

      function showResult(){
        if(!selectedRegion || !selectedColor){
          resultMount.innerHTML = `<p class="muted">已選：${ selectedRegion ? REGIONS.find(r=>r.key===selectedRegion).label : '—' } / ${ selectedColor ? COLORS.find(c=>c.key===selectedColor).label : '—' }。請繼續選擇。</p>`;
          return;
        }
        const regionExplain = (EXPLAINS[selectedRegion] && EXPLAINS[selectedRegion][selectedColor]) || [];
        const colorExplain  = (EXPLAINS._color[selectedColor] || []);
        const merged = unique([ ...regionExplain, ...colorExplain ]);
        resultMount.innerHTML = renderList(merged);
        resultContainer?.scrollIntoView({ behavior:'smooth', block:'nearest' });
      }

      // 初始提示
      resultMount.innerHTML = `<p class="muted">請先選擇部位與顏色。</p>`;
    }
  };

  window.TongueTeaching = TongueTeaching;
})();
