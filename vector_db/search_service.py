"""
search_service.py
=================
Pinecone 語意搜尋模組（RAG 長期記憶檢索）。

使用方式
--------
    from vector_db.search_service import search_long_term_context

    context_text = search_long_term_context(
        user_id="u_001",
        partner_name="小美",
        query="最近有沒有看什麼好電影",
        top_k=5,
    )
    # context_text 為格式化字串，可直接塞入 Gemini Prompt
"""

import logging
import os

from dotenv import load_dotenv
from pinecone import Pinecone

# ── 環境設定 ────────────────────────────────────────────────────────────────

load_dotenv()

PINECONE_API_KEY = os.environ["PINECONE_API_KEY"]
PINECONE_INDEX   = os.getenv("PINECONE_INDEX", "chatstar")

logger = logging.getLogger(__name__)

# ── Pinecone 客戶端（惰性初始化） ──────────────────────────────────────────

_pc: Pinecone | None = None
_index = None


def _get_index():
    global _pc, _index
    if _index is None:
        _pc    = Pinecone(api_key=PINECONE_API_KEY)
        _index = _pc.Index(PINECONE_INDEX)
    return _index


# ══════════════════════════════════════════════════════════════════════════════
# 公開 API
# ══════════════════════════════════════════════════════════════════════════════

def search_long_term_context(
    user_id: str,
    partner_name: str,
    query: str,
    top_k: int = 5,
) -> str:
    """
    對當前聊天對象的相關 Namespace 進行語意搜尋，
    回傳格式化字串供 Gemini Prompt 使用。

    搜尋範圍包含：
    - {user_id}_{partner}_buddy_prefs  （對象的興趣偏好）
    - {user_id}_{partner}_buddy_topics （和對象聊過的話題）
    - {user_id}_user_prefs             （使用者自己的偏好，輔助參考）

    Parameters
    ----------
    user_id : str
        目前登入的使用者 ID。
    partner_name : str
        當前聊天對象的名稱（對應 BuddyInfo.dmbuddy）。
    query : str
        用於語意搜尋的查詢文字（通常是當前最新的輸入訊息）。
    top_k : int
        總共取回的最相關結果數量（預設 5）。

    Returns
    -------
    str
        格式化的長期記憶文字，可直接塞入 Prompt。
        若查無相關資料，回傳空字串。
    """
    from vector_db.sync_service import ns_buddy_prefs, ns_buddy_topics, ns_user_prefs

    namespaces_to_search = [
        ns_buddy_prefs(user_id, partner_name),
        ns_buddy_topics(user_id, partner_name),
        ns_user_prefs(user_id),
    ]

    all_results: list[dict] = []

    idx = _get_index()

    for ns in namespaces_to_search:
        try:
            response = idx.search_records(
                namespace=ns,
                query={
                    "inputs": {"text": query},
                    "top_k": top_k,
                },
                fields=["text", "type", "partner"],
            )
            hits = response.get("result", {}).get("hits", [])
            for hit in hits:
                score  = hit.get("_score", 0)
                fields = hit.get("fields", {})
                text   = fields.get("text", "")
                if text and score > 0.5:   # 相似度門檻：0.5（cosine）
                    all_results.append({
                        "text":  text,
                        "score": score,
                        "type":  fields.get("type", ""),
                    })
        except Exception as e:
            logger.warning("Pinecone 搜尋失敗 (namespace=%s): %s", ns, e)

    if not all_results:
        return ""

    # 依相似度排序，去重，取前 top_k 筆
    all_results.sort(key=lambda x: x["score"], reverse=True)
    seen_texts: set[str] = set()
    unique_results: list[dict] = []
    for r in all_results:
        if r["text"] not in seen_texts:
            seen_texts.add(r["text"])
            unique_results.append(r)
        if len(unique_results) >= top_k:
            break

    # 格式化輸出
    lines = [f"・{r['text']}" for r in unique_results]
    context = "\n".join(lines)
    logger.info("📚 Pinecone 長期記憶：找到 %d 筆相關資訊", len(unique_results))
    return context
