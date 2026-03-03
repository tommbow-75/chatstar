from sqlalchemy.orm import Session
from . import models, schemas

# -----------------
# User CRUD
# -----------------
def get_user(db: Session, user_id: str):
    return db.query(models.User).filter(models.User.user_id == user_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(**user.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# -----------------
# BuddyInfo CRUD
# -----------------
def get_buddy(db: Session, buddy_id: int):
    return db.query(models.BuddyInfo).filter(models.BuddyInfo.id == buddy_id).first()

def get_buddies_by_user(db: Session, user_id: str, skip: int = 0, limit: int = 100):
    return db.query(models.BuddyInfo).filter(models.BuddyInfo.user_id == user_id).offset(skip).limit(limit).all()

def create_buddy(db: Session, buddy: schemas.BuddyInfoCreate):
    db_buddy = models.BuddyInfo(**buddy.model_dump())
    db.add(db_buddy)
    db.commit()
    db.refresh(db_buddy)
    return db_buddy

# -----------------
# ChatLog CRUD
# -----------------
def get_chat_logs_by_user_buddy(db: Session, user_id: str, dmbuddy: str, skip: int = 0, limit: int = 100):
    return db.query(models.ChatLog).filter(
        models.ChatLog.user_id == user_id,
        models.ChatLog.dmbuddy == dmbuddy
    ).order_by(models.ChatLog.date.desc()).offset(skip).limit(limit).all()

def create_chat_log(db: Session, chat: schemas.ChatLogCreate):
    db_chat = models.ChatLog(**chat.model_dump())
    db.add(db_chat)
    db.commit()
    db.refresh(db_chat)
    return db_chat

# -----------------
# UserTopicLog CRUD
# -----------------
def get_user_topics(db: Session, user_id: str):
    return db.query(models.UserTopicLog).filter(models.UserTopicLog.user_id == user_id).all()

def create_user_topic(db: Session, topic: schemas.UserTopicLogCreate):
    db_topic = models.UserTopicLog(**topic.model_dump())
    db.add(db_topic)
    db.commit()
    db.refresh(db_topic)
    return db_topic

# -----------------
# BuddyTopicLog CRUD
# -----------------
def get_buddy_topics(db: Session, user_id: str, dmbuddy: str):
    return db.query(models.BuddyTopicLog).filter(
        models.BuddyTopicLog.user_id == user_id,
        models.BuddyTopicLog.dmbuddy == dmbuddy
    ).all()

def create_buddy_topic(db: Session, topic: schemas.BuddyTopicLogCreate):
    db_topic = models.BuddyTopicLog(**topic.model_dump())
    db.add(db_topic)
    db.commit()
    db.refresh(db_topic)
    return db_topic
