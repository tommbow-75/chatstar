from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend import schemas, crud
from backend.database import get_db

# 建立 AI 好友相關的路由群組，所有路徑前綴為 /buddies，標籤為 "Buddies"
router = APIRouter(prefix="/buddies", tags=["Buddies"])

@router.post("/", response_model=schemas.BuddyInfo)
def create_buddy(buddy: schemas.BuddyInfoCreate, db: Session = Depends(get_db)):
    """
    [POST /buddies/] 為指定使用者建立新的 AI 好友設定。
    先確認 user_id 對應的使用者存在，若不存在回傳 404 錯誤；
    若使用者存在則建立好友設定並回傳完整 BuddyInfo 資料。
    """
    db_user = crud.get_user(db, user_id=buddy.user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.create_buddy(db=db, buddy=buddy)

@router.get("/users/{user_id}", response_model=List[schemas.BuddyInfo])
def read_buddies_for_user(user_id: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    [GET /buddies/users/{user_id}] 取得指定使用者的所有 AI 好友列表。
    支援分頁查詢：skip（略過前 N 筆）與 limit（最多回傳 N 筆）。
    """
    return crud.get_buddies_by_user(db, user_id=user_id, skip=skip, limit=limit)

@router.get("/{buddy_id}", response_model=schemas.BuddyInfo)
def read_buddy(buddy_id: int, db: Session = Depends(get_db)):
    """
    [GET /buddies/{buddy_id}] 依主鍵 buddy_id 取得單一 AI 好友設定。
    若好友不存在，回傳 404 錯誤。
    """
    db_buddy = crud.get_buddy(db, buddy_id=buddy_id)
    if db_buddy is None:
        raise HTTPException(status_code=404, detail="Buddy not found")
    return db_buddy

@router.put("/{buddy_id}", response_model=schemas.BuddyInfo)
def update_buddy(buddy_id: int, buddy_update: schemas.BuddyInfoUpdate, db: Session = Depends(get_db)):
    """
    [PUT /buddies/{buddy_id}] 更新指定 AI 好友的設定。
    支援部分更新，若好友不存在則回傳 404 錯誤。
    """
    db_buddy = crud.update_buddy(db, buddy_id=buddy_id, buddy_update=buddy_update)
    if db_buddy is None:
        raise HTTPException(status_code=404, detail="Buddy not found")
    return db_buddy

@router.delete("/{buddy_id}", response_model=schemas.BuddyInfo)
def delete_buddy(buddy_id: int, db: Session = Depends(get_db)):
    """
    [DELETE /buddies/{buddy_id}] 刪除指定 AI 好友設定。
    若好友不存在則回傳 404 錯誤。
    """
    db_buddy = crud.delete_buddy(db, buddy_id=buddy_id)
    if db_buddy is None:
        raise HTTPException(status_code=404, detail="Buddy not found")
    return db_buddy
