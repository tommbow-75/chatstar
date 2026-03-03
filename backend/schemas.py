from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, Any, Dict, List

# =======================
# User
# =======================
class UserBase(BaseModel):
    user_id: str
    username: str
    preferences: Optional[Dict[str, Any]] = None
    user_api: Optional[str] = None

class UserCreate(UserBase):
    pass

class User(UserBase):
    model_config = ConfigDict(from_attributes=True)


# =======================
# BuddyInfo
# =======================
class BuddyInfoBase(BaseModel):
    dmbuddy: str
    buddy_prefs: Optional[Dict[str, Any]] = None

class BuddyInfoCreate(BuddyInfoBase):
    user_id: str

class BuddyInfo(BuddyInfoBase):
    id: int
    user_id: str
    model_config = ConfigDict(from_attributes=True)


# =======================
# ChatLog
# =======================
class ChatLogBase(BaseModel):
    dmbuddy: str
    received_mess: Optional[str] = None
    generated_mess: Optional[Dict[str, Any]] = None
    selected_mess: Optional[str] = None

class ChatLogCreate(ChatLogBase):
    user_id: str

class ChatLog(ChatLogBase):
    id: int
    user_id: str
    date: datetime
    model_config = ConfigDict(from_attributes=True)


# =======================
# UserTopicLog
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
# BuddyTopicLog
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
