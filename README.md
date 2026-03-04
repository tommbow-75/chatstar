# ChatStar — AI 聊天回覆輔助工具

ChatStar 是一款 PC 端桌面應用程式，透過**螢幕截圖 + Gemini Vision AI** 分析通訊軟體（LINE、Telegram 等）的對話內容，自動給予三種風格的繁體中文回覆建議。

---

## 功能特色

| 功能 | 說明 |
|------|------|
| 📷 自訂監聽區域 | 全螢幕半透明遮罩，拖拉框選任意對話視窗區域 |
| 🔄 即時首掃 | 框選後立即分析當前對話，無需等待畫面變動 |
| 🧠 工作記憶系統 | 首次全量提取對話脈絡，後續增量追蹤最新訊息 |
| 💬 三風格回覆建議 | 正式 / 輕鬆 / 簡短，點擊即複製到剪貼簿 |
| 🔵 區域視覺化 | 螢幕上以藍色邊框精準標示目前監聽範圍 |
| ♻️ 重新框選 | 掃描中可直接重新框選，記憶自動清空重置 |
| �️ 高 DPI 支援 | 自動偵測 Windows 顯示縮放比例，截圖位置精準 |

---

## 環境需求

- **Python 3.12+** 與 **`uv`** 套件管理工具（[安裝 uv](https://docs.astral.sh/uv/getting-started/installation/)）
- **Google Gemini API Key**（[取得免費額度](https://aistudio.google.com/app/apikey)）

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
3. 開啟 LINE 或其他通訊軟體，切換至目標對話視窗，**捲動至最新訊息**
4. 點擊「**📷 選取監聽區域**」
5. 螢幕變暗後，拖拉框選對話區域，放開後開始監聽
6. AI 先提取完整對話背景（全量），再生成三種回覆建議
7. 收到新訊息時，AI 自動提取最新一則並更新建議

---

## 專案結構

```
chatstar/
├── main.py                   # 應用程式入口 & 流程控制
├── .env                      # API Key 設定（不提交 git）
├── core/
│   ├── ai_provider.py        # AI 抽象層 + GeminiProvider 實作
│   ├── memory_manager.py     # 工作記憶（對話 buffer 管理）
│   └── scanner.py            # 背景截圖 & 差異偵測執行緒
└── ui/
    ├── main_window.py        # 主控制面板視窗
    ├── selection_window.py   # 全螢幕透明選取視窗（含 DPI 換算）
    ├── region_overlay.py     # 螢幕區域藍框標示（穿透視窗）
    └── reply_panel.py        # 三張回覆建議卡片 + 複製按鈕
```

---

## 系統架構

```
框選區域
   │
   ▼
MemoryManager.reset()          ← 每次重新框選清空記憶
   │
   ▼
ScreenScanner (QThread, 每 2 秒)
   │
   ├── 首次截圖
   │     ├── extract_all_messages()  → MemoryManager.add_messages()
   │     └── analyze_chat_image(context)
   │
   └── 後續截圖（畫面變動率 > 0.5%）
         ├── extract_latest_message() → MemoryManager.add_latest()（去重）
         └── analyze_chat_image(context)
                        │
               GeminiProvider (gemini-flash-latest, JPEG 1024px)
                        │
                Gemini Vision API
                        │
           ┌────────────┼────────────┐
        正式回覆      輕鬆回覆      簡短回覆
           └────────────┴────────────┘
                  ReplyPanel（UI）
                  一鍵複製到剪貼簿
```

---

## 工作記憶系統

每次 AI 分析時，會將近期對話注入 Prompt 做為背景，讓回覆建議具有連貫的對話脈絡感。

| 時機 | 動作 |
|------|------|
| 首次框選 | Gemini 從截圖由下往上提取所有對話（最新優先），填充 buffer |
| 後續有新訊息 | 只提取最後一則，去重後 append 至 buffer |
| 重新框選 | `memory.reset()` 清空 buffer，下次重新全量提取 |
| 每次生成建議 | 將 buffer 最近 8 則注入 System Prompt |

> **為何由下往上提取？** Gemini 在生成長 JSON 時可能提前停止，由下往上確保最新（最關鍵）的訊息優先被記錄。

---

## 設定說明

```env
# .env
GEMINI_API_KEY=your_gemini_api_key_here
```

可在 `core/ai_provider.py` 調整：
- `MAX_EDGE = 1024` — 圖片長邊上限（px）
- `JPEG_QUALITY = 85` — JPEG 品質
- `model = "gemini-flash-latest"` — Gemini 模型

可在 `main.py` 調整：
- `MemoryManager(max_window=8)` — 對話記憶視窗大小（則數）
- `ScreenScanner(interval=2.0)` — 截圖間隔（秒）

---

## Token 消耗估算

首次框選會發送**兩次** Gemini 呼叫（全量提取 + 生成建議），後續每次僅一至兩次。

| 設定 | Token/次 | 費用（Flash）|
|------|----------|-------------|
| 1024px JPEG（預設）| ~800 tokens | ~$0.00006 / 次 |
| 768px JPEG | ~550 tokens | ~$0.00004 / 次 |

---

## 擴充 AI 服務

若要替換 Gemini，只需實作 `core/ai_provider.py` 中的 `BaseAIProvider`：

```python
class MyOpenAIProvider(BaseAIProvider):
    def analyze_chat_image(self, image, context="") -> list[str]:
        ...
    def extract_all_messages(self, image) -> list[str]:
        ...
    def extract_latest_message(self, image) -> str:
        ...
```