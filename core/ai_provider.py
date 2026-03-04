import json
import io
from abc import ABC, abstractmethod
from typing import List, Optional
from PIL import Image

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

# ────────────────────── 抽象介面 ──────────────────────

class BaseAIProvider(ABC):
    @abstractmethod
    def analyze_chat_image(self, image: Image.Image, context: str = "") -> List[str]:
        """
        接收對話視窗截圖與對話背景，回傳 3 種回覆建議字串列表。
        """
        raise NotImplementedError

    @abstractmethod
    def extract_all_messages(self, image: Image.Image) -> List[str]:
        """首次截圖：提取畫面中所有對話訊息，由舊到新排列。"""
        raise NotImplementedError

    @abstractmethod
    def extract_latest_message(self, image: Image.Image) -> str:
        """後續截圖：只提取畫面中最後一則（最新）訊息。"""
        raise NotImplementedError


# ────────────────────── Prompts ──────────────────────

# 全量提取：首次框選時使用，擷取畫面中所有訊息
# ⚠️ 由下往上提取：確保即使模型提早停止，最新訊息也已被記錄
EXTRACT_ALL_PROMPT = """\
這是一張 LINE 聊天視窗的截圖。請依照以下步驟處理：

步驟一：定位畫面最下方（最新）的訊息泡泡作為起點。

步驟二：從最下方往上，逐一列出每一個訊息泡泡：
- 靠左的泡泡（白色/灰色底，對方頭像在左側）→ 格式：「對方：文字內容」
- 靠右的泡泡（綠色底，靠右對齊）→ 格式：「我：文字內容」
- 貼圖、表情包、圖片 → 格式：「對方：[貼圖]」或「我：[貼圖]」
- 每一個泡泡都必須輸出，不論多短（包含「ok」、「喔」等單字）

步驟三：以 JSON 格式輸出，messages 陣列中第一個元素是最新訊息，最後一個是最舊訊息：

只輸出 JSON，不要輸出思考過程：
{"messages": ["我：我在裡面了", "我：ok", "對方：沒關係 我有車", "對方：你好嗎"]}
"""


# 增量提取：後續截圖時使用，只需要最新一則
EXTRACT_LATEST_PROMPT = """\
請看這張聊天視窗截圖，找出畫面中最下方（最新）的那一則訊息。

規則：
- 靠左的訊息（白色底）= 對方說的，格式為「對方：訊息內容」
- 靠右的訊息（綠色底）= 我說的，格式為「我：訊息內容」

嚴格以 JSON 格式回覆，不要有任何額外文字：
{"latest": "對方：那明天見！"}
"""

# 回覆建議生成：帶入對話背景 context 後使用
SUGGEST_SYSTEM_PROMPT = """\
你是一位貼心的社交助手，專門幫助使用者回覆通訊軟體（如 LINE、Telegram）的訊息。

我會傳給你一張聊天視窗的截圖。截圖中：
- 靠左的訊息泡泡（通常是白色底）是【對方】說的話
- 靠右的訊息泡泡（通常是綠色底）是【我】說的話

{long_term_section}

{context_section}

請根據以上背景與截圖中最新的對話內容，生成 3 種不同風格的繁體中文回覆建議：
1. 「正式」—有禮貌、措辭得體
2. 「輕鬆」—幽默、友善、口語化
3. 「簡短」—一句話、直接有力

嚴格以 JSON 格式回覆，不要有任何額外文字或 markdown 代碼區塊：
{{"formal": "...", "casual": "...", "brief": "..."}}
"""


# ────────────────────── Gemini 實作 ──────────────────────

