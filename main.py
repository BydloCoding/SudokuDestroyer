from random import choice
from time import sleep, time
import sudoku
import ctypes
from rect import Rect
from PIL import Image
import pyautogui
import ctypes
from vk_sdk import thread
import colors
user32 = ctypes.windll.user32
screensize = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)


def GetWindowRectFromName(name: str) -> tuple:
    hwnd = ctypes.windll.user32.FindWindowW(0, name)
    rect = ctypes.wintypes.RECT()
    ctypes.windll.user32.GetWindowRect(hwnd, ctypes.pointer(rect))
    ctypes.windll.user32.SetForegroundWindow(hwnd)
    ctypes.windll.user32.ShowWindow(hwnd, 9)
    return Rect(rect.left, rect.top, rect.right, rect.bottom)


class Locater(object):
    __slots__ = "locateImg", "onImg", "relative", "locate_kwargs", "click_kwargs", "result"

    def __init__(self, locateImg, onImg, relative=None, locate_kwargs=None, click_kwargs=None) -> None:
        self.locateImg = locateImg
        self.onImg = onImg
        self.relative = relative or Rect(0, 0, 0, 0)
        self.locate_kwargs = locate_kwargs or {}
        self.click_kwargs = click_kwargs or {}

    def do(self):
        loc = pyautogui.locate(
            self.locateImg, self.onImg, **self.locate_kwargs)
        if loc:
            loc = pyautogui.center(loc)
            pyautogui.click(self.relative.x + loc.x,
                            self.relative.y + loc.y, **self.click_kwargs)
            self.result = True
            return self
        self.result = False
        return self

    @classmethod
    def locate_and_click(cls, *args, **kwargs):
        return cls(*args, **kwargs).do()


class LocateRetry(object):
    __slots__ = "interval", "duration", "screenshot_function", "success_callback", "every", "locater", "start_time"

    def __init__(self, interval, duration, screenshot_function, success_callback, *args, **kwargs) -> None:
        self.duration = duration
        self.start_time = time()
        self.screenshot_function = screenshot_function
        self.locater = Locater(*args, **kwargs)
        self.success_callback = success_callback
        self.every = thread.every(interval)(self.retry)

    def retry(self):
        if time() - self.start_time > self.duration:
            self.every.stopped = True
            return

        self.locater.onImg = self.screenshot_function()
        self.locater.do()
        if self.locater.result:
            self.every.stopped = True
            self.success_callback()


