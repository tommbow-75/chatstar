from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend import schemas, crud
from backend.database import get_db

router = APIRouter(prefix="/topics", tags=["Topics"])

# User Topics
@router.post("/users", response_model=schemas.UserTopicLog)
def create_user_topic(topic: schemas.UserTopicLogCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=topic.user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.create_user_topic(db=db, topic=topic)

@router.get("/users/{user_id}", response_model=List[schemas.UserTopicLog])
def read_user_topics(user_id: str, db: Session = Depends(get_db)):
    return crud.get_user_topics(db, user_id=user_id)

# Buddy Topics
@router.post("/buddies", response_model=schemas.BuddyTopicLog)
def create_buddy_topic(topic: schemas.BuddyTopicLogCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=topic.user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.create_buddy_topic(db=db, topic=topic)

@router.get("/users/{user_id}/buddies/{dmbuddy}", response_model=List[schemas.BuddyTopicLog])
def read_buddy_topics(user_id: str, dmbuddy: str, db: Session = Depends(get_db)):
    return crud.get_buddy_topics(db, user_id=user_id, dmbuddy=dmbuddy)
