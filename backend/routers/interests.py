from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend import schemas, crud
from backend.database import get_db

router = APIRouter(prefix="/interests", tags=["Interests"])

@router.post("/", response_model=schemas.Interest)
def create_interest(interest: schemas.InterestCreate, db: Session = Depends(get_db)):
    db_partner = crud.get_partner(db, partner_id=interest.partner_id)
    if not db_partner:
        raise HTTPException(status_code=404, detail="Partner not found")
    return crud.create_interest(db=db, interest=interest)

@router.get("/partners/{partner_id}", response_model=List[schemas.Interest])
def read_interests_by_partner(partner_id: int, db: Session = Depends(get_db)):
    return crud.get_interests_by_partner(db, partner_id=partner_id)
