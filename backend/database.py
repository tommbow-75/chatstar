import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# 從 .env 檔案載入環境變數
load_dotenv()

# 使用 PostgreSQL（支援 Neon 雲端 / 本地端）
# DATABASE_URL 格式: postgresql://user:password@host:5432/dbname
_raw_url = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/chatstar"
)

# SQLAlchemy 需要 postgresql+psycopg2:// 作為 driver 前綴
_url = _raw_url.replace("postgresql://", "postgresql+psycopg2://", 1)

# Neon 雲端須加 sslmode=require（若 URL 中尚未包含）
_is_cloud = "localhost" not in _raw_url and "127.0.0.1" not in _raw_url
if _is_cloud and "sslmode" not in _url:
    _url += ("&" if "?" in _url else "?") + "sslmode=require"

SQLALCHEMY_DATABASE_URL = _url

# pool_pre_ping=True：每次取用連線前先 ping，避免 idle 後連線失效
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)

# 讓 psycopg2 能自動將 Python dict/list 序列化為 JSONB
# register_adapter(dict, Json)：插入 dict 時以 JSON 字串形式傳給 PostgreSQL
# 這是解決「column is of type jsonb but expression is of type text」的標準做法
try:
    from psycopg2.extensions import register_adapter
    from psycopg2.extras import Json
    register_adapter(dict, Json)
except Exception:
    pass


# 建立 Session 工廠，每次呼叫 SessionLocal() 會產生一個新的資料庫 Session
# autocommit=False: 需手動 commit；autoflush=False: 不自動刷新至資料庫
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 建立所有 ORM Model 的 Base Class，所有資料表 Model 都須繼承此類別
Base = declarative_base()

def get_db():
    """
    FastAPI 相依性注入（Dependency Injection）函式。
    產生一個資料庫 Session 供 API endpoint 使用，
    並在請求結束後（無論成功或失敗）自動關閉 Session，確保連線不洩漏。
    使用方式：在 endpoint 參數加上 db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
