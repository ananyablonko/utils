import webrtcvad
import collections
from pydantic import BaseModel, computed_field, Field
from typing import Deque, Any, Optional, Literal


class VAD(BaseModel):
    aggressiveness: Literal[1, 2, 3, 4]
    frame_ms: Literal[10, 20, 30] = 30
    sample_rate: Literal[8000, 16000, 32000, 48000] = 16_000
    window_size: int = 100

    def model_post_init(self, context: Any) -> None:
        super().model_post_init(context)
        self._vad = webrtcvad.Vad(self.aggressiveness)
        self._is_voiced_tracking: Deque[bool] = collections.deque(maxlen=self.window_size)
        self._input: Deque[bytes] = collections.deque(maxlen=self.window_size)

        self._is_voiced_tracking.extend([False] * self.window_size)
        self._input.append(b"\0\0")

        self._voiced_total: int = 0
        self._unvoiced_total: int = 0

    @computed_field
    @property
    def frame_size(self) -> int:
        return int(self.sample_rate * self.frame_ms / 1000) * 2

    @property
    def triggered(self) -> bool:
        return self._voiced_total > 0 or self._unvoiced_total < (self.window_size / 4)

    def is_speech(self, audio: bytes) -> bool:
        if not any(audio):
            return False
        
        for i in range(0, len(audio), self.frame_size):
            chunk = audio[i:i+self.frame_size]
            frame = chunk + b"\0" * (self.frame_size - len(chunk))
            if self._vad.is_speech(frame, self.sample_rate):
                return True
        return False

    def process(self, audio: bytes) -> Optional[bytes]:
        is_speech = self.is_speech(audio)
        
        was_speech = self._is_voiced_tracking[0]
        self._voiced_total += is_speech - was_speech
        self._is_voiced_tracking.append(is_speech)

        res = None
        if self.triggered:
            # print("+" if is_speech else "-", end="")
            res = self._input.popleft()
            self._unvoiced_total = 0 if was_speech else self._unvoiced_total + 1

            
        self._input.append(audio)
        return res