class GameManager(object):
    window_name = "NoxPlayer"

    def find_hwnd(self):
        self.hwnd = ctypes.windll.user32.FindWindowW(0, self.window_name)
        if not self.hwnd:
            print("Process is not running!")
            sleep(5)
            self.find_hwnd()

    def get_rect(self):
        rect = ctypes.wintypes.RECT()
        ctypes.windll.user32.GetWindowRect(self.hwnd, ctypes.pointer(rect))
        self.rect = Rect(rect.left, rect.top, rect.right, rect.bottom)

    def show_window(self):
        ctypes.windll.user32.SetForegroundWindow(self.hwnd)
        ctypes.windll.user32.ShowWindow(self.hwnd, 9)

    def take_screenshot(self):
        self.game_area = pyautogui.screenshot(region=self.rect.to_pyautogui())
        self.pic = self.game_area.load()
        return self.game_area

    def __init__(self) -> None:
        self.imgs = [Image.open(f"images/{i}.png") for i in range(1, 10)]
        self.find_hwnd()
        self.get_rect()
        self.show_window()
        self.take_screenshot()
        self.set_game_state()
        if not self.in_game:
            self.run_game()
        else:
            self.mode = "custom"
            self.solve()

    def solve(self):
        self.take_screenshot()
        matrix = [[0 for _ in range(9)] for _ in range(9)]
        for i in range(100, self.rect.h):
            if self.pic[200, i] == colors.GRID_SEP:
                gridY = i
                break

        for i in range(0, self.rect.w):
            if self.pic[i, gridY] == colors.GRID_SEP:
                gridX = i
                break

        startX = 0
        shouldBind = False

        for i in range(gridX, self.rect.w):
            relY = gridY + 5
            pixel = self.pic[i, relY]
            if pixel in colors.CELL or colors.color_dist(pixel, colors.GRID_CELL) < 100:
                if not startX:
                    startX = i
                if shouldBind:
                    size = i - startX + 1
                    if size > 100:
                        size = size / 2
                    stepSizeX = size
                    stepSizeY = size
                    break
            elif startX and (pixel in colors.GRID_SEP_ALL or colors.color_dist(colors.GRID_SEP_BATTLE, pixel) < 200) and not shouldBind:
                shouldBind = True

        buttons = {}
        for i in range(1, 10):
            with Image.open(f"images/{i}_row.png") as f:
                loc = pyautogui.locate(f, self.game_area, confidence=0.9)
                if loc:
                    point = pyautogui.center(loc)
                    realPoint = (point.x + self.rect.x, point.y + self.rect.y)
                    buttons[i] = realPoint

        print("Step 2: grabbing matrix")

        positions = []
        for stepY in range(9):
            for stepX in range(9):
                x = gridX + stepSizeX * stepX
                y = gridY + stepSizeY * stepY
                crop = self.game_area.crop(
                    (x, y, x + stepSizeX, y + stepSizeY))
                crop.save("1.png")
                for digit in range(0, 9):
                    loc = pyautogui.locate(
                        self.imgs[digit], crop, grayscale=True, confidence=0.9)
                    if loc:
                        matrix[stepY][stepX] = digit + 1
                        break
                else:
                    positions.append((stepY, stepX))

        print("Grabbed matrix:\n")
        sudoku.print_board(matrix)
        print("Step 3: solving sudoku..\n")
        sudoku.solve(matrix)
        print("Sudoku was solved! Output:\n")
        sudoku.print_board(matrix)

        print("Step 4: solution")

        for position in positions:
            x = gridX + position[1] * stepSizeX
            y = gridY + position[0] * stepSizeY
            x1 = x + stepSizeX
            y1 = y + stepSizeY
            point = pyautogui.center(Rect(x, y, x1, y1).to_pyautogui())
            pyautogui.click(point.x + self.rect.x, point.y + self.rect.y)
            restored = matrix[position[0]][position[1]]
            if restored and (loc := buttons.get(restored)):
                pyautogui.click(loc)

        self.run_post_actions()

    def locate_and_click(self, image, **kwargs):
        return Locater.locate_and_click(image, self.game_area, self.rect, **kwargs)

    def locate_and_click_retry(self, interval, duration, success_callback, image, **kwargs):
        return LocateRetry(interval, duration, self.take_screenshot, success_callback, image, self.game_area, self.rect, **kwargs)

    def run_post_actions(self):
        match self.mode:
            case "battle" | "battle_master":
                self.locate_and_click_retry(1, 5, self.run_game,
                                            'images/reject_battle.png', locate_kwargs={"confidence": 0.7, "grayscale": True})

    def attemp_find_grid(self):
        self.take_screenshot()
        gridY = -1
        gridX = -1
        for i in range(100, self.rect.h):
            if self.pic[200, i] == colors.GRID_SEP:
                gridY = i
                break

        if gridY < 0:
            return

        for i in range(0, self.rect.w):
            if self.pic[i, gridY] == colors.GRID_SEP:
                gridX = i
                break

        if gridX < 0:
            return

        self.every_checker.stopped = True

        sleep(2)
        self.solve()

    def post_run_game(self):
        match self.mode:
            case "battle":
                loc = self.locate_and_click(
                    'images/battle_regular.png', locate_kwargs={"confidence": 0.8, "grayscale": True})
            case "battle_master":
                loc = self.locate_and_click(
                    'images/battle_master.png', locate_kwargs={"confidence": 0.8, "grayscale": True})

        sleep(2)
        self.take_screenshot()
        popup = self.locate_and_click('images/popup.png', locate_kwargs={
                                      "confidence": 0.7, "grayscale": True}, click_kwargs={"clicks": 5})
        if popup.result:
            self.locate_and_click(
                'images/popup_close.png', locate_kwargs={"confidence": 0.8, "grayscale": True})
            sleep(0.3)
            loc.do()

        self.every_checker = thread.every(1)(self.attemp_find_grid)

    def run_game(self):
        self.mode = choice(["battle_master"])
        print(f"I have decided to play {self.mode}")

        match self.mode:
            case "battle" | "battle_master":
                self.locate_and_click_retry(1, 5, self.post_run_game,
                                            'images/battle.png', locate_kwargs={"confidence": 0.8, "grayscale": True})
                sleep(0.5)

    # initial
    def set_game_state(self):
        # battle mode
        loc = pyautogui.locate(
            'images/info.png', self.game_area, confidence=0.8)
        # main page + daily
        loc2 = pyautogui.locate(
            'images/title.png', self.game_area, confidence=0.8)
        self.in_game = loc is None and loc2 is None


GameManager()
