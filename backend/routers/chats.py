from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend import schemas, crud
from backend.database import get_db

router = APIRouter(prefix="/chats", tags=["Chat History"])

@router.post("/", response_model=schemas.ChatLog)
def create_chat(chat: schemas.ChatLogCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=chat.user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.create_chat_log(db=db, chat=chat)

@router.get("/users/{user_id}/buddies/{dmbuddy}", response_model=List[schemas.ChatLog])
def read_chats_by_user_buddy(user_id: str, dmbuddy: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_chat_logs_by_user_buddy(db, user_id=user_id, dmbuddy=dmbuddy, skip=skip, limit=limit)
