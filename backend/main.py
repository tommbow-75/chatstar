from fastapi import FastAPI
from backend.database import engine
from backend import models

from backend.routers import users, buddies, chats, topics

# 建立所有的資料表
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ChatStar Backend API",
    description="Backend service for ChatStar AI Assistant using PostgreSQL",
    version="1.0.0"
)

# 註冊所有的 API 路由
app.include_router(users.router)
app.include_router(buddies.router)
app.include_router(chats.router)
app.include_router(topics.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to ChatStar API"}
