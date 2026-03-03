# ChatStar — AI 聊天回覆輔助工具

ChatStar 是一款 PC 端桌面應用程式，透過**螢幕截圖 + Gemini Vision AI** 分析通訊軟體（LINE、Telegram 等）的對話內容，自動給予三種風格的繁體中文回覆建議。

---

## 功能特色

| 功能 | 說明 |
|------|------|
| 📷 自訂監聽區域 | 全螢幕半透明遮罩，拖拉框選任意對話視窗區域 |
| 🔄 即時首掃 | 框選後立即分析當前對話，無需等待畫面變動 |
| 🧠 AI 圖像理解 | 直接將截圖傳給 Gemini Vision，由 AI 自行判斷對話脈絡 |
| 💬 三風格回覆建議 | 正式 / 輕鬆 / 簡短，點擊即複製到剪貼簿 |
| 🔵 區域視覺化 | 螢幕上以藍色邊框標示目前監聽範圍 |
| ♻️ 重新框選 | 掃描中可直接點「重新框選」，不需重啟程式 |
| 💰 Token 優化 | 圖片自動縮小至 768px + JPEG 壓縮，降低 API 費用 |

---

## 環境需求

- **Python 3.12+** 與 **`uv`** 套件管理工具（[安裝 uv](https://docs.astral.sh/uv/getting-started/installation/)）
- **Google Gemini API Key**（[取得免費額度](https://aistudio.google.com/app/apikey)）

> ⚠️ 不再需要安裝 Tesseract OCR，已全面改用 Gemini Vision。

---

## 安裝步驟

```bash
# 1. 克隆專案
git clone <repo-url>
cd chatstar

# 2. 建立虛擬環境並安裝依賴
uv sync

# 3. 填入 Gemini API Key
cp .env.example .env
# 編輯 .env，填入 GEMINI_API_KEY=AIza...
```

---

## 啟動方式

```bash
uv run main.py
```

---

## 使用流程

1. 程式啟動後顯示**主控制面板**
2. 在「Gemini Key」欄位輸入 API Key（若 `.env` 已設定則自動填入）
3. 開啟 LINE 或其他通訊軟體，切換至目標對話視窗
4. 點擊「**📷 選取監聽區域**」
5. 螢幕變暗後，拖拉框選對話區域，放開後開始監聽
6. 螢幕上出現藍色邊框標示監聽範圍，AI 立即分析當前對話
7. 面板顯示三種回覆建議：點「📋 一鍵複製」→ 貼入通訊軟體
8. 收到新訊息時（畫面有變動），AI 自動重新分析

---

## 專案結構

```
chatstar/
├── main.py                   # 應用程式入口 & 流程控制
├── .env                      # API Key 設定（不提交 git）
├── core/
│   ├── ai_provider.py        # AI 抽象層 + GeminiProvider 實作
│   ├── scanner.py            # 背景截圖 & 圖像差異偵測執行緒
│   └── ocr_engine.py         # (舊) Tesseract OCR，已棄用
└── ui/
    ├── main_window.py        # 主控制面板視窗
    ├── selection_window.py   # 全螢幕透明選取視窗
    ├── region_overlay.py     # 螢幕區域藍框標示（穿透視窗）
    └── reply_panel.py        # 三張回覆建議卡片 + 複製按鈕
```

---

## 系統架構

```
框選區域
   │
   ▼
ScreenScanner (QThread, 每 2 秒)
   │
   ├── 首次截圖 → 立即送 AI
   └── 後續截圖 → ImageChops 比對 → 變動率 > 0.5% → 送 AI
                                                        │
                                               GeminiProvider
                                               (圖片壓縮 JPEG 768px)
                                                        │
                                               Gemini Vision API
                                                        │
                                          ┌─────────────┼─────────────┐
                                       正式回覆      輕鬆回覆      簡短回覆
                                          └─────────────┴─────────────┘
                                                  ReplyPanel（UI）
                                                  一鍵複製到剪貼簿
```

---

## 設定說明（`.env`）

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

---

## Token 消耗估算

| 設定 | Token/次 | 費用（Flash Lite）|
|------|----------|-------------------|
| 768px JPEG（預設）| ~550 tokens | ~$0.00003 / 次 |
| 原始大圖 PNG | ~1500+ tokens | ~$0.00009 / 次 |

可在 `core/ai_provider.py` 調整：
- `MAX_EDGE = 768` — 圖片長邊上限（px）
- `JPEG_QUALITY = 85` — JPEG 品質
- `core/scanner.py` 的 `interval=2.0` — 截圖間隔（秒）

---

## 擴充 AI 服務

若要替換 Gemini，只需實作 `core/ai_provider.py` 中的 `BaseAIProvider`：

```python
class MyOpenAIProvider(BaseAIProvider):
    def analyze_chat_image(self, image: Image.Image) -> List[str]:
        # 呼叫 OpenAI Vision API...
        return ["正式回覆", "輕鬆回覆", "簡短回覆"]
```

---

## 路線圖（Roadmap）

- [ ] 懸浮球模式（最小化為螢幕邊緣小球）
- [ ] 對話紀錄儲存
- [ ] 支援自訂 System Prompt / 人設
- [ ] 多語言回覆（英文、日文等）
- [ ] 切換不同 AI 模型的 UI 設定