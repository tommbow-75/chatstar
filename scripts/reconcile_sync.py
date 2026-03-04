"""
reconcile_sync.py
=================
歷史資料對帳腳本：將 PostgreSQL 中的所有現有資料批量寫入 Pinecone。

使用情境
--------
1. **首次部署**：在整合 Pinecone 前就已有歷史資料的使用者，
   需要執行此腳本把舊資料補入 Pinecone。
2. **災難復原**：Pinecone 資料因意外被清空時，可重新全量同步。
3. **資料修復**：背景同步任務曾因網路中斷導致部分資料未寫入 Pinecone，
   執行此腳本補齊遺漏的向量。

執行方式
--------
    cd c:\\project\\github_push\\chatstar
    uv run python scripts/reconcile_sync.py

    # 只同步特定使用者
    uv run python scripts/reconcile_sync.py --user-id u_001

    # 乾跑模式（只顯示會寫入什麼，不實際寫入）
    uv run python scripts/reconcile_sync.py --dry-run
"""

import sys
import argparse
import logging
import os

# 確保能找到專案根目錄的模組
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from backend.database import SessionLocal
from backend import models
from vector_db.sync_service import (
    upsert_vectors, delete_namespace,
    ns_user_prefs, ns_user_topics, ns_buddy_prefs, ns_buddy_topics,
    build_user_pref_records, build_buddy_pref_records,
    build_user_topic_record, build_buddy_topic_record,
)

# ── 日誌設定 ────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# 各資料表的同步邏輯
# ══════════════════════════════════════════════════════════════════════════════

def sync_user_preferences(db, user: models.User, dry_run: bool) -> int:
    """同步特定使用者的 preferences 到 Pinecone。回傳寫入筆數。"""
    if not user.preferences:
        return 0
    records = build_user_pref_records(user.user_id, user.preferences)
    if not records:
        return 0
    ns = ns_user_prefs(user.user_id)
    if dry_run:
        logger.info("  [DRY-RUN] 會寫入 %d 筆 user_prefs → %s", len(records), ns)
        return len(records)
    delete_namespace(ns)
    upsert_vectors(ns, records)
    return len(records)


def sync_buddy_preferences(db, buddy: models.BuddyInfo, dry_run: bool) -> int:
    """同步特定聊天對象的 interests 到 Pinecone。回傳寫入筆數。"""
    if not buddy.interests:
        return 0
    records = build_buddy_pref_records(buddy.user_id, buddy.id, buddy.dmbuddy, buddy.interests)
    if not records:
        return 0
    ns = ns_buddy_prefs(buddy.user_id, buddy.dmbuddy)
    if dry_run:
        logger.info("  [DRY-RUN] 會寫入 %d 筆 buddy_prefs → %s", len(records), ns)
        return len(records)
    delete_namespace(ns)
    upsert_vectors(ns, records)
    return len(records)


def sync_user_topics(db, user_id: str, dry_run: bool) -> int:
    """同步特定使用者的所有 UserTopicLog 到 Pinecone。回傳寫入筆數。"""
    topics = db.query(models.UserTopicLog).filter(
        models.UserTopicLog.user_id == user_id
    ).all()
    if not topics:
        return 0

    records = []
    for t in topics:
        if t.id is None:
            logger.warning("  ⚠️ UserTopicLog (user=%s, topic=%s) 缺少 id，略過", user_id, t.topic[:30])
            continue
        records.append(build_user_topic_record(user_id, t.id, t.topic))

    if not records:
        return 0
    ns = ns_user_topics(user_id)
    if dry_run:
        logger.info("  [DRY-RUN] 會寫入 %d 筆 user_topics → %s", len(records), ns)
        return len(records)
    upsert_vectors(ns, records)
    return len(records)


def sync_buddy_topics(db, user_id: str, dmbuddy: str, dry_run: bool) -> int:
    """同步特定聊天對象的所有 BuddyTopicLog 到 Pinecone。回傳寫入筆數。"""
    topics = db.query(models.BuddyTopicLog).filter(
        models.BuddyTopicLog.user_id == user_id,
        models.BuddyTopicLog.dmbuddy == dmbuddy,
    ).all()
    if not topics:
        return 0

    records = []
    for t in topics:
        if t.id is None:
            logger.warning("  ⚠️ BuddyTopicLog (user=%s, buddy=%s) 缺少 id，略過", user_id, dmbuddy)
            continue
        records.append(build_buddy_topic_record(user_id, t.id, dmbuddy, t.topic))

    if not records:
        return 0
    ns = ns_buddy_topics(user_id, dmbuddy)
    if dry_run:
        logger.info("  [DRY-RUN] 會寫入 %d 筆 buddy_topics → %s", len(records), ns)
        return len(records)
    upsert_vectors(ns, records)
    return len(records)


# ══════════════════════════════════════════════════════════════════════════════
# 主流程
# ══════════════════════════════════════════════════════════════════════════════

def run_reconcile(target_user_id: str | None, dry_run: bool):
    db = SessionLocal()
    total_written = 0

    try:
        # 取得要同步的使用者列表
        query = db.query(models.User)
        if target_user_id:
            query = query.filter(models.User.user_id == target_user_id)
        users = query.all()

        if not users:
            logger.warning("找不到任何使用者資料，退出。")
            return

        logger.info("準備同步 %d 位使用者的資料到 Pinecone%s",
                    len(users), "（乾跑模式）" if dry_run else "")

        for user in users:
            logger.info("━━━ 使用者: %s (%s) ━━━", user.username, user.user_id)

            # 1. 使用者自身偏好
            n = sync_user_preferences(db, user, dry_run)
            logger.info("  user_prefs: %d 筆", n)
            total_written += n

            # 2. 使用者話題
            n = sync_user_topics(db, user.user_id, dry_run)
            logger.info("  user_topics: %d 筆", n)
            total_written += n

            # 3. 各聊天對象
            buddies = db.query(models.BuddyInfo).filter(
                models.BuddyInfo.user_id == user.user_id
            ).all()

            for buddy in buddies:
                logger.info("  ── 聊天對象: %s", buddy.dmbuddy)

                n = sync_buddy_preferences(db, buddy, dry_run)
                logger.info("     buddy_prefs: %d 筆", n)
                total_written += n

                n = sync_buddy_topics(db, user.user_id, buddy.dmbuddy, dry_run)
                logger.info("     buddy_topics: %d 筆", n)
                total_written += n

    finally:
        db.close()

    action = "會寫入" if dry_run else "已寫入"
    logger.info("=" * 50)
    logger.info("✅ 對帳完成！共%s %d 筆向量到 Pinecone。", action, total_written)


# ── 執行入口 ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ChatStar Pinecone 資料對帳腳本")
    parser.add_argument("--user-id", type=str, default=None, help="只同步特定使用者 ID（預設：同步全部）")
    parser.add_argument("--dry-run", action="store_true", help="乾跑模式：只顯示計畫，不實際寫入 Pinecone")
    args = parser.parse_args()

    run_reconcile(target_user_id=args.user_id, dry_run=args.dry_run)
