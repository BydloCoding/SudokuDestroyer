from vk_sdk.thread import every
from pyautogui import locateOnScreen, center, click
from time import sleep
import os

@every(5)
def scan():
    loc1 = locateOnScreen("numbers/btn1.png", confidence = 0.8)
    if loc1 is not None:
        click(center(loc1))
    loc2 = locateOnScreen("numbers/btn2.png", confidence = 0.8)
    if loc2 is not None:
        click(center(loc2))
        sleep(3)
        os.system("py main.py")
    