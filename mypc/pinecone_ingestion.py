"""
pinecone_ingestion.py
=====================
監聽 PostgreSQL NOTIFY 事件，當 user/buddy 的 preferences 或 topic
寫入資料庫時，自動產生自然語言描述並透過 langchain-pinecone 寫入 Pinecone。

啟動方式
--------
    python mypc/pinecone_ingestion.py

需要的環境變數（.env）
----------------------
    DATABASE_URL        postgresql://user:pw@host/db
    PINECONE_API_KEY    your-pinecone-api-key
    PINECONE_INDEX      your-index-name  （預設: chatstar）
    GOOGLE_API_KEY      your-google-api-key （用於 GoogleGenerativeAIEmbeddings）

資料庫端 TRIGGER 設定請見本檔底部的 SQL 範例。
"""

import os
import json
import select
import logging
from datetime import datetime, timezone
from typing import List, Optional, Union

import psycopg2
import psycopg2.extensions
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.documents import Document

# ── 環境變數 ────────────────────────────────────────────────────────────────────
load_dotenv()

DATABASE_URL   = os.environ["DATABASE_URL"]
PINECONE_INDEX = os.getenv("PINECONE_INDEX", "chatstar")

# ── 日誌 ────────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── 監聽頻道（需與 DB TRIGGER 中 pg_notify() 的 channel 一致） ──────────────────
CHANNELS = [
    "user_preferences_updated",   # User 的 preferences 寫入/更新時觸發
    "user_topic_inserted",        # UserTopicLog 插入新話題時觸發
    "buddy_preferences_updated",  # BuddyInfo 的 buddy_prefs 寫入/更新時觸發
    "buddy_topic_inserted",       # BuddyTopicLog 插入新話題時觸發
]

# ── 自然語言範本 ─────────────────────────────────────────────────────────────────
TEMPLATES = {
    "preferences": "{role} 的興趣是 {item}",
    "topic":       "{role} 最近聊過的話題是 {item}",
}


# ── 核心邏輯 ─────────────────────────────────────────────────────────────────────

