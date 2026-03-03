from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend import schemas, crud
from backend.database import get_db

router = APIRouter(prefix="/partners", tags=["Partners"])

@router.post("/", response_model=schemas.Partner)
def create_partner(partner: schemas.PartnerCreate, db: Session = Depends(get_db)):
    # Verify user exists first
    db_user = crud.get_user(db, user_id=partner.user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.create_partner(db=db, partner=partner)

@router.get("/users/{user_id}", response_model=List[schemas.Partner])
def read_partners_for_user(user_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_partners(db, user_id=user_id, skip=skip, limit=limit)

@router.get("/{partner_id}", response_model=schemas.Partner)
def read_partner(partner_id: int, db: Session = Depends(get_db)):
    db_partner = crud.get_partner(db, partner_id=partner_id)
    if db_partner is None:
        raise HTTPException(status_code=404, detail="Partner not found")
    return db_partner

