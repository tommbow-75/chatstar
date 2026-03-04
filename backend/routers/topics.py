from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend import schemas, crud
from backend.database import get_db

# 建立話題記錄相關的路由群組，所有路徑前綴為 /topics，標籤為 "Topics"
router = APIRouter(prefix="/topics", tags=["Topics"])

# --- 使用者個人話題（User Topics）---

@router.post("/users", response_model=schemas.UserTopicLog)
def create_user_topic(topic: schemas.UserTopicLogCreate, db: Session = Depends(get_db)):
    """
    [POST /topics/users] 為指定使用者新增一個個人興趣話題記錄。
    先確認 user_id 對應的使用者存在，若不存在回傳 404 錯誤；
    若使用者存在則將話題寫入資料庫。
    """
    db_user = crud.get_user(db, user_id=topic.user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.create_user_topic(db=db, topic=topic)

@router.get("/users/{user_id}", response_model=List[schemas.UserTopicLog])
def read_user_topics(user_id: str, db: Session = Depends(get_db)):
    """
    [GET /topics/users/{user_id}] 取得指定使用者的所有個人興趣話題列表。
    """
    return crud.get_user_topics(db, user_id=user_id)

# --- AI 好友話題（Buddy Topics）---

@router.post("/buddies", response_model=schemas.BuddyTopicLog)
def create_buddy_topic(topic: schemas.BuddyTopicLogCreate, db: Session = Depends(get_db)):
    """
    [POST /topics/buddies] 為指定使用者與特定 AI 好友新增一個話題記錄。
    先確認 user_id 對應的使用者存在，若不存在回傳 404 錯誤；
    若使用者存在則將（user_id, dmbuddy, topic）三者組合寫入資料庫。
    """
    db_user = crud.get_user(db, user_id=topic.user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.create_buddy_topic(db=db, topic=topic)

@router.get("/users/{user_id}/buddies/{dmbuddy}", response_model=List[schemas.BuddyTopicLog])
def read_buddy_topics(user_id: str, dmbuddy: str, db: Session = Depends(get_db)):
    """
    [GET /topics/users/{user_id}/buddies/{dmbuddy}] 取得指定使用者與特定 AI 好友的所有共同話題記錄。
    """
    return crud.get_buddy_topics(db, user_id=user_id, dmbuddy=dmbuddy)
