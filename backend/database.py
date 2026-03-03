import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# 從 .env 檔案載入環境變數
load_dotenv()

# 使用 PostgreSQL
# 預設連線字串範例: postgresql://user:password@localhost:5432/dbname
# 優先讀取環境變數 DATABASE_URL，若未設定則使用預設本地連線字串
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:postgres@localhost:5432/chatstar"
)

# 建立 SQLAlchemy 資料庫引擎，負責管理資料庫連線
engine = create_engine(SQLALCHEMY_DATABASE_URL)

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