class GeminiProvider(BaseAIProvider):
    # 送圖前壓縮設定
    # Gemini 圖片 Token 量正比於解析度（tiles），縮小可節省大量 Token
    MAX_EDGE = 1024     # 長邊上限（px）；1024 在 Token 與文字辨識清晰度間取得較佳平衡
    JPEG_QUALITY = 85   # JPEG 品質（80-90 為文字辨識的最佳平衡點）

    def __init__(self, api_key: str, model: str = "gemini-flash-latest"):
        if not GENAI_AVAILABLE:
            raise ImportError("請執行 `uv add google-genai` 安裝 Gemini SDK")
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def _image_to_bytes(self, image: Image.Image) -> bytes:
        """
        壓縮圖片後轉為 bytes：
        1. 等比縮放，長邊限制在 MAX_EDGE px
        2. 輸出 JPEG（比 PNG 小 5-10x），對文字辨識影響極小
        """
        w, h = image.size
        max_edge = max(w, h)
        if max_edge > self.MAX_EDGE:
            scale = self.MAX_EDGE / max_edge
            image = image.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

        buf = io.BytesIO()
        image.convert("RGB").save(buf, format="JPEG", quality=self.JPEG_QUALITY, optimize=True)
        compressed = buf.getvalue()
        print(f"[圖片大小] {w}×{h} → {image.width}×{image.height}  {len(compressed)//1024} KB")
        return compressed


    def _call_gemini(self, image: Image.Image, prompt: str) -> str:
        """共用的 Gemini API 呼叫，回傳清理後的原始文字。"""
        img_bytes = self._image_to_bytes(image)
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"),
                    prompt,
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                )
            )
        except Exception as e:
            raise RuntimeError(f"Gemini API 呼叫失敗：{e}") from e

        raw = (response.text or "").strip()
        print(f"[Gemini 回覆] {raw[:200]}")

        if not raw:
            raise ValueError("Gemini 回傳了空回覆。請確認模型名稱與 API Key 是否正確。")

        # 清理可能的 markdown 包裝
        if raw.startswith("```"):
            parts = raw.split("```")
            raw = parts[1] if len(parts) > 1 else raw
            if raw.lower().startswith("json"):
                raw = raw[4:]
        return raw.strip()

    # ──────────── 提取方法（記憶系統用）────────────

    def extract_all_messages(self, image: Image.Image) -> List[str]:
        """首次截圖全量提取：回傳所有訊息字串列表。"""
        raw = self._call_gemini(image, EXTRACT_ALL_PROMPT)
        try:
            data = json.loads(raw)
            messages = data.get("messages", [])
            print(f"[全量提取] 共 {len(messages)} 則訊息")
            return [m for m in messages if isinstance(m, str) and m.strip()]
        except json.JSONDecodeError as e:
            print(f"[全量提取] JSON 解析失敗：{e}，回傳空列表")
            return []

    def extract_latest_message(self, image: Image.Image) -> str:
        """後續截圖增量提取：只回傳最新一則訊息字串。"""
        raw = self._call_gemini(image, EXTRACT_LATEST_PROMPT)
        try:
            data = json.loads(raw)
            latest = data.get("latest", "")
            print(f"[增量提取] 最新訊息：{latest[:60]}")
            return latest if isinstance(latest, str) else ""
        except json.JSONDecodeError as e:
            print(f"[增量提取] JSON 解析失敗：{e}，回傳空字串")
            return ""

    # ──────────── 建議生成方法 ────────────

    def analyze_chat_image(
        self,
        image: Image.Image,
        context: str = "",
        long_term_context: str = "",
    ) -> List[str]:
        """
        傳送圖像（加上對話背景）給 Gemini，回傳 3 種回覆建議。

        Parameters
        ----------
        context : str
            短期記憶：由 MemoryManager.get_context_prompt() 提供的近期 8 則對話。
        long_term_context : str
            長期記憶：由 Pinecone search_service 查詢的相關資訊。
            若為空字串，則此區塊不顯示在 Prompt 中。
        """
        if long_term_context:
            long_term_section = (
                "【長期記憶】關於聊天對象的已知資訊（供參考）：\n"
                + long_term_context
            )
        else:
            long_term_section = ""

        if context:
            context_section = context
        else:
            context_section = "（無對話背景記錄）"

        prompt = SUGGEST_SYSTEM_PROMPT.format(
            long_term_section=long_term_section,
            context_section=context_section,
        )
        raw = self._call_gemini(image, prompt)

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(f"無法解析 Gemini 回覆的 JSON：{e}\n原始內容：{raw[:300]}") from e

        return [
            data.get("formal", "（無正式回覆）"),
            data.get("casual", "（無輕鬆回覆）"),
            data.get("brief",  "（無簡短回覆）"),
        ]
