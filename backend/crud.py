from sqlalchemy.orm import Session
from . import models, schemas
from datetime import datetime, timedelta
import threading
import logging

logger = logging.getLogger(__name__)

# ── Pinecone 同步（背景觸發）────────────────────────────────────────────────
# 延遲匯入，避免 Pinecone 連線在模組載入時立即建立
def _run_in_background(fn, *args, **kwargs):
    """在獨立執行緒中執行函式，不阻塞主流程。錯誤只記錄日誌，不拋出例外。"""
    def wrapper():
        try:
            fn(*args, **kwargs)
        except Exception as e:
            logger.error("Pinecone 背景同步失敗: %s", e)
    threading.Thread(target=wrapper, daemon=True).start()


def _sync_user_prefs(user_id: str, preferences):
    """將 User.preferences 同步至 Pinecone（全刪全建）。"""
    from vector_db.sync_service import (
        ns_user_prefs, delete_namespace, upsert_vectors, build_user_pref_records
    )
    ns = ns_user_prefs(user_id)
    delete_namespace(ns)
    records = build_user_pref_records(user_id, preferences)
    if records:
        upsert_vectors(ns, records)


def _sync_buddy_prefs(user_id: str, buddy_id: int, dmbuddy: str, interests):
    """將 BuddyInfo.interests 同步至 Pinecone（全刪全建）。"""
    from vector_db.sync_service import (
        ns_buddy_prefs, delete_namespace, upsert_vectors, build_buddy_pref_records
    )
    ns = ns_buddy_prefs(user_id, dmbuddy)
    delete_namespace(ns)
    records = build_buddy_pref_records(user_id, buddy_id, dmbuddy, interests)
    if records:
        upsert_vectors(ns, records)


def _sync_add_user_topic(user_id: str, topic_id: int, topic: str):
    """將單條 UserTopicLog 寫入 Pinecone。"""
    from vector_db.sync_service import ns_user_topics, upsert_vectors, build_user_topic_record
    record = build_user_topic_record(user_id, topic_id, topic)
    upsert_vectors(ns_user_topics(user_id), [record])


def _sync_delete_user_topic(user_id: str, topic_id: int):
    """從 Pinecone 刪除單條 UserTopicLog 向量。"""
    from vector_db.sync_service import ns_user_topics, delete_by_ids
    delete_by_ids(ns_user_topics(user_id), [f"user_topic_{topic_id}"])


def _sync_add_buddy_topic(user_id: str, topic_id: int, dmbuddy: str, topic: str):
    """將單條 BuddyTopicLog 寫入 Pinecone。"""
    from vector_db.sync_service import ns_buddy_topics, upsert_vectors, build_buddy_topic_record
    record = build_buddy_topic_record(user_id, topic_id, dmbuddy, topic)
    upsert_vectors(ns_buddy_topics(user_id, dmbuddy), [record])


def _sync_delete_buddy_topic(user_id: str, topic_id: int, dmbuddy: str):
    """從 Pinecone 刪除單條 BuddyTopicLog 向量。"""
    from vector_db.sync_service import ns_buddy_topics, delete_by_ids
    delete_by_ids(ns_buddy_topics(user_id, dmbuddy), [f"buddy_topic_{topic_id}"])


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
    若有 preferences，同步寫入 Pinecone。
    """
    db_user = models.User(**user.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    # 若新建時已有 preferences，同步至 Pinecone
    if db_user.preferences:
        _run_in_background(_sync_user_prefs, db_user.user_id, db_user.preferences)
    return db_user

def update_user(db: Session, user_id: str, user_update: schemas.UserUpdate):
    """
    更新指定使用者的資料。
    僅更新 user_update 中有展開的欄位（exclude_unset），支援部分更新。
    若 preferences 有變動，觸發 Pinecone 全刪全建同步。
    """
    db_user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if db_user is None:
        return None
    update_data = user_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_user, key, value)
    db.commit()
    db.refresh(db_user)
    # preferences 有更新時，觸發 Pinecone 背景同步
    if "preferences" in update_data:
        _run_in_background(_sync_user_prefs, user_id, db_user.preferences)
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
    若有 interests，同步寫入 Pinecone。
    """
    db_buddy = models.BuddyInfo(**buddy.model_dump())
    db.add(db_buddy)
    db.commit()
    db.refresh(db_buddy)
    if db_buddy.interests:
        _run_in_background(
            _sync_buddy_prefs,
            db_buddy.user_id, db_buddy.id, db_buddy.dmbuddy, db_buddy.interests
        )
    return db_buddy

