from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend import schemas, crud
from backend.database import get_db

# 建立對話記錄相關的路由群組，所有路徑前綴為 /chats，標籤為 "Chat History"
router = APIRouter(prefix="/chats", tags=["Chat History"])

@router.post("/", response_model=schemas.ChatLog)
def create_chat(chat: schemas.ChatLogCreate, db: Session = Depends(get_db)):
    """
    [POST /chats/] 建立一筆新的對話記錄。
    先確認 user_id 對應的使用者存在，若不存在回傳 404 錯誤；
    若使用者存在則將本次對話（收到的訊息、AI 生成的候選回覆、最終選擇）寫入資料庫。
    """
    db_user = crud.get_user(db, user_id=chat.user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.create_chat_log(db=db, chat=chat)

@router.get("/users/{user_id}/buddies/{dmbuddy}", response_model=List[schemas.ChatLog])
def read_chats_by_user_buddy(user_id: str, dmbuddy: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    [GET /chats/users/{user_id}/buddies/{dmbuddy}] 取得指定使用者與特定 AI 好友的對話歷史。
    結果依時間倒序排列（最新的在前），支援分頁查詢。
    """
    return crud.get_chat_logs_by_user_buddy(db, user_id=user_id, dmbuddy=dmbuddy, skip=skip, limit=limit)
