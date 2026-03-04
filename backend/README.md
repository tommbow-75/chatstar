# ChatStar Backend API 文件

這份文件總結了 `backend` 目錄內的程式架構、資料庫設計以及 API 功能。這個後端服務主要使用 **FastAPI** 建立，並搭配 **PostgreSQL** 與 **SQLAlchemy** 作為資料庫連線與 ORM 操作。

## 📁 檔案結構

- `main.py`：應用程式的進入點。主要負責建立 FastAPI 實例、連接資料庫、自動建立尚未存在的資料表，並註冊各個路由 (Routers)。
- `database.py`：處理 PostgreSQL 資料庫連線配置，包含讀取環境變數 `DATABASE_URL`，以及提供 `get_db()` 生成器來管理資料庫 Session 生命週期。
- `models.py`：定義 SQLAlchemy 的 ORM 資料庫模型，對應建立在 PostgreSQL 中的關聯式資料表。
- `schemas.py`：定義 Pydantic 模型 (Schemas)，主要用於 API 的請求資料驗證 (Request) 以及回應格式定義 (Response)。
- `crud.py`：封裝所有針對資料庫的 CRUD（新增、讀取、更新、刪除）操作邏輯。
- `routers/`：這是一個包含各領域子路由的資料夾（利用 `APIRouter` 進行切割），各功能模組化分別放置。

## 🗄️ 資料庫模型 (Models) 及關聯設計

從 `models.py` 來看，共有以下 5 個主要的資料表：

1. **User (使用者, `users`)**
   - 包含主鍵 `user_id`、`username`、`preferences` (JSONB)、`user_api`。
   - 與其他表有一對多的關聯 (`buddies`, `chat_logs`, `user_topics`, `buddy_topics`)，採 `cascade="all, delete-orphan"` 以利連鎖刪除。
2. **BuddyInfo (AI 聊天夥伴設定, `buddy_info`)**
   - 儲存使用者各別設定的對話夥伴 (`dmbuddy`) 以及其參數偏好 (`buddy_prefs` - JSONB)。
3. **ChatLog (對話紀錄, `chat_logs`)**
   - 存放使用者與特定夥伴 (`dmbuddy`) 的對話內容，包含收到的訊息 (`received_mess`)、系統生成的可能回覆 (`generated_mess` - JSONB)、以及使用者最終選擇的訊息 (`selected_mess`)。
4. **UserTopicLog (使用者話題紀錄, `user_topics_log`)**
   - 紀錄使用者觸發過的話題，採用複合主鍵 (`user_id`, `topic`) 避免重複。
5. **BuddyTopicLog (夥伴話題紀錄, `buddy_topics_log`)**
   - 紀錄使用者與特定夥伴觸發的話題，採三重複合主鍵 (`user_id`, `dmbuddy`, `topic`)。

> 備註：`routers/` 目錄內另外有 `partners.py` 與 `interests.py`，但在目前的 `models.py`、`schemas.py` 及 `main.py` 中皆未使用到它們的相關定義，推測屬於早期的廢棄程式碼或是尚未實作完畢的功能。

## 🔌 API 路由 (Routers)

`/backend/routers/` 實作了以下幾種 API Endpoints：

### 1. 使用者 (Users - `routers/users.py`)
- `POST /users/`: 建立使用者，若 `user_id` 已存在則回報 400 錯誤。
- `GET /users/`: 取得所有使用者的列表 (支援 pagination)。
- `GET /users/{user_id}`: 根據 `user_id` 取得單一使用者的資料。

### 2. 聊天夥伴 (Buddies - `routers/buddies.py`)
- `POST /buddies/`: 新增使用者的聊天夥伴設定。
- `GET /buddies/users/{user_id}`: 取得特定使用者所擁有的所有夥伴清單。
- `GET /buddies/{buddy_id}`: 利用夥伴記錄的 PK (`id`) 取得詳細資訊。

### 3. 對話紀錄 (Chats - `routers/chats.py`)
- `POST /chats/`: 新增一筆聊天對話紀錄（需有對應的 user 存在）。
- `GET /chats/users/{user_id}/buddies/{dmbuddy}`: 讀取特定使用者與特定夥伴之間的所有對話歷史（依時間倒序排列顯示最新的在前）。

### 4. 話題紀錄 (Topics - `routers/topics.py`)
- **使用者話題：**
  - `POST /topics/users`: 紀錄使用者級別的話題。
  - `GET /topics/users/{user_id}`: 讀取某個使用者的所有話題紀錄。
- **夥伴話題：**
  - `POST /topics/buddies`: 紀錄針對特定夥伴的話題。
  - `GET /topics/users/{user_id}/buddies/{dmbuddy}`: 取得特定使用者對特定夥伴的所有話題。

## ⚙️ 運作流程統整

1. **啟動流程**：啟動 `main.py` 時，程式會匯入 `database.engine` 並呼叫 `metadata.create_all()` 確保資料庫與所有的 tables 都有建立好。
2. **請求處理**：當外部打 API 來時，FastAPI 透過對應的 `router` (`users`, `chats` 等) 接手。
3. **資料驗證**：進入 Router 函式時，Request body 會直接由 `schemas.py` 的 Pydantic 模型驗證格式是否正確。
4. **資料庫存取**：接著從 `database.get_db()` 取得資料庫 session，並呼叫 `crud.py` 對應的資料操作函數執行查詢或新增資料，最終透過 Pydantic 回傳 JSON。
