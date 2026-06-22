from collections import deque


class History:
    """固定長リングバッファ。スパークライン描画用に直近値を保持する。"""
    def __init__(self, capacity: int):
        self._buf = deque(maxlen=capacity)

    def push(self, value: float) -> None:
        self._buf.append(float(value))

    def values(self) -> list:
        return list(self._buf)

    def __len__(self) -> int:
        return len(self._buf)