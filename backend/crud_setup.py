"""backend/crud_setup.py — 設置嚮導專用的一次性寫入 helper。

將 username、preferences（JSONB）、topics 一次性儲存至資料庫，
並同步至 Pinecone 向量資料庫。
"""

from sqlalchemy.orm import Session
from .models import User, UserTopicLog


def create_user_with_setup(
    db: Session,
    user_id: str,
    username: str,
    preferences: list[str],
    topics: list[str],
) -> User:
    """
    建立新使用者，並同時寫入興趣（preferences JSONB）與話題記錄。

    :param db:          SQLAlchemy Session
    :param user_id:     使用者 ID（英數字，max 12）
    :param username:    顯示名稱
    :param preferences: 興趣列表，例如 ["音樂", "旅遊"]
    :param topics:      話題列表，例如 ["最近看了哆啦A夢", "打算去日本"]
    :return:            新建的 User ORM 物件
    """
    # 1. 建立 User（preferences 儲存為 JSONB 陣列）
    user = User(
        user_id=user_id,
        username=username,
        preferences=preferences,  # SQLAlchemy 會自動序列化 list → JSONB
    )
    db.add(user)
    db.flush()  # 先 flush 取得 user_id 以供外鍵使用，尚未 commit

    # 2. 批次新增話題記錄（保留物件參考，commit 後要 refresh 取得 SERIAL id）
    topic_objs = []
    for topic in topics:
        if not topic:
            continue
        obj = UserTopicLog(user_id=user_id, topic=topic)
        db.add(obj)
        topic_objs.append(obj)

    db.commit()
    db.refresh(user)
    for obj in topic_objs:
        db.refresh(obj)  # 取得資料庫 SERIAL 自動生成的 id

    # 3. 同步至 Pinecone（背景執行，不阻塞 UI）
    from .crud import _run_in_background, _sync_user_prefs, _sync_add_user_topic
    if preferences:
        _run_in_background(_sync_user_prefs, user_id, preferences)
    for obj in topic_objs:
        if obj.id is not None:
            _run_in_background(_sync_add_user_topic, user_id, obj.id, obj.topic)

    return user
