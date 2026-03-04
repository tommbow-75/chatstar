from fastapi import FastAPI
from backend.database import engine
from backend import models

from backend.routers import users, buddies, chats, topics

# 根據 models.py 中定義的所有 ORM Model，在資料庫中自動建立對應的資料表
# 若資料表已存在則不會重建（不會刪除舊資料）
models.Base.metadata.create_all(bind=engine)

# ── 自動 schema migration：補充舊版資料庫缺少的欄位 ──
# create_all 只建立不存在的「表格」，不會自動添加新的「欄位」。
# 以下在啟動時執行 DDL，為既有資料表補齊新欄位（已存在則跳過）。
try:
    with engine.connect() as conn:
        conn.execute(
            __import__("sqlalchemy").text(
                "ALTER TABLE buddy_info ADD COLUMN IF NOT EXISTS interests JSONB"
            )
        )
        conn.commit()
except Exception as _e:
    print(f"[Migration] buddy_info.interests 欄位檢查失敗（可忽略）: {_e}")

# 建立 FastAPI 應用程式實例，設定 API 文件標題、描述與版本號
app = FastAPI(
    title="ChatStar Backend API",
    description="Backend service for ChatStar AI Assistant using PostgreSQL",
    version="1.0.0"
)

# 將各功能模組的路由（router）掛載至主應用程式
# 每個 router 負責一個資源類別的 API endpoint
app.include_router(users.router)    # 使用者相關 API
app.include_router(buddies.router)  # AI 好友相關 API
app.include_router(chats.router)    # 對話記錄相關 API
app.include_router(topics.router)   # 話題記錄相關 API

@app.get("/")
def read_root():
    """
    根路徑健康檢查端點（Health Check）。
    用於確認 API 伺服器是否正常運作，回傳歡迎訊息。
    """
    return {"message": "Welcome to ChatStar API"}
