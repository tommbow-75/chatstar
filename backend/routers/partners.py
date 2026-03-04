from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend import schemas, crud
from backend.database import get_db

# 建立 partners 相關的路由群組，所有路徑前綴為 /partners，標籤為 "Partners"
router = APIRouter(prefix="/partners", tags=["Partners"])

@router.post("/", response_model=schemas.Partner)
def create_partner(partner: schemas.PartnerCreate, db: Session = Depends(get_db)):
    """
    [POST /partners/] 為指定使用者建立新的 partner 記錄。
    先確認 user_id 對應的使用者存在，若不存在回傳 404 錯誤；
    若使用者存在則建立 partner 記錄並回傳完整資料。
    """
    # Verify user exists first
    db_user = crud.get_user(db, user_id=partner.user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.create_partner(db=db, partner=partner)

@router.get("/users/{user_id}", response_model=List[schemas.Partner])
def read_partners_for_user(user_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    [GET /partners/users/{user_id}] 取得指定使用者的所有 partner 列表。
    支援分頁查詢：skip（略過前 N 筆）與 limit（最多回傳 N 筆）。
    """
    return crud.get_partners(db, user_id=user_id, skip=skip, limit=limit)

@router.get("/{partner_id}", response_model=schemas.Partner)
def read_partner(partner_id: int, db: Session = Depends(get_db)):
    """
    [GET /partners/{partner_id}] 依主鍵 partner_id 取得單一 partner 資料。
    若 partner 不存在，回傳 404 錯誤。
    """
    db_partner = crud.get_partner(db, partner_id=partner_id)
    if db_partner is None:
        raise HTTPException(status_code=404, detail="Partner not found")
    return db_partner