def update_buddy(db: Session, buddy_id: int, buddy_update: schemas.BuddyInfoUpdate):
    """
    更新指定 AI 好友的設定。
    僅更新有展開的欄位。若 interests 有變動，觸發 Pinecone 全刪全建同步。
    """
    db_buddy = db.query(models.BuddyInfo).filter(models.BuddyInfo.id == buddy_id).first()
    if db_buddy is None:
        return None
    update_data = buddy_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_buddy, key, value)
    db.commit()
    db.refresh(db_buddy)
    if "interests" in update_data:
        _run_in_background(
            _sync_buddy_prefs,
            db_buddy.user_id, db_buddy.id, db_buddy.dmbuddy, db_buddy.interests
        )
    return db_buddy

def delete_buddy(db: Session, buddy_id: int):
    """刪除指定 AI 好友設定。"""
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
    新增一筆使用者興趣話題記錄至資料庫，並同步寫入 Pinecone。
    """
    db_topic = models.UserTopicLog(**topic.model_dump())
    db.add(db_topic)
    db.commit()
    db.refresh(db_topic)
    # 同步至 Pinecone（使用自增 id）
    if db_topic.id is not None:
        _run_in_background(
            _sync_add_user_topic, db_topic.user_id, db_topic.id, db_topic.topic
        )
    return db_topic

# -----------------
# BuddyTopicLog CRUD
# -----------------
def get_buddy_topics(db: Session, user_id: str, dmbuddy: str):
    """查詢特定使用者與特定 AI 好友的共同話題記錄。在查詢前自動清除超過三個月（90天）的話題。"""
    three_months_ago = datetime.now() - timedelta(days=90)
    db.query(models.BuddyTopicLog).filter(
        models.BuddyTopicLog.user_id == user_id,
        models.BuddyTopicLog.dmbuddy == dmbuddy,
        models.BuddyTopicLog.created_at < three_months_ago
    ).delete(synchronize_session=False)
    db.commit()

    return db.query(models.BuddyTopicLog).filter(
        models.BuddyTopicLog.user_id == user_id,
        models.BuddyTopicLog.dmbuddy == dmbuddy
    ).all()

def create_buddy_topic(db: Session, topic: schemas.BuddyTopicLogCreate):
    """
    新增一筆使用者與 AI 好友的話題記錄至資料庫，並同步寫入 Pinecone。
    """
    db_topic = models.BuddyTopicLog(**topic.model_dump())
    db.add(db_topic)
    db.commit()
    db.refresh(db_topic)
    # 同步至 Pinecone（使用自增 id）
    if db_topic.id is not None:
        _run_in_background(
            _sync_add_buddy_topic,
            db_topic.user_id, db_topic.id, db_topic.dmbuddy, db_topic.topic
        )
    return db_topic

def delete_user_topic(db: Session, user_id: str, topic: str):
    """刪除指定使用者的某一條個人話題記錄，並從 Pinecone 移除對應向量。"""
    db_topic = db.query(models.UserTopicLog).filter(
        models.UserTopicLog.user_id == user_id,
        models.UserTopicLog.topic == topic
    ).first()
    if db_topic is None:
        return None
    topic_id = db_topic.id  # 先記錄 id，刪除後就找不到了
    db.delete(db_topic)
    db.commit()
    # 從 Pinecone 刪除
    if topic_id is not None:
        _run_in_background(_sync_delete_user_topic, user_id, topic_id)
    return db_topic

def delete_buddy_topic(db: Session, user_id: str, dmbuddy: str, topic: str):
    """刪除指定使用者與特定聊天對象的某一條話題記錄，並從 Pinecone 移除對應向量。"""
    db_topic = db.query(models.BuddyTopicLog).filter(
        models.BuddyTopicLog.user_id == user_id,
        models.BuddyTopicLog.dmbuddy == dmbuddy,
        models.BuddyTopicLog.topic == topic
    ).first()
    if db_topic is None:
        return None
    topic_id = db_topic.id  # 先記錄 id，刪除後就找不到了
    db.delete(db_topic)
    db.commit()
    # 從 Pinecone 刪除
    if topic_id is not None:
        _run_in_background(_sync_delete_buddy_topic, user_id, topic_id, dmbuddy)
    return db_topic
