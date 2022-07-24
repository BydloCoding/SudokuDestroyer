class Rect():
    __slots__ = "x", "y", "x2", "y2", "w", "h"

    def __init__(self, x, y, x2, y2) -> None:
        self.x = x
        self.y = y
        self.x2 = x2
        self.y2 = y2
        self.w = x2 - x
        self.h = y2 - y

    def to_pyautogui(self):
        return (self.x, self.y, self.w, self.h)
