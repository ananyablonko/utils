import __init__
import numpy as np

from ds.circular_buffer import CircularBuffer

def test_basic_read_write():
    buffer = CircularBuffer(np.empty(5, dtype=np.int32))
    
    buffer.write(np.array([1, 2, 3]))
    assert buffer.count == 3
    
    data = buffer.read(2)
    assert np.array_equal(data, np.array([1, 2]))
    assert buffer.count == 1
    
    buffer.write(np.array([4, 5]))
    assert buffer.count == 3
    
    data = buffer.read(3)
    assert np.array_equal(data, np.array([3, 4, 5]))
    assert buffer.count == 0

def test_wraparound():
    buffer = CircularBuffer(np.empty(4, dtype=np.int32))
    
    buffer.write(np.array([1, 2, 3]))
    buffer.read(2)
    buffer.write(np.array([4, 5, 6]))
    assert buffer.count == 4
    
    data = buffer.read(4)
    assert np.array_equal(data, np.array([3, 4, 5, 6]))
    assert buffer.count == 0


def main() -> None:
    test_basic_read_write()
    test_wraparound()


if __name__ == '__main__':
    main()