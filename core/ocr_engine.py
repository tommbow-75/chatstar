import pytesseract
from PIL import Image, ImageEnhance, ImageOps
from dataclasses import dataclass, field
from typing import List, Tuple, Dict

@dataclass
class ChatMessage:
    speaker: str  # "我" 或 "對方"
    text: str

@dataclass
class StructuredChat:
    messages: List[ChatMessage] = field(default_factory=list)

    def __str__(self):
        lines = []
        for msg in self.messages:
            prefix = "【我】   " if msg.speaker == "我" else "【對方】"
            lines.append(f"{prefix}：{msg.text}")
        return "\n".join(lines)

    def has_new_content(self, other: "StructuredChat") -> bool:
        return str(self) != str(other)


class BaseOCREngine:
    def extract_text(self, image: Image.Image) -> str:
        raise NotImplementedError

    def extract_structured(self, image: Image.Image) -> StructuredChat:
        raise NotImplementedError


class TesseractOCREngine(BaseOCREngine):
    def __init__(self, tesseract_cmd=None, threshold: float = 0.5):
        """
        threshold: 文字區塊中心 X / 圖片寬度 的閾值
                   >= threshold → 我方（右側）
                   <  threshold → 對方（左側）
        """
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        self.threshold = threshold

    def _preprocess_normal(self, image: Image.Image) -> Image.Image:
        """
        正常前處理：用於「深色文字 + 淺色/白色底」的泡泡（對方訊息）
        """
        w, h = image.size
        image = image.resize((w * 2, h * 2), Image.LANCZOS)
        image = image.convert("L")
        image = ImageEnhance.Contrast(image).enhance(2.0)
        return image

    def _preprocess_inverted(self, image: Image.Image) -> Image.Image:
        """
        反轉前處理：用於「白色文字 + 深色/綠色底」的泡泡（LINE 我方訊息）
        反轉像素後白字→黑字，綠底→紫底，Tesseract 大幅提升辨識率
        """
        w, h = image.size
        image = image.resize((w * 2, h * 2), Image.LANCZOS)
        image = image.convert("L")
        image = ImageOps.invert(image)            # 白字→黑字
        image = ImageEnhance.Contrast(image).enhance(2.0)
        return image

    def _run_ocr_dict(self, image: Image.Image) -> dict:
        """對前處理後的影像執行 OCR，回傳 DICT 結果。"""
        try:
            return pytesseract.image_to_data(
                image,
                lang='chi_tra+eng',
                output_type=pytesseract.Output.DICT
            )
        except Exception as e:
            print(f"OCR Error: {e}")
            return {}

    def _parse_lines(self, data: dict, img_width: int) -> List[Tuple]:
        """
        從 OCR DICT 解析出各行的 (key, center_x, text) 列表。
        key = (block_num, par_num, line_num)
        """
        n = len(data.get('text', []))
        lines: Dict = {}

        for i in range(n):
            text = str(data['text'][i]).strip()
            if not text:
                continue
            try:
                conf = float(data['conf'][i])
            except (ValueError, TypeError):
                conf = -1
            if conf < -1:
                continue

            key = (data['block_num'][i], data['par_num'][i], data['line_num'][i])
            left = data['left'][i]
            width = data['width'][i]
            lines.setdefault(key, []).append((left, width, text))

        result = []
        for key in sorted(lines.keys()):
            items = lines[key]
            line_text = " ".join(t for _, _, t in items).strip()
            if not line_text:
                continue
            min_left = min(left for left, _, _ in items)
            max_right = max(left + w for left, w, _ in items)
            center_x = (min_left + max_right) / 2
            result.append((key, center_x / img_width, line_text))

        return result

    def extract_text(self, image: Image.Image) -> str:
        try:
            proc = self._preprocess_normal(image)
            return pytesseract.image_to_string(proc, lang='chi_tra+eng').strip()
        except Exception as e:
            print(f"OCR Error: {e}")
            return ""

    def extract_structured(self, image: Image.Image) -> StructuredChat:
        """
        雙重 OCR 策略：
        1. 正常前處理（高對比灰階）→ 辨識深色文字（對方的白底黑字）
        2. 反轉前處理             → 辨識白色文字（我方的綠底白字）
        
        合併兩次結果：
        - Pass 1 辨識到的行 → 篩選出靠左的（對方）
        - Pass 2 辨識到的行 → 篩選出靠右的（我方）
        
        這樣可以分別對最適合的底色做辨識，不互相干擾。
        """
        chat = StructuredChat()
        threshold = self.threshold

        proc_normal = self._preprocess_normal(image)
        proc_invert = self._preprocess_inverted(image)
        w = proc_normal.width  # 2x 放大後的寬度

        data_normal = self._run_ocr_dict(proc_normal)
        data_invert = self._run_ocr_dict(proc_invert)

        lines_normal = self._parse_lines(data_normal, w)
        lines_invert = self._parse_lines(data_invert, w)

        # 從正常版取對方訊息（靠左）
        other_lines = [(key, cx, txt) for key, cx, txt in lines_normal if cx < threshold]
        # 從反轉版取我方訊息（靠右）
        my_lines = [(key, cx, txt) for key, cx, txt in lines_invert if cx >= threshold]

        # 合併並按 key（行位置）排序
        all_lines = [(key, "對方", txt) for key, cx, txt in other_lines] + \
                    [(key, "我", txt) for key, cx, txt in my_lines]
        all_lines.sort(key=lambda x: x[0])

        if not all_lines:
            return chat

        # 合併相鄰且說話者相同的行
        current_speaker = all_lines[0][1]
        current_text = all_lines[0][2]

        for _, speaker, text in all_lines[1:]:
            if speaker == current_speaker:
                current_text += " " + text
            else:
                if current_text.strip():
                    chat.messages.append(ChatMessage(speaker=current_speaker, text=current_text.strip()))
                current_speaker = speaker
                current_text = text

        if current_text.strip():
            chat.messages.append(ChatMessage(speaker=current_speaker, text=current_text.strip()))

        return chat
