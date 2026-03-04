from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Any, Dict, List

# =======================
# User（使用者）
# =======================
class UserBase(BaseModel):
    """使用者資料的基底 Schema。"""
    user_id: str                                      # 使用者唯一識別碼
    username: str                                     # 使用者顯示名稱
    preferences: Optional[List[str]] = None           # 使用者興趣標籤列表（如 ["音樂", "旅遊"]）

class UserCreate(UserBase):
    """建立新使用者時使用的 Schema。"""
    pass

class UserUpdate(BaseModel):
    """更新使用者時使用的 Schema，所有欄位皆為可選。"""
    username: Optional[str] = None
    preferences: Optional[List[str]] = None

class User(UserBase):
    """讀取使用者資料時的回應 Schema。"""
    model_config = ConfigDict(from_attributes=True)


# =======================
# BuddyInfo（聊天對象）
# =======================
class BuddyInfoBase(BaseModel):
    """聊天對象的基底 Schema。"""
    dmbuddy: str                                       # 聊天對象名稱
    interests: Optional[List[str]] = None             # 聊天對象的興趣標籤列表（如 ["音樂", "旅遊"]）

class BuddyInfoCreate(BuddyInfoBase):
    """建立新聊天對象時使用的 Schema，需額外提供所屬的 user_id。"""
    user_id: str

class BuddyInfoUpdate(BaseModel):
    """更新聊天對象時使用的 Schema，所有欄位皆為可選。"""
    dmbuddy: Optional[str] = None
    interests: Optional[List[str]] = None

class BuddyInfo(BuddyInfoBase):
    """讀取聊天對象資料時的回應 Schema。"""
    id: int
    user_id: str
    model_config = ConfigDict(from_attributes=True)


# =======================
# ChatLog（對話記錄）
# =======================
class ChatLogBase(BaseModel):
    """對話記錄的基底 Schema。"""
    dmbuddy: str
    received_mess: Optional[str] = None
    generated_mess: Optional[Dict[str, Any]] = None
    selected_mess: Optional[str] = None

class ChatLogCreate(ChatLogBase):
    """建立新對話記錄時使用的 Schema。"""
    user_id: str

class ChatLog(ChatLogBase):
    """讀取對話記錄時的回應 Schema。"""
    id: int
    user_id: str
    date: datetime
    model_config = ConfigDict(from_attributes=True)


# =======================
# UserTopicLog（使用者話題記錄）
# =======================
class UserTopicLogBase(BaseModel):
    topic: str

class UserTopicLogCreate(UserTopicLogBase):
    user_id: str

class UserTopicLog(UserTopicLogBase):
    user_id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# =======================
# BuddyTopicLog（聊天對象話題記錄）
# =======================
class BuddyTopicLogBase(BaseModel):
    dmbuddy: str
    topic: str

class BuddyTopicLogCreate(BuddyTopicLogBase):
    user_id: str

class BuddyTopicLog(BuddyTopicLogBase):
    user_id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
