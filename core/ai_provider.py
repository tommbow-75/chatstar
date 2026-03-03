import json
import io
import base64
from abc import ABC, abstractmethod
from typing import List
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
    def analyze_chat_image(self, image: Image.Image) -> List[str]:
        """
        接收對話視窗截圖，回傳 3 種回覆建議字串列表。
        """
        raise NotImplementedError

# ────────────────────── Gemini 實作 ──────────────────────

SYSTEM_PROMPT = """\
你是一位貼心的社交助手，專門幫助使用者回覆通訊軟體（如 LINE、Telegram）的訊息。

我會傳給你一張聊天視窗的截圖。截圖中：
- 靠左的訊息泡泡（通常是白色底）是【對方】說的話
- 靠右的訊息泡泡（通常是綠色底或帶有「已讀」標示）是【我】說的話

請根據最新的對話內容，生成 3 種不同風格的繁體中文回覆建議：
1. 「正式」—有禮貌、措辭得體
2. 「輕鬆」—幽默、友善、口語化
3. 「簡短」—一句話、直接有力

嚴格以 JSON 格式回覆，不要有任何額外文字或 markdown 代碼區塊：
{"formal": "...", "casual": "...", "brief": "..."}
"""

class GeminiProvider(BaseAIProvider):
    def __init__(self, api_key: str, model: str = "gemini-flash-lite-latest"):
        if not GENAI_AVAILABLE:
            raise ImportError("請執行 `uv add google-genai` 安裝 Gemini SDK")
        self.client = genai.Client(api_key=api_key)
        self.model = model

    # 送圖前壓縮設定
    # Gemini 圖片 Token 量正比於解析度（tiles），縮小可節省大量 Token
    MAX_EDGE = 768      # 長邊上限（px）；可依需求調高，但 768 已足夠閱讀文字
    JPEG_QUALITY = 85   # JPEG 品質（80-90 為文字辨識的最佳平衡點）

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


    def analyze_chat_image(self, image: Image.Image) -> List[str]:
        """
        傳送圖像給 Gemini，解析回傳的 JSON 並取得三種回覆建議。
        透過 response_mime_type 強制模型回傳 JSON，提高穩定性。
        """
        img_bytes = self._image_to_bytes(image)

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"),
                    SYSTEM_PROMPT,
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                )
            )
        except Exception as e:
            raise RuntimeError(f"Gemini API 呼叫失敗：{e}") from e

        raw = (response.text or "").strip()
        print(f"[Gemini 原始回覆] {raw[:200]}")  # 除錯用

        if not raw:
            raise ValueError("Gemini 回傳了空回覆。請確認模型名稱與 API Key 是否正確。")

        # 清理可能的 markdown 包裝
        if raw.startswith("```"):
            parts = raw.split("```")
            raw = parts[1] if len(parts) > 1 else raw
            if raw.lower().startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(f"無法解析 Gemini 回覆的 JSON：{e}\n原始內容：{raw[:300]}") from e

        return [
            data.get("formal", "（無正式回覆）"),
            data.get("casual", "（無輕鬆回覆）"),
            data.get("brief",  "（無簡短回覆）"),
        ]

