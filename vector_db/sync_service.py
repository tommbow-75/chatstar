"""
sync_service.py
===============
Pinecone 向量資料庫的寫入/刪除模組。

架構說明
--------
本模組使用 Pinecone Inference API（自動 Embedding）：
由於 Index `chatstar` 建立時已綁定 `multilingual-e5-large`，
只需傳入 `text` 欄位，Pinecone 會自動完成向量化，
程式碼中**不需要呼叫任何 Embedding 模型**。

Namespace 命名規則（用於物理隔離不同使用者的資料）
-------------------------------------------------
  {user_id}_user_prefs           ← User.preferences 拆解後的向量
  {user_id}_user_topics          ← UserTopicLog 的每條 topic
  {user_id}_{dmbuddy}_buddy_prefs  ← BuddyInfo.interests 拆解後
  {user_id}_{dmbuddy}_buddy_topics ← BuddyTopicLog 的每條 topic

Vector Record 格式（傳入 upsert_vectors 的 records 列表）
---------------------------------------------------------
  {
    "_id":    "buddy_5_interests_0",   # 唯一 ID（不能有空格）
    "text":   "小美 的興趣是 看懸疑電影",  # ← 會被自動向量化
    "user_id": "u_001",                # Metadata（供過濾用）
    "partner": "小美",
    "type":   "buddy_prefs",
    "source_id": 5
  }

使用範例
--------
    from vector_db.sync_service import upsert_vectors, delete_namespace

    ns = "u_001_小美_buddy_prefs"
    upsert_vectors(ns, [
        {"_id": "buddy_5_0", "text": "小美 的興趣是 看懸疑電影",
         "user_id": "u_001", "partner": "小美", "type": "buddy_prefs", "source_id": 5},
    ])
"""

import logging
import os
import threading
from typing import Any

from dotenv import load_dotenv
from pinecone import Pinecone

# ── 環境設定 ────────────────────────────────────────────────────────────────

load_dotenv()

PINECONE_API_KEY = os.environ["PINECONE_API_KEY"]
PINECONE_INDEX   = os.getenv("PINECONE_INDEX", "chatstar")

# ── 日誌 ────────────────────────────────────────────────────────────────────

logger = logging.getLogger(__name__)

# ── Pinecone 客戶端初始化 ────────────────────────────────────────────────────

_pc: Pinecone | None = None
_index = None
_lock  = threading.Lock()


def _get_index():
    """取得（或惰性初始化）Pinecone Index 連線（執行緒安全）。"""
    global _pc, _index
    if _index is None:
        with _lock:
            if _index is None:
                _pc    = Pinecone(api_key=PINECONE_API_KEY)
                _index = _pc.Index(PINECONE_INDEX)
                logger.info("✅ Pinecone index '%s' 已連線", PINECONE_INDEX)
    return _index


# ══════════════════════════════════════════════════════════════════════════════
# 公開 API
# ══════════════════════════════════════════════════════════════════════════════

def upsert_vectors(namespace: str, records: list[dict[str, Any]]) -> None:
    """
    將一批記錄 upsert 到指定 Namespace。

    Parameters
    ----------
    namespace : str
        目標 Namespace（如 "u_001_小美_buddy_prefs"）。
    records : list[dict]
        每筆記錄必須包含 `_id` 與 `text` 欄位；其餘欄位作為 Metadata 儲存。
        Pinecone Inference API 會自動將 `text` 轉為向量。

    Notes
    -----
    - 單次建議不超過 96 筆（Pinecone upsert_records 上限）。
    - 若 ID 已存在，Pinecone 會覆寫（upsert 行為）。
    """
    if not records:
        return
    try:
        idx = _get_index()
        idx.upsert_records(namespace=namespace, records=records)
        logger.info("✅ Pinecone upsert %d 筆 → namespace='%s'", len(records), namespace)
    except Exception as e:
        logger.error("❌ Pinecone upsert 失敗 (namespace=%s): %s", namespace, e)


def delete_by_ids(namespace: str, ids: list[str]) -> None:
    """
    依 ID 列表刪除 Namespace 中的特定向量。

    Parameters
    ----------
    namespace : str
        目標 Namespace。
    ids : list[str]
        要刪除的 Vector ID 列表。
    """
    if not ids:
        return
    try:
        idx = _get_index()
        idx.delete(ids=ids, namespace=namespace)
        logger.info("🗑️ Pinecone 已刪除 %d 筆 → namespace='%s'", len(ids), namespace)
    except Exception as e:
        logger.error("❌ Pinecone delete 失敗 (namespace=%s, ids=%s): %s", namespace, ids, e)


def delete_namespace(namespace: str) -> None:
    """
    清空整個 Namespace（全刪全建策略使用）。

    當偏好資料（preferences / interests）被完整更新時，
    先呼叫此函式清空舊向量，再重新 upsert 最新資料。

    Parameters
    ----------
    namespace : str
        要清空的 Namespace 名稱。
    """
    try:
        idx = _get_index()
        idx.delete(delete_all=True, namespace=namespace)
        logger.info("🗑️ Pinecone namespace '%s' 已全部清空", namespace)
    except Exception as e:
        logger.error("❌ Pinecone delete_all 失敗 (namespace=%s): %s", namespace, e)


