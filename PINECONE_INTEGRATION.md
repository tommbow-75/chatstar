# Pinecone RAG 整合文件

本文記錄 ChatStar 導入 Pinecone 向量資料庫（RAG 長期記憶架構）的完整實作說明。

---

## 架構概覽

採用「PostgreSQL 為主、Pinecone 為輔」的雙資料庫策略：

- **PostgreSQL**：所有資料的唯一事實來源（UI 讀寫均走這裡）
- **Pinecone**：語意記憶庫，專門提供給 Gemini AI 做相關性檢索
- **同步方式**：資料寫入 PostgreSQL 成功後，以背景 daemon thread 非同步寫入 Pinecone，不阻塞 UI

```
使用者操作
    ↓
PostgreSQL CRUD（crud.py）← 立即返回給 UI
    ↓ 背景 daemon thread
vector_db/sync_service.py → Pinecone（自動 Embedding）

截圖觸發 AI 分析
    ↓
vector_db/search_service.py  ← 查詢 Pinecone 長期記憶
    ↓
Gemini Prompt = [長期記憶] + [短期記憶 8則] + 截圖
    ↓
3 種回覆建議
```

---

## Pinecone Index 設定

| 項目 | 值 |
|---|---|
| Index 名稱 | `chatstar` |
| Embedding Model | `multilingual-e5-large` |
| 向量維度 | **1024**（注意：不是 1536） |
| Metric | `cosine` |
| 架構 | Serverless（AWS us-east-1） |

> **重要**：Index 已設定 `embed.fieldMap.text = "text"`，Pinecone Inference API 會自動將傳入的 `text` 欄位向量化，程式碼中**不需要自行呼叫 Embedding 模型**。

### 手動環境建置步驟（供開發者重現環境）

若您是新加入此專案的協作者，請依照以下步驟建立專屬的 Pinecone 環境：

