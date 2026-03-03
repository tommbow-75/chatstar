from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend import schemas, crud
from backend.database import get_db

# 建立 interests 相關的路由群組，所有路徑前綴為 /interests，標籤為 "Interests"
router = APIRouter(prefix="/interests", tags=["Interests"])

@router.post("/", response_model=schemas.Interest)
def create_interest(interest: schemas.InterestCreate, db: Session = Depends(get_db)):
    """
    [POST /interests/] 為指定 partner 建立新的 Interest 記錄。
    先確認 partner_id 對應的 partner 存在，若不存在回傳 404 錯誤；
    若 partner 存在則建立 interest 記錄並回傳完整資料。
    """
    db_partner = crud.get_partner(db, partner_id=interest.partner_id)
    if not db_partner:
        raise HTTPException(status_code=404, detail="Partner not found")
    return crud.create_interest(db=db, interest=interest)

@router.get("/partners/{partner_id}", response_model=List[schemas.Interest])
def read_interests_by_partner(partner_id: int, db: Session = Depends(get_db)):
    """
    [GET /interests/partners/{partner_id}] 取得指定 partner 的所有 interest 記錄列表。
    """
    return crud.get_interests_by_partner(db, partner_id=partner_id)
