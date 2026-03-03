from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend import schemas, crud
from backend.database import get_db

router = APIRouter(prefix="/buddies", tags=["Buddies"])

@router.post("/", response_model=schemas.BuddyInfo)
def create_buddy(buddy: schemas.BuddyInfoCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=buddy.user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.create_buddy(db=db, buddy=buddy)

@router.get("/users/{user_id}", response_model=List[schemas.BuddyInfo])
def read_buddies_for_user(user_id: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_buddies_by_user(db, user_id=user_id, skip=skip, limit=limit)

@router.get("/{buddy_id}", response_model=schemas.BuddyInfo)
def read_buddy(buddy_id: int, db: Session = Depends(get_db)):
    db_buddy = crud.get_buddy(db, buddy_id=buddy_id)
    if db_buddy is None:
        raise HTTPException(status_code=404, detail="Buddy not found")
    return db_buddy
