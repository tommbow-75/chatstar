# ChatStar: Pinecone (向量資料庫) 整合實施計畫

這份文件記錄了為 ChatStar 專案導入 Pinecone 向量資料庫，以實現 **RAG (Retrieval-Augmented Generation, 檢索增強生成)** 長期記憶架構的完整規劃與實作細節。

## 1. 核心架構目標：應用程式層級雙寫 (Application-Level Sync)

為了確保桌面端 UI 操作的即時性，同時補足 AI 在長期記憶上的不足，整體架構將採用**「以 PostgreSQL 為主要資料庫，背景非同步同步至 Pinecone」**的策略：

- **單一事實庫 (Source of Truth)**：現有的 PostgreSQL (透過 `crud.py` 管理) 負責儲存所有使用者的對話與興趣設定。UI 介面僅依賴 PostgreSQL，保證查詢與渲染效率。
- **長期記憶庫 (Vector Database)**：Pinecone 僅負責儲存對話/興趣的「語意向量陣列」，不直接被 UI 讀取，專門提供給 `google-genai` (Gemini) 進行相關性檢索。
- **非同步同步 (Asynchronous Sync)**：透過 FastAPI 的 `BackgroundTasks`，在資料寫入/更新 PostgreSQL 成功後，由背景任務呼叫 Embedding 模型並上傳至 Pinecone，絕不阻塞 UI 反應。

## 2. Pinecone 儲存與檢索策略設計

### 2.1 Metadata Filtering (後設資料過濾)
為防止 AI 搞混不同使用者的興趣，或將 A 的對話套用在 B 的回覆中，每一筆存入 Pinecone 的向量資料必須加上**嚴格的 Metadata (標籤)**。

當建立 Pinecone 向量時，資料結構規範如下：
```json
{
  "id": "buddy_5_hobby_1",       // 唯一識別碼（結合 PostgreSQL 的 PK 與資料切片）
  "values": [0.1, -0.2, ...],    // Embedding 向量陣列
  "metadata": {
    "user_id": "u_001",          // 識別：所屬的使用者
    "partner_id": "p_小美",      // 識別：聊天對象 (★ RAG 檢索過濾的核心)
    "type": "partner_interest",  // 分類：對象特質或歷史對話
    "text": "興趣是看懸疑電影"    // 內容：檢索成功後，要餵給 Gemini 閱讀的原始文字
  }
}
```

在檢索時 (Query)，**強制加上硬性條件 (Hard Filter)**，確保相似度計算只在特定對象的資料集內進行：
```python
filter={"partner_id": {"$eq": 當前聊天對象名稱或ID}}
```

### 2.2 JSONB 欄位處理策略 (Chunking)
為了讓向量相似度比對更精準，且**不修改現有 PostgreSQL `models.py` 的架構設計與 UI**，我們在背景同步階段實施「資料拆解」：

- **PostgreSQL 端**：照常將興趣清單 `["看懸疑電影", "打排球"]` 以 `JSONB` 格式存入 `User` 或 `BuddyInfo` 中。
- **Pinecone 腳本端**：`sync_service.py` 負責將 JSONB 陣列拆解。上述陣列將被拆解為 2 句獨立文字，並分別轉換為 2 筆 Pinecone 向量儲存。

### 2.3 更新與刪除策略 (Delete-and-Recreate)
對於從 JSONB 拆解出的多筆向量，為了降低邏輯複雜度與確保一致性，當使用者局部更新 JSONB 內容時，採用**「全刪全建 (Soft-delete & Re-insert)」**：

1. 收到更新請求。
2. 背景任務：向 Pinecone 發送 `Delete` 請求，透過 ID 前綴 (`buddy_5_*`) 或 Metadata Filter 清空該對象相關的所有舊向量。
3. 背景任務：將最新完整的 JSONB 內容重新拆解、產生 Embedding，並 `Upsert` 寫入 Pinecone。

這保證了兩邊資料庫狀態 100% 吻合，絕不留殘餘資料。

---

## 3. 分階段開發任務清單 (Task List)

### Phase 1: 環境與服務建置 (Infrastructure)
- [ ] 安裝必要依賴：使用 `uv add pinecone-client`。
- [ ] 設定環境變數：在 `.env` 中確認 `PINECONE_API_KEY`、`EMBED_MODEL` 配置（預設為 `multilingual-e5-large`，或是使用 `google-genai` 的 `text-embedding-004`）。
- [ ] 開發同步模組 `pinecone/sync_service.py`：
  - `get_embedding(text)`: 串接模型以獲得向量陣列。
  - `upsert_to_pinecone(...)`: 負責將文字向量化並寫入。
  - `delete_from_pinecone(...)`: 負責清除指定條件的向量資料。

### Phase 2: FastAPI 雙寫整合 (Backend Sync)
- [ ] 檢視 `backend/models.py`：強烈建議幫 `UserTopicLog` 與 `BuddyTopicLog` 這兩張使用複合主鍵的表，額外加上一組獨立會自動遞增的 `id`（做為 Pinecone Vector ID 的基準），並加上 `updated_at` 欄位。
- [ ] 整合 `crud.py` 或 Web Router：在新增 (Insert)、更新 (Update)、刪除 (Delete) 的 API 邏輯中，引入 `fastapi.BackgroundTasks`。
- [ ] 確保在 UI 送出成功回覆 (Return) 後，背景自動將資料導向 `sync_service.py` 處理。

### Phase 3: RAG 架構 AI 整合 (Prompting)
- [ ] 開發檢索模組 `pinecone/search_service.py`：撰寫函式接收「最新的對話輸入」與「當前聊天對象 ID」，尋找 Pinecone 中最相似的 Top-K 資料。
- [ ] 升級 `core/ai_provider.py`：修改建構給 Gemini 的 Prompt 模板，在原有的系統提示與「短期記憶 (近期 8 則)」外，額外安插一塊**「長期記憶補充區」**，將 Pinecone 查出的內容自動帶入。

### Phase 4: 修復與維護工具 (Ops)
- [ ] 撰寫 `scripts/reconcile_sync.py`：建立對帳腳本，批次比對 PostgreSQL 中所有的 ID 與狀態，協助將舊資料批量轉入 Pinecone，或修復背景任務可能因斷線而導致未同步的少數遺漏資料。

---
*Created per AI architecture consultation for ChatStar Project.*
