from sqlalchemy.orm import Session
from . import models, schemas

# -----------------
# User CRUD
# -----------------
def get_user(db: Session, user_id: str):
    """依照 user_id 從資料庫查詢單一使用者，若不存在則回傳 None。"""
    return db.query(models.User).filter(models.User.user_id == user_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    """查詢所有使用者列表，支援分頁（skip: 略過筆數, limit: 最大回傳筆數）。"""
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    """
    建立新使用者並寫入資料庫。
    將 Pydantic schema 轉換為 ORM Model 後新增至 Session，commit 後刷新取得完整資料。
    """
    db_user = models.User(**user.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# -----------------
# BuddyInfo CRUD
# -----------------
def get_buddy(db: Session, buddy_id: int):
    """依照 buddy_id（主鍵）查詢單一 AI 好友設定，若不存在則回傳 None。"""
    return db.query(models.BuddyInfo).filter(models.BuddyInfo.id == buddy_id).first()

def get_buddies_by_user(db: Session, user_id: str, skip: int = 0, limit: int = 100):
    """查詢特定使用者的所有 AI 好友列表，支援分頁。"""
    return db.query(models.BuddyInfo).filter(models.BuddyInfo.user_id == user_id).offset(skip).limit(limit).all()

def create_buddy(db: Session, buddy: schemas.BuddyInfoCreate):
    """
    建立新的 AI 好友設定並寫入資料庫。
    需搭配有效的 user_id（外鍵），新增成功後回傳完整的 BuddyInfo 物件。
    """
    db_buddy = models.BuddyInfo(**buddy.model_dump())
    db.add(db_buddy)
    db.commit()
    db.refresh(db_buddy)
    return db_buddy

# -----------------
# ChatLog CRUD
# -----------------
def get_chat_logs_by_user_buddy(db: Session, user_id: str, dmbuddy: str, skip: int = 0, limit: int = 100):
    """
    查詢特定使用者與特定 AI 好友之間的對話記錄。
    以時間倒序（最新的在前）排列，支援分頁。
    """
    return db.query(models.ChatLog).filter(
        models.ChatLog.user_id == user_id,
        models.ChatLog.dmbuddy == dmbuddy
    ).order_by(models.ChatLog.date.desc()).offset(skip).limit(limit).all()

def create_chat_log(db: Session, chat: schemas.ChatLogCreate):
    """
    建立一筆新的對話記錄並寫入資料庫。
    記錄包含收到的訊息、AI 生成的候選回覆，以及使用者最終選擇的回覆。
    """
    db_chat = models.ChatLog(**chat.model_dump())
    db.add(db_chat)
    db.commit()
    db.refresh(db_chat)
    return db_chat

# -----------------
# UserTopicLog CRUD
# -----------------
def get_user_topics(db: Session, user_id: str):
    """查詢特定使用者的所有興趣話題記錄。"""
    return db.query(models.UserTopicLog).filter(models.UserTopicLog.user_id == user_id).all()

def create_user_topic(db: Session, topic: schemas.UserTopicLogCreate):
    """
    新增一筆使用者興趣話題記錄至資料庫。
    用於追蹤使用者個人感興趣的話題。
    """
    db_topic = models.UserTopicLog(**topic.model_dump())
    db.add(db_topic)
    db.commit()
    db.refresh(db_topic)
    return db_topic

# -----------------
# BuddyTopicLog CRUD
# -----------------
def get_buddy_topics(db: Session, user_id: str, dmbuddy: str):
    """查詢特定使用者與特定 AI 好友的共同話題記錄。"""
    return db.query(models.BuddyTopicLog).filter(
        models.BuddyTopicLog.user_id == user_id,
        models.BuddyTopicLog.dmbuddy == dmbuddy
    ).all()

def create_buddy_topic(db: Session, topic: schemas.BuddyTopicLogCreate):
    """
    新增一筆使用者與 AI 好友的話題記錄至資料庫。
    用於記錄該使用者針對特定 AI 好友所關注的對話話題。
    """
    db_topic = models.BuddyTopicLog(**topic.model_dump())
    db.add(db_topic)
    db.commit()
    db.refresh(db_topic)
    return db_topic