1. **註冊/登入 Pinecone**：前往 [Pinecone 官網](https://www.pinecone.io/) 註冊並登入（免費方案即可）。
2. **建立 Index**：進入左側選單的 **Indexes**，點擊右上角 **Create Index** 按鈕。
3. **填寫 Index 基本資訊**：
   - **Index Name**: 輸入 `chatstar`（若改名，後續需在 `.env` 同步修改）
   - **Dimensions**: 填寫 **1024**（非常重要，不能填錯）
   - **Metric**: 選擇 **cosine**
4. **設定 Inference Model（整合 Embedding）**：
   - 勾選或進入設定 Inference 功能的選項（視當時介面而定，通常在 Setup 階段）。
   - Model 選擇：**multilingual-e5-large**。
   - Field Map 設定：配置 `text` 作為被向量化的目標欄位（讓系統知道要針對哪一個 JSON 欄位進行 Embedding）。
5. **選擇基礎架構**：
   - 選擇 **Serverless** 架構。
   - Region 可選擇 AWS `us-east-1`（或其他離您最近的區域）。
6. **取得 API Key 並設定專案**：
   - 點擊建立後，前往左側選單的 **API Keys**。
   - 複製您的 Default Key。
   - 在專案根目錄下的 `.env` 檔案中加入：
     ```env
     PINECONE_API_KEY=您剛剛複製的金鑰
     PINECONE_INDEX=chatstar
     ```

---

## Namespace 命名規則

用 Namespace 物理隔離不同使用者的資料（比 Metadata Filter 更快更安全）：

| Namespace | 對應資料 |
|---|---|
| `{user_id}_user_prefs` | `User.preferences` 拆解後的向量 |
| `{user_id}_user_topics` | `UserTopicLog` 的每條話題 |
| `{user_id}_{dmbuddy}_buddy_prefs` | `BuddyInfo.interests` 拆解後的向量 |
| `{user_id}_{dmbuddy}_buddy_topics` | `BuddyTopicLog` 的每條話題 |

> `{dmbuddy}` 中的空格會自動替換為 `_`（在 `sync_service.py` 的 ns 輔助函式中處理）。

---

## 新增 / 修改的檔案

### 新建

#### `vector_db/sync_service.py`

Pinecone 寫入/刪除核心模組。主要函式：

| 函式 | 說明 |
|---|---|
| `upsert_vectors(namespace, records)` | 批次寫入向量（Pinecone 自動 Embedding） |
| `delete_by_ids(namespace, ids)` | 依 ID 刪除向量 |
| `delete_namespace(namespace)` | 清空整個 Namespace（全刪全建時使用） |
| `ns_user_prefs(user_id)` | 產生 Namespace 名稱（避免拼寫錯誤） |
| `build_user_pref_records(...)` | 將 JSONB preferences 轉為 Pinecone Records 列表 |
| `build_buddy_topic_record(...)` | 將單條 BuddyTopicLog 轉為 Pinecone Record |

Record 格式（傳入 `upsert_vectors` 的每筆資料）：
```python
{
    "_id":      "buddy_5_pref_0",         # 唯一 ID（不能含空格）
    "text":     "小美 的興趣是 看懸疑電影",  # ← 會被自動向量化
    "user_id":  "u_001",                  # 以下均為 Metadata
    "partner":  "小美",
    "type":     "buddy_prefs",
    "source_id": 5,
}
```

#### `vector_db/search_service.py`

Pinecone 語意搜尋模組，供 `core/scanner.py` 呼叫：

```python
from vector_db.search_service import search_long_term_context

context = search_long_term_context(
    user_id="u_001",
    partner_name="小美",
    query="最近有沒有看什麼好電影",
    top_k=5,
)
# 回傳格式化的字串，可直接放入 Gemini Prompt
```

搜尋範圍：`buddy_prefs` + `buddy_topics` + `user_prefs` 三個 Namespace。  
相似度門檻：`cosine > 0.5`（低於此分的結果會被濾掉）。

#### `scripts/reconcile_sync.py`

歷史資料對帳腳本（首次部署或災難復原用）：

```bash
# 乾跑模式（只顯示計畫，不實際寫入）
uv run python scripts/reconcile_sync.py --dry-run

# 全量同步
uv run python scripts/reconcile_sync.py

# 只同步特定使用者
uv run python scripts/reconcile_sync.py --user-id u_001
```

### 修改

#### `backend/models.py`

`UserTopicLog` 和 `BuddyTopicLog` 各加了獨立自增 `id` 欄位：
```python
id = Column(Integer, autoincrement=True, unique=True, index=True)
```
此欄位作為 Pinecone Vector ID 的唯一基準（格式：`user_topic_{id}` / `buddy_topic_{id}`）。

> ⚠️ 此欄位需要手動執行資料庫遷移（見下方）。

#### `backend/crud.py`

在以下操作後，以 `threading.Thread(daemon=True)` 觸發 Pinecone 背景同步：

| CRUD 操作 | Pinecone 動作 |
|---|---|
| `create_user` / `update_user` (preferences) | 全刪全建 `user_prefs` Namespace |
| `create_buddy` / `update_buddy` (interests) | 全刪全建 `buddy_prefs` Namespace |
| `create_user_topic` | Upsert 單筆到 `user_topics` |
| `delete_user_topic` | 刪除對應 Vector |
| `create_buddy_topic` | Upsert 單筆到 `buddy_topics` |
| `delete_buddy_topic` | 刪除對應 Vector |

#### `core/scanner.py`

`ScreenScanner` 新增 `user_id` 和 `partner_name` 參數。  
每次截圖觸發建議生成前，會先呼叫 `search_long_term_context()` 查詢 Pinecone。  
若 Pinecone 查詢失敗，會靜默處理並降級回「無長期記憶」模式，不影響主流程。

#### `core/ai_provider.py`

`SUGGEST_SYSTEM_PROMPT` 新增 `{long_term_section}` 佔位符。  
`analyze_chat_image` 新增 `long_term_context: str = ""` 參數。  
當 `long_term_context` 有值時，Prompt 中會出現：  
```
【長期記憶】關於聊天對象的已知資訊（供參考）：
・小美 的興趣是 看懸疑電影
・小美 最近聊過的話題是 週末要去爬山
```

#### `main.py`

- 新增全域變數 `current_user_id: str = ""`，登入後由 `main()` 寫入。
- `on_region_selected` 中從 `main_win.get_selected_buddy()` 取得當前聊天對象名稱，傳入 `ScreenScanner`。

---

## 部署注意事項

### 1. 資料庫遷移（首次部署必做）

在 Neon PostgreSQL 控制台執行以下 SQL：

```sql
ALTER TABLE user_topics_log ADD COLUMN IF NOT EXISTS id SERIAL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_topics_log_id ON user_topics_log(id);

ALTER TABLE buddy_topics_log ADD COLUMN IF NOT EXISTS id SERIAL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_buddy_topics_log_id ON buddy_topics_log(id);
```

### 2. 初始資料同步

SQL 跑完後，執行對帳腳本把現有的歷史資料匯入 Pinecone：
```bash
uv run python scripts/reconcile_sync.py --dry-run  # 先確認
uv run python scripts/reconcile_sync.py            # 再執行
```

### 3. 環境變數

確認 `.env` 中有以下設定：
```env
PINECONE_API_KEY=你的金鑰
PINECONE_INDEX=chatstar
```

---

## 已知注意事項

- **模組命名**：本地目錄已命名為 `vector_db/`（原始計畫為 `pinecone/`），因為 `pinecone` 與官方 SDK 套件名稱衝突，會導致 `ModuleNotFoundError`。
- **`partner_name` 為空時**：若 `MainWindow.get_selected_buddy()` 方法不存在或回傳空字串，Scanner 會自動跳過 Pinecone 查詢，不影響現有功能。
- **Pinecone 查詢失敗**：網路異常等情況下，`search_service.py` 會 catch 例外並回傳空字串，Gemini 仍可正常生成回覆（無長期記憶模式）。
- **EMBED_DIM**：`multilingual-e5-large` 的向量維度是 **1024**，`.env.example` 中已修正（舊版本誤寫為 1536）。

---

*整合日期：2026-03-04*
