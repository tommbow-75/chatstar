from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend import schemas, crud
from backend.database import get_db

# 建立使用者相關的路由群組，所有路徑前綴為 /users，標籤為 "Users"
router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    [POST /users/] 建立新使用者。
    先檢查 user_id 是否已存在，若已存在回傳 400 錯誤；
    若不存在則將新使用者寫入資料庫並回傳完整使用者資料。
    """
    db_user = crud.get_user(db, user_id=user.user_id)
    if db_user:
        raise HTTPException(status_code=400, detail="User already registered")
    return crud.create_user(db=db, user=user)

@router.get("/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    [GET /users/] 取得所有使用者列表。
    支援分頁查詢：skip（略過前 N 筆）與 limit（最多回傳 N 筆）。
    """
    return crud.get_users(db, skip=skip, limit=limit)

@router.get("/{user_id}", response_model=schemas.User)
def read_user(user_id: str, db: Session = Depends(get_db)):
    """
    [GET /users/{user_id}] 依 user_id 取得單一使用者資料。
    若使用者不存在，回傳 404 錯誤。
    """
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.put("/{user_id}", response_model=schemas.User)
def update_user(user_id: str, user_update: schemas.UserUpdate, db: Session = Depends(get_db)):
    """
    [PUT /users/{user_id}] 更新指定使用者的資料。
    支援部分更新，若使用者不存在則回傳 404 錯誤。
    """
    db_user = crud.update_user(db, user_id=user_id, user_update=user_update)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.delete("/{user_id}", response_model=schemas.User)
def delete_user(user_id: str, db: Session = Depends(get_db)):
    """
    [DELETE /users/{user_id}] 刪除指定使用者及其所有關聯資料。
    若使用者不存在則回傳 404 錯誤。
    """
    db_user = crud.delete_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user
