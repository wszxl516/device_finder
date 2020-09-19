#!/bin/python
from collections import namedtuple
import ctypes
import os
from kbd import DisableEcho
event = {
    'Left': 0x1,
    'Middle': 0x4,
    'Right': 0x2
}


class Position(ctypes.Structure):
    _fields_ = [
        ('x', ctypes.c_int8),
        ('y', ctypes.c_int8)
    ]


class MiceEvent(ctypes.Structure):
    _fields_ = [
        ('button', ctypes.c_uint8),
        ('position', Position)
    ]


class Mice:
    KeyEvent = namedtuple('MiceEvent', ('left', 'middle', 'right', 'x', 'y'))
    buffer_size = ctypes.sizeof(MiceEvent)

    def __init__(self, _path, disable_echo=True):
        self.fd = None
        self.fd = os.open(_path, os.O_RDONLY)
        self.disable_echo = DisableEcho() if disable_echo else None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__del__()

    def __del__(self):
        if self.disable_echo is not None:
            self.disable_echo.restore()
        try:
            if self.fd is not None:
                os.close(self.fd)
        except OSError:
            pass

    def raw(self):
        buffer = os.read(self.fd, self.buffer_size)
        mice_event = MiceEvent.from_buffer_copy(buffer)
        return self.KeyEvent(mice_event.button & event.get('Left') > 0,
                             mice_event.button & event.get('Middle') > 0,
                             mice_event.button & event.get('Right') > 0,
                             mice_event.position.x,
                             mice_event.position.y)

    def loop(self):
        while True:
            try:
                yield self.raw()
            except KeyboardInterrupt:
                break


if __name__ == '__main__':
    m = Mice('/dev/input/mouse0')
    for e in m.loop():
        print(e)
