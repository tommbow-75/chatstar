# ChatStar 專案指令上下文 (GEMINI.md)

本文件為 Gemini CLI 提供關於 `ChatStar` 專案的架構概覽、技術細節及開發規範，作為後續協作的基礎。

---

## 🚀 專案概述

**ChatStar** 是一款基於 **PyQt6** 開發的 PC 桌面應用程式，旨在透過 **Gemini Vision AI** 分析通訊軟體（如 LINE、Telegram）的截圖內容，自動提供多種風格的繁體中文回覆建議。

### 核心流程
1. **框選區域**：用戶在螢幕上框選聊天視窗區域。
2. **監聽掃描**：`ScreenScanner` 定時監控該區域，偵測畫面變動（差異率 > 0.5%）。
3. **AI 分析**：
   - **首次**：全量提取訊息（由下往上）以建立背景脈絡。
   - **後續**：增量提取最新訊息，更新 `MemoryManager`（工作記憶）。
4. **生成建議**：根據當前對話背景與雙方的興趣資料，生成多種風格的回覆建議。
5. **UI 回饋**：顯示回覆卡片，點擊即可複製到剪貼簿。

---

## 🛠 技術棧

- **語言**: Python 3.12+
- **套件管理**: `uv` (優先使用 `uv sync`, `uv run`, `uv add`)
- **前端 GUI**: PyQt6
- **後端 API**: FastAPI (異步運行於 `BackendThread`)
- **資料庫**: PostgreSQL (透過 SQLAlchemy ORM), 支援 JSONB
- **AI 模型**: Google Gemini Vision (`gemini-flash-latest`)
- **圖像處理**: Pillow, mss (截圖), pytesseract (OCR 輔助)
- **環境管理**: `python-dotenv`

---

## 📂 目錄結構說明

- `main.py`: 應用程式進入點，初始化並協調 UI、後端執行緒與 AI 掃描器。
- `backend/`:
    - `main.py`: FastAPI 路由掛載與伺服器設定。
    - `models.py`: SQLAlchemy 資料模型（User, BuddyInfo, ChatLog, Topic）。
    - `database.py`: 資料庫連接配置。
    - `schemas.py`: Pydantic 資料驗證 Schema。
    - `crud.py`: 資料庫 CRUD 操作函式（User、BuddyInfo 均支援完整增刪改查）。
    - `routers/`: 各功能模組的 API Endpoint（users, buddies, chats, topics）。
- `core/`:
    - `ai_provider.py`: AI 抽象層與 `GeminiProvider` 實作，包含圖像壓縮與 Prompts。
    - `scanner.py`: 負責截圖、差異偵測與定時調度。
    - `memory_manager.py`: 管理對話緩衝區（Window Size 預設為 8）。
    - `backend_thread.py`: 在背景運行 uvicorn 伺服器。
- `ui/`:
    - `main_window.py`: 主控制面板（含「📊 資料管理」按鈕）。
    - `selection_window.py`: 全螢幕半透明遮罩選取視窗。
    - `region_overlay.py`: 穿透式的螢幕藍框標示。
    - `reply_panel.py`: 回覆建議展示元件。
    - `data_manager_window.py`: **資料管理視窗**（使用者與聊天對象的增刪改查）。

---

## 💾 資料模型設計

資料庫只儲存**使用者**與**聊天對象**的興趣、個人特質等非敏感資訊，供 AI 系統參考以生成更合適的回覆。

### User（使用者）
| 欄位 | 類型 | 說明 |
|------|------|------|
| `user_id` | String(50) PK | 使用者唯一識別碼 |
| `username` | String(100) | 顯示名稱 |
| `interests` | JSONB | 使用者興趣與個人特質（供 AI 參考） |

### BuddyInfo（聊天對象）
| 欄位 | 類型 | 說明 |
|------|------|------|
| `id` | Integer PK | 自動遞增主鍵 |
| `user_id` | String FK | 所屬使用者（CASCADE 刪除） |
| `dmbuddy` | String(100) | 聊天對象名稱 |
| `interests` | JSONB | 對象的興趣與特質（供 AI 參考） |

### interests 欄位 JSON 格式範例
```json
{
  "喜好": ["旅遊", "咖啡"],
  "個性": "外向、幽默",
  "話題": ["電影", "科技"],
  "備註": "不喜歡政治話題"
}
```

---

## 💻 開發指令

### 環境初始化
```bash
# 安裝依賴
uv sync

# 設定環境變數
cp .env.example .env
# 編輯 .env 填入 GEMINI_API_KEY 與 DATABASE_URL
```

### 啟動應用
```bash
# ✅ 正確方式：從專案根目錄執行
uv run python main.py

# ❌ 錯誤方式（backend 使用相對套件路徑，不可直接執行）
# python backend/main.py
```

### 資料庫遷移
- 專案使用 `Base.metadata.create_all` 自動建立新資料表。
- **現有資料表不會自動更新欄位**，若 model 有異動需手動執行 ALTER TABLE 或重建資料表：
```sql
-- 重建範例（⚠️ 會清除現有資料）
DROP TABLE IF EXISTS buddy_info, chat_logs, user_topics_log, buddy_topics_log, users CASCADE;
-- 重啟應用程式後 create_all 會自動重建
```

---

## ⚠️ 關鍵開發規範

1. **圖像處理**:
   - `GeminiProvider` 內建縮放機制（`MAX_EDGE = 1024`），發送前會轉為 JPEG 並壓縮。
   - 截圖座標處理需考慮 **High DPI** 縮放比例（由 `SelectionWindow` 處理）。

2. **AI 互動**:
   - 所有 AI 回傳皆要求為 **JSON 格式**。
   - 提取訊息時採用 **「由下往上」** 策略，確保最新訊息的優先權。
   - Prompt 嚴格區分「全量提取」、「增量提取」與「回覆生成」。

3. **後端通訊**:
   - 後端預設運行於 `http://127.0.0.1:8000`。
   - **前端（data_manager_window.py）** 透過 `requests` 直接呼叫本地 API 進行資料管理。
   - FastAPI Swagger 文件：`http://127.0.0.1:8000/docs`。

4. **程式碼風格**:
   - 註解與 UI 顯示文字請使用 **繁體中文**。
   - 保持主執行緒（UI）與背景執行緒（Scanner, Backend）的隔離。

5. **資料管理視窗** (`DataManagerWindow`):
   - 透過 `open_data_manager` 信號從主視窗開啟，不阻塞主視窗。
   - 使用 `QTabWidget` 分頁，切換至「聊天對象」分頁時自動重新載入使用者列表。

---

## 📝 待辦事項 (Roadmap)
- [ ] 核心摘要功能（長對話濃縮）。
- [ ] 將 `interests` 資料整合進 AI Prompt，提升回覆品質。
- [ ] 懸浮球（Floating Ball）模式實作。
- [ ] 自定義 System Prompt 支援。
- [ ] 考慮改用 SQLite 減少外部依賴（目前需要 PostgreSQL）。
