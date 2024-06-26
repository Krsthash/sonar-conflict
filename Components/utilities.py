import colorsys
import math
import random
import tkinter
import time
from tkinter import filedialog

import pygame


def random_int(low, high):
    return math.floor((high - low + 1) * random.random()) + low


def prompt_file():
    """Create a Tk file dialog and cleanup when finished"""
    top = tkinter.Tk()
    top.withdraw()  # hide window
    file_name = tkinter.filedialog.askopenfilename(parent=top)
    top.destroy()
    return file_name


def hex_to_rgb(hex_code):
    rgb = []
    for i in (0, 2, 4):
        decimal = int(hex_code[i: i + 2], 16)
        rgb.append(decimal)

    return tuple(rgb)


def darken(amount, color):
    if amount <= 1:
        return "#000000"
    darkened_color = colorsys.rgb_to_hls(*hex_to_rgb(color[1:]))
    darkened_color = (
        darkened_color[0],
        darkened_color[1] - (darkened_color[1] / amount),
        darkened_color[2],
    )
    darkened_color = colorsys.hls_to_rgb(*darkened_color)
    darkened_color = "#%02x%02x%02x" % tuple(
        int(value) for value in darkened_color
    )
    return darkened_color


def calculate_azimuth(rel_x, rel_y, distance):
    if rel_x == 0:
        if rel_y < 0:
            angle = 0
        else:
            angle = 180
    else:
        angle = math.degrees(math.asin(rel_y / distance))
        if rel_x < 0 and rel_y > 0:
            angle = 90 + (90 - angle)
        elif rel_x < 0 and rel_y < 0:
            angle = -180 + (angle * -1)
        if -90 <= angle <= 0:
            angle += 90
        elif 0 < angle <= 90:
            angle += 90
        elif -90 > angle >= -180:
            angle += 90
        else:
            angle = -90 - (180 - angle)
    if angle < 0:
        angle += 360
    return angle


def mid_rect(rect, txtsurf, concatenate_surf=None, end_text=False):
    """
    Helper function to calculate the middle point of a Rect object and
    calculate the coordinates for placing a centered text inside of it.
    :param concatenate_surf: Text surface that you want to concatenate.
    :param end_text: Set this to true if you want the coordinates of the second surface when concatenating.
    """
    if concatenate_surf and not end_text:
        return ((rect[0] + (rect[2] / 2 - (txtsurf.get_width() + concatenate_surf.get_width()) / 2)),
                (rect[1] + (rect[3] / 2 - txtsurf.get_height() / 2)))

    elif concatenate_surf and end_text:
        return (
            rect[0] + ((rect[2] / 2 - (
                    (txtsurf.get_width() + concatenate_surf.get_width()) / 2) + concatenate_surf.get_width())),
            (rect[1] + (rect[3] / 2 - txtsurf.get_height() / 2)))
    else:
        return ((rect[0] + (rect[2] / 2 - txtsurf.get_width() / 2)),
                (rect[1] + (rect[3] / 2 - txtsurf.get_height() / 2)))


def fade_out(sound, duration, fps, start_volume=None, end_volume=0):
    frequency = 1/fps
    if start_volume is None:
        start_volume = sound.get_volume()
    else:
        sound.set_volume(start_volume)
    volume_change = (end_volume - start_volume) / ((duration / 1000) / frequency)
    interval = ((duration / 1000) / frequency)
    return volume_change, interval