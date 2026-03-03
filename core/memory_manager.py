from collections import deque


class MemoryManager:
    """
    管理對話工作記憶（Working Memory）。

    策略：
    - 首次啟動：全量提取截圖中所有訊息，填充 buffer
    - 後續更新：只提取最新一則，去重後 append
    - 重新框選：呼叫 reset()，清空 buffer 並重置狀態
    """

    def __init__(self, max_window: int = 8):
        """
        max_window: 保留最近幾則訊息做為 context 注入（預設 8）
        """
        self._buffer: deque[str] = deque(maxlen=max_window)
        self.is_initialized: bool = False  # False 代表需要做一次全量提取

    # ──────────────────── 狀態操作 ────────────────────

    def reset(self) -> None:
        """重新框選時呼叫：清空記憶，下次 scan 回到全量提取模式。"""
        self._buffer.clear()
        self.is_initialized = False
        print("[MemoryManager] 記憶已清空，等待下次全量提取")

    # ──────────────────── 寫入操作 ────────────────────

    def add_messages(self, messages: list[str]) -> None:
        """
        全量填充（首次初始化用）。
        注意：EXTRACT_ALL_PROMPT 回傳「最新→最舊」順序，
        此處自動 reverse 為「由舊到新」再存入 buffer。
        """
        self._buffer.clear()
        for msg in reversed(messages):   # ← reverse 回正確時序
            if msg and msg.strip():
                self._buffer.append(msg.strip())
        self.is_initialized = True
        print(f"[MemoryManager] 全量初始化完成，共 {len(self._buffer)} 則，最新：{list(self._buffer)[-1][:40] if self._buffer else '(空)'}")


    def add_latest(self, message: str) -> bool:
        """
        增量 append（後續更新用）。
        若新訊息與 buffer 最後一則相同，則跳過（去重）。
        回傳 True 代表確實新增了，False 代表重複跳過。
        """
        message = message.strip()
        if not message:
            return False

        if self._buffer and self._buffer[-1] == message:
            print(f"[MemoryManager] 重複訊息，跳過：{message[:40]}")
            return False

        self._buffer.append(message)
        print(f"[MemoryManager] 新增訊息：{message[:60]}")
        return True

    # ──────────────────── 讀取操作 ────────────────────

    def get_context_prompt(self) -> str:
        """
        將 buffer 組成注入 Prompt 的純文字區塊。
        若 buffer 為空則回傳空字串。
        """
        if not self._buffer:
            return ""

        lines = "\n".join(f"  {msg}" for msg in self._buffer)
        return f"以下是截圖視窗中最近的對話紀錄（由舊到新）：\n{lines}\n"

    def __len__(self) -> int:
        return len(self._buffer)

    def __repr__(self) -> str:
        return f"MemoryManager(initialized={self.is_initialized}, messages={len(self._buffer)})"
