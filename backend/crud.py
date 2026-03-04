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

def update_user(db: Session, user_id: str, user_update: schemas.UserUpdate):
    """
    更新指定使用者的資料。
    僅更新 user_update 中有展開的欄位（exclude_unset），支援部分更新。
    """
    db_user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if db_user is None:
        return None
    update_data = user_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_user, key, value)
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: str):
    """
    刪除指定使用者。
    因應用 CASCADE 刪除模式，關聯的 buddies/chat_logs 將一併被刪除。
    """
    db_user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if db_user is None:
        return None
    db.delete(db_user)
    db.commit()
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

def update_buddy(db: Session, buddy_id: int, buddy_update: schemas.BuddyInfoUpdate):
    """
    更新指定 AI 好友的設定。
    僅更新 buddy_update 中有展開的欄位（exclude_unset）。
    """
    db_buddy = db.query(models.BuddyInfo).filter(models.BuddyInfo.id == buddy_id).first()
    if db_buddy is None:
        return None
    update_data = buddy_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_buddy, key, value)
    db.commit()
    db.refresh(db_buddy)
    return db_buddy

def delete_buddy(db: Session, buddy_id: int):
    """\u522a\u9664\u6307\u5b9a AI \u597d\u53cb\u8a2d\u5b9a。"""
    db_buddy = db.query(models.BuddyInfo).filter(models.BuddyInfo.id == buddy_id).first()
    if db_buddy is None:
        return None
    db.delete(db_buddy)
    db.commit()
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
