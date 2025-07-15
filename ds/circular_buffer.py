import asyncio
import numpy as np

class CircularBuffer:
    def __init__(self, empty_buffer: np.ndarray) -> None:
        self.r = self.w = 0
        self.buf = empty_buffer
        self.size = empty_buffer.shape[0]
        self.count: int = 0
        self._space = asyncio.Condition()
    
    def read(self, n: int) -> np.ndarray:
        if n > self.count:
            n = self.count
        
        if self.r + n <= self.size:
            result = self.buf[self.r:self.r + n]
        else:
            first_part = self.buf[self.r:]
            second_part = self.buf[:n - len(first_part)]
            result = np.concatenate([first_part, second_part])
        
        self.r = (self.r + n) % self.size
        self.count -= n
        return result
    
    async def notify(self) -> None:
        async with self._space:
            self._space.notify_all()

    def write(self, data: np.ndarray) -> None:
        available_space = self.size - self.count
        if data.shape[0] > available_space:
            raise ValueError("Buffer is full!")
        self._write(data)
    
    async def try_write(self, data: np.ndarray) -> None:
        async with self._space:
            while data.shape[0] > self.size - self.count:
                await self._space.wait()
        self._write(data)
    
    def _write(self, data: np.ndarray) -> None:
        n = data.shape[0]

        if self.w + n <= self.size:
            self.buf[self.w:self.w + n] = data
        else:
            first_part_size = self.size - self.w
            self.buf[self.w:] = data[:first_part_size]
            self.buf[:n - first_part_size] = data[first_part_size:]
        
        self.count += n
        self.w = (self.w + n) % self.size
