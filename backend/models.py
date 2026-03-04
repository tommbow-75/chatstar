from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    """
    使用者資料表（users）。
    儲存使用者的基本資料與興趣偏好，供 AI 系統產生回覆建議時參考。
    """
    __tablename__ = "users"

    user_id = Column(String(50), primary_key=True, index=True)   # 使用者唯一識別碼（主鍵）
    username = Column(String(100), nullable=False)                # 使用者顯示名稱
    interests = Column(JSONB)                                     # 使用者興趣與個人特質（JSON 格式，供 AI 參考）

    # ORM 關聯屬性（非資料庫欄位）：方便在 Python 中直接存取關聯資料
    buddies = relationship("BuddyInfo", back_populates="user", cascade="all, delete-orphan")         # 該使用者的所有聊天對象
    chat_logs = relationship("ChatLog", back_populates="user", cascade="all, delete-orphan")          # 該使用者的所有對話記錄
    user_topics = relationship("UserTopicLog", back_populates="user", cascade="all, delete-orphan")   # 該使用者的個人話題記錄
    buddy_topics = relationship("BuddyTopicLog", back_populates="user", cascade="all, delete-orphan") # 該使用者與聊天對象的話題記錄

class BuddyInfo(Base):
    """
    聊天對象資料表（buddy_info）。
    儲存聊天對象的基本資料與興趣偏好，供 AI 系統產生更合適的回覆建議。
    每筆資料對應一個使用者（user_id）與一個聊天對象名稱（dmbuddy）。
    """
    __tablename__ = "buddy_info"

    id = Column(Integer, primary_key=True, index=True)                                              # 自動遞增主鍵
    user_id = Column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)   # 所屬使用者（外鍵）
    dmbuddy = Column(String(100), nullable=False)                                                    # 聊天對象名稱
    interests = Column(JSONB)                                                                        # 聊天對象的興趣與特質（JSON 格式，供 AI 參考）

    user = relationship("User", back_populates="buddies")  # 反向關聯至 User

class ChatLog(Base):
    """
    對話記錄資料表（chat_logs）。
    記錄每一次與 AI 好友的互動過程，包含收到的訊息、AI 生成的候選回覆，
    以及使用者最終選擇發送的回覆內容。
    """
    __tablename__ = "chat_logs"

    id = Column(Integer, primary_key=True, index=True)                                              # 自動遞增主鍵
    user_id = Column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)   # 所屬使用者（外鍵）
    dmbuddy = Column(String(100), nullable=False)                                                    # 對話的 AI 好友名稱
    received_mess = Column(Text)                                                                     # 從對方（真實好友）收到的訊息
    generated_mess = Column(JSONB)                                                                   # AI 生成的多個候選回覆（JSON 陣列格式）
    selected_mess = Column(Text)                                                                     # 使用者最終選擇並發送的回覆
    date = Column(DateTime, server_default=func.now())                                               # 對話發生時間（預設為資料庫伺服器當前時間）

    user = relationship("User", back_populates="chat_logs")  # 反向關聯至 User

class UserTopicLog(Base):
    """
    使用者話題記錄資料表（user_topics_log）。
    記錄使用者個人感興趣的對話話題，使用 (user_id, topic) 作為複合主鍵以防止重複。
    """
    __tablename__ = "user_topics_log"
    # SQLAlchemy mapped class needs a primary key, so we use a composite primary key strategy
    user_id = Column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True) # 所屬使用者（外鍵，複合主鍵之一）
    topic = Column(Text, primary_key=True)                                                           # 話題內容（複合主鍵之一）
    created_at = Column(DateTime, server_default=func.now())                                         # 話題新增時間

    user = relationship("User", back_populates="user_topics")  # 反向關聯至 User

class BuddyTopicLog(Base):
    """
    AI 好友話題記錄資料表（buddy_topics_log）。
    記錄使用者針對特定 AI 好友所關注的對話話題，
    使用 (user_id, dmbuddy, topic) 作為複合主鍵確保唯一性。
    """
    __tablename__ = "buddy_topics_log"

    user_id = Column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True) # 所屬使用者（外鍵，複合主鍵之一）
    dmbuddy = Column(String(100), primary_key=True)                                                  # 對應的 AI 好友名稱（複合主鍵之一）
    topic = Column(Text, primary_key=True)                                                           # 話題內容（複合主鍵之一）
    created_at = Column(DateTime, server_default=func.now())                                         # 話題新增時間

    user = relationship("User", back_populates="buddy_topics")  # 反向關聯至 User
