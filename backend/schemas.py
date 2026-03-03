from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, Any, Dict, List

# =======================
# User（使用者）
# 定義使用者相關的資料驗證 Schema
# =======================
class UserBase(BaseModel):
    """使用者資料的基底 Schema，包含所有共用欄位。"""
    user_id: str                               # 使用者唯一識別碼
    username: str                              # 使用者顯示名稱
    preferences: Optional[Dict[str, Any]] = None  # 個人偏好設定（選填，JSON 格式）
    user_api: Optional[str] = None             # 個人 API 金鑰（選填）

class UserCreate(UserBase):
    """建立新使用者時使用的 Schema，與 UserBase 相同，無需額外欄位。"""
    pass

class User(UserBase):
    """讀取使用者資料時的回應 Schema，啟用 ORM 模式以支援從 SQLAlchemy Model 轉換。"""
    model_config = ConfigDict(from_attributes=True)


# =======================
# BuddyInfo（AI 好友設定）
# 定義 AI 好友相關的資料驗證 Schema
# =======================
class BuddyInfoBase(BaseModel):
    """AI 好友設定的基底 Schema，包含所有共用欄位。"""
    dmbuddy: str                                       # AI 好友名稱（對應 IG DM 對象）
    buddy_prefs: Optional[Dict[str, Any]] = None       # 好友個人化設定（選填，JSON 格式）

class BuddyInfoCreate(BuddyInfoBase):
    """建立新 AI 好友時使用的 Schema，需額外提供所屬的 user_id。"""
    user_id: str

class BuddyInfo(BuddyInfoBase):
    """讀取 AI 好友資料時的回應 Schema，包含資料庫生成的 id 與 user_id。"""
    id: int
    user_id: str
    model_config = ConfigDict(from_attributes=True)


# =======================
# ChatLog（對話記錄）
# 定義對話記錄相關的資料驗證 Schema
# =======================
class ChatLogBase(BaseModel):
    """對話記錄的基底 Schema，包含所有共用欄位。"""
    dmbuddy: str                                           # 對話的 AI 好友名稱
    received_mess: Optional[str] = None                    # 從真實好友收到的訊息（選填）
    generated_mess: Optional[Dict[str, Any]] = None        # AI 生成的候選回覆（選填，JSON 格式）
    selected_mess: Optional[str] = None                    # 使用者選擇發送的最終回覆（選填）

class ChatLogCreate(ChatLogBase):
    """建立新對話記錄時使用的 Schema，需額外提供所屬的 user_id。"""
    user_id: str

class ChatLog(ChatLogBase):
    """讀取對話記錄時的回應 Schema，包含資料庫生成的 id、user_id 及時間戳記。"""
    id: int
    user_id: str
    date: datetime          # 對話發生的時間
    model_config = ConfigDict(from_attributes=True)


# =======================
# UserTopicLog（使用者話題記錄）
# 定義使用者個人興趣話題相關的資料驗證 Schema
# =======================
class UserTopicLogBase(BaseModel):
    """使用者話題記錄的基底 Schema。"""
    topic: str           # 話題內容

class UserTopicLogCreate(UserTopicLogBase):
    """建立新使用者話題記錄時使用的 Schema，需額外提供所屬的 user_id。"""
    user_id: str

class UserTopicLog(UserTopicLogBase):
    """讀取使用者話題記錄時的回應 Schema，包含 user_id 及建立時間。"""
    user_id: str
    created_at: datetime    # 話題新增的時間
    model_config = ConfigDict(from_attributes=True)


# =======================
# BuddyTopicLog（AI 好友話題記錄）
# 定義使用者與特定 AI 好友共享的話題記錄 Schema
# =======================
class BuddyTopicLogBase(BaseModel):
    """AI 好友話題記錄的基底 Schema。"""
    dmbuddy: str         # 對應的 AI 好友名稱
    topic: str           # 話題內容

class BuddyTopicLogCreate(BuddyTopicLogBase):
    """建立新 AI 好友話題記錄時使用的 Schema，需額外提供所屬的 user_id。"""
    user_id: str

class BuddyTopicLog(BuddyTopicLogBase):
    """讀取 AI 好友話題記錄時的回應 Schema，包含 user_id 及建立時間。"""
    user_id: str
    created_at: datetime    # 話題新增的時間
    model_config = ConfigDict(from_attributes=True)