def make_documents(channel: str, payload_str: str) -> list[Document]:
    """解析 NOTIFY payload，回傳 LangChain Document 列表。"""
    try:
        payload = json.loads(payload_str)
    except json.JSONDecodeError:
        logger.error("無法解析 payload: %s", payload_str)
        return []

    user_id: int | None = payload.get("user_id")
    role: str           = payload.get("role", "user")   # "user" | "buddy"
    items               = payload.get("items")           # str 或 list[str]

    if user_id is None or not items:
        logger.warning("payload 缺少必要欄位: %s", payload)
        return []

    data_type = "preferences" if "preferences" in channel else "topic"
    template  = TEMPLATES[data_type]

    if isinstance(items, str):
        items = [items]

    docs = []
    for item in items:
        item = str(item).strip()
        if not item:
            continue

        text = template.format(role=role, item=item)
        docs.append(Document(
            page_content=text,
            metadata={
                "user_id":    user_id,
                "role":       role,
                "type":       data_type,
                "item":       item,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        ))
        logger.debug("  準備寫入 → %s", text)

    return docs


def listen_and_ingest() -> None:
    """監聽 PostgreSQL NOTIFY，接收後轉為 Document 並寫入 Pinecone。"""

    # ── 初始化 LangChain embedding model + Pinecone vector store ────────────────
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    vector_store = PineconeVectorStore(
        index_name=PINECONE_INDEX,
        embedding=embeddings,
    )
    logger.info("✅ 已連線 Pinecone index: %s", PINECONE_INDEX)

    # ── PostgreSQL LISTEN ────────────────────────────────────────────────────────
    conn = psycopg2.connect(DATABASE_URL)
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    cur  = conn.cursor()

    for ch in CHANNELS:
        cur.execute(f"LISTEN {ch};")
    logger.info("🟢 開始監聽 channels: %s", ", ".join(CHANNELS))

    try:
        while True:
            if select.select([conn], [], [], 5) == ([], [], []):
                continue  # 等待逾時，繼續監聽

            conn.poll()
            while conn.notifies:
                notify = conn.notifies.pop(0)
                logger.info("📬 收到通知 channel=%s", notify.channel)

                docs = make_documents(notify.channel, notify.payload)
                if docs:
                    try:
                        # add_documents 自動完成 embedding + upsert
                        logger.info("準備將 %d 筆文件寫入 Pinecone...", len(docs))
                        vector_store.add_documents(docs)
                        logger.info("✅ 已寫入 %d 筆向量到 Pinecone", len(docs))
                    except Exception as e:
                        logger.error("❌ 寫入 Pinecone 失敗: %s", e)
                        import traceback
                        logger.error(traceback.format_exc())

    except KeyboardInterrupt:
        logger.info("🛑 停止監聽。")
    finally:
        cur.close()
        conn.close()


# ── 主程式 ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    listen_and_ingest()


# ══════════════════════════════════════════════════════════════════════════════
# 資料庫端 TRIGGER 範例（PostgreSQL）
# payload 格式: {"user_id": 123, "role": "user"|"buddy", "items": [...]}
# ══════════════════════════════════════════════════════════════════════════════

# ── User preferences ──────────────────────────────────────────────────────────
# CREATE OR REPLACE FUNCTION notify_user_preferences() RETURNS TRIGGER LANGUAGE plpgsql AS $$
# BEGIN
#   PERFORM pg_notify('user_preferences_updated',
#     json_build_object('user_id', NEW.user_id, 'role', 'user', 'items', NEW.preferences)::text);
#   RETURN NEW;
# END; $$;
# DROP TRIGGER IF EXISTS trg_user_preferences ON users;
# CREATE TRIGGER trg_user_preferences
#   AFTER INSERT OR UPDATE OF preferences ON users
#   FOR EACH ROW EXECUTE FUNCTION notify_user_preferences();

# ── UserTopicLog ──────────────────────────────────────────────────────────────
# CREATE OR REPLACE FUNCTION notify_user_topic() RETURNS TRIGGER LANGUAGE plpgsql AS $$
# BEGIN
#   PERFORM pg_notify('user_topic_inserted',
#     json_build_object('user_id', NEW.user_id, 'role', 'user', 'items', ARRAY[NEW.topic])::text);
#   RETURN NEW;
# END; $$;
# DROP TRIGGER IF EXISTS trg_user_topic ON user_topics_log;
# CREATE TRIGGER trg_user_topic
#   AFTER INSERT ON user_topics_log
#   FOR EACH ROW EXECUTE FUNCTION notify_user_topic();

# ── BuddyInfo preferences ─────────────────────────────────────────────────────
# CREATE OR REPLACE FUNCTION notify_buddy_preferences() RETURNS TRIGGER LANGUAGE plpgsql AS $$
# BEGIN
#   PERFORM pg_notify('buddy_preferences_updated',
#     json_build_object('user_id', NEW.user_id, 'role', 'buddy',
#       'items', NEW.interests)::text);
#   RETURN NEW;
# END; $$;
# DROP TRIGGER IF EXISTS trg_buddy_preferences ON buddy_info;
# CREATE TRIGGER trg_buddy_preferences
#   AFTER INSERT OR UPDATE OF interests ON buddy_info
#   FOR EACH ROW EXECUTE FUNCTION notify_buddy_preferences();

# ── BuddyTopicLog ─────────────────────────────────────────────────────────────
# CREATE OR REPLACE FUNCTION notify_buddy_topic() RETURNS TRIGGER LANGUAGE plpgsql AS $$
# BEGIN
#   PERFORM pg_notify('buddy_topic_inserted',
#     json_build_object('user_id', NEW.user_id, 'role', 'buddy',
#       'items', ARRAY[NEW.topic])::text);
#   RETURN NEW;
# END; $$;
# DROP TRIGGER IF EXISTS trg_buddy_topic ON buddy_topics_log;
# CREATE TRIGGER trg_buddy_topic
#   AFTER INSERT ON buddy_topics_log
#   FOR EACH ROW EXECUTE FUNCTION notify_buddy_topic();