# ══════════════════════════════════════════════════════════════════════════════
# Namespace 名稱生成輔助函式（統一格式，避免拼寫錯誤）
# ══════════════════════════════════════════════════════════════════════════════

def ns_user_prefs(user_id: str) -> str:
    """回傳使用者偏好的 Namespace 名稱。"""
    return f"{user_id}_user_prefs"

def ns_user_topics(user_id: str) -> str:
    """回傳使用者話題的 Namespace 名稱。"""
    return f"{user_id}_user_topics"

def ns_buddy_prefs(user_id: str, dmbuddy: str) -> str:
    """回傳聊天對象偏好的 Namespace 名稱。"""
    safe_buddy = dmbuddy.replace(" ", "_")
    return f"{user_id}_{safe_buddy}_buddy_prefs"

def ns_buddy_topics(user_id: str, dmbuddy: str) -> str:
    """回傳聊天對象話題的 Namespace 名稱。"""
    safe_buddy = dmbuddy.replace(" ", "_")
    return f"{user_id}_{safe_buddy}_buddy_topics"


# ══════════════════════════════════════════════════════════════════════════════
# 資料轉換輔助函式（PostgreSQL 資料 → Pinecone Records）
# ══════════════════════════════════════════════════════════════════════════════

def build_user_pref_records(user_id: str, preferences: list | dict | None) -> list[dict]:
    """
    將 User.preferences（JSONB）拆解為 Pinecone Records 列表。

    Parameters
    ----------
    user_id : str
        使用者 ID（作為 Record ID 前綴與 Metadata）。
    preferences : list | dict | None
        PostgreSQL 中儲存的偏好資料。
        支援格式：字串列表 `["看電影", "打球"]` 或字典 `{"interests": [...]}`。

    Returns
    -------
    list[dict]
        可直接傳入 `upsert_vectors` 的 Records 列表。
    """
    if not preferences:
        return []

    items = _extract_list_items(preferences)
    records = []
    for i, item in enumerate(items):
        item = str(item).strip()
        if not item:
            continue
        records.append({
            "_id":      f"user_{user_id}_pref_{i}",
            "text":     f"使用者自己 的興趣是 {item}",
            "user_id":  user_id,
            "partner":  "",
            "type":     "user_prefs",
            "source_id": 0,
        })
    return records


def build_buddy_pref_records(user_id: str, buddy_id: int, dmbuddy: str, interests: list | dict | None) -> list[dict]:
    """
    將 BuddyInfo.interests（JSONB）拆解為 Pinecone Records 列表。

    Parameters
    ----------
    buddy_id : int
        BuddyInfo 的主鍵（作為 Record ID 前綴）。
    dmbuddy : str
        聊天對象名稱（作為 Metadata）。
    interests : list | dict | None
        PostgreSQL 中儲存的興趣資料。
    """
    if not interests:
        return []

    items = _extract_list_items(interests)
    records = []
    for i, item in enumerate(items):
        item = str(item).strip()
        if not item:
            continue
        records.append({
            "_id":      f"buddy_{buddy_id}_pref_{i}",
            "text":     f"{dmbuddy} 的興趣是 {item}",
            "user_id":  user_id,
            "partner":  dmbuddy,
            "type":     "buddy_prefs",
            "source_id": buddy_id,
        })
    return records


def build_user_topic_record(user_id: str, topic_id: int, topic: str) -> dict:
    """
    將單條 UserTopicLog 轉為 Pinecone Record。

    Parameters
    ----------
    topic_id : int
        UserTopicLog 的獨立自增 id（需先在 models.py 加上此欄位）。
    topic : str
        話題內容。
    """
    return {
        "_id":      f"user_topic_{topic_id}",
        "text":     f"使用者自己 最近聊過的話題是 {topic}",
        "user_id":  user_id,
        "partner":  "",
        "type":     "user_topics",
        "source_id": topic_id,
    }


def build_buddy_topic_record(user_id: str, topic_id: int, dmbuddy: str, topic: str) -> dict:
    """
    將單條 BuddyTopicLog 轉為 Pinecone Record。

    Parameters
    ----------
    topic_id : int
        BuddyTopicLog 的獨立自增 id（需先在 models.py 加上此欄位）。
    dmbuddy : str
        聊天對象名稱。
    topic : str
        話題內容。
    """
    return {
        "_id":      f"buddy_topic_{topic_id}",
        "text":     f"{dmbuddy} 最近聊過的話題是 {topic}",
        "user_id":  user_id,
        "partner":  dmbuddy,
        "type":     "buddy_topics",
        "source_id": topic_id,
    }


# ── 私有輔助 ─────────────────────────────────────────────────────────────────

def _extract_list_items(data: list | dict | str) -> list:
    """從不同格式的 JSONB 資料中提取字串列表。"""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        # 嘗試常見的 key 名稱
        for key in ("interests", "preferences", "items", "list"):
            if key in data:
                val = data[key]
                return val if isinstance(val, list) else [val]
        # 若無已知 key，取第一個 value
        first = next(iter(data.values()), [])
        return first if isinstance(first, list) else [str(first)]
    if isinstance(data, str):
        return [data]
    return []
