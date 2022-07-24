from math import sqrt


GRID_SEP = (112, 112, 112)
GRID_CELL = (234, 234, 234)
GRID_CELL_SELECTED = (255, 246, 180)
GRID_SEP_BATTLE = (163, 160, 136)

CELL = GRID_CELL_SELECTED, GRID_CELL, (250, 250, 250)
GRID_SEP_ALL = GRID_SEP, GRID_SEP_BATTLE, (156, 156, 156), (161, 161, 161)


def color_dist(rgb1, rgb2):
    rmean = 0.5*(rgb1[0]+rgb2[0])
    r = rgb1[0] - rgb2[0]
    g = rgb1[1] - rgb2[1]
    b = rgb1[2] - rgb2[2]
    d = sqrt((int((512+rmean)*r*r) >> 8) + 4*g*g + (int((767-rmean)*b*b) >> 8))
    return int(d)
