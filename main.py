import asyncio
import colorsys
import datetime
import json
import math
import os
import random
import string
import threading
import time
import tkinter
from tkinter import filedialog

import pygame
import pyperclip

import server_api


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


def mid_rect(rect, txtsurf):
    return ((rect[0] + (rect[2] / 2 - txtsurf.get_width() / 2)),
            (rect[1] + (rect[3] / 2 - txtsurf.get_height() / 2)))


class App:
    def __init__(self):
        self.LAUNCH_AUTH = [None, 0]
        self.CHEATS = False
        self.ENEMY_VISIBLE_AS = None
        self.ENEMY_SONAR = 0
        self.DEBUG = False
        self.max_sen = 0
        self.max_rec = 0
        self.ship_sync = 0
        self.designationP = None
        self.designationE = None
        self.starts_in = None
        self.NOTICE_QUEUE = []
        self.TARGETS_DESTROYED_ENEMY = 0
        self.SHIPS_DESTROYED_ENEMY = 0
        self.TARGETS_DESTROYED = 0
        self.SHIPS_DESTROYED = 0
        self.score_board_rect = None
        self.SCOREBOARD_OPEN = False
        self.ENEMY_SCORE = 0
        self.LOCAL_SCORE = 0
        self.LOSS_SCREEN = False
        self.WIN_SCREEN = False
        self.ENEMY_VISIBLE = False
        self.ERROR_DELAY = 0
        self.join_game_box = None
        self.JOIN_STATUS = 0
        self.GAME_CODE_VAR = [False, "Game code"]
        self.game_code_box = None
        self.copy_box = None
        self.must_update = False
        self.HOST_STATUS = 0
        self.GAME_CODE = None
        self.mission_name = None
        self.team_selected = 2
        self.pos = None
        self.back_box = None
        self.host_game_box = None
        self.usa_team_box = None
        self.random_team_box = None
        self.ru_team_box = None
        self.random_game_rect = None
        self.mission_name_box = None
        self.browse_game_rect = None
        self.JOIN_GAME_SCREEN = False
        self.HOST_GAME_SCREEN = False
        self.TARGET_DAMAGE_QUEUE = []
        self.SINK_QUEUE = []
        self.UPDATE_TORP_QUEUE = []
        self.FIRED_TORPEDOES = {}
        self.WEAPON_SCREEN = False
        self.FRIENDLY_TARGET_LOCATIONS = []
        self.ENEMY_TARGET_LOCATIONS = []
        self.HEALTH = 100
        self.TORPEDOES = {}
        self.DETECTION_CHANCE = 0.04
        self.ASM_FIRED = []
        self.LAM_FIRED = []
        self.range_indicator = 50
        self.reset_box = None
        self.passive_transfer_box = None
        self.active_transfer_box = None
        self.TRANSFER_CONTACT_INFO_A = False
        self.TRANSFER_CONTACT_INFO_P = False
        self.mode_var = -1
        self.depth_var = [False, ""]
        self.distance_var = [False, ""]
        self.bearing_var = [False, ""]
        self.fire_box = None
        self.change_mode_box = None
        self.depth_box = None
        self.distance_box = None
        self.bearing_box = None
        self.SELECTED_WEAPON = None
        self.FRIENDLY_PORT_LOCATIONS = []
        self.WEAPON_LAYOUT = {}
        self.PLAYER_ID = 1
        self.ACTIVE_SONAR_SELECTED_CONTACT = None
        self.identifying_delay = 0
        self.PASSIVE_SELECTED_CONTACT = None
        self.PASSIVE_SONAR_FREEZE = False
        self.sonar_cursor_position = None
        self.OBJECTS = {}
        self.PASSIVE_SONAR_BUTTON_HOVER = False
        self.big_font = pygame.font.Font('freesansbold.ttf', 32)
        self.middle_font = pygame.font.Font('freesansbold.ttf', 15)
        self.small_font = pygame.font.Font('freesansbold.ttf', 10)
        self.PASSIVE_SONAR_DISPLAY_CONTACTS = []
        self.ACTIVE_SONAR_CONTACTS = {}
        self.ACTIVE_SONAR_PING_DELAY = 0
        self.ACTIVE_SONAR_PING_RADIUS = 0
        self.ACTIVE_SONAR = False
        self.BALLAST = 50
        self.GEAR = 0
        self.LOCAL_ACCELERATION = 0
        self.LOCAL_VELOCITY = 0
        # self.ENEMY_POSITION = None
        self.LOCAL_POSITION = None
        self.quit_rect = None
        self.host_game_rect = None
        self.join_game_rect = None
        self.fps = 60
        self.current_fps = self.fps
        self.mapsurface = None
        self.running = True
        self.size = (1280, 720)
        self.moving = False
        self.MAP_OPEN = False
        self.MAIN_MENU_OPEN = True
        self.JOIN_GAME_OPEN = False
        self.GAME_OPEN = False
        self.GAME_INIT = False
        self.SONAR_SCREEN = False

        # Clock to ensure stable fps
        self.clock = pygame.time.Clock()

        # create window
        self.window = pygame.display.set_mode(self.size, pygame.DOUBLEBUF | pygame.HWSURFACE)
        pygame.display.set_caption("Sonar Conflict")

        # create map
        current_dir = os.path.dirname(os.path.realpath(__name__))
        self.map = pygame.image.load(current_dir + '/Assets/map.png')
        self.map_rect = self.map.get_rect(topleft=self.window.get_rect().topleft)

        # collision detection map
        self.coll_detection = pygame.image.load(current_dir + '/Assets/map.png')

        # create window
        pygame.display.flip()

    def render_notifications(self):

        # debug info
        if server_api.LAST_UPDATE_AT and server_api.LAST_SEND_AT and self.DEBUG:
            rec_ = float(time.time() - server_api.LAST_UPDATE_AT)
            sen = float(time.time() - server_api.LAST_SEND_AT)
            if self.max_rec < rec_:
                self.max_rec = rec_
            if self.max_sen < sen:
                self.max_sen = sen
            txtsurf = self.middle_font.render(f"Received: {rec_:.2f} "
                                              f"Sent: {sen:.2f} "
                                              f"MaxRecieved: {self.max_rec:.2f} "
                                              f"MaxSent: {self.max_sen:.2f} "
                                              f"FPS: {self.current_fps:.0f}", True, '#03fca9')
            self.window.blit(txtsurf, (10, 10))
        else:
            self.max_sen = 0
            self.max_rec = 0

        i = 0
        for message in self.NOTICE_QUEUE:
            color = 'orange'
            if message[2] == 0:
                color = "green"
            elif message[2] == 1:
                color = "red"
            txtsurf = self.middle_font.render(f'{message[0]}', True, color)
            self.window.blit(txtsurf, (self.size[0] - 150 - txtsurf.get_width() / 2, (28 - i * 4) * self.pos))
            message[1] += 0.0167
            if message[1] > 5:
                self.NOTICE_QUEUE.remove(message)
            i += 1
            if i > 6:
                break

    def clear_scene(self):
        self.MAP_OPEN = False
        self.SCOREBOARD_OPEN = False
        self.MAIN_MENU_OPEN = False
        self.GAME_OPEN = False
        self.JOIN_GAME_SCREEN = False
        self.HOST_GAME_SCREEN = False

    def open_map(self):
        # Uncomment to reset map's position
        # self.map_rect = self.map.get_rect(topleft=self.window.get_rect().topleft)
        self.blitmap()

    def blitmap(self):
        current_dir = os.path.dirname(os.path.realpath(__name__))
        self.map = pygame.image.load(current_dir + '/Assets/map.png')
        self.map_render()
        self.mapsurface = pygame.transform.smoothscale(self.map, self.map_rect.size)
        self.window.fill(0)
        self.window.blit(self.mapsurface, self.map_rect)
        self.render_notifications()
        pygame.draw.line(self.window, 'green', (100, self.size[1] - 100),
                         (100 + self.range_indicator, self.size[1] - 100))
        pygame.draw.line(self.window, 'green', (100, self.size[1] - 100), (100, self.size[1] - 105))
        pygame.draw.line(self.window, 'green', (100 + self.range_indicator, self.size[1] - 100),
                         (100 + self.range_indicator, self.size[1] - 105))
        txtsurf = self.small_font.render("100km", True, 'green')
        self.window.blit(txtsurf, (100 + self.range_indicator // 2 - txtsurf.get_width() // 2, self.size[1] - 95))

    def map_render(self):
        # Location marker rendering
        length = 10
        point1 = (self.LOCAL_POSITION[0] + length * math.cos(math.radians(self.LOCAL_POSITION[2] - 90)),
                  self.LOCAL_POSITION[1] + length * math.sin(math.radians(self.LOCAL_POSITION[2] - 90)))
        pygame.draw.aaline(self.map, 'red', (self.LOCAL_POSITION[0], self.LOCAL_POSITION[1]), point1)
        pygame.draw.circle(self.map, 'green', (self.LOCAL_POSITION[0], self.LOCAL_POSITION[1]), 2)
        # Friendly ship locations
        for ship in self.OBJECTS:
            if ship[:13] == "Friendly_ship":
                length = 5
                point1 = (self.OBJECTS[ship][0][0] + length * math.cos(math.radians(self.OBJECTS[ship][0][2] - 90)),
                          self.OBJECTS[ship][0][1] + length * math.sin(math.radians(self.OBJECTS[ship][0][2] - 90)))
                pygame.draw.aaline(self.map, 'red', (self.OBJECTS[ship][0][0], self.OBJECTS[ship][0][1]), point1)
                pygame.draw.circle(self.map, 'green', (self.OBJECTS[ship][0][0], self.OBJECTS[ship][0][1]), 1)
        # Enemy ship locations
        if self.CHEATS:
            for ship in self.OBJECTS:
                if ship.count("Enemy_ship"):
                    length = 5
                    point1 = (
                        self.OBJECTS[ship][0][0] + length * math.cos(math.radians(self.OBJECTS[ship][0][2] - 90)),
                        self.OBJECTS[ship][0][1] + length * math.sin(math.radians(self.OBJECTS[ship][0][2] - 90)))
                    pygame.draw.aaline(self.map, 'red', (self.OBJECTS[ship][0][0], self.OBJECTS[ship][0][1]),
                                       point1)
                    pygame.draw.circle(self.map, 'purple', (self.OBJECTS[ship][0][0], self.OBJECTS[ship][0][1]), 1)

        # Port locations
        for port in self.FRIENDLY_PORT_LOCATIONS:
            pygame.draw.circle(self.map, 'green', (port[0], port[1]), 4)

        # Friendly target locations
        for target in self.FRIENDLY_TARGET_LOCATIONS:
            pygame.draw.circle(self.map, 'yellow', (target[0], target[1]), 2)
            txtsurf = self.small_font.render(f"{target[2]}%", True, '#b6b6d1')
            self.map.blit(txtsurf, (target[0], target[1]))

        # Enemy target locations
        for target in self.ENEMY_TARGET_LOCATIONS:
            pygame.draw.circle(self.map, 'orange', (target[0], target[1]), 2)
            txtsurf = self.small_font.render(f"{target[2]}%", True, '#b6b6d1')
            self.map.blit(txtsurf, (target[0], target[1]))

        # Enemy torpedoes
        if self.CHEATS:
            for torpedo in self.TORPEDOES:
                length = 5
                point1 = (
                    self.TORPEDOES[torpedo][0][0] + length * math.cos(math.radians(self.TORPEDOES[torpedo][0][2] - 90)),
                    self.TORPEDOES[torpedo][0][1] + length * math.sin(math.radians(self.TORPEDOES[torpedo][0][2] - 90)))
                pygame.draw.aaline(self.map, 'red', (self.TORPEDOES[torpedo][0][0], self.TORPEDOES[torpedo][0][1]),
                                   point1)
                pygame.draw.circle(self.map, 'red', (self.TORPEDOES[torpedo][0][0], self.TORPEDOES[torpedo][0][1]), 2)
        # Enemy relayed position
        if self.ENEMY_VISIBLE:
            length = 5
            point1 = (self.OBJECTS['Enemy'][0][0] + length * math.cos(math.radians(self.OBJECTS['Enemy'][0][2] - 90)),
                      self.OBJECTS['Enemy'][0][1] + length * math.sin(math.radians(self.OBJECTS['Enemy'][0][2] - 90)))
            pygame.draw.aaline(self.map, 'red', (self.OBJECTS['Enemy'][0][0], self.OBJECTS['Enemy'][0][1]), point1)
            pygame.draw.circle(self.map, 'pink', (self.OBJECTS['Enemy'][0][0], self.OBJECTS['Enemy'][0][1]), 1)
        if self.ENEMY_VISIBLE_AS:
            length = self.ENEMY_VISIBLE_AS[0] + random_int(-10, 10)
            if length < 0:
                length = 10
            elif length > 150:
                length = 150
            point1 = (self.ENEMY_VISIBLE_AS[1][0] + length * math.cos(math.radians(self.ENEMY_VISIBLE_AS[1][2] - 270
                                                                                   + random_int(-5, 5))),
                      self.ENEMY_VISIBLE_AS[1][1] + length * math.sin(math.radians(self.ENEMY_VISIBLE_AS[1][2] - 270
                                                                                   + random_int(-5, 5))))
            pygame.draw.aaline(self.map, 'yellow', (self.ENEMY_VISIBLE_AS[1][0], self.ENEMY_VISIBLE_AS[1][1]), point1)
        # Enemy position
        if self.CHEATS:
            length = 5
            point1 = (self.OBJECTS['Enemy'][0][0] + length * math.cos(math.radians(self.OBJECTS['Enemy'][0][2] - 90)),
                      self.OBJECTS['Enemy'][0][1] + length * math.sin(math.radians(self.OBJECTS['Enemy'][0][2] - 90)))
            pygame.draw.aaline(self.map, 'red', (self.OBJECTS['Enemy'][0][0], self.OBJECTS['Enemy'][0][1]), point1)
            pygame.draw.circle(self.map, 'pink', (self.OBJECTS['Enemy'][0][0], self.OBJECTS['Enemy'][0][1]), 1)

        pygame.display.update()

    def on_cleanup(self):
        os._exit(0)

    def open_main_menu(self):
        self.window.fill("#021019")

        txtsurf = self.big_font.render("Sonar Conflict", True, "#b6b6d1")
        self.window.blit(txtsurf, (self.size[0] // 2 - txtsurf.get_width() // 2,
                                   self.size[1] // 4 - txtsurf.get_height() // 2))
        width = 200
        height = 50
        self.join_game_rect = pygame.Rect(self.size[0] // 2 - width // 2, self.size[1] // 3 - height // 2, width,
                                          height)
        pygame.draw.rect(self.window, '#b6b6d1', self.join_game_rect, width=2)
        font = pygame.font.Font('freesansbold.ttf', 28)
        txtsurf = font.render("Join a game", True, "#b6b6d1")
        self.window.blit(txtsurf, (self.join_game_rect.left + (
                (self.join_game_rect.right - self.join_game_rect.left) - txtsurf.get_width()) // 2,
                                   self.join_game_rect.top + (
                                           (
                                                   self.join_game_rect.bottom - self.join_game_rect.top) - txtsurf.get_height()) // 2,
                                   self.join_game_rect.right - (
                                           (
                                                   self.join_game_rect.bottom - self.join_game_rect.top) - txtsurf.get_height()) // 2,
                                   self.join_game_rect.bottom - (
                                           (
                                                   self.join_game_rect.bottom - self.join_game_rect.top) - txtsurf.get_height()) // 2))
        self.host_game_rect = pygame.Rect(self.size[0] // 2 - width // 2, self.size[1] // 2.3 - height // 2, width,
                                          height)
        pygame.draw.rect(self.window, '#b6b6d1', self.host_game_rect, width=2)
        txtsurf = font.render("Host a game", True, "#b6b6d1")
        self.window.blit(txtsurf, (self.host_game_rect.left + (
                (self.host_game_rect.right - self.host_game_rect.left) - txtsurf.get_width()) // 2,
                                   self.host_game_rect.top + (
                                           (
                                                   self.host_game_rect.bottom - self.host_game_rect.top) - txtsurf.get_height()) // 2,
                                   self.host_game_rect.right - (
                                           (
                                                   self.host_game_rect.bottom - self.host_game_rect.top) - txtsurf.get_height()) // 2,
                                   self.host_game_rect.bottom - (
                                           (
                                                   self.host_game_rect.bottom - self.host_game_rect.top) - txtsurf.get_height()) // 2))
        self.quit_rect = pygame.Rect(self.size[0] // 2 - width // 2, self.size[1] // 1.5 - height // 2, width,
                                     height)
        pygame.draw.rect(self.window, '#b6b6d1', self.quit_rect, width=2)
        txtsurf = font.render("Quit", True, "#b6b6d1")
        self.window.blit(txtsurf, (self.host_game_rect.left + (
                (self.quit_rect.right - self.host_game_rect.left) - txtsurf.get_width()) // 2,
                                   self.quit_rect.top + (
                                           (
                                                   self.quit_rect.bottom - self.quit_rect.top) - txtsurf.get_height()) // 2,
                                   self.quit_rect.right - (
                                           (
                                                   self.quit_rect.bottom - self.quit_rect.top) - txtsurf.get_height()) // 2,
                                   self.quit_rect.bottom - (
                                           (
                                                   self.quit_rect.bottom - self.quit_rect.top) - txtsurf.get_height()) // 2))

    def check_map_events(self, event):
        if event.type == pygame.QUIT:
            self.running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.moving = True
                if self.CHEATS:
                    print(pygame.mouse.get_pos())
            elif event.button == 2:
                if self.CHEATS:
                    self.LOCAL_POSITION[0] = pygame.mouse.get_pos()[0]
                    self.LOCAL_POSITION[1] = pygame.mouse.get_pos()[1]
                    print(f"Teleported to {pygame.mouse.get_pos()}")
            elif event.button == 4 or event.button == 5:
                zoom = 1.2 if event.button == 4 else 0.8
                mx, my = event.pos
                left = mx + (self.map_rect.left - mx) * zoom
                right = mx + (self.map_rect.right - mx) * zoom
                top = my + (self.map_rect.top - my) * zoom
                bottom = my + (self.map_rect.bottom - my) * zoom
                self.range_indicator *= zoom
                if left > 0 or right < 1306 or top > 0 or bottom < self.size[1]:
                    left = 0
                    right = 1306
                    top = 0
                    bottom = 720
                    self.range_indicator = 50
                elif right > 3000 and bottom > 2000:
                    self.range_indicator /= zoom
                    return

                self.map_rect = pygame.Rect(left, top, right - left, bottom - top)
                self.blitmap()

        elif event.type == pygame.MOUSEBUTTONUP:
            self.moving = False

        elif event.type == pygame.MOUSEMOTION and self.moving:
            if self.map_rect.left + event.rel[0] > 0 or self.map_rect.right + event.rel[0] < \
                    1306 or self.map_rect.top + event.rel[1] > 0 or self.map_rect.bottom + event.rel[1] < self.size[1]:
                return
            self.map_rect.move_ip(event.rel)
            self.blitmap()

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_m or event.key == pygame.K_e:
                self.clear_scene()
                self.GAME_OPEN = True
            elif event.key == pygame.K_LCTRL:
                if self.GEAR > -3:
                    self.GEAR -= 1
                print(self.GEAR)
            elif event.key == pygame.K_LSHIFT:
                if self.GEAR != 3:
                    self.GEAR += 1
                print(self.GEAR)
            elif event.key == pygame.K_TAB:
                self.clear_scene()
                self.SCOREBOARD_OPEN = True
                self.MAP_OPEN = True

        pygame.display.update()

    def main_menu_events(self, event):
        pygame.mouse.set_cursor(*pygame.cursors.Cursor(pygame.SYSTEM_CURSOR_ARROW))
        if event.type == pygame.QUIT:
            self.running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.join_game_rect.collidepoint(pygame.mouse.get_pos()):
                self.clear_scene()
                self.JOIN_GAME_SCREEN = True
                # self.PLAYER_ID = 0
                # server_api.PLAYER = self.PLAYER_ID
                # if self.PLAYER_ID:
                #     server_api.CHANNEL = server_api.fetch_channel_object(1130614819146444832)
                #     server_api.LISTENING_CHANNEL = server_api.fetch_channel_object(1130614839631413269)
                # else:
                #     server_api.CHANNEL = server_api.fetch_channel_object(1130614839631413269)
                #     server_api.LISTENING_CHANNEL = server_api.fetch_channel_object(1130614819146444832)
                # self.clear_scene()
                # self.GAME_OPEN = True
                # self.GAME_INIT = True
                # self.game_init()
            elif event.button == 1 and self.host_game_rect.collidepoint(pygame.mouse.get_pos()):
                self.clear_scene()
                self.HOST_GAME_SCREEN = True
                # self.PLAYER_ID = 1
                # server_api.PLAYER = self.PLAYER_ID
                # if self.PLAYER_ID:
                #     server_api.CHANNEL = server_api.fetch_channel_object(1130614819146444832)
                #     server_api.LISTENING_CHANNEL = server_api.fetch_channel_object(1130614839631413269)
                # else:
                #     server_api.CHANNEL = server_api.fetch_channel_object(1130614839631413269)
                #     server_api.LISTENING_CHANNEL = server_api.fetch_channel_object(1130614819146444832)
                # self.clear_scene()
                # self.GAME_OPEN = True
                # self.GAME_INIT = True
                # self.game_init()
            elif event.button == 1 and self.quit_rect.collidepoint(pygame.mouse.get_pos()):
                self.clear_scene()
                self.running = False

        if self.join_game_rect.collidepoint(pygame.mouse.get_pos()):
            pygame.mouse.set_cursor(*pygame.cursors.Cursor(pygame.SYSTEM_CURSOR_HAND))
            pygame.draw.rect(self.window, 'white', self.join_game_rect, width=2)
            font = pygame.font.Font('freesansbold.ttf', 28)
            txtsurf = font.render("Join a game", True, "white")
            self.window.blit(txtsurf, (self.join_game_rect.left + (
                    (self.join_game_rect.right - self.join_game_rect.left) - txtsurf.get_width()) // 2,
                                       self.join_game_rect.top + (
                                               (
                                                       self.join_game_rect.bottom - self.join_game_rect.top) - txtsurf.get_height()) // 2,
                                       self.join_game_rect.right - (
                                               (
                                                       self.join_game_rect.bottom - self.join_game_rect.top) - txtsurf.get_height()) // 2,
                                       self.join_game_rect.bottom - (
                                               (
                                                       self.join_game_rect.bottom - self.join_game_rect.top) - txtsurf.get_height()) // 2))
        elif self.host_game_rect.collidepoint(pygame.mouse.get_pos()):
            pygame.mouse.set_cursor(*pygame.cursors.Cursor(pygame.SYSTEM_CURSOR_HAND))
            pygame.draw.rect(self.window, 'white', self.host_game_rect, width=2)
            font = pygame.font.Font('freesansbold.ttf', 28)
            txtsurf = font.render("Host a game", True, "white")
            self.window.blit(txtsurf, (self.host_game_rect.left + (
                    (self.host_game_rect.right - self.host_game_rect.left) - txtsurf.get_width()) // 2,
                                       self.host_game_rect.top + (
                                               (
                                                       self.host_game_rect.bottom - self.host_game_rect.top) - txtsurf.get_height()) // 2,
                                       self.host_game_rect.right - (
                                               (
                                                       self.host_game_rect.bottom - self.host_game_rect.top) - txtsurf.get_height()) // 2,
                                       self.host_game_rect.bottom - (
                                               (
                                                       self.host_game_rect.bottom - self.host_game_rect.top) - txtsurf.get_height()) // 2))
        elif self.quit_rect.collidepoint(pygame.mouse.get_pos()):
            pygame.mouse.set_cursor(*pygame.cursors.Cursor(pygame.SYSTEM_CURSOR_HAND))
            pygame.draw.rect(self.window, 'white', self.quit_rect, width=2)
            font = pygame.font.Font('freesansbold.ttf', 28)
            txtsurf = font.render("Quit", True, "white")
            self.window.blit(txtsurf, (self.quit_rect.left + (
                    (self.quit_rect.right - self.quit_rect.left) - txtsurf.get_width()) // 2,
                                       self.quit_rect.top + (
                                               (
                                                       self.quit_rect.bottom - self.quit_rect.top) - txtsurf.get_height()) // 2,
                                       self.quit_rect.right - (
                                               (
                                                       self.quit_rect.bottom - self.quit_rect.top) - txtsurf.get_height()) // 2,
                                       self.quit_rect.bottom - (
                                               (
                                                       self.quit_rect.bottom - self.quit_rect.top) - txtsurf.get_height()) // 2))
        pygame.display.update()

    def game_init(self):
        # Load mission information from a file
        with open(self.mission_name, 'r') as file:
            mission = json.load(file)
        code = 'usa'
        enemy_code = 'ru'
        if not self.PLAYER_ID:
            code = 'ru'
            enemy_code = 'usa'
        self.FRIENDLY_PORT_LOCATIONS = mission[code]['ports']
        self.FRIENDLY_TARGET_LOCATIONS = mission[code]['targets']  # X, Y, Health
        self.ENEMY_TARGET_LOCATIONS = mission[enemy_code]['targets']
        # x, y, azimuth, depth
        self.LOCAL_POSITION = [mission[code]['spawn'][0], mission[code]['spawn'][1],
                               mission[code]['spawn'][2], 0, mission[code]['spawn'][3]]
        # x, y, azimuth, pitch, depth
        # self.ENEMY_POSITION = [mission[enemy_code]['spawn'][0], mission[enemy_code]['spawn'][1],
        #                        mission[enemy_code]['spawn'][2], mission[enemy_code]['spawn'][3]]
        self.OBJECTS['Enemy'] = [[mission[enemy_code]['spawn'][0], mission[enemy_code]['spawn'][1],
                                  mission[enemy_code]['spawn'][2], mission[enemy_code]['spawn'][3]], 'Submarine', 0, 1,
                                 100, -25]
        # [x, y, azimuth, depth], type, velocity, detection_chance, HEALTH* ACTIVE_SONAR**
        if not self.PLAYER_ID:
            self.designationP = "Russian"
            self.designationE = "American"
        else:
            self.designationP = "Russian"
            self.designationE = "American"
        i = 1
        for vessel in mission[code]['ships']:
            self.OBJECTS[f'Friendly_ship_{i}'] = [[vessel[0], vessel[1], vessel[2], 0],
                                                  self.designationP, 0.008, 0.8, 100, -25]
            i += 1
        i = 1
        for vessel in mission[enemy_code]['ships']:
            self.OBJECTS[f'Enemy_ship_{i}'] = [[vessel[0], vessel[1], vessel[2], 0],
                                               self.designationE, 0.008, 0.8, 100, -25]
            i += 1
        self.SONAR_SCREEN = True
        self.sonar_screen_render()
        self.weapon_screen_render()

    def game_events(self, event):
        self.PASSIVE_SONAR_BUTTON_HOVER = False
        self.sonar_cursor_position = None
        pygame.mouse.set_cursor(*pygame.cursors.Cursor(pygame.SYSTEM_CURSOR_ARROW))
        if event.type == pygame.QUIT:
            self.running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if pygame.Rect(self.size[0] // 2, 30,
                               self.size[0] // 2 - 30, self.size[1] - 30).collidepoint(pygame.mouse.get_pos()):
                    # Select contact
                    mouse_pos = pygame.mouse.get_pos()
                    flag = 0
                    for contact in self.PASSIVE_SONAR_DISPLAY_CONTACTS:
                        # print((int(contact[0]), contact[1]+31), mouse_pos)
                        if mouse_pos[0] - 2 < contact[0] < mouse_pos[0] + 2 and \
                                mouse_pos[1] - 2 < contact[1] + 31 < mouse_pos[1] + 2:
                            self.PASSIVE_SELECTED_CONTACT = contact
                            self.identifying_delay = 0
                            flag = 1
                    if not flag:
                        self.PASSIVE_SELECTED_CONTACT = None
                        self.identifying_delay = 0
                elif pygame.Rect(10, 650, 200, 40).collidepoint(pygame.mouse.get_pos()):
                    self.identifying_delay = 0.0167
                elif pygame.Rect(0, 0, 400, 400).collidepoint(pygame.mouse.get_pos()):
                    mouse_pos = pygame.mouse.get_pos()
                    for contact in list(self.ACTIVE_SONAR_CONTACTS):
                        if mouse_pos[0] - 5 < self.ACTIVE_SONAR_CONTACTS[contact][0] < mouse_pos[0] + 5 and \
                                mouse_pos[1] - 5 < self.ACTIVE_SONAR_CONTACTS[contact][1] < mouse_pos[1]:
                            self.ACTIVE_SONAR_SELECTED_CONTACT = contact

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_m:
                self.clear_scene()
                self.MAP_OPEN = True
                self.open_map()
                self.map_render()
            elif event.key == pygame.K_F1:
                if self.DEBUG:
                    print("Debug mode OFF")
                    self.DEBUG = False
                else:
                    print("debug mode ON")
                    self.DEBUG = True
            elif event.key == pygame.K_LCTRL:
                if self.GEAR > -3:
                    self.GEAR -= 1
                print(self.GEAR)
            elif event.key == pygame.K_LSHIFT:
                if self.GEAR != 3:
                    self.GEAR += 1
                print(self.GEAR)
            elif event.key == pygame.K_t:
                if self.ACTIVE_SONAR:
                    self.ACTIVE_SONAR = False
                    self.ACTIVE_SONAR_PING_DELAY = 0
                    self.ACTIVE_SONAR_PING_RADIUS = 0
                    self.NOTICE_QUEUE.append(["Active sonar off!", 0, 0])
                else:
                    self.ACTIVE_SONAR = True
                    self.ACTIVE_SONAR_PING_DELAY = 0
                    self.ACTIVE_SONAR_PING_RADIUS = 0
                    self.NOTICE_QUEUE.append(["Active sonar on!", 0, 0])
            elif event.key == pygame.K_f:
                if self.PASSIVE_SONAR_FREEZE:
                    self.PASSIVE_SONAR_FREEZE = False
                    self.NOTICE_QUEUE.append(["Passive sonar unfrozen!", 0, 0])
                else:
                    self.PASSIVE_SONAR_FREEZE = True
                    self.NOTICE_QUEUE.append(["Passive sonar frozen!", 0, 0])
            elif event.key == pygame.K_e:
                self.WEAPON_SCREEN = True
                self.SONAR_SCREEN = False
                self.TRANSFER_CONTACT_INFO_P = False
                self.TRANSFER_CONTACT_INFO_A = False
            elif event.key == pygame.K_TAB:
                self.clear_scene()
                self.SCOREBOARD_OPEN = True

        elif pygame.Rect(10, 650, 200, 40).collidepoint(pygame.mouse.get_pos()):
            self.PASSIVE_SONAR_BUTTON_HOVER = True
            pygame.mouse.set_cursor(*pygame.cursors.Cursor(pygame.SYSTEM_CURSOR_HAND))

        elif pygame.Rect(self.size[0] // 2, 30,
                         self.size[0] // 2 - 30, self.size[1] - 30).collidepoint(pygame.mouse.get_pos()):
            mouse_pos = pygame.mouse.get_pos()
            self.sonar_cursor_position = mouse_pos

    def weapon_screen_events(self, event):
        pygame.mouse.set_cursor(*pygame.cursors.Cursor(pygame.SYSTEM_CURSOR_ARROW))
        if event.type == pygame.QUIT:
            self.running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.bearing_var[0] = False
                self.distance_var[0] = False
                self.depth_var[0] = False
                for weapon in self.WEAPON_LAYOUT:
                    if pygame.Rect(weapon).collidepoint(pygame.mouse.get_pos()):
                        flag = 0
                        for port in self.FRIENDLY_PORT_LOCATIONS:
                            rel_x = port[0] - self.LOCAL_POSITION[0]
                            rel_y = port[1] - self.LOCAL_POSITION[1]
                            distance = math.sqrt(rel_x * rel_x + rel_y * rel_y)
                            if distance <= 30:
                                flag = 1
                                # Weapon refilling
                                if self.WEAPON_LAYOUT[weapon][1] != 'Fired':
                                    if not self.PLAYER_ID:
                                        # RU
                                        if self.WEAPON_LAYOUT[weapon][0][0] == 0:
                                            if self.WEAPON_LAYOUT[weapon][1] == '3M54-1 Kalibr':
                                                self.WEAPON_LAYOUT[weapon][1] = 'P-800 Oniks'
                                            else:
                                                self.WEAPON_LAYOUT[weapon][1] = '3M54-1 Kalibr'
                                        else:
                                            if self.WEAPON_LAYOUT[weapon][1] == 'Futlyar':
                                                self.WEAPON_LAYOUT[weapon][1] = 'Sonar decoy'
                                            else:
                                                self.WEAPON_LAYOUT[weapon][1] = 'Futlyar'
                                    else:
                                        # American
                                        if self.WEAPON_LAYOUT[weapon][0][0] == 0:
                                            if self.WEAPON_LAYOUT[weapon][1] == 'TLAM-E':
                                                self.WEAPON_LAYOUT[weapon][1] = 'TASM'
                                            else:
                                                self.WEAPON_LAYOUT[weapon][1] = 'TLAM-E'
                                        else:
                                            if self.WEAPON_LAYOUT[weapon][1] == 'Mk-48':
                                                self.WEAPON_LAYOUT[weapon][1] = 'UGM-84'
                                            elif self.WEAPON_LAYOUT[weapon][1] == 'UGM-84':
                                                self.WEAPON_LAYOUT[weapon][1] = 'Sonar decoy'
                                            else:
                                                self.WEAPON_LAYOUT[weapon][1] = 'Mk-48'
                        if not flag:
                            if self.WEAPON_LAYOUT[weapon][0][1] == 0 and self.SELECTED_WEAPON:
                                if self.WEAPON_LAYOUT[self.SELECTED_WEAPON][0][0] == self.WEAPON_LAYOUT[weapon][0][0] \
                                        and self.WEAPON_LAYOUT[self.SELECTED_WEAPON][0][1] != 0 and \
                                        self.WEAPON_LAYOUT[self.SELECTED_WEAPON][1] != 'Fired':
                                    temp = self.WEAPON_LAYOUT[weapon][1]
                                    self.WEAPON_LAYOUT[weapon][1] = self.WEAPON_LAYOUT[self.SELECTED_WEAPON][1]
                                    self.WEAPON_LAYOUT[self.SELECTED_WEAPON][1] = temp
                        self.SELECTED_WEAPON = weapon
                if pygame.Rect(self.bearing_box).collidepoint(pygame.mouse.get_pos()):
                    self.bearing_var[0] = True
                elif pygame.Rect(self.distance_box).collidepoint(pygame.mouse.get_pos()):
                    self.distance_var[0] = True
                elif pygame.Rect(self.depth_box).collidepoint(pygame.mouse.get_pos()):
                    self.depth_var[0] = True
                elif pygame.Rect(self.change_mode_box).collidepoint(pygame.mouse.get_pos()):
                    if self.SELECTED_WEAPON:
                        if self.WEAPON_LAYOUT[self.SELECTED_WEAPON][0][0] == 1 and \
                                self.WEAPON_LAYOUT[self.SELECTED_WEAPON][0][1] == 0 and \
                                self.WEAPON_LAYOUT[self.SELECTED_WEAPON][1] != 'UGM-84':
                            if self.mode_var:
                                self.mode_var = 0
                            else:
                                self.mode_var = 1
                        else:
                            self.mode_var = -1
                elif pygame.Rect(self.active_transfer_box).collidepoint(pygame.mouse.get_pos()):
                    if self.TRANSFER_CONTACT_INFO_A:
                        self.TRANSFER_CONTACT_INFO_A = False
                    else:
                        self.TRANSFER_CONTACT_INFO_A = True
                elif pygame.Rect(self.passive_transfer_box).collidepoint(pygame.mouse.get_pos()):
                    if self.TRANSFER_CONTACT_INFO_P:
                        self.TRANSFER_CONTACT_INFO_P = False
                    else:
                        self.TRANSFER_CONTACT_INFO_P = True
                elif pygame.Rect(self.reset_box).collidepoint(pygame.mouse.get_pos()):
                    self.bearing_var[1] = ''
                    self.depth_var[1] = ''
                    self.distance_var[1] = ''
                    self.TRANSFER_CONTACT_INFO_P = False
                    self.TRANSFER_CONTACT_INFO_A = False
                elif pygame.Rect(self.fire_box).collidepoint(pygame.mouse.get_pos()):
                    flag = 0
                    if self.SELECTED_WEAPON and self.bearing_var[1].replace(".", "").isnumeric() and self.depth_var[
                        1].replace(".", "").isnumeric() and \
                            self.distance_var[1].replace(".", "").isnumeric():
                        if self.WEAPON_LAYOUT[self.SELECTED_WEAPON][0][1] == 0 and \
                                self.WEAPON_LAYOUT[self.SELECTED_WEAPON][1] != '':
                            if self.WEAPON_LAYOUT[self.SELECTED_WEAPON][0][0] == 0 and self.mode_var == -1 and \
                                    self.LOCAL_POSITION[4] < 60:
                                print("ALLOWED")
                                flag = 1
                            elif self.WEAPON_LAYOUT[self.SELECTED_WEAPON][1] == 'UGM-84' and self.mode_var == -1 and \
                                    self.LOCAL_POSITION[4] < 100:
                                print("ALLOWED")
                                flag = 1
                            elif self.WEAPON_LAYOUT[self.SELECTED_WEAPON][1] == 'Futlyar' and self.mode_var != -1 and \
                                    self.LOCAL_POSITION[4] < 600:
                                print("ALLOWED")
                                flag = 1
                            elif self.WEAPON_LAYOUT[self.SELECTED_WEAPON][1] == 'Mk-48' and self.mode_var != -1 and \
                                    self.LOCAL_POSITION[4] < 800:
                                print("ALLOWED")
                                flag = 1
                            elif self.WEAPON_LAYOUT[self.SELECTED_WEAPON][1] == 'Sonar decoy' and \
                                    self.mode_var != -1 and self.LOCAL_POSITION[4] < 400:
                                print("ALLOWED")
                                flag = 1
                            else:
                                print("NOT ALLOWED")
                        else:
                            print("NOT ALLOWED")
                    else:
                        print("NOT ALLOWED")
                    if flag:
                        self.LAUNCH_AUTH = [True, 3]
                        if self.WEAPON_LAYOUT[self.SELECTED_WEAPON][1] == '3M54-1 Kalibr':
                            speed = 3.5  # 1 pixel = 2.09km 0.0193 = 1km/h | 1 px = actual 12.5km # random speed idk
                            range = 150  # = 2500km  # = 300 km
                            distance = float(self.distance_var[1]) / 2  # converting to px
                            if distance > range:
                                time = range / speed
                            else:
                                time = distance / speed
                            # VLS launch
                            angle = self.LOCAL_POSITION[2] + float(self.bearing_var[1])
                            if angle > 360:
                                angle -= 360
                            print(angle)
                            impact_x = self.LOCAL_POSITION[0] - distance * math.cos(math.radians(angle + 90))
                            impact_y = self.LOCAL_POSITION[1] - distance * math.sin(math.radians(angle + 90))
                            print(impact_x, impact_y, distance)
                            flag = None
                            for target in self.ENEMY_TARGET_LOCATIONS:
                                if target[0] - 10 < impact_x < target[0] + 10 and \
                                        target[1] - 10 < impact_y < target[1] + 10:
                                    flag = target
                                    print(target[0], target[1])
                                    print("HIT!")

                            destruction = random_int(25, 50)

                            if distance > range:
                                flag = None
                                print("TARGET OUT OF RANGE")
                                self.LAM_FIRED.append(
                                    [time, True, flag, 'Ran out of fuel!',
                                     self.WEAPON_LAYOUT[self.SELECTED_WEAPON][1], destruction])
                            elif flag:
                                self.LAM_FIRED.append(
                                    [time, True, flag, 'Target hit!', self.WEAPON_LAYOUT[self.SELECTED_WEAPON][1],
                                     destruction])
                            else:
                                self.LAM_FIRED.append(
                                    [time, False, flag, 'Target missed!', self.WEAPON_LAYOUT[self.SELECTED_WEAPON][1],
                                     destruction])
                            self.WEAPON_LAYOUT[self.SELECTED_WEAPON][1] = ''
                        elif self.WEAPON_LAYOUT[self.SELECTED_WEAPON][1] == 'TLAM-E':
                            speed = 1.74
                            range = 200  # = 2500km  # = 400 km
                            distance = float(self.distance_var[1]) / 2  # converting to px
                            if distance > range:
                                time = range / speed
                            else:
                                time = distance / speed
                            angle = self.LOCAL_POSITION[2] + float(self.bearing_var[1])
                            if angle > 360:
                                angle -= 360
                            print(angle)
                            impact_x = self.LOCAL_POSITION[0] - distance * math.cos(math.radians(angle + 90))
                            impact_y = self.LOCAL_POSITION[1] - distance * math.sin(math.radians(angle + 90))
                            print(impact_x, impact_y, distance)
                            flag = None
                            for target in self.ENEMY_TARGET_LOCATIONS:
                                if target[0] - 30 < impact_x < target[0] + 30 and \
                                        target[1] - 30 < impact_y < target[1] + 30:
                                    flag = target
                                    print(target[0], target[1])
                                    print("HIT!")

                            destruction = random_int(40, 60)

                            if distance > range:
                                flag = None
                                print("TARGET OUT OF RANGE")
                                self.LAM_FIRED.append(
                                    [time, True, flag, 'Ran out of fuel!', self.WEAPON_LAYOUT[self.SELECTED_WEAPON][1],
                                     destruction])
                            elif flag:
                                self.LAM_FIRED.append(
                                    [time, True, flag, 'Target hit!', self.WEAPON_LAYOUT[self.SELECTED_WEAPON][1],
                                     destruction])
                            else:
                                self.LAM_FIRED.append(
                                    [time, False, flag, 'Target missed!', self.WEAPON_LAYOUT[self.SELECTED_WEAPON][1],
                                     destruction])
                            self.WEAPON_LAYOUT[self.SELECTED_WEAPON][1] = ''
                        elif self.WEAPON_LAYOUT[self.SELECTED_WEAPON][1] == 'P-800 Oniks':
                            sensor_range = 13
                            speed = 2.5
                            range = 40  # = 2500km  # = 80 km
                            distance = float(self.distance_var[1]) / 2  # converting to px
                            if distance > range:
                                time = range / speed
                            else:
                                time = distance / speed
                            angle = self.LOCAL_POSITION[2] + float(self.bearing_var[1])
                            if angle > 360:
                                angle -= 360
                            print(angle)
                            impact_x = self.LOCAL_POSITION[0] - distance * math.cos(math.radians(angle + 90))
                            impact_y = self.LOCAL_POSITION[1] - distance * math.sin(math.radians(angle + 90))
                            # Anti missile defence
                            if random_int(0, 10) < 1:
                                destruction = 0
                                print("Defense system defeated the missile.")
                            else:
                                destruction = random_int(40, 60)
                            if distance > range:
                                message = 'Out of fuel!'
                            else:
                                message = 'Target missed!'
                            self.ASM_FIRED.append([time, impact_x, impact_y, message,
                                                   self.WEAPON_LAYOUT[self.SELECTED_WEAPON][1], destruction,
                                                   sensor_range])
                            self.WEAPON_LAYOUT[self.SELECTED_WEAPON][1] = ''
                        elif self.WEAPON_LAYOUT[self.SELECTED_WEAPON][1] == 'TASM':
                            sensor_range = 15
                            speed = 2
                            range = 55  # = 2500km  # = 110 km
                            distance = float(self.distance_var[1]) / 2  # converting to px
                            if distance > range:
                                time = range / speed
                            else:
                                time = distance / speed
                            angle = self.LOCAL_POSITION[2] + float(self.bearing_var[1])
                            if angle > 360:
                                angle -= 360
                            impact_x = self.LOCAL_POSITION[0] - distance * math.cos(math.radians(angle + 90))
                            impact_y = self.LOCAL_POSITION[1] - distance * math.sin(math.radians(angle + 90))
                            # Anti missile defence
                            if random_int(0, 10) < 4:
                                destruction = 0
                                print("Defense system defeated the missile.")
                            else:
                                destruction = random_int(50, 65)
                            if distance > range:
                                message = 'Out of fuel!'
                            else:
                                message = 'Target missed!'
                            self.ASM_FIRED.append([time, impact_x, impact_y, message,
                                                   self.WEAPON_LAYOUT[self.SELECTED_WEAPON][1], destruction,
                                                   sensor_range])
                            self.WEAPON_LAYOUT[self.SELECTED_WEAPON][1] = ''
                        elif self.WEAPON_LAYOUT[self.SELECTED_WEAPON][1] == 'UGM-84':
                            sensor_range = 16
                            speed = 1.92
                            range = 45  # = 2500km  # = 90 km
                            distance = float(self.distance_var[1]) / 2  # converting to px
                            if distance > range:
                                time = range / speed
                            else:
                                time = distance / speed
                            angle = self.LOCAL_POSITION[2] + float(self.bearing_var[1])
                            if angle > 360:
                                angle -= 360
                            impact_x = self.LOCAL_POSITION[0] - distance * math.cos(math.radians(angle + 90))
                            impact_y = self.LOCAL_POSITION[1] - distance * math.sin(math.radians(angle + 90))
                            # Anti missile defence
                            if random_int(0, 10) < 3:
                                destruction = 0
                                print("Defense system defeated the missile.")
                            else:
                                destruction = random_int(45, 65)
                            if distance > range:
                                message = 'Out of fuel!'
                            else:
                                message = 'Target missed!'
                            self.ASM_FIRED.append([time, impact_x, impact_y, message,
                                                   self.WEAPON_LAYOUT[self.SELECTED_WEAPON][1], destruction,
                                                   sensor_range])
                            self.WEAPON_LAYOUT[self.SELECTED_WEAPON][1] = ''
                        elif self.WEAPON_LAYOUT[self.SELECTED_WEAPON][1] == 'Futlyar':
                            print("FIRED!")
                            speed = 0.0367
                            range = 35  # 70 km
                            distance = float(self.distance_var[1]) / 2  # converting to px
                            angle = self.LOCAL_POSITION[2] + float(self.bearing_var[1])
                            if angle > 360:
                                angle -= 360
                            time = range / (speed * 60)
                            impact_x = self.LOCAL_POSITION[0] - distance * math.cos(math.radians(angle + 90))
                            impact_y = self.LOCAL_POSITION[1] - distance * math.sin(math.radians(angle + 90))
                            mode = True
                            if self.mode_var == 0:
                                mode = False
                            torpedo_info = [
                                [self.LOCAL_POSITION[0], self.LOCAL_POSITION[1],
                                 self.LOCAL_POSITION[2], speed, self.LOCAL_POSITION[3]],
                                [impact_x, impact_y, float(self.depth_var[1])], False, time, 'Enemy', 0,
                                mode, self.SELECTED_WEAPON]
                            self.UPDATE_TORP_QUEUE.append(f"{torpedo_info}")
                            # server_api.send_message(, 1084976743565234289)
                            self.WEAPON_LAYOUT[self.SELECTED_WEAPON][1] = 'Fired'
                            self.FIRED_TORPEDOES[self.SELECTED_WEAPON] = [False, mode, -1]
                        elif self.WEAPON_LAYOUT[self.SELECTED_WEAPON][1] == 'Mk-48':
                            print("FIRED!")
                            speed = 0.0367
                            range = 35  # 70 km
                            distance = float(self.distance_var[1]) / 2  # converting to px
                            angle = self.LOCAL_POSITION[2] + float(self.bearing_var[1])
                            if angle > 360:
                                angle -= 360
                            time = range / (speed * 60)
                            impact_x = self.LOCAL_POSITION[0] - distance * math.cos(math.radians(angle + 90))
                            impact_y = self.LOCAL_POSITION[1] - distance * math.sin(math.radians(angle + 90))
                            mode = True
                            if self.mode_var == 0:
                                mode = False
                            torpedo_info = [
                                [self.LOCAL_POSITION[0], self.LOCAL_POSITION[1],
                                 self.LOCAL_POSITION[2], speed, self.LOCAL_POSITION[3]],
                                [impact_x, impact_y, float(self.depth_var[1])], False, time, 'Enemy', 0,
                                mode, self.SELECTED_WEAPON]
                            self.UPDATE_TORP_QUEUE.append(f"{torpedo_info}")
                            self.WEAPON_LAYOUT[self.SELECTED_WEAPON][1] = 'Fired'
                            self.FIRED_TORPEDOES[self.SELECTED_WEAPON] = [False, mode, -1]
                        elif self.WEAPON_LAYOUT[self.SELECTED_WEAPON][1] == 'Fired':
                            print("TORPEDO UPDATE!!")
                            distance = float(self.distance_var[1]) / 2  # converting to px
                            angle = self.LOCAL_POSITION[2] + float(self.bearing_var[1])
                            if angle > 360:
                                angle -= 360
                            mode = True
                            if self.mode_var == 0:
                                mode = False
                            impact_x = self.LOCAL_POSITION[0] - distance * math.cos(math.radians(angle + 90))
                            impact_y = self.LOCAL_POSITION[1] - distance * math.sin(math.radians(angle + 90))
                            torpedo_info = [
                                [self.LOCAL_POSITION[0], self.LOCAL_POSITION[1],
                                 self.LOCAL_POSITION[2], 'update', self.LOCAL_POSITION[3]],
                                [impact_x, impact_y, float(self.depth_var[1])], False, 'update', 'Enemy', 0,
                                mode, self.SELECTED_WEAPON]
                            self.UPDATE_TORP_QUEUE.append(f"{torpedo_info}")
                            self.WEAPON_LAYOUT[self.SELECTED_WEAPON][1] = 'Fired'
                    else:
                        self.LAUNCH_AUTH = [False, 3]

        elif event.type == pygame.KEYDOWN:
            if self.bearing_var[0]:
                if event.key == pygame.K_BACKSPACE:
                    self.bearing_var[1] = self.bearing_var[1][:-1]
                elif len(self.bearing_var[1]) <= 5:
                    if (pygame.key.name(event.key)).isnumeric():
                        self.bearing_var[1] += pygame.key.name(event.key)
                    elif pygame.key.name(event.key) == '.':
                        self.bearing_var[1] += '.'
            elif self.distance_var[0]:
                if event.key == pygame.K_BACKSPACE:
                    self.distance_var[1] = self.distance_var[1][:-1]
                elif event.key == pygame.K_UP:
                    self.distance_var[1] = str(float(self.distance_var[1]) + 1)
                elif event.key == pygame.K_DOWN:
                    self.distance_var[1] = str(float(self.distance_var[1]) - 1)
                elif len(self.distance_var[1]) <= 8:
                    if (pygame.key.name(event.key)).isnumeric():
                        self.distance_var[1] += pygame.key.name(event.key)
                    elif pygame.key.name(event.key) == '.':
                        self.distance_var[1] += '.'
            elif self.depth_var[0]:
                if event.key == pygame.K_BACKSPACE:
                    self.depth_var[1] = self.depth_var[1][:-1]
                elif event.key == pygame.K_UP:
                    self.depth_var[1] = str(float(self.depth_var[1]) + 1)
                elif event.key == pygame.K_DOWN:
                    self.depth_var[1] = str(float(self.depth_var[1]) - 1)
                elif len(self.depth_var[1]) <= 5:
                    if (pygame.key.name(event.key)).isnumeric():
                        self.depth_var[1] += pygame.key.name(event.key)
                    elif pygame.key.name(event.key) == '.':
                        self.depth_var[1] += '.'
            elif event.key == pygame.K_m:
                self.clear_scene()
                self.MAP_OPEN = True
                self.open_map()
                self.map_render()
            elif event.key == pygame.K_LCTRL:
                if self.GEAR > -3:
                    self.GEAR -= 1
                print(self.GEAR)
            elif event.key == pygame.K_LSHIFT:
                if self.GEAR != 3:
                    self.GEAR += 1
                print(self.GEAR)
            elif event.key == pygame.K_e:
                self.WEAPON_SCREEN = False
                self.SONAR_SCREEN = True
            elif event.key == pygame.K_r:
                for port in self.FRIENDLY_PORT_LOCATIONS:
                    rel_x = port[0] - self.LOCAL_POSITION[0]
                    rel_y = port[1] - self.LOCAL_POSITION[1]
                    distance = math.sqrt(rel_x * rel_x + rel_y * rel_y)
                    if distance <= 30:
                        for weapon in self.WEAPON_LAYOUT:
                            if not self.PLAYER_ID:
                                # RU
                                if self.WEAPON_LAYOUT[weapon][0][0] == 0:
                                    if self.WEAPON_LAYOUT[weapon][1] == '3M54-1 Kalibr':
                                        self.WEAPON_LAYOUT[weapon][1] = 'P-800 Oniks'
                                    else:
                                        self.WEAPON_LAYOUT[weapon][1] = '3M54-1 Kalibr'
                                else:
                                    if self.WEAPON_LAYOUT[weapon][1] == 'Futlyar':
                                        self.WEAPON_LAYOUT[weapon][1] = 'Sonar decoy'
                                    else:
                                        self.WEAPON_LAYOUT[weapon][1] = 'Futlyar'
                            else:
                                # USA
                                if self.WEAPON_LAYOUT[weapon][0][0] == 0:
                                    if self.WEAPON_LAYOUT[weapon][1] == 'TLAM-E':
                                        self.WEAPON_LAYOUT[weapon][1] = 'TASM'
                                    else:
                                        self.WEAPON_LAYOUT[weapon][1] = 'TLAM-E'
                                else:
                                    if self.WEAPON_LAYOUT[weapon][1] == 'Mk-48':
                                        self.WEAPON_LAYOUT[weapon][1] = 'UGM-84'
                                    elif self.WEAPON_LAYOUT[weapon][1] == 'UGM-84':
                                        self.WEAPON_LAYOUT[weapon][1] = 'Sonar decoy'
                                    else:
                                        self.WEAPON_LAYOUT[weapon][1] = 'Mk-48'
            elif event.key == pygame.K_TAB:
                self.clear_scene()
                self.SCOREBOARD_OPEN = True

    def weapon_screen_render(self):
        self.window.fill(0)
        self.render_notifications()

        # Splitter lines
        pygame.draw.line(self.window, '#b6b6d1', (300, 0), (300, self.size[1]))
        pygame.draw.line(self.window, '#b6b6d1', (300, 100), (self.size[0], 100))
        pygame.draw.line(self.window, '#b6b6d1', (0, 300), (300, 300))
        pygame.draw.line(self.window, '#b6b6d1', (self.size[0] - 320, 0), (self.size[0] - 320, self.size[1]))

        # Selected weapon information
        if self.SELECTED_WEAPON:
            txtsurf_ = self.middle_font.render(f'Weapon: ', True, '#b6b6d1')
            self.window.blit(txtsurf_, (self.size[0] - 300, 25 - txtsurf_.get_height() / 2))
            txtsurf = self.middle_font.render(f'{self.WEAPON_LAYOUT[self.SELECTED_WEAPON][1]}', True, '#DADAFA')
            self.window.blit(txtsurf, (self.size[0] - 300 + txtsurf_.get_width(), 25 - txtsurf.get_height() / 2))
            txtsurf_ = self.middle_font.render(f'Type: ', True, '#b6b6d1')
            self.window.blit(txtsurf_, (self.size[0] - 300, 50 - txtsurf_.get_height() / 2))
            if self.WEAPON_LAYOUT[self.SELECTED_WEAPON][1] == '3M54-1 Kalibr':
                txtsurf = self.middle_font.render(f'Land-attack missile', True, '#c95918')
                self.window.blit(txtsurf, (self.size[0] - 300 + txtsurf_.get_width(), 50 - txtsurf.get_height() / 2))
                # TODO: Add descriptions for all weapons
                txtsurf = self.middle_font.render(f'Characteristics:', True, '#b6b6d1')
                self.window.blit(txtsurf, (self.size[0] - 300, 125 - txtsurf.get_height() / 2))
                txtsurf_ = self.middle_font.render(f'Maximum range: ', True, '#b6b6d1')
                self.window.blit(txtsurf_, (self.size[0] - 300, 150 - txtsurf_.get_height() / 2))
                txtsurf = self.middle_font.render(f'300km', True, '#DADAFA')
                self.window.blit(txtsurf, (self.size[0] - 300 + txtsurf_.get_width(), 150 - txtsurf.get_height() / 2))
                txtsurf_ = self.middle_font.render(f'Max speed: ', True, '#b6b6d1')
                self.window.blit(txtsurf_, (self.size[0] - 300, 175 - txtsurf_.get_height() / 2))
                txtsurf = self.middle_font.render(f'3 Mach', True, '#DADAFA')
                self.window.blit(txtsurf, (self.size[0] - 300 + txtsurf_.get_width(), 175 - txtsurf.get_height() / 2))
                txtsurf_ = self.middle_font.render(f'Damage: ', True, '#b6b6d1')
                self.window.blit(txtsurf_, (self.size[0] - 300, 200 - txtsurf_.get_height() / 2))
                txtsurf = self.middle_font.render(f'25-50%', True, '#DADAFA')
                self.window.blit(txtsurf, (self.size[0] - 300 + txtsurf_.get_width(), 200 - txtsurf.get_height() / 2))
                txtsurf_ = self.middle_font.render(f'Sensor range: ', True, '#b6b6d1')
                self.window.blit(txtsurf_, (self.size[0] - 300, 225 - txtsurf_.get_height() / 2))
                txtsurf = self.middle_font.render(f'20km', True, '#DADAFA')
                self.window.blit(txtsurf, (self.size[0] - 300 + txtsurf_.get_width(), 225 - txtsurf.get_height() / 2))
                txtsurf_ = self.middle_font.render(f'Launch depth: ', True, '#b6b6d1')
                self.window.blit(txtsurf_, (self.size[0] - 300, 250 - txtsurf_.get_height() / 2))
                txtsurf = self.middle_font.render(f'60m', True, '#DADAFA')
                self.window.blit(txtsurf, (self.size[0] - 300 + txtsurf_.get_width(), 250 - txtsurf.get_height() / 2))
                txtsurf = self.middle_font.render(f'Description:', True, '#b6b6d1')
                self.window.blit(txtsurf, (self.size[0] - 300, 275 - txtsurf.get_height() / 2))
                desc = f"The Novator Kalibr, (Калибр, caliber),\nalso referred to as 3M54-1" \
                       f"Kalibr,\nis a family of Russian cruise " \
                       f"missiles\ndeveloped by NPO Novator (OKB-8).\nIt first saw service " \
                       f"in 1994. There are \nship-launched, submarine-launched\nand " \
                       f"air-launched versions of the missile.\nVariants are made for anti-ship,\n" \
                       f"anti-submarine and land attack\nuse. The missile can carry " \
                       f"a warhead\nweighing up to 500 kilograms\n(1,100 lb) of explosive."
                i = 0
                for line in desc.split('\n'):
                    txtsurf = self.middle_font.render(line, True, '#DADAFA')
                    self.window.blit(txtsurf, (self.size[0] - 300, 300 + i*25 - txtsurf.get_height() / 2))
                    i += 1
            elif self.WEAPON_LAYOUT[self.SELECTED_WEAPON][1] == 'P-800 Oniks':
                txtsurf = self.middle_font.render(f'Anti-ship missile', True, '#16c7c7')
                self.window.blit(txtsurf, (self.size[0] - 300 + txtsurf_.get_width(), 50 - txtsurf.get_height() / 2))
                # TODO: Add descriptions for all weapons
                txtsurf = self.middle_font.render(f'Characteristics:', True, '#b6b6d1')
                self.window.blit(txtsurf, (self.size[0] - 300, 125 - txtsurf.get_height() / 2))
                txtsurf_ = self.middle_font.render(f'Maximum range: ', True, '#b6b6d1')
                self.window.blit(txtsurf_, (self.size[0] - 300, 150 - txtsurf_.get_height() / 2))
                txtsurf = self.middle_font.render(f'80km', True, '#DADAFA')
                self.window.blit(txtsurf, (self.size[0] - 300 + txtsurf_.get_width(), 150 - txtsurf.get_height() / 2))
                txtsurf_ = self.middle_font.render(f'Max speed: ', True, '#b6b6d1')
                self.window.blit(txtsurf_, (self.size[0] - 300, 175 - txtsurf_.get_height() / 2))
                txtsurf = self.middle_font.render(f'2.6 Mach', True, '#DADAFA')
                self.window.blit(txtsurf, (self.size[0] - 300 + txtsurf_.get_width(), 175 - txtsurf.get_height() / 2))
                txtsurf_ = self.middle_font.render(f'Damage: ', True, '#b6b6d1')
                self.window.blit(txtsurf_, (self.size[0] - 300, 200 - txtsurf_.get_height() / 2))
                txtsurf = self.middle_font.render(f'40-60%', True, '#DADAFA')
                self.window.blit(txtsurf, (self.size[0] - 300 + txtsurf_.get_width(), 200 - txtsurf.get_height() / 2))
                txtsurf_ = self.middle_font.render(f'Sensor range: ', True, '#b6b6d1')
                self.window.blit(txtsurf_, (self.size[0] - 300, 225 - txtsurf_.get_height() / 2))
                txtsurf = self.middle_font.render(f'26km', True, '#DADAFA')
                self.window.blit(txtsurf, (self.size[0] - 300 + txtsurf_.get_width(), 225 - txtsurf.get_height() / 2))
                txtsurf_ = self.middle_font.render(f'Launch depth: ', True, '#b6b6d1')
                self.window.blit(txtsurf_, (self.size[0] - 300, 250 - txtsurf_.get_height() / 2))
                txtsurf = self.middle_font.render(f'60m', True, '#DADAFA')
                self.window.blit(txtsurf, (self.size[0] - 300 + txtsurf_.get_width(), 250 - txtsurf.get_height() / 2))
                txtsurf = self.middle_font.render(f'Description:', True, '#b6b6d1')
                self.window.blit(txtsurf, (self.size[0] - 300, 275 - txtsurf.get_height() / 2))
                desc = f"The P-800 Oniks (П-800 Оникс),\nalso known as " \
                       f"Yakhont\n(Russian: Яхонт; English: ruby), is\na Soviet / Russian supersonic anti-ship\ncruise" \
                       f"missile developed by\nNPO Mashinostroyeniya as a ramjet\nversion of P-80 Zubr. Its GRAU\n" \
                       f"designation is 3M55, the air\nlaunched Kh-61 variant also exists."
                i = 0
                for line in desc.split('\n'):
                    txtsurf = self.middle_font.render(line, True, '#DADAFA')
                    self.window.blit(txtsurf, (self.size[0] - 300, 300 + i*25 - txtsurf.get_height() / 2))
                    i += 1
            elif self.WEAPON_LAYOUT[self.SELECTED_WEAPON][1] == 'Futlyar':
                txtsurf = self.middle_font.render(f'Torpedo', True, '#263ded')
                self.window.blit(txtsurf, (self.size[0] - 300 + txtsurf_.get_width(), 50 - txtsurf.get_height() / 2))
                # TODO: Add descriptions for all weapons
                txtsurf = self.middle_font.render(f'Characteristics:', True, '#b6b6d1')
                self.window.blit(txtsurf, (self.size[0] - 300, 125 - txtsurf.get_height() / 2))
                txtsurf_ = self.middle_font.render(f'Maximum range: ', True, '#b6b6d1')
                self.window.blit(txtsurf_, (self.size[0] - 300, 150 - txtsurf_.get_height() / 2))
                txtsurf = self.middle_font.render(f'70km (eff. 45km)', True, '#DADAFA')
                self.window.blit(txtsurf, (self.size[0] - 300 + txtsurf_.get_width(), 150 - txtsurf.get_height() / 2))
                txtsurf_ = self.middle_font.render(f'Max speed: ', True, '#b6b6d1')
                self.window.blit(txtsurf_, (self.size[0] - 300, 175 - txtsurf_.get_height() / 2))
                txtsurf = self.middle_font.render(f'114 km/h', True, '#DADAFA')
                self.window.blit(txtsurf, (self.size[0] - 300 + txtsurf_.get_width(), 175 - txtsurf.get_height() / 2))
                txtsurf_ = self.middle_font.render(f'Damage: ', True, '#b6b6d1')
                self.window.blit(txtsurf_, (self.size[0] - 300, 200 - txtsurf_.get_height() / 2))
                txtsurf = self.middle_font.render(f'30-50%', True, '#DADAFA')
                self.window.blit(txtsurf, (self.size[0] - 300 + txtsurf_.get_width(), 200 - txtsurf.get_height() / 2))
                txtsurf_ = self.middle_font.render(f'Sensor range: ', True, '#b6b6d1')
                self.window.blit(txtsurf_, (self.size[0] - 300, 225 - txtsurf_.get_height() / 2))
                txtsurf = self.middle_font.render(f'20km/40km (active)', True, '#DADAFA')
                self.window.blit(txtsurf, (self.size[0] - 300 + txtsurf_.get_width(), 225 - txtsurf.get_height() / 2))
                txtsurf_ = self.middle_font.render(f'Launch depth: ', True, '#b6b6d1')
                self.window.blit(txtsurf_, (self.size[0] - 300, 250 - txtsurf_.get_height() / 2))
                txtsurf = self.middle_font.render(f'600m', True, '#DADAFA')
                self.window.blit(txtsurf, (self.size[0] - 300 + txtsurf_.get_width(), 250 - txtsurf.get_height() / 2))
                txtsurf = self.middle_font.render(f'Description:', True, '#b6b6d1')
                self.window.blit(txtsurf, (self.size[0] - 300, 275 - txtsurf.get_height() / 2))
                desc = f"Futlyar (Fizik-2) is a Russian\ndeep-water homing torpedo tested\nby the Russian " \
                       f"Navy in 2017; " \
                       f"it entered\nservice in the same year. Futlyar\nis a wire-guided, combustion-driven\n" \
                       f"torpedo " \
                       f"with " \
                       f"a top speed\nof 114km/h and a maximum depth\nof more than 500m. Homing\noptions " \
                       f"are Active or " \
                       f"Passive.\nActive utilises active sonar to\ntrack the target which increases\nthe " \
                       f"range at " \
                       f"which " \
                       f"the target\ncan be found, but\nexposes your position to the enemy."
                # TODO: Active torpedo mode makes you visible for a few seconds to an enemy in range.
                i = 0
                for line in desc.split('\n'):
                    txtsurf = self.middle_font.render(line, True, '#DADAFA')
                    self.window.blit(txtsurf, (self.size[0] - 300, 300 + i * 25 - txtsurf.get_height() / 2))
                    i += 1
            elif self.WEAPON_LAYOUT[self.SELECTED_WEAPON][1] == 'Sonar decoy':
                txtsurf = self.middle_font.render(f'Countermeasure', True, '#ffff82')
                self.window.blit(txtsurf, (self.size[0] - 300 + txtsurf_.get_width(), 50 - txtsurf.get_height() / 2))
                txtsurf = self.middle_font.render(f'Characteristics:', True, '#b6b6d1')
                self.window.blit(txtsurf, (self.size[0] - 300, 125 - txtsurf.get_height() / 2))
                txtsurf_ = self.middle_font.render(f'Maximum range: ', True, '#b6b6d1')
                self.window.blit(txtsurf_, (self.size[0] - 300, 150 - txtsurf_.get_height() / 2))
                txtsurf = self.middle_font.render(f'30km', True, '#DADAFA')
                self.window.blit(txtsurf, (self.size[0] - 300 + txtsurf_.get_width(), 150 - txtsurf.get_height() / 2))
                txtsurf_ = self.middle_font.render(f'Max speed: ', True, '#b6b6d1')
                self.window.blit(txtsurf_, (self.size[0] - 300, 175 - txtsurf_.get_height() / 2))
                txtsurf = self.middle_font.render(f'54 km/h', True, '#DADAFA')
                self.window.blit(txtsurf, (self.size[0] - 300 + txtsurf_.get_width(), 175 - txtsurf.get_height() / 2))
                txtsurf_ = self.middle_font.render(f'Launch depth: ', True, '#b6b6d1')
                self.window.blit(txtsurf_, (self.size[0] - 300, 200 - txtsurf_.get_height() / 2))
                txtsurf = self.middle_font.render(f'400m', True, '#DADAFA')
                self.window.blit(txtsurf, (self.size[0] - 300 + txtsurf_.get_width(), 200 - txtsurf.get_height() / 2))
                txtsurf = self.middle_font.render(f'Description:', True, '#b6b6d1')
                self.window.blit(txtsurf, (self.size[0] - 300, 225 - txtsurf.get_height() / 2))
                desc = f"Sonar decoy is a countermeasure\nagainst torpedoes. It is fired\nfrom a torpedo " \
                       f"tube and has\nan increased sonar signature to\nfool sensors on a torpedo. " \
                       f"Newer models\nare fitted with a noisemaker\nwhich can fool enemy passive sonar.\n" \
                       f"Once deployed the decoy will go to the\nspecified bearing and distance before\n" \
                       f"self destructing. There are two\nmodes, active and passive,\nactive mode will simulate " \
                       f"active\nsonar echoes coming from the\ntarget which can confuse\nenemy active sonar " \
                       f"torpedoes\nbut will not be effective\nagainst the passive sensors."
                i = 0
                for line in desc.split('\n'):
                    txtsurf = self.middle_font.render(line, True, '#DADAFA')
                    self.window.blit(txtsurf, (self.size[0] - 300, 250 + i * 25 - txtsurf.get_height() / 2))
                    i += 1
            elif self.WEAPON_LAYOUT[self.SELECTED_WEAPON][1] == 'Mk-48':
                txtsurf = self.middle_font.render(f'Torpedo', True, '#263ded')
                self.window.blit(txtsurf, (self.size[0] - 300 + txtsurf_.get_width(), 50 - txtsurf.get_height() / 2))
                # TODO: Add descriptions for all weapons
                txtsurf = self.middle_font.render(f'Characteristics:', True, '#b6b6d1')
                self.window.blit(txtsurf, (self.size[0] - 300, 125 - txtsurf.get_height() / 2))
                txtsurf_ = self.middle_font.render(f'Maximum range: ', True, '#b6b6d1')
                self.window.blit(txtsurf_, (self.size[0] - 300, 150 - txtsurf_.get_height() / 2))
                txtsurf = self.middle_font.render(f'70km (eff. 45km)', True, '#DADAFA')
                self.window.blit(txtsurf, (self.size[0] - 300 + txtsurf_.get_width(), 150 - txtsurf.get_height() / 2))
                txtsurf_ = self.middle_font.render(f'Max speed: ', True, '#b6b6d1')
                self.window.blit(txtsurf_, (self.size[0] - 300, 175 - txtsurf_.get_height() / 2))
                txtsurf = self.middle_font.render(f'106 km/h', True, '#DADAFA')
                self.window.blit(txtsurf, (self.size[0] - 300 + txtsurf_.get_width(), 175 - txtsurf.get_height() / 2))
                txtsurf_ = self.middle_font.render(f'Damage: ', True, '#b6b6d1')
                self.window.blit(txtsurf_, (self.size[0] - 300, 200 - txtsurf_.get_height() / 2))
                txtsurf = self.middle_font.render(f'30-50%', True, '#DADAFA')
                self.window.blit(txtsurf, (self.size[0] - 300 + txtsurf_.get_width(), 200 - txtsurf.get_height() / 2))
                txtsurf_ = self.middle_font.render(f'Sensor range: ', True, '#b6b6d1')
                self.window.blit(txtsurf_, (self.size[0] - 300, 225 - txtsurf_.get_height() / 2))
                txtsurf = self.middle_font.render(f'20km/40km (active)', True, '#DADAFA')
                self.window.blit(txtsurf, (self.size[0] - 300 + txtsurf_.get_width(), 225 - txtsurf.get_height() / 2))
                txtsurf_ = self.middle_font.render(f'Launch depth: ', True, '#b6b6d1')
                self.window.blit(txtsurf_, (self.size[0] - 300, 250 - txtsurf_.get_height() / 2))
                txtsurf = self.middle_font.render(f'800m', True, '#DADAFA')
                self.window.blit(txtsurf, (self.size[0] - 300 + txtsurf_.get_width(), 250 - txtsurf.get_height() / 2))
                txtsurf = self.middle_font.render(f'Description:', True, '#b6b6d1')
                self.window.blit(txtsurf, (self.size[0] - 300, 275 - txtsurf.get_height() / 2))
                desc = f"The Mark 48 and its improved\nAdvanced Capability (ADCAP) variant\nare American heavyweight\n" \
                       f"submarine-launched torpedoes.\nThey were designed to sink\ndeep-diving nuclear-powered\n" \
                       f"submarines and high-performance\n surface ships." \
                       f"It has a top speed\nof 114km/h and a maximum depth\nof more than 500m. Homing\noptions " \
                       f"are Active or " \
                       f"Passive.\nActive utilises active sonar to\ntrack the target which increases\nthe " \
                       f"range at " \
                       f"which " \
                       f"the target\ncan be found, but\nexposes your position to the enemy."
                # TODO: Active torpedo mode makes you visible for a few seconds to an enemy in range.
                i = 0
                for line in desc.split('\n'):
                    txtsurf = self.middle_font.render(line, True, '#DADAFA')
                    self.window.blit(txtsurf, (self.size[0] - 300, 300 + i * 25 - txtsurf.get_height() / 2))
                    i += 1
            elif self.WEAPON_LAYOUT[self.SELECTED_WEAPON][1] == 'TLAM-E':
                txtsurf = self.middle_font.render(f'Land-attack missile', True, '#c95918')
                self.window.blit(txtsurf, (self.size[0] - 300 + txtsurf_.get_width(), 50 - txtsurf.get_height() / 2))
                # TODO: Add descriptions for all weapons
                txtsurf = self.middle_font.render(f'Characteristics:', True, '#b6b6d1')
                self.window.blit(txtsurf, (self.size[0] - 300, 125 - txtsurf.get_height() / 2))
                txtsurf_ = self.middle_font.render(f'Maximum range: ', True, '#b6b6d1')
                self.window.blit(txtsurf_, (self.size[0] - 300, 150 - txtsurf_.get_height() / 2))
                txtsurf = self.middle_font.render(f'400km', True, '#DADAFA')
                self.window.blit(txtsurf, (self.size[0] - 300 + txtsurf_.get_width(), 150 - txtsurf.get_height() / 2))
                txtsurf_ = self.middle_font.render(f'Max speed: ', True, '#b6b6d1')
                self.window.blit(txtsurf_, (self.size[0] - 300, 175 - txtsurf_.get_height() / 2))
                txtsurf = self.middle_font.render(f'0.74 Mach', True, '#DADAFA')
                self.window.blit(txtsurf, (self.size[0] - 300 + txtsurf_.get_width(), 175 - txtsurf.get_height() / 2))
                txtsurf_ = self.middle_font.render(f'Damage: ', True, '#b6b6d1')
                self.window.blit(txtsurf_, (self.size[0] - 300, 200 - txtsurf_.get_height() / 2))
                txtsurf = self.middle_font.render(f'40-60%', True, '#DADAFA')
                self.window.blit(txtsurf, (self.size[0] - 300 + txtsurf_.get_width(), 200 - txtsurf.get_height() / 2))
                txtsurf_ = self.middle_font.render(f'Sensor range: ', True, '#b6b6d1')
                self.window.blit(txtsurf_, (self.size[0] - 300, 225 - txtsurf_.get_height() / 2))
                txtsurf = self.middle_font.render(f'60km', True, '#DADAFA')
                self.window.blit(txtsurf, (self.size[0] - 300 + txtsurf_.get_width(), 225 - txtsurf.get_height() / 2))
                txtsurf_ = self.middle_font.render(f'Launch depth: ', True, '#b6b6d1')
                self.window.blit(txtsurf_, (self.size[0] - 300, 250 - txtsurf_.get_height() / 2))
                txtsurf = self.middle_font.render(f'60m', True, '#DADAFA')
                self.window.blit(txtsurf, (self.size[0] - 300 + txtsurf_.get_width(), 250 - txtsurf.get_height() / 2))
                txtsurf = self.middle_font.render(f'Description:', True, '#b6b6d1')
                self.window.blit(txtsurf, (self.size[0] - 300, 275 - txtsurf.get_height() / 2))
                desc = f"The Tomahawk Land Attack Missile\n(TLAM) is a long-range, all-weather,\njet-powered, subsonic " \
                       f"cruise\nmissile that is primarily used\nby the United States Navy\nand Royal Navy in ship\nand " \
                       f"submarine-based\nland-attack operations.\nMissile possesses an advanced\ncourse correction " \
                       f"system\ncalled TERCOM (Terrain Contour\nMatching). " \
                       f"This system allows for\nlow altitude flight and precise routes."
                i = 0
                for line in desc.split('\n'):
                    txtsurf = self.middle_font.render(line, True, '#DADAFA')
                    self.window.blit(txtsurf, (self.size[0] - 300, 300 + i*25 - txtsurf.get_height() / 2))
                    i += 1
            elif self.WEAPON_LAYOUT[self.SELECTED_WEAPON][1] == 'TASM':
                txtsurf = self.middle_font.render(f'Anti-ship missile', True, '#16c7c7')
                self.window.blit(txtsurf, (self.size[0] - 300 + txtsurf_.get_width(), 50 - txtsurf.get_height() / 2))
                # TODO: Add descriptions for all weapons
                txtsurf = self.middle_font.render(f'Characteristics:', True, '#b6b6d1')
                self.window.blit(txtsurf, (self.size[0] - 300, 125 - txtsurf.get_height() / 2))
                txtsurf_ = self.middle_font.render(f'Maximum range: ', True, '#b6b6d1')
                self.window.blit(txtsurf_, (self.size[0] - 300, 150 - txtsurf_.get_height() / 2))
                txtsurf = self.middle_font.render(f'110km', True, '#DADAFA')
                self.window.blit(txtsurf, (self.size[0] - 300 + txtsurf_.get_width(), 150 - txtsurf.get_height() / 2))
                txtsurf_ = self.middle_font.render(f'Max speed: ', True, '#b6b6d1')
                self.window.blit(txtsurf_, (self.size[0] - 300, 175 - txtsurf_.get_height() / 2))
                txtsurf = self.middle_font.render(f'0.8 Mach', True, '#DADAFA')
                self.window.blit(txtsurf, (self.size[0] - 300 + txtsurf_.get_width(), 175 - txtsurf.get_height() / 2))
                txtsurf_ = self.middle_font.render(f'Damage: ', True, '#b6b6d1')
                self.window.blit(txtsurf_, (self.size[0] - 300, 200 - txtsurf_.get_height() / 2))
                txtsurf = self.middle_font.render(f'50-65%', True, '#DADAFA')
                self.window.blit(txtsurf, (self.size[0] - 300 + txtsurf_.get_width(), 200 - txtsurf.get_height() / 2))
                txtsurf_ = self.middle_font.render(f'Sensor range: ', True, '#b6b6d1')
                self.window.blit(txtsurf_, (self.size[0] - 300, 225 - txtsurf_.get_height() / 2))
                txtsurf = self.middle_font.render(f'30km', True, '#DADAFA')
                self.window.blit(txtsurf, (self.size[0] - 300 + txtsurf_.get_width(), 225 - txtsurf.get_height() / 2))
                txtsurf_ = self.middle_font.render(f'Launch depth: ', True, '#b6b6d1')
                self.window.blit(txtsurf_, (self.size[0] - 300, 250 - txtsurf_.get_height() / 2))
                txtsurf = self.middle_font.render(f'60m', True, '#DADAFA')
                self.window.blit(txtsurf, (self.size[0] - 300 + txtsurf_.get_width(), 250 - txtsurf.get_height() / 2))
                txtsurf = self.middle_font.render(f'Description:', True, '#b6b6d1')
                self.window.blit(txtsurf, (self.size[0] - 300, 275 - txtsurf.get_height() / 2))
                desc = f"The TASM was the first version\nof the anti-ship variant\nof the Tomahawk, equipped\nwith an " \
                       f"active radar\nseeker, rather than TERCOM.\nTASM, along with other Tomahawk\nconventional " \
                       f"variants,\ncarried a 454 kg conventional\nwarhead. Its range was\nshorter than other " \
                       f"variants\n" \
                       f"but it was known for its agility,\ncapable of various flight patterns.\nDue to the lower " \
                       f"speeds\nof the missile, ship defence\nsystems have an easier time\nshooting them down."
                i = 0
                for line in desc.split('\n'):
                    txtsurf = self.middle_font.render(line, True, '#DADAFA')
                    self.window.blit(txtsurf, (self.size[0] - 300, 300 + i*25 - txtsurf.get_height() / 2))
                    i += 1
            elif self.WEAPON_LAYOUT[self.SELECTED_WEAPON][1] == 'UGM-84':
                txtsurf = self.middle_font.render(f'Anti-ship missile', True, '#16c7c7')
                self.window.blit(txtsurf, (self.size[0] - 300 + txtsurf_.get_width(), 50 - txtsurf.get_height() / 2))
                # TODO: Add descriptions for all weapons
                txtsurf = self.middle_font.render(f'Characteristics:', True, '#b6b6d1')
                self.window.blit(txtsurf, (self.size[0] - 300, 125 - txtsurf.get_height() / 2))
                txtsurf_ = self.middle_font.render(f'Maximum range: ', True, '#b6b6d1')
                self.window.blit(txtsurf_, (self.size[0] - 300, 150 - txtsurf_.get_height() / 2))
                txtsurf = self.middle_font.render(f'90km', True, '#DADAFA')
                self.window.blit(txtsurf, (self.size[0] - 300 + txtsurf_.get_width(), 150 - txtsurf.get_height() / 2))
                txtsurf_ = self.middle_font.render(f'Max speed: ', True, '#b6b6d1')
                self.window.blit(txtsurf_, (self.size[0] - 300, 175 - txtsurf_.get_height() / 2))
                txtsurf = self.middle_font.render(f'0.92 Mach', True, '#DADAFA')
                self.window.blit(txtsurf, (self.size[0] - 300 + txtsurf_.get_width(), 175 - txtsurf.get_height() / 2))
                txtsurf_ = self.middle_font.render(f'Damage: ', True, '#b6b6d1')
                self.window.blit(txtsurf_, (self.size[0] - 300, 200 - txtsurf_.get_height() / 2))
                txtsurf = self.middle_font.render(f'45-65%', True, '#DADAFA')
                self.window.blit(txtsurf, (self.size[0] - 300 + txtsurf_.get_width(), 200 - txtsurf.get_height() / 2))
                txtsurf_ = self.middle_font.render(f'Sensor range: ', True, '#b6b6d1')
                self.window.blit(txtsurf_, (self.size[0] - 300, 225 - txtsurf_.get_height() / 2))
                txtsurf = self.middle_font.render(f'32km', True, '#DADAFA')
                self.window.blit(txtsurf, (self.size[0] - 300 + txtsurf_.get_width(), 225 - txtsurf.get_height() / 2))
                txtsurf_ = self.middle_font.render(f'Launch depth: ', True, '#b6b6d1')
                self.window.blit(txtsurf_, (self.size[0] - 300, 250 - txtsurf_.get_height() / 2))
                txtsurf = self.middle_font.render(f'100m', True, '#DADAFA')
                self.window.blit(txtsurf, (self.size[0] - 300 + txtsurf_.get_width(), 250 - txtsurf.get_height() / 2))
                txtsurf = self.middle_font.render(f'Description:', True, '#b6b6d1')
                self.window.blit(txtsurf, (self.size[0] - 300, 275 - txtsurf.get_height() / 2))
                desc = f"The Harpoon is an all-weather,\nover-the-horizon, anti-ship\nmissile manufactured by\n" \
                       f"McDonnell Douglas. There\nare also " \
                       f"cruise missile\nvariants.The regular Harpoon\nuses active radar homing\nand flies just above " \
                       f"the\nwater and due to being\nslightly faster than the\nTomahawk TASM it can evade\n" \
                       f"defenses a bit easier. The\nmissile can be launched from\nvarious platforms including\n" \
                       f"torpedo tubes on submarines."
                i = 0
                for line in desc.split('\n'):
                    txtsurf = self.middle_font.render(line, True, '#DADAFA')
                    self.window.blit(txtsurf, (self.size[0] - 300, 300 + i*25 - txtsurf.get_height() / 2))
                    i += 1

        # Fired ordnance information
        i = 0
        for missile in self.LAM_FIRED:
            if missile[0] > 0:
                txtsurf = self.middle_font.render(f"{missile[4]}: Impact in: {float(missile[0]):.2f}", True, '#b6b6d1')
                self.window.blit(txtsurf, (20, 320 + i * 20))
            else:
                if missile[3] == "Target hit!":
                    txtsurf = self.middle_font.render(f"{missile[4]}: {missile[3]}", True, 'green')
                    self.window.blit(txtsurf, (20, 320 + i * 20))
                else:
                    txtsurf = self.middle_font.render(f"{missile[4]}: {missile[3]}", True, 'red')
                    self.window.blit(txtsurf, (20, 320 + i * 20))
            i += 1
        for missile in self.ASM_FIRED:
            if missile[0] > 0:
                txtsurf = self.middle_font.render(f"{missile[4]}: Impact in: {float(missile[0]):.2f}", True, '#b6b6d1')
                self.window.blit(txtsurf, (20, 320 + i * 20))
            else:
                if missile[3] == "Target hit!":
                    txtsurf = self.middle_font.render(f"{missile[4]}: {missile[3]}", True, 'green')
                    self.window.blit(txtsurf, (20, 320 + i * 20))
                else:
                    txtsurf = self.middle_font.render(f"{missile[4]}: {missile[3]}", True, 'red')
                    self.window.blit(txtsurf, (20, 320 + i * 20))
            i += 1
        for torpedo in self.FIRED_TORPEDOES:
            index = list(self.WEAPON_LAYOUT.keys()).index(torpedo) - 31
            txtsurf1 = self.middle_font.render(
                f"Torp {index}: ", True,
                '#b6b6d1')
            self.window.blit(txtsurf1, (20, 320 + i * 20))
            color = "red"
            if self.FIRED_TORPEDOES[torpedo][0]:
                color = "green"
            txtsurf2 = self.middle_font.render(
                f"S:{self.FIRED_TORPEDOES[torpedo][0]} ", True,
                color)
            self.window.blit(txtsurf2, (20 + txtsurf1.get_width(), 320 + i * 20))
            color = "red"
            if self.FIRED_TORPEDOES[torpedo][1]:
                color = "green"
            txtsurf3 = self.middle_font.render(
                f"M: {self.FIRED_TORPEDOES[torpedo][1]}", True,
                color)
            self.window.blit(txtsurf3, (20 + txtsurf2.get_width() + txtsurf1.get_width(), 320 + i * 20))
            i += 1

        # Position details
        speed = self.LOCAL_VELOCITY * self.fps
        txtsurf = self.middle_font.render(f"Speed: ", True, '#b6b6d1')
        self.window.blit(txtsurf, (20, 30))
        txtsurf = self.middle_font.render(f"Gear: ", True, '#b6b6d1')
        self.window.blit(txtsurf, (20, 55))
        txtsurf = self.middle_font.render(f"Depth: ", True, '#b6b6d1')
        self.window.blit(txtsurf, (20, 80))
        txtsurf = self.middle_font.render(f"Pitch: ", True, '#b6b6d1')
        self.window.blit(txtsurf, (20, 105))
        txtsurf = self.middle_font.render(f"Heading: ", True, '#b6b6d1')
        self.window.blit(txtsurf, (20, 130))
        txtsurf = self.middle_font.render(f"Ballast: ", True, '#b6b6d1')
        self.window.blit(txtsurf, (20, 155))
        txtsurf = self.middle_font.render(f"Health: ", True, '#b6b6d1')
        self.window.blit(txtsurf, (20, 180))
        # txtsurf = self.middle_font.render(f"X: ", True, '#b6b6d1')
        # self.window.blit(txtsurf, (20, 180))
        # txtsurf = self.middle_font.render(f"Y: ", True, '#b6b6d1')
        # self.window.blit(txtsurf, (20, 205))

        txtsurf = self.middle_font.render(f"{speed / 0.0193:.2f}km/h", True, '#b6b6d1')
        self.window.blit(txtsurf, (100, 30))
        txtsurf = self.middle_font.render(f"{self.GEAR}", True, '#b6b6d1')
        self.window.blit(txtsurf, (100, 55))
        txtsurf = self.middle_font.render(f"{self.LOCAL_POSITION[4]:.2f}", True, '#b6b6d1')
        self.window.blit(txtsurf, (100, 80))
        txtsurf = self.middle_font.render(f"{self.LOCAL_POSITION[3]:.2f}", True, '#b6b6d1')
        self.window.blit(txtsurf, (100, 105))
        heading = self.LOCAL_POSITION[2]
        if heading < 0:
            heading += 360
        txtsurf = self.middle_font.render(f"{heading:.2f}", True, '#b6b6d1')
        self.window.blit(txtsurf, (100, 130))
        txtsurf = self.middle_font.render(f"{self.BALLAST:.2f}", True, '#b6b6d1')
        self.window.blit(txtsurf, (100, 155))
        txtsurf = self.middle_font.render(f"{self.HEALTH:.2f}", True, '#b6b6d1')
        self.window.blit(txtsurf, (100, 180))
        # txtsurf = self.middle_font.render(f"{self.LOCAL_POSITION[0]:.2f}", True, '#b6b6d1')
        # self.window.blit(txtsurf, (100, 180))
        # txtsurf = self.middle_font.render(f"{self.LOCAL_POSITION[1]:.2f}", True, '#b6b6d1')
        # self.window.blit(txtsurf, (100, 205))

        # Russian weapon layout
        if not self.PLAYER_ID:
            # Vertical Launch System
            for i in range(8):
                rect = (320, 120 + i * 40, 50, 7)
                if rect not in list(self.WEAPON_LAYOUT):
                    self.WEAPON_LAYOUT[rect] = [(0, 0), '']
                if self.WEAPON_LAYOUT[rect][1] != '':
                    if self.WEAPON_LAYOUT[rect][1] == '3M54-1 Kalibr':
                        pygame.draw.rect(self.window, '#c95918', rect, border_radius=5)
                    else:
                        pygame.draw.rect(self.window, '#16c7c7', rect, border_radius=5)
                    txtsurf = self.small_font.render(self.WEAPON_LAYOUT[rect][1], True, '#b6b6d1')
                    self.window.blit(txtsurf, (rect[0], rect[1] + 10))
                # [Rect] VLS/T (Tube/Storage), Weapon type
                pygame.draw.rect(self.window, 'red', rect, border_radius=5, width=1)
            txtsurf = self.small_font.render("VLS", True, '#b6b6d1')
            self.window.blit(txtsurf, mid_rect((320, 440, 50, 7), txtsurf))
            kalibr = 0
            oniks = 0
            futlyar = 0
            decoy = 0
            for weapon in self.WEAPON_LAYOUT:
                if self.WEAPON_LAYOUT[weapon][1] == '3M54-1 Kalibr':
                    kalibr += 1
                elif self.WEAPON_LAYOUT[weapon][1] == 'P-800 Oniks':
                    oniks += 1
                elif self.WEAPON_LAYOUT[weapon][1] == 'Futlyar':
                    futlyar += 1
                elif self.WEAPON_LAYOUT[weapon][1] == 'Sonar decoy':
                    decoy += 1
            i = 0
            if kalibr:
                txtsurf = self.small_font.render(f"Kalibr: {kalibr}", True, '#b6b6d1')
                self.window.blit(txtsurf, mid_rect((320, 460, 50, 7), txtsurf))
                i += 1
            if oniks:
                txtsurf = self.small_font.render(f"Oniks: {oniks}", True, '#b6b6d1')
                self.window.blit(txtsurf, mid_rect((320, 460 + i * 20, 50, 7), txtsurf))
            # VLS Storage
            for j in range(3):
                for i in range(8):
                    rect = (400 + j * 80, 120 + i * 40, 50, 7)
                    if rect not in list(self.WEAPON_LAYOUT):
                        self.WEAPON_LAYOUT[rect] = [(0, 1), '']
                    if self.WEAPON_LAYOUT[rect][1] != '':
                        if self.WEAPON_LAYOUT[rect][1] == '3M54-1 Kalibr':
                            pygame.draw.rect(self.window, '#c95918', rect, border_radius=5)
                        else:
                            pygame.draw.rect(self.window, '#16c7c7', rect, border_radius=5)
                        txtsurf = self.small_font.render(self.WEAPON_LAYOUT[rect][1], True, '#b6b6d1')
                        self.window.blit(txtsurf, (rect[0], rect[1] + 10))
                    pygame.draw.rect(self.window, '#b6b6d1', rect, border_radius=5, width=1)
            txtsurf = self.small_font.render("VLS Storage", True, '#b6b6d1')
            self.window.blit(txtsurf, mid_rect((480, 440, 50, 7), txtsurf))
            # Torpedo tubes
            for i in range(10):
                rect = (640, 120 + i * 40, 50, 7)
                if rect not in list(self.WEAPON_LAYOUT):
                    self.WEAPON_LAYOUT[rect] = [(1, 0), '']
                if self.WEAPON_LAYOUT[rect][1] != '':
                    if self.WEAPON_LAYOUT[rect][1] == 'Futlyar':
                        pygame.draw.rect(self.window, '#263ded', rect, border_radius=5)
                    elif self.WEAPON_LAYOUT[rect][1] == 'Fired':
                        pygame.draw.rect(self.window, '#5e0801', rect, border_radius=5)
                    else:
                        pygame.draw.rect(self.window, '#ffff82', rect, border_radius=5)
                    txtsurf = self.small_font.render(self.WEAPON_LAYOUT[rect][1], True, '#b6b6d1')
                    self.window.blit(txtsurf, (rect[0], rect[1] + 10))
                pygame.draw.rect(self.window, 'red', rect, border_radius=5, width=1)
            txtsurf = self.small_font.render("Torpedo", True, '#b6b6d1')
            self.window.blit(txtsurf, mid_rect((640, 520, 50, 7), txtsurf))
            txtsurf = self.small_font.render("tubes", True, '#b6b6d1')
            self.window.blit(txtsurf, mid_rect((640, 530, 50, 7), txtsurf))
            i = 0
            if futlyar:
                txtsurf = self.small_font.render(f"Futlyar: {futlyar}", True, '#b6b6d1')
                self.window.blit(txtsurf, mid_rect((640, 550 + i * 20, 50, 7), txtsurf))
                i += 1
            if decoy:
                txtsurf = self.small_font.render(f"Sonar decoy: {decoy}", True, '#b6b6d1')
                self.window.blit(txtsurf, mid_rect((640, 550 + i * 20, 50, 7), txtsurf))

            # Torpedo tube storage
            for j in range(3):
                for i in range(10):
                    rect = (720 + j * 80, 120 + i * 40, 50, 7)
                    if rect not in list(self.WEAPON_LAYOUT):
                        self.WEAPON_LAYOUT[rect] = [(1, 1), '']
                    if self.WEAPON_LAYOUT[rect][1] != '':
                        if self.WEAPON_LAYOUT[rect][1] == 'Futlyar':
                            pygame.draw.rect(self.window, '#263ded', rect, border_radius=5)
                        else:
                            pygame.draw.rect(self.window, '#ffff82', rect, border_radius=5)
                        txtsurf = self.small_font.render(self.WEAPON_LAYOUT[rect][1], True, '#b6b6d1')
                        self.window.blit(txtsurf, (rect[0], rect[1] + 10))
                    pygame.draw.rect(self.window, '#b6b6d1', rect, border_radius=5, width=1)
            txtsurf = self.small_font.render("Torpedo", True, '#b6b6d1')
            self.window.blit(txtsurf, mid_rect((800, 520, 50, 7), txtsurf))
            txtsurf = self.small_font.render("storage", True, '#b6b6d1')
            self.window.blit(txtsurf, mid_rect((800, 530, 50, 7), txtsurf))
        else:
            # American weapon layout
            # Vertical Launch System
            for i in range(12):
                rect = (320, 120 + i * 40, 50, 7)
                if rect not in list(self.WEAPON_LAYOUT):
                    self.WEAPON_LAYOUT[rect] = [(0, 0), '']
                if self.WEAPON_LAYOUT[rect][1] != '':
                    if self.WEAPON_LAYOUT[rect][1] == 'TLAM-E':
                        pygame.draw.rect(self.window, '#c95918', rect, border_radius=5)
                    else:
                        pygame.draw.rect(self.window, '#16c7c7', rect, border_radius=5)
                    txtsurf = self.small_font.render(self.WEAPON_LAYOUT[rect][1], True, '#b6b6d1')
                    self.window.blit(txtsurf, (rect[0], rect[1] + 10))
                # [Rect] VLS/T (Tube/Storage), Weapon type
                pygame.draw.rect(self.window, 'red', rect, border_radius=5, width=1)
            txtsurf = self.small_font.render("VLS", True, '#b6b6d1')
            self.window.blit(txtsurf, mid_rect((320, 600, 50, 7), txtsurf))
            tlam = 0
            tasm = 0
            mk48 = 0
            ugm84 = 0
            decoy = 0
            for weapon in self.WEAPON_LAYOUT:
                if self.WEAPON_LAYOUT[weapon][1] == 'TLAM-E':
                    tlam += 1
                elif self.WEAPON_LAYOUT[weapon][1] == 'TASM':
                    tasm += 1
                elif self.WEAPON_LAYOUT[weapon][1] == 'Mk-48':
                    mk48 += 1
                elif self.WEAPON_LAYOUT[weapon][1] == 'UGM-84':
                    ugm84 += 1
                elif self.WEAPON_LAYOUT[weapon][1] == 'Sonar decoy':
                    decoy += 1
            i = 0
            if tlam:
                txtsurf = self.small_font.render(f"TLAM-E: {tlam}", True, '#b6b6d1')
                self.window.blit(txtsurf, mid_rect((320, 620, 50, 7), txtsurf))
                i += 1
            if tasm:
                txtsurf = self.small_font.render(f"TASM: {tasm}", True, '#b6b6d1')
                self.window.blit(txtsurf, mid_rect((320, 620 + i * 20, 50, 7), txtsurf))

            for j in range(2):
                for i in range(12):
                    rect = (400 + j * 80, 120 + i * 40, 50, 7)
                    if rect not in list(self.WEAPON_LAYOUT):
                        self.WEAPON_LAYOUT[rect] = [(0, 1), '']
                    if self.WEAPON_LAYOUT[rect][1] != '':
                        if self.WEAPON_LAYOUT[rect][1] == 'TLAM-E':
                            pygame.draw.rect(self.window, '#c95918', rect, border_radius=5)
                        else:
                            pygame.draw.rect(self.window, '#16c7c7', rect, border_radius=5)
                        txtsurf = self.small_font.render(self.WEAPON_LAYOUT[rect][1], True, '#b6b6d1')
                        self.window.blit(txtsurf, (rect[0], rect[1] + 10))
                    pygame.draw.rect(self.window, '#b6b6d1', rect, border_radius=5, width=1)
            txtsurf = self.small_font.render("VLS Storage", True, '#b6b6d1')
            self.window.blit(txtsurf, mid_rect((480, 600, 50, 7), txtsurf))
            for i in range(4):
                rect = (560, 120 + i * 40, 50, 7)
                if rect not in list(self.WEAPON_LAYOUT):
                    self.WEAPON_LAYOUT[rect] = [(0, 1), '']
                if self.WEAPON_LAYOUT[rect][1] != '':
                    if self.WEAPON_LAYOUT[rect][1] == 'TLAM-E':
                        pygame.draw.rect(self.window, '#c95918', rect, border_radius=5)
                    else:
                        pygame.draw.rect(self.window, '#16c7c7', rect, border_radius=5)
                    txtsurf = self.small_font.render(self.WEAPON_LAYOUT[rect][1], True, '#b6b6d1')
                    self.window.blit(txtsurf, (rect[0], rect[1] + 10))
                pygame.draw.rect(self.window, '#b6b6d1', rect, border_radius=5, width=1)
            # Torpedo tubes
            for i in range(4):
                rect = (640, 120 + i * 40, 50, 7)
                if rect not in list(self.WEAPON_LAYOUT):
                    self.WEAPON_LAYOUT[rect] = [(1, 0), '']
                if self.WEAPON_LAYOUT[rect][1] != '':
                    if self.WEAPON_LAYOUT[rect][1] == 'Mk-48':
                        pygame.draw.rect(self.window, '#263ded', rect, border_radius=5)
                    elif self.WEAPON_LAYOUT[rect][1] == 'UGM-84':
                        pygame.draw.rect(self.window, '#16c7c7', rect, border_radius=5)
                    elif self.WEAPON_LAYOUT[rect][1] == 'Fired':
                        pygame.draw.rect(self.window, '#5e0801', rect, border_radius=5)
                    else:
                        pygame.draw.rect(self.window, '#ffff82', rect, border_radius=5)
                    txtsurf = self.small_font.render(self.WEAPON_LAYOUT[rect][1], True, '#b6b6d1')
                    self.window.blit(txtsurf, (rect[0], rect[1] + 10))
                pygame.draw.rect(self.window, 'red', rect, border_radius=5, width=1)
            txtsurf = self.small_font.render(f"Torpedo", True, '#b6b6d1')
            self.window.blit(txtsurf, mid_rect((640, 280, 50, 7), txtsurf))
            txtsurf = self.small_font.render(f"tubes", True, '#b6b6d1')
            self.window.blit(txtsurf, mid_rect((640, 290, 50, 7), txtsurf))
            i = 0
            if mk48:
                txtsurf = self.small_font.render(f"Mk-48: {mk48}", True, '#b6b6d1')
                self.window.blit(txtsurf, mid_rect((640, 310 + i * 20, 50, 7), txtsurf))
                i += 1
            if ugm84:
                txtsurf = self.small_font.render(f"UGM-84: {ugm84}", True, '#b6b6d1')
                self.window.blit(txtsurf, mid_rect((640, 310 + i * 20, 50, 7), txtsurf))
                i += 1
            if decoy:
                txtsurf = self.small_font.render(f"Sonar decoy: {decoy}", True, '#b6b6d1')
                self.window.blit(txtsurf, mid_rect((640, 310 + i * 20, 50, 7), txtsurf))
            for j in range(2):
                for i in range(11):
                    rect = (720 + j * 80, 120 + i * 40, 50, 7)
                    if rect not in list(self.WEAPON_LAYOUT):
                        self.WEAPON_LAYOUT[rect] = [(1, 1), '']
                    if self.WEAPON_LAYOUT[rect][1] != '':
                        if self.WEAPON_LAYOUT[rect][1] == 'Mk-48':
                            pygame.draw.rect(self.window, '#263ded', rect, border_radius=5)
                        elif self.WEAPON_LAYOUT[rect][1] == 'UGM-84':
                            pygame.draw.rect(self.window, '#16c7c7', rect, border_radius=5)
                        else:
                            pygame.draw.rect(self.window, '#ffff82', rect, border_radius=5)
                        txtsurf = self.small_font.render(self.WEAPON_LAYOUT[rect][1], True, '#b6b6d1')
                        self.window.blit(txtsurf, (rect[0], rect[1] + 10))
                    pygame.draw.rect(self.window, '#b6b6d1', rect, border_radius=5, width=1)
            txtsurf = self.small_font.render("Torpedo", True, '#b6b6d1')
            self.window.blit(txtsurf, mid_rect((800, 560, 50, 7), txtsurf))
            txtsurf = self.small_font.render("storage", True, '#b6b6d1')
            self.window.blit(txtsurf, mid_rect((800, 570, 50, 7), txtsurf))
        # Selected weapon render
        if self.SELECTED_WEAPON:
            pygame.draw.rect(self.window, 'green', self.SELECTED_WEAPON, border_radius=5, width=1)

        # Reset button
        self.reset_box = (380, 70, 20, 20)
        pygame.draw.rect(self.window, 'red', self.reset_box, border_radius=2)
        txtsurf = self.middle_font.render("R", True, 'black')
        self.window.blit(txtsurf, (380 + (10 - txtsurf.get_width() // 2), 70 + (10 - txtsurf.get_height() // 2)))

        # Transfer contact information buttons
        self.active_transfer_box = (320, 70, 20, 20)
        if self.TRANSFER_CONTACT_INFO_A:
            pygame.draw.rect(self.window, '#D3FFD4', self.active_transfer_box, border_radius=2)
        else:
            pygame.draw.rect(self.window, 'green', self.active_transfer_box, border_radius=2)
        txtsurf = self.middle_font.render("A", True, 'black')
        self.window.blit(txtsurf, (320 + (10 - txtsurf.get_width() // 2), 70 + (10 - txtsurf.get_height() // 2)))

        self.passive_transfer_box = (350, 70, 20, 20)
        if self.TRANSFER_CONTACT_INFO_P:
            pygame.draw.rect(self.window, '#D3FFD4', self.passive_transfer_box, border_radius=2)
        else:
            pygame.draw.rect(self.window, 'green', self.passive_transfer_box, border_radius=2)
        txtsurf = self.middle_font.render("P", True, 'black')
        self.window.blit(txtsurf, (350 + (10 - txtsurf.get_width() // 2), 70 + (10 - txtsurf.get_height() // 2)))

        # Launch information
        txtsurf = self.middle_font.render("Bearing", True, '#b6b6d1')
        self.window.blit(txtsurf, (320, 37.5 - txtsurf.get_height()))
        self.bearing_box = (320, 37.5, 70, 25)
        if not self.bearing_var[0]:
            pygame.draw.rect(self.window, '#b6b6d1', self.bearing_box, width=2)
        else:
            pygame.draw.rect(self.window, 'white', self.bearing_box, width=2)
        txtsurf = self.middle_font.render(f"{self.bearing_var[1]}", True, 'white')
        self.window.blit(txtsurf, (325, 37.5 + (12.5 - txtsurf.get_height() // 2)))

        txtsurf = self.middle_font.render("Depth", True, '#b6b6d1')
        self.window.blit(txtsurf, (410, 37.5 - txtsurf.get_height()))
        self.depth_box = (410, 37.5, 70, 25)
        if not self.depth_var[0]:
            pygame.draw.rect(self.window, '#b6b6d1', self.depth_box, width=2)
        else:
            pygame.draw.rect(self.window, 'white', self.depth_box, width=2)
        txtsurf = self.middle_font.render(f"{self.depth_var[1]}", True, 'white')
        self.window.blit(txtsurf, (415, 37.5 + (12.5 - txtsurf.get_height() // 2)))

        txtsurf = self.middle_font.render("Distance", True, '#b6b6d1')
        self.window.blit(txtsurf, (500, 37.5 - txtsurf.get_height()))
        self.distance_box = (500, 37.5, 100, 25)
        if not self.distance_var[0]:
            pygame.draw.rect(self.window, '#b6b6d1', self.distance_box, width=2)
        else:
            pygame.draw.rect(self.window, 'white', self.distance_box, width=2)
        txtsurf = self.middle_font.render(f"{self.distance_var[1]}", True, 'white')
        self.window.blit(txtsurf, (505, 37.5 + (12.5 - txtsurf.get_height() // 2)))

        txtsurf = self.middle_font.render("Mode: ", True, '#b6b6d1')
        self.window.blit(txtsurf, (620, 37.5 + (12.5 - txtsurf.get_height() // 2)))
        if self.mode_var == 1:
            txtsurf = self.middle_font.render("Active", True, '#FFFDD2')
        elif self.mode_var == 0:
            txtsurf = self.middle_font.render("Passive", True, '#DFFFD3')
        else:
            txtsurf = self.middle_font.render("Normal", True, 'white')
        self.window.blit(txtsurf, (680, 37.5 + (12.5 - txtsurf.get_height() // 2)))

        self.change_mode_box = (750, 37.5, 25, 25)
        pygame.draw.rect(self.window, '#b6b6d1', self.change_mode_box, border_radius=2)

        self.fire_box = (795, 37.5, 80, 25)
        pygame.draw.rect(self.window, 'red', self.fire_box, border_radius=2)
        txtsurf = self.middle_font.render("FIRE", True, 'white')
        self.window.blit(txtsurf, (795 + (40 - txtsurf.get_width() // 2), 37.5 + (12.5 - txtsurf.get_height() // 2)))

        if self.LAUNCH_AUTH[0] is not None:
            self.LAUNCH_AUTH[1] -= 0.0167 * (self.fps/self.current_fps)
            if self.LAUNCH_AUTH[1] > 0:
                if self.LAUNCH_AUTH[0]:
                    txtsurf = self.middle_font.render("Launch authorized.", True, 'green')
                    self.window.blit(txtsurf,
                                     (795 + (40 - txtsurf.get_width() // 2), 75 + (12.5 - txtsurf.get_height() // 2)))
                else:
                    txtsurf = self.middle_font.render("Launch unauthorized.", True, 'red')
                    self.window.blit(txtsurf,
                                     (795 + (40 - txtsurf.get_width() // 2), 75 + (12.5 - txtsurf.get_height() // 2)))
            else:
                self.LAUNCH_AUTH[1] = 0
                self.LAUNCH_AUTH[0] = None

        pygame.display.update()

    def on_execute(self):
        WATER_DRAG = 0.00001
        map_delay = 0
        self.open_main_menu()
        while self.running:
            tick_time = self.clock.tick(self.fps)
            self.current_fps = self.clock.get_fps()
            if self.current_fps:
                fps_d = self.fps / self.current_fps
            else:
                fps_d = 1
            # print(self.clock.get_fps())
            # Scene checks
            if self.GAME_INIT:
                self.ship_sync += 0.0167 * fps_d
                # Collision detection
                if self.coll_detection.get_at((int(self.LOCAL_POSITION[0]), int(self.LOCAL_POSITION[1])))[:3] != (
                        2, 16, 25):
                    print("COLLIDED WITH LAND.")
                    self.LOCAL_VELOCITY = 0
                    self.LOCAL_ACCELERATION = 0
                    self.HEALTH = 0

                # # Checking if the player is alive
                # if self.HEALTH <= 0:
                #     print("PLAYER DIED.")

                # Movement calculations
                if self.GEAR == 1:
                    self.DETECTION_CHANCE = 0.1
                    self.LOCAL_ACCELERATION = 0.000014
                    if self.LOCAL_VELOCITY >= 0.008:
                        self.LOCAL_ACCELERATION -= (self.LOCAL_VELOCITY - 0.008) / 200
                elif self.GEAR == 2:
                    self.DETECTION_CHANCE = 0.3
                    self.LOCAL_ACCELERATION = 0.000018
                    if self.LOCAL_VELOCITY >= 0.014:
                        self.LOCAL_ACCELERATION -= (self.LOCAL_VELOCITY - 0.014) / 200
                elif self.GEAR == 3:
                    self.DETECTION_CHANCE = 0.5
                    self.LOCAL_ACCELERATION = 0.00002
                    if self.LOCAL_VELOCITY >= 0.018:
                        self.LOCAL_ACCELERATION -= (self.LOCAL_VELOCITY - 0.018) / 200
                elif self.GEAR == 0:
                    self.DETECTION_CHANCE = 0.04
                    self.LOCAL_ACCELERATION = 0
                elif self.GEAR == -1:
                    self.DETECTION_CHANCE = 0.1
                    self.LOCAL_ACCELERATION = -0.000014
                    if self.LOCAL_VELOCITY <= -0.008:
                        self.LOCAL_ACCELERATION += (abs(self.LOCAL_VELOCITY + 0.008)) / 200
                elif self.GEAR == -2:
                    self.DETECTION_CHANCE = 0.3
                    self.LOCAL_ACCELERATION = -0.000018
                    if self.LOCAL_VELOCITY <= -0.014:
                        self.LOCAL_ACCELERATION += (abs(self.LOCAL_VELOCITY + 0.014)) / 200
                elif self.GEAR == -3:
                    self.DETECTION_CHANCE = 0.5
                    self.LOCAL_ACCELERATION = -0.00002
                    if self.LOCAL_VELOCITY <= -0.018:
                        self.LOCAL_ACCELERATION += (abs(self.LOCAL_VELOCITY + 0.018)) / 200

                self.LOCAL_VELOCITY += self.LOCAL_ACCELERATION

                if self.LOCAL_VELOCITY - WATER_DRAG >= 0:
                    self.LOCAL_VELOCITY -= WATER_DRAG
                elif self.LOCAL_VELOCITY + WATER_DRAG <= 0:
                    self.LOCAL_VELOCITY += WATER_DRAG
                else:
                    self.LOCAL_VELOCITY = 0

                # print(f"Acceleration: {self.LOCAL_ACCELERATION} Velocity: {self.LOCAL_VELOCITY} "
                #       f"Depth: {self.LOCAL_POSITION[4]} Pitch: {self.LOCAL_POSITION[3]} Ballast: {self.BALLAST}")

                self.LOCAL_POSITION[0] += (self.LOCAL_VELOCITY * fps_d) * math.cos(
                    math.radians(self.LOCAL_POSITION[2] - 90))
                self.LOCAL_POSITION[1] += (self.LOCAL_VELOCITY * fps_d) * math.sin(
                    math.radians(self.LOCAL_POSITION[2] - 90))

                if -1 < self.LOCAL_POSITION[3] < 1:
                    pitch = 0
                else:
                    pitch = self.LOCAL_POSITION[3]
                self.LOCAL_POSITION[4] -= (self.LOCAL_VELOCITY * fps_d) * math.sin(math.radians(pitch)) * 1.2
                if 49 < self.BALLAST < 51:
                    BALLAST = 50
                else:
                    BALLAST = self.BALLAST
                self.LOCAL_POSITION[4] += (BALLAST - 50) * 0.0005 * fps_d
                if self.LOCAL_POSITION[4] < 0:
                    self.LOCAL_POSITION[4] = 0
                elif self.LOCAL_POSITION[4] >= 700:
                    self.LOCAL_POSITION[4] = 700

                # Other vessel's simulation
                for vessel in self.OBJECTS:
                    if self.OBJECTS[vessel][2] != 0:
                        self.OBJECTS[vessel][0][0] += (self.OBJECTS[vessel][2] * fps_d) * math.cos(
                            math.radians(self.OBJECTS[vessel][0][2] - 90))
                        self.OBJECTS[vessel][0][1] += (self.OBJECTS[vessel][2] * fps_d) * math.sin(
                            math.radians(self.OBJECTS[vessel][0][2] - 90))
                    try:
                        if self.coll_detection.get_at(
                                (int(self.OBJECTS[vessel][0][0]), int(self.OBJECTS[vessel][0][1])))[:3] != (
                                2, 16, 25):
                            self.OBJECTS[vessel][0][2] += 180
                            if self.OBJECTS[vessel][0][2] > 360:
                                self.OBJECTS[vessel][0][2] -= 360
                    except Exception as e:
                        print(e)
                        self.OBJECTS[vessel][0][2] += 180
                        if self.OBJECTS[vessel][0][2] > 360:
                            self.OBJECTS[vessel][0][2] -= 360

                # Land attack missile simulation:
                for missile in self.LAM_FIRED:
                    missile[0] -= 0.01667 * fps_d
                    if missile[2]:
                        target = self.ENEMY_TARGET_LOCATIONS[self.ENEMY_TARGET_LOCATIONS.index(missile[2])]
                    if missile[0] <= 0:
                        if missile[1] and missile[2]:  # Will hit and has a target
                            print("TARGET HIT!")
                            missile[2][2] -= missile[5]
                            if missile[2][2] - missile[5] < 0:
                                self.LOCAL_SCORE += missile[2][2] * 0.5  # Base damage score
                                self.NOTICE_QUEUE.append(["Target damaged!", 0, 0])
                            else:
                                self.LOCAL_SCORE += missile[5] * 0.5  # Base damage score
                                self.NOTICE_QUEUE.append(["Target damaged!", 0, 0])
                            if missile[2][2] < 0:
                                missile[2][2] = 0
                                self.ENEMY_TARGET_LOCATIONS.remove(target)
                                self.LOCAL_SCORE += 50  # Base destruction score
                                self.TARGETS_DESTROYED += 1
                                self.NOTICE_QUEUE.append(["Target destroyed!", 0, 0])
                                # Max score from destroying a base = 100 (50 destruction, 50 max damage)
                            self.TARGET_DAMAGE_QUEUE.append([missile[2][0], missile[2][1], missile[5]])
                        missile[1] = False
                    if missile[0] < -5:
                        self.LAM_FIRED.remove(missile)

                # Anti ship missile simulation:
                for missile in self.ASM_FIRED:
                    missile[0] -= 0.01667 * fps_d
                    if missile[0] <= 0 and missile[3] == 'Target missed!':
                        for ship in list(self.OBJECTS):
                            if ship.count('ship'):
                                sr = missile[6]  # Sensor range (range at which missile tracks on its own)
                                if self.OBJECTS[ship][0][0] - sr < missile[1] < self.OBJECTS[ship][0][0] + sr and \
                                        self.OBJECTS[ship][0][1] - sr < missile[2] < self.OBJECTS[ship][0][1] + sr:
                                    print("SHIP HIT!")
                                    missile[3] = 'Target hit!'
                                    self.OBJECTS[ship][4] -= missile[5]
                                    if self.OBJECTS[ship][4] <= 0:
                                        self.LOCAL_SCORE += 200  # Ship destruction score
                                        self.SHIPS_DESTROYED += 1
                                        self.OBJECTS.pop(ship)
                                        # Max ship destruction score = 200
                                        self.SINK_QUEUE.append(ship)
                                        self.NOTICE_QUEUE.append(["Ship destroyed!", 0, 0])
                                    else:
                                        self.NOTICE_QUEUE.append(["Ship hit!", 0, 0])

                    if missile[0] < -5:
                        self.ASM_FIRED.remove(missile)

                # Friendly ships relaying enemy positions
                flag = 0
                min_d = None
                for ship in list(self.OBJECTS):
                    if ship.count("Friendly_ship"):
                        rel_x = self.OBJECTS[ship][0][0] - self.OBJECTS["Enemy"][0][0]
                        rel_y = self.OBJECTS[ship][0][1] - self.OBJECTS["Enemy"][0][1]
                        distance = math.sqrt(rel_x * rel_x + rel_y * rel_y)
                        # Ships could only really detect you from 50km in the worst case scenario (dc = 0.5)
                        # if -20 < self.OBJECTS[ship][5] < 1:
                        #     self.OBJECTS[ship][5] = 2
                        if distance + ((1 - self.OBJECTS["Enemy"][3]) * 50) <= 50:
                            print("Enemy visible to friendly ships!")
                            flag = 1
                        if self.OBJECTS['Enemy'][5] >= 1 and distance <= 60:
                            print("Enemy's active sonar heard by a friendly ship!")
                            if not min_d:
                                min_d = [distance, [self.OBJECTS[ship][0][0], self.OBJECTS[ship][0][1],
                                                    calculate_azimuth(rel_x, rel_y, distance)]]
                            elif min_d[0] > distance:
                                min_d = [distance, [self.OBJECTS[ship][0][0], self.OBJECTS[ship][0][1],
                                                    calculate_azimuth(rel_x, rel_y, distance)]]
                if flag:
                    self.ENEMY_VISIBLE = True
                    f = 0
                    for notice in self.NOTICE_QUEUE:
                        if notice[0] == "Enemy submarine detected!":
                            f = 1
                    if not f:
                        self.NOTICE_QUEUE.append(["Enemy submarine detected!", 0, 0])
                else:
                    self.ENEMY_VISIBLE = False
                self.ENEMY_VISIBLE_AS = min_d
                if min_d:
                    f = 0
                    for notice in self.NOTICE_QUEUE:
                        if notice[0] == "Active sonar heard!":
                            f = 1
                    if not f:
                        self.NOTICE_QUEUE.append(["Active sonar heard!", 0, 0])

                # Enemy ships trying to detect/shoot simulation
                for ship in list(self.OBJECTS):
                    if ship.count("Enemy_ship"):
                        rel_x = self.OBJECTS[ship][0][0] - self.LOCAL_POSITION[0]
                        rel_y = self.OBJECTS[ship][0][1] - self.LOCAL_POSITION[1]
                        distance = math.sqrt(rel_x * rel_x + rel_y * rel_y)
                        # Ships could only really detect you from 50km in the worst case scenario (dc = 0.5)
                        # if -20 < self.OBJECTS[ship][5] < 1:
                        #     self.OBJECTS[ship][5] = 2
                        if distance + ((1 - self.DETECTION_CHANCE) * 50) <= 50 or \
                                (self.ACTIVE_SONAR and distance <= 30):
                            if self.OBJECTS[ship][5] < 1:
                                self.OBJECTS[ship][5] = 2
                        if self.OBJECTS[ship][5] > -20 and distance < 60:  # Ship's active sonar range 120km
                            # [x, y, azimuth, velocity, depth], [destination x, destination y, depth], sensor on/off,
                            # timer, sender, active_sonar_ping_duration, active sonar on/off, weapon_bay
                            if self.OBJECTS[ship][5] < 1:
                                self.OBJECTS[ship][5] = 2
                            flag = 0
                            for torpedo in self.TORPEDOES:
                                if self.TORPEDOES[torpedo][4] == ship:
                                    flag = torpedo
                                    if self.TORPEDOES[torpedo][3] > 10:
                                        flag = 1
                            if flag != 1 and distance < 25:
                                # Leading the target
                                time = distance / 2.2
                                if time < 1:
                                    time = 1
                                dest_x = self.LOCAL_POSITION[0] + ((self.LOCAL_VELOCITY * fps_d) * math.cos(
                                    math.radians(self.LOCAL_POSITION[2] - 90))) * time * 60
                                dest_y = self.LOCAL_POSITION[1] + ((self.LOCAL_VELOCITY * fps_d) * math.sin(
                                    math.radians(self.LOCAL_POSITION[2] - 90))) * time * 60

                                print(self.LOCAL_POSITION[0], self.LOCAL_POSITION[1], dest_x, dest_y)
                                if flag == 0:
                                    id = 0
                                else:
                                    id = int(flag.split('_')[-1]) + 1
                                self.TORPEDOES[f'Enemy_ship_torpedo_{id}'] = [
                                    [self.OBJECTS[ship][0][0], self.OBJECTS[ship][0][1],
                                     self.OBJECTS[ship][0][2], 0.0367, self.OBJECTS[ship][0][3]],
                                    [dest_x, dest_y, self.LOCAL_POSITION[4]], False, 20, ship, 0,
                                    True]
                                self.NOTICE_QUEUE.append(["Torpedo in the water!", 0, 1])

                # Enemy torpedo simulation
                for key in list(self.TORPEDOES):
                    torpedo = self.TORPEDOES[key]
                    if torpedo[6]:  # If torpedo is in the active mode
                        if torpedo[5] <= 1:
                            torpedo[5] = 2
                    torpedo[3] -= 0.0167 * fps_d
                    if torpedo[3] <= 0:
                        self.TORPEDOES.pop(key)
                    if not torpedo[2]:  # Sensor hasn't been activated yet
                        rel_x = torpedo[1][0] - torpedo[0][0]
                        rel_y = torpedo[1][1] - torpedo[0][1]
                        distance = math.sqrt(rel_x * rel_x + rel_y * rel_y)
                        angle = calculate_azimuth(rel_x, rel_y, distance)
                        if torpedo[0][2] - angle > 180:
                            angle = (360 - torpedo[0][2]) + angle
                        elif torpedo[0][2] - angle < -180:
                            angle = -((360 - angle) + torpedo[0][2])
                        else:
                            angle = -(torpedo[0][2] - angle)
                        turn = 0.34 * fps_d
                        if turn > abs(angle):
                            turn = abs(angle)
                        if angle > 0:
                            torpedo[0][2] += turn
                        else:
                            torpedo[0][2] -= turn
                        dive_rate = 0.24 * fps_d
                        depth = torpedo[1][2] - torpedo[0][4]
                        if dive_rate > depth:
                            dive_rate = depth
                        if depth > 0:
                            torpedo[0][4] += dive_rate
                        else:
                            torpedo[0][4] -= dive_rate
                        print(f"Depth to destination: {depth} Distance: {distance}")
                        torpedo[0][0] += (torpedo[0][3] * fps_d) * math.cos(
                            math.radians(torpedo[0][2] - 90))
                        torpedo[0][1] += (torpedo[0][3] * fps_d) * math.sin(
                            math.radians(torpedo[0][2] - 90))
                        if -10 < distance < 10 and -30 < depth < 30:
                            torpedo[2] = True
                    else:
                        # Go into seeking mode
                        min_distance = [None, None]
                        for ship in self.OBJECTS:
                            if ship.count('Friendly_ship'):
                                rel_x = self.OBJECTS[ship][0][0] - torpedo[0][0]
                                rel_y = self.OBJECTS[ship][0][1] - torpedo[0][1]
                                distance = math.sqrt(rel_x * rel_x + rel_y * rel_y)
                                if not min_distance[0]:
                                    min_distance[0] = distance
                                    min_distance[1] = ship
                                if min_distance[0] > distance:
                                    min_distance[0] = distance
                                    min_distance[1] = ship
                        rel_x = self.LOCAL_POSITION[0] - torpedo[0][0]
                        rel_y = self.LOCAL_POSITION[1] - torpedo[0][1]
                        distance = math.sqrt(rel_x * rel_x + rel_y * rel_y)
                        if not min_distance[0]:
                            min_distance[0] = distance
                            min_distance[1] = 'Player'
                        if min_distance[0] > distance:
                            min_distance[0] = distance
                            min_distance[1] = 'Player'
                        if min_distance[1] == 'Player':
                            rel_x = self.LOCAL_POSITION[0] - torpedo[0][0]
                            rel_y = self.LOCAL_POSITION[1] - torpedo[0][1]
                            distance = math.sqrt(rel_x * rel_x + rel_y * rel_y)
                            angle = calculate_azimuth(rel_x, rel_y, distance)
                            if torpedo[0][2] - angle > 180:
                                angle = (360 - torpedo[0][2]) + angle
                            elif torpedo[0][2] - angle < -180:
                                angle = -((360 - angle) + torpedo[0][2])
                            else:
                                angle = -(torpedo[0][2] - angle)
                            depth = self.LOCAL_POSITION[4] - torpedo[0][4]
                            max_distance = 10
                            if torpedo[6]:
                                max_distance = 20
                            if distance < max_distance and 150 > angle > -150 and -40 < depth < 40:
                                turn = 0.34 * fps_d
                                if turn > abs(angle):
                                    turn = abs(angle)
                                if angle > 0:
                                    torpedo[0][2] += turn
                                else:
                                    torpedo[0][2] -= turn
                                dive_rate = 0.08 * fps_d
                                if dive_rate > depth:
                                    dive_rate = depth
                                if depth > 0:
                                    torpedo[0][4] += dive_rate
                                else:
                                    torpedo[0][4] -= dive_rate
                                print(f"Depth to target: {depth} Distance: {distance}")
                                # Updating torpedo's position
                                torpedo[0][0] += (torpedo[0][3] * fps_d) * math.cos(
                                    math.radians(torpedo[0][2] - 90))
                                torpedo[0][1] += (torpedo[0][3] * fps_d) * math.sin(
                                    math.radians(torpedo[0][2] - 90))
                                if -0.2 < distance < 0.2 and -0.2 < depth < 0.2:
                                    print("TORPEDO HIT!")
                                    self.TORPEDOES.pop(key)
                                    self.HEALTH -= random_int(30, 50)
                                    self.NOTICE_QUEUE.append(["We got hit!", 0, 1])
                            else:
                                # Updating torpedo's position
                                torpedo[0][0] += (torpedo[0][3] * fps_d) * math.cos(
                                    math.radians(torpedo[0][2] - 90))
                                torpedo[0][1] += (torpedo[0][3] * fps_d) * math.sin(
                                    math.radians(torpedo[0][2] - 90))
                        else:
                            rel_x = self.OBJECTS[min_distance[1]][0][0] - torpedo[0][0]
                            rel_y = self.OBJECTS[min_distance[1]][0][1] - torpedo[0][1]
                            distance = math.sqrt(rel_x * rel_x + rel_y * rel_y)
                            angle = calculate_azimuth(rel_x, rel_y, distance)
                            if torpedo[0][2] - angle > 180:
                                angle = (360 - torpedo[0][2]) + angle
                            elif torpedo[0][2] - angle < -180:
                                angle = -((360 - angle) + torpedo[0][2])
                            else:
                                angle = -(torpedo[0][2] - angle)
                            depth = self.OBJECTS[min_distance[1]][0][3] - torpedo[0][4]
                            max_distance = 10
                            if torpedo[6]:
                                max_distance = 20
                            if distance < max_distance and 120 > angle > -120 and -50 < depth < 50:
                                turn = 0.34 * fps_d
                                if turn > abs(angle):
                                    turn = abs(angle)
                                if angle > 0:
                                    torpedo[0][2] += turn
                                else:
                                    torpedo[0][2] -= turn
                                dive_rate = 0.1 * fps_d
                                if dive_rate > depth:
                                    dive_rate = depth
                                if depth > 0:
                                    torpedo[0][4] += dive_rate
                                else:
                                    torpedo[0][4] -= dive_rate
                                # Updating torpedo's position
                                torpedo[0][0] += (torpedo[0][3] * fps_d) * math.cos(
                                    math.radians(torpedo[0][2] - 90))
                                torpedo[0][1] += (torpedo[0][3] * fps_d) * math.sin(
                                    math.radians(torpedo[0][2] - 90))
                                if -1 < distance < 1 and -1 < depth < 1:
                                    print("TORPEDO HIT!")
                                    self.TORPEDOES.pop(key)
                                    self.OBJECTS[min_distance[1]][4] -= random_int(30, 50)
                                    if self.OBJECTS[min_distance[1]][4] <= 0:
                                        self.SINK_QUEUE.append(min_distance[1])
                                        self.OBJECTS.pop(min_distance[1])
                                        print("TORPEDO SUNK THE SHIP!")
                                        self.ENEMY_SCORE += 200
                                        self.SHIPS_DESTROYED_ENEMY += 1
                                        self.NOTICE_QUEUE.append(["Friendly ship got destroyed.", 0, 1])
                                    else:
                                        self.NOTICE_QUEUE.append(["Friendly ship got damaged.", 0, 1])
                            else:
                                # Updating torpedo's position
                                torpedo[0][0] += (torpedo[0][3] * fps_d) * math.cos(
                                    math.radians(torpedo[0][2] - 90))
                                torpedo[0][1] += (torpedo[0][3] * fps_d) * math.sin(
                                    math.radians(torpedo[0][2] - 90))

            if self.MAIN_MENU_OPEN:
                self.open_main_menu()
            elif self.GAME_OPEN:
                if self.SONAR_SCREEN:
                    self.sonar_screen_render()
                elif self.WEAPON_SCREEN:
                    self.weapon_screen_render()
            elif self.SCOREBOARD_OPEN:
                self.scoreboard_render()
            elif self.MAP_OPEN:
                map_delay += tick_time
                if map_delay > self.fps * 2:
                    self.blitmap()
                    map_delay = 0
            elif self.HOST_GAME_SCREEN:
                self.host_game_render()
            elif self.JOIN_GAME_SCREEN:
                self.join_game_render()
            elif self.WIN_SCREEN:
                self.win_screen_render()
            elif self.LOSS_SCREEN:
                self.loss_screen_render()
            # Scene event checks
            for event in pygame.event.get():
                if self.SCOREBOARD_OPEN:
                    self.scoreboard_events(event)
                elif self.MAP_OPEN:
                    self.check_map_events(event)
                elif self.MAIN_MENU_OPEN:
                    self.main_menu_events(event)
                elif self.SONAR_SCREEN:
                    self.game_events(event)
                elif self.WEAPON_SCREEN:
                    self.weapon_screen_events(event)
                elif self.HOST_GAME_SCREEN:
                    self.host_game_screen_events(event)
                elif self.JOIN_GAME_SCREEN:
                    self.join_game_screen_events(event)

            if self.GAME_INIT:
                keys = pygame.key.get_pressed()
                if keys[pygame.K_a]:
                    if not self.LOCAL_VELOCITY == 0:
                        if self.LOCAL_POSITION[2] > -360:
                            turn_rate = 0.15 * (1 - (abs(self.LOCAL_VELOCITY) / 0.034))
                            self.LOCAL_POSITION[2] -= turn_rate * fps_d
                        else:
                            self.LOCAL_POSITION[2] = 0
                elif keys[pygame.K_d]:
                    if not self.LOCAL_VELOCITY == 0:
                        if self.LOCAL_POSITION[2] < 360:
                            turn_rate = 0.15 * (1 - (abs(self.LOCAL_VELOCITY) / 0.034))
                            self.LOCAL_POSITION[2] += turn_rate * fps_d
                        else:
                            self.LOCAL_POSITION[2] = 0
                if keys[pygame.K_w]:
                    if not self.LOCAL_VELOCITY == 0:
                        if self.LOCAL_POSITION[4] > 0.2:
                            if self.LOCAL_POSITION[3] < 45:
                                pitch_rate = 0.08 * (1 - (abs(self.LOCAL_VELOCITY) / 0.034))
                                self.LOCAL_POSITION[3] += pitch_rate * fps_d
                        else:
                            self.LOCAL_POSITION[3] = 0
                elif keys[pygame.K_s]:
                    if not self.LOCAL_VELOCITY == 0:
                        if self.LOCAL_POSITION[3] > -45:
                            pitch_rate = 0.08 * (1 - (abs(self.LOCAL_VELOCITY) / 0.034))
                            self.LOCAL_POSITION[3] -= pitch_rate * fps_d
                if keys[pygame.K_UP]:
                    # self.LOCAL_POSITION[0] = 762
                    # self.LOCAL_POSITION[1] = 228
                    if self.depth_var[0]:
                        self.depth_var[1] = str(float(self.depth_var[1]) + 1)
                    elif self.bearing_var[0]:
                        self.bearing_var[1] = str(float(self.bearing_var[1]) + 1)
                    elif self.distance_var[0]:
                        self.distance_var[1] = str(float(self.distance_var[1]) + 1)
                    elif self.BALLAST < 100:
                        self.BALLAST += 0.1 * fps_d
                        if self.BALLAST > 100:
                            self.BALLAST = 100
                elif keys[pygame.K_DOWN]:
                    if self.depth_var[0]:
                        self.depth_var[1] = str(float(self.depth_var[1]) - 1)
                    elif self.bearing_var[0]:
                        self.bearing_var[1] = str(float(self.bearing_var[1]) - 1)
                    elif self.distance_var[0]:
                        self.distance_var[1] = str(float(self.distance_var[1]) - 1)
                    if self.BALLAST > 0:
                        self.BALLAST -= 0.5 * fps_d
                        if self.BALLAST < 0:
                            self.BALLAST = 0
                torpedo_send_info = []
                for torpedo in self.TORPEDOES:
                    torpedo_send_info.append(
                        f"{str(torpedo).replace(',', 'C')}!{self.TORPEDOES[torpedo][2]}!{self.TORPEDOES[torpedo][6]}")
                if not len(torpedo_send_info):
                    torpedo_send_info = None
                if not server_api.SEND_INFO:
                    if self.HEALTH <= 0:
                        server_api.SEND_INFO = f"[{self.PLAYER_ID}] Player has died."
                        self.clear_scene()
                        self.LOSS_SCREEN = True
                        continue
                    for weapon in self.FIRED_TORPEDOES:
                        if self.FIRED_TORPEDOES[weapon][2] < 0:
                            self.FIRED_TORPEDOES[weapon][2] = 0
                    torpedo_send_info2 = ""
                    for torp in self.UPDATE_TORP_QUEUE:
                        torpedo_send_info2 += f'AND{torp}'
                    sink_info = ""
                    for ship in self.SINK_QUEUE:
                        sink_info += f'{ship}!'
                    if sink_info == "":
                        sink_info = "None"
                    else:
                        sink_info = sink_info[:-1]

                    target_info = ""
                    for target in self.TARGET_DAMAGE_QUEUE:
                        target_info += f'{target[0]}!{target[1]}!{target[2]}?'
                    if target_info == "":
                        target_info = "None"
                    else:
                        target_info = target_info[:-1]

                    ship_sync_info = "None"
                    if self.ship_sync > 5:
                        self.ship_sync = 0
                        ship_sync_info = ""
                        for ship in self.OBJECTS:
                            if ship.count("Friendly"):
                                ship_sync_info += f'{self.OBJECTS[ship][0][0]}!{self.OBJECTS[ship][0][1]}!' \
                                                  f'{self.OBJECTS[ship][0][2]}!{ship}?'
                        else:
                            ship_sync_info = ship_sync_info[:-1]
                        if ship_sync_info == "":
                            ship_sync_info = "None"

                    print(torpedo_send_info2)
                    if self.ACTIVE_SONAR:
                        sonar_info = 1
                    else:
                        sonar_info = 0
                    server_api.SEND_INFO = f"[{self.PLAYER_ID}] [{self.LOCAL_POSITION[0]:.2f}, " \
                                           f"{self.LOCAL_POSITION[1]:.2f}, {self.LOCAL_POSITION[2]:.2f}, " \
                                           f"{self.LOCAL_POSITION[4]:.2f}, {self.LOCAL_VELOCITY:.5f}, " \
                                           f"{self.DETECTION_CHANCE}, {sonar_info}, {sink_info}, " \
                                           f"{target_info}, {torpedo_send_info}]" \
                                           f" {torpedo_send_info2}ANDSYUI{ship_sync_info}"
                    self.UPDATE_TORP_QUEUE = []
                    self.SINK_QUEUE = []
                    self.TARGET_DAMAGE_QUEUE = []
                if server_api.UPDATE_INFO:
                    print(server_api.UPDATE_INFO)
                    # print(server_api.TORPEDO_INFO)
                    if server_api.UPDATE_INFO.count("PLAYER HAS DIED"):
                        print("Recieved information about player's death, R.I.P.")
                        self.clear_scene()
                        self.WIN_SCREEN = True
                        continue
                    self.OBJECTS['Enemy'][0][0] = float(server_api.UPDATE_INFO[0])
                    self.OBJECTS['Enemy'][0][1] = float(server_api.UPDATE_INFO[1])
                    self.OBJECTS['Enemy'][0][2] = float(server_api.UPDATE_INFO[2])
                    self.OBJECTS['Enemy'][0][3] = float(server_api.UPDATE_INFO[3])
                    self.OBJECTS['Enemy'][2] = float(server_api.UPDATE_INFO[4])
                    self.OBJECTS['Enemy'][3] = float(server_api.UPDATE_INFO[5])
                    self.OBJECTS['Enemy'][5] = float(server_api.UPDATE_INFO[6])
                    if self.OBJECTS['Enemy'][5] <= 0:
                        self.ENEMY_SONAR = 0
                    if server_api.UPDATE_INFO[7] != 'None':
                        for ship in server_api.UPDATE_INFO[6].split("!"):
                            if ship.count("Friendly"):  # You destroyed enemy's friendly ship
                                ship = ship.replace("Friendly", "Enemy")
                                print(ship)
                                if ship in list(self.OBJECTS):
                                    self.OBJECTS.pop(ship)
                                    print(f"Ship {ship} has been sunk by you!")
                                    self.LOCAL_SCORE += 200  # Ship sink score
                                    self.SHIPS_DESTROYED += 1
                                    self.NOTICE_QUEUE.append(["Ship destroyed!", 0, 0])
                            elif ship.count("Enemy"):  # They destroyed your friendly ship
                                ship = ship.replace("Enemy", "Friendly")
                                print(ship)
                                if ship in list(self.OBJECTS):
                                    self.OBJECTS.pop(ship)
                                    print(f"Ship {ship} has been sunk by the enemy!")
                                    self.ENEMY_SCORE += 200  # Ship sink score
                                    self.SHIPS_DESTROYED_ENEMY += 1
                                    self.NOTICE_QUEUE.append(["Friendly ship got destroyed!", 0, 1])
                    if server_api.UPDATE_INFO[8] != 'None':
                        for target in server_api.UPDATE_INFO[7].split("?"):
                            target = target.split("!")
                            for enemy_target in self.FRIENDLY_TARGET_LOCATIONS:
                                if str(enemy_target[0]) == target[0] and str(enemy_target[1]) == target[1]:
                                    enemy_target[2] -= int(target[2])
                                    if enemy_target[2] - int(target[2]) < 0:
                                        self.ENEMY_SCORE += enemy_target[2] * 0.5  # Base damage score
                                        self.NOTICE_QUEUE.append(["Friendly base got damaged!", 0, 1])
                                    else:
                                        self.ENEMY_SCORE += int(target[2]) * 0.5  # Base damage score
                                        self.NOTICE_QUEUE.append(["Friendly base got damaged!", 0, 1])
                                    if enemy_target[2] < 0:
                                        enemy_target[2] = 0
                                        self.ENEMY_SCORE += 50
                                        self.TARGETS_DESTROYED_ENEMY += 1
                                        self.FRIENDLY_TARGET_LOCATIONS.remove(enemy_target)
                                        self.NOTICE_QUEUE.append(["Friendly base got destroyed!", 0, 1])
                                    break
                    if server_api.SHIP_SYNC_INFO != 'None':
                        print("SHIP INFO RECIEVED!")
                        temp_s = []
                        for ship in self.OBJECTS:
                            if ship.count("Enemy_ship"):
                                temp_s.append(ship)
                        temp_s_update = []
                        for ship in server_api.SHIP_SYNC_INFO.split("?"):
                            temp = ship.split('!')
                            temp[-1] = temp[-1].replace("Friendly", "Enemy")
                            temp_s_update.append(temp)
                        for ship in temp_s:
                            for ship_update in temp_s_update:
                                if ship == ship_update[-1]:
                                    # print(f"Updated ship info for: {ship}")
                                    self.OBJECTS[ship][0][0] = float(ship_update[0])
                                    self.OBJECTS[ship][0][1] = float(ship_update[1])
                                    self.OBJECTS[ship][0][2] = float(ship_update[2])
                        server_api.SHIP_SYNC_INFO = "None"
                    torpedo_update_info = server_api.UPDATE_INFO[9:]
                    # print(torpedo_update_info)
                    # print(list(self.WEAPON_LAYOUT), list(self.FIRED_TORPEDOES))
                    for weapon in list(self.WEAPON_LAYOUT):
                        if weapon in list(self.FIRED_TORPEDOES) and self.FIRED_TORPEDOES[weapon][2] >= 0:
                            flag = 0
                            torp_info = None
                            for info in torpedo_update_info:
                                if info.replace("'", '').split('!')[0].replace('C', ',') == str(weapon).replace(' ',
                                                                                                                ''):
                                    flag = 1
                                    torp_info = info.replace("'", '')
                                    break
                            if not flag:
                                self.FIRED_TORPEDOES[weapon][2] += 1
                                if self.FIRED_TORPEDOES[weapon][2] > 4:
                                    self.WEAPON_LAYOUT[weapon][1] = ''
                                    self.FIRED_TORPEDOES.pop(weapon)
                                else:
                                    print("YOU GOT A CHANCE")
                            else:
                                print("THAT'S IT, THAT'S MY BOY")
                                t1 = False
                                t2 = False
                                if torp_info.split('!')[1] == 'True':
                                    t1 = True
                                if torp_info.split('!')[2] == 'True':
                                    t2 = True
                                self.FIRED_TORPEDOES[weapon][0] = t1  # Sensor active (bool)
                                self.FIRED_TORPEDOES[weapon][1] = t2  # Mode (bool) (act./pas.)

                    server_api.UPDATE_INFO = None
                if server_api.TORPEDO_INFO:
                    print(server_api.TORPEDO_INFO, "TORPEDO INFORMATION!!")
                    for info in server_api.TORPEDO_INFO:
                        if info[8] == 'True':
                            t1 = True
                        else:
                            t1 = False
                        if info[12] == 'True':
                            t2 = True
                        else:
                            t2 = False
                        flag = 0
                        torp_key = (int(info[13].replace("(", '')),
                                    int(info[14]),
                                    int(info[15]),
                                    int(info[16].replace(")", '')))
                        if torp_key in list(self.TORPEDOES.keys()):
                            flag = 1
                        if flag:
                            print("Updating existing torpedo's settings.")
                            self.TORPEDOES[torp_key][1][0] = float(info[5])
                            self.TORPEDOES[torp_key][1][1] = float(info[6])
                            self.TORPEDOES[torp_key][1][2] = float(info[7])
                            self.TORPEDOES[torp_key][6] = t2
                        else:
                            try:
                                print("Launching a new torpedo!")
                                torp = [[float(info[0]), float(info[1]),
                                         float(info[2]),
                                         float(info[3]), float(info[4])],
                                        [float(info[5]), float(info[6]),
                                         float(info[7])],
                                        t1, float(info[9]), info[10],
                                        float(info[11]), t2]
                                self.TORPEDOES[torp_key] = torp
                            except ValueError:
                                print("Torpedo no longer exists.")
                        server_api.TORPEDO_INFO = None

        self.on_cleanup()

    def sonar_screen_render(self):
        self.window.fill('black')
        self.render_notifications()

        def calculate_bearing(rel_x, rel_y, distance):
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

            if self.LOCAL_POSITION[2] < 0:
                local_position = self.LOCAL_POSITION[2] + 360
            else:
                local_position = self.LOCAL_POSITION[2]
            if angle < 0:
                angle += 360
            if angle - local_position < -180:
                bearing_ = (360 - local_position) + angle
            elif angle - local_position > 180:
                bearing_ = ((360 - angle) + local_position) * -1
            else:
                bearing_ = angle - local_position
            return bearing_

        flag = 0
        if self.PASSIVE_SELECTED_CONTACT:
            for contact in self.PASSIVE_SONAR_DISPLAY_CONTACTS:
                if contact[2] == self.PASSIVE_SELECTED_CONTACT[2] and contact[1] < 5:
                    flag = 1
        if not flag:
            self.PASSIVE_SELECTED_CONTACT = None
            self.identifying_delay = 0

        ACTIVE_SONAR_RANGE = 80
        PASSIVE_SONAR_RANGE = 80
        # Active sonar

        pygame.draw.circle(self.window, 'green', (200, 200), 180, width=2)

        for i in range(180):
            angle = i * 2 - 350
            x = 200 + 180 * math.cos(math.radians(angle + 90))
            y = 200 - 180 * math.sin(math.radians(angle + 90))
            if i % 5 != 0:
                x2 = 200 + 175 * math.cos(math.radians(angle + 90))
                y2 = 200 - 175 * math.sin(math.radians(angle + 90))
            else:
                x2 = 200 + 170 * math.cos(math.radians(angle + 90))
                y2 = 200 - 170 * math.sin(math.radians(angle + 90))
                x3 = 200 + 190 * math.cos(math.radians(angle + 90))
                y3 = 200 - 190 * math.sin(math.radians(angle + 90))
                txtsurf = self.small_font.render(f"{abs(angle)}", True, "#b6b6d1")
                self.window.blit(txtsurf, (x3 - txtsurf.get_width() // 2,
                                           y3 - txtsurf.get_height() // 2))
            pygame.draw.line(self.window, 'green', (x, y), (x2, y2), width=2)
        x = 200 + 180 * math.sin(math.radians(self.LOCAL_POSITION[2]))
        y = 200 - 180 * math.cos(math.radians(self.LOCAL_POSITION[2]))
        pygame.draw.line(self.window, 'white', (200, 200), (x, y), width=1)
        pygame.draw.circle(self.window, 'green', (200, 200), 3)
        i = 0
        for contact in list(self.ACTIVE_SONAR_CONTACTS):
            i += 1
            self.ACTIVE_SONAR_CONTACTS[contact][2] -= 0.016 * self.fps / self.current_fps
            if self.ACTIVE_SONAR_CONTACTS[contact][2] > 0:
                pygame.draw.circle(self.window, darken(self.ACTIVE_SONAR_CONTACTS[contact][2] + 1, '#00ff00'),
                                   (self.ACTIVE_SONAR_CONTACTS[contact][0],
                                    self.ACTIVE_SONAR_CONTACTS[contact][1]), 5)
                txtsurf = self.small_font.render(f"{i}", True, "#b6b6d1")
                self.window.blit(txtsurf, (self.ACTIVE_SONAR_CONTACTS[contact][0] - 10,
                                           self.ACTIVE_SONAR_CONTACTS[contact][1] - 10))
            else:
                self.ACTIVE_SONAR_CONTACTS.pop(contact)

        # Selected active sonar contact
        txtsurf = self.middle_font.render("Selected contact: ", True, '#b6b6d1')
        self.window.blit(txtsurf, (400, 15))
        txtsurf = self.middle_font.render("Type: ", True, '#b6b6d1')
        self.window.blit(txtsurf, (400, 40))
        txtsurf = self.middle_font.render("Bearing: ", True, '#b6b6d1')
        self.window.blit(txtsurf, (400, 65))
        txtsurf = self.middle_font.render("Speed: ", True, '#b6b6d1')
        self.window.blit(txtsurf, (400, 90))
        txtsurf = self.middle_font.render("Depth: ", True, '#b6b6d1')
        self.window.blit(txtsurf, (400, 115))
        txtsurf = self.middle_font.render("Distance: ", True, '#b6b6d1')
        self.window.blit(txtsurf, (400, 140))
        txtsurf = self.middle_font.render("Heading: ", True, '#b6b6d1')
        self.window.blit(txtsurf, (400, 165))
        a_contact_type = None
        a_contact_bearing = 0
        a_contact_speed = 0
        a_contact_depth = 0
        a_contact_distance = 0
        a_contact_heading = 0
        if self.ACTIVE_SONAR_SELECTED_CONTACT and \
                list(self.ACTIVE_SONAR_CONTACTS).count(self.ACTIVE_SONAR_SELECTED_CONTACT) > 0 and \
                self.ACTIVE_SONAR_SELECTED_CONTACT in list(self.OBJECTS):
            a_contact_type = self.OBJECTS[self.ACTIVE_SONAR_SELECTED_CONTACT][1]
            rel_x = (self.ACTIVE_SONAR_CONTACTS[self.ACTIVE_SONAR_SELECTED_CONTACT][0] - 200) / (
                    200 / ACTIVE_SONAR_RANGE)
            rel_y = (self.ACTIVE_SONAR_CONTACTS[self.ACTIVE_SONAR_SELECTED_CONTACT][1] - 200) / (
                    200 / ACTIVE_SONAR_RANGE)
            distance = math.sqrt(rel_x * rel_x + rel_y * rel_y)
            a_contact_bearing = calculate_bearing(rel_x, rel_y, distance)
            if a_contact_bearing < 0:
                a_contact_bearing += 360
            a_contact_speed = self.OBJECTS[self.ACTIVE_SONAR_SELECTED_CONTACT][2]
            a_contact_depth = self.OBJECTS[self.ACTIVE_SONAR_SELECTED_CONTACT][0][3]
            a_contact_distance = distance
            a_contact_heading = self.OBJECTS[self.ACTIVE_SONAR_SELECTED_CONTACT][0][2]
            if self.TRANSFER_CONTACT_INFO_A:
                self.bearing_var[1] = f"{float(a_contact_bearing):.2f}"
                self.depth_var[1] = f"{float(a_contact_depth):.2f}"
                self.distance_var[1] = f"{float(a_contact_distance) * 2.0923:.2f}"
                # self.TRANSFER_CONTACT_INFO_A = False
        txtsurf = self.middle_font.render(f"{a_contact_type}", True, '#b6b6d1')
        self.window.blit(txtsurf, (490, 40))
        txtsurf = self.middle_font.render(f"{a_contact_bearing:.2f}", True, '#b6b6d1')
        self.window.blit(txtsurf, (490, 65))
        txtsurf = self.middle_font.render(f"{(a_contact_speed * 60) / 0.0193:.2f}km/h", True, '#b6b6d1')
        self.window.blit(txtsurf, (490, 90))
        txtsurf = self.middle_font.render(f"{a_contact_depth:.2f}m", True, '#b6b6d1')
        self.window.blit(txtsurf, (490, 115))
        txtsurf = self.middle_font.render(f"{float(a_contact_distance) * 2.0923:.2f}km", True, '#b6b6d1')
        self.window.blit(txtsurf, (490, 140))
        txtsurf = self.middle_font.render(f"{a_contact_heading:.2f} (azimuth)", True, '#b6b6d1')
        self.window.blit(txtsurf, (490, 165))

        if self.ACTIVE_SONAR:
            if self.ACTIVE_SONAR_PING_RADIUS >= 180:
                self.ACTIVE_SONAR_PING_RADIUS = 0
                self.ACTIVE_SONAR_PING_DELAY += 0.017 * self.fps / self.current_fps
            if self.ACTIVE_SONAR_PING_DELAY == 0:
                pygame.draw.circle(self.window, 'white', (200, 200), self.ACTIVE_SONAR_PING_RADIUS, width=1)
                self.ACTIVE_SONAR_PING_RADIUS += 1.5 * self.fps / self.current_fps
                # Make the coordinates relative:
                for vessel in self.OBJECTS:
                    rel_x = self.OBJECTS[vessel][0][0] - self.LOCAL_POSITION[0]
                    rel_y = self.OBJECTS[vessel][0][1] - self.LOCAL_POSITION[1]
                    distance = math.sqrt(rel_x * rel_x + rel_y * rel_y)
                    if self.ACTIVE_SONAR_PING_RADIUS < distance * (
                            200 / ACTIVE_SONAR_RANGE) < self.ACTIVE_SONAR_PING_RADIUS + 5 and \
                            distance <= ACTIVE_SONAR_RANGE:
                        # Draw it on the sonar display
                        rel_x = rel_x * (
                                200 / ACTIVE_SONAR_RANGE) + 200
                        rel_y = rel_y * (
                                200 / ACTIVE_SONAR_RANGE) + 200
                        pygame.draw.circle(self.window, '#386e2c', (rel_x, rel_y), 5)
                        self.ACTIVE_SONAR_CONTACTS[vessel] = [rel_x, rel_y, 4]
            else:
                if self.ACTIVE_SONAR_PING_DELAY + 0.017 * self.fps / self.current_fps >= 1.5:
                    self.ACTIVE_SONAR_PING_DELAY = 0
                else:
                    self.ACTIVE_SONAR_PING_DELAY += 0.017 * self.fps / self.current_fps
        # Passive sonar
        p1_sonar_start = self.size[0] // 2
        p1_sonar_end = self.size[0] // 2 + (self.size[0] // 2 - 30) // 2
        p2_sonar_start = self.size[0] // 2 + (self.size[0] // 2 - 30) // 2
        p2_sonar_end = self.size[0] - 30

        scale = (p1_sonar_end - p1_sonar_start) / 360
        pygame.draw.rect(self.window, '#b6b6d1', (self.size[0] // 2 - 30, 0, self.size[0] // 2 + 30, self.size[1]),
                         width=2)
        pygame.draw.rect(self.window, '#b6b6d1', (self.size[0] // 2, 30, self.size[0] // 2 - 30, self.size[1]), width=2)
        pygame.draw.rect(self.window, '#b6b6d1', (self.size[0] // 2, 30, (self.size[0] // 2 - 30) // 2, self.size[1]),
                         width=2)
        txtsurf = self.small_font.render(f"Time", True, "#b6b6d1")
        txtsurf = pygame.transform.rotate(txtsurf, 90)
        self.window.blit(txtsurf, (self.size[0] // 2 + 15 - 30 - txtsurf.get_width() // 2,
                                   self.size[1] // 2 - txtsurf.get_height() // 2))
        labels = ['180', '270', '0', '90', '180']
        for i in range(5):
            x = self.size[0] / 2 + i * (((self.size[0] // 2 - 30) // 2) / 4 - 0.5)
            y = 30
            pygame.draw.line(self.window, '#b6b6d1', (x, y), (x, y - 5), width=1)
            txtsurf = self.small_font.render(f"{labels[i]}", True, "#b6b6d1")
            self.window.blit(txtsurf, (x - txtsurf.get_width() // 2,
                                       y - 10 - txtsurf.get_height() // 2))
        for i in range(5):
            x = self.size[0] / 2 + (self.size[0] // 2 - 30) // 2 + i * ((self.size[0] // 2 - 30) // 2) / 4 - 1
            y = 30
            pygame.draw.line(self.window, '#b6b6d1', (x, y), (x, y - 5), width=1)
            if i > 0:
                txtsurf = self.small_font.render(f"{labels[i]}", True, "#b6b6d1")
                self.window.blit(txtsurf, (x - txtsurf.get_width() // 2,
                                           y - 10 - txtsurf.get_height() // 2))

        for contact in self.PASSIVE_SONAR_DISPLAY_CONTACTS:
            if contact[1] > self.size[1] - 31:
                self.PASSIVE_SONAR_DISPLAY_CONTACTS.remove(contact)
                continue
            # pygame.draw.circle(self.window, '#386e2c', (contact[0],
            #                                             30+contact[1]), 1)
            if not self.PASSIVE_SONAR_FREEZE:
                contact[1] += 1
            pygame.draw.circle(self.window, contact[3], (contact[0], 30 + contact[1]), 1)  # '#386e2c'

        # Make the coordinates relative:
        for vessel in self.OBJECTS:
            rel_x = self.OBJECTS[vessel][0][0] - self.LOCAL_POSITION[0]
            rel_y = self.OBJECTS[vessel][0][1] - self.LOCAL_POSITION[1]
            distance = math.sqrt(rel_x * rel_x + rel_y * rel_y)
            bearing = calculate_bearing(rel_x, rel_y, distance)
            distance_ratio = (distance / PASSIVE_SONAR_RANGE) * 10
            detection_ratio = (1 - self.OBJECTS[vessel][3]) * 10
            if distance + ((1 - self.OBJECTS[vessel][3]) * PASSIVE_SONAR_RANGE) <= PASSIVE_SONAR_RANGE:
                # Draw it on the passive sonar display
                # print(f"Angle: {angle} Local Angle: {local_position} "
                #       f"Bearing: {bearing}")
                if not self.PASSIVE_SONAR_FREEZE:
                    if self.OBJECTS[vessel][0][3] < self.LOCAL_POSITION[4]:
                        rel_x = p1_sonar_start + (p1_sonar_end - p1_sonar_start) / 2 + bearing
                        rel_x -= (p1_sonar_start + (p1_sonar_end - p1_sonar_start) / 2)
                        zero = p1_sonar_start + (p1_sonar_end - p1_sonar_start) / 2
                        self.PASSIVE_SONAR_DISPLAY_CONTACTS.append(
                            [(zero + rel_x * scale) + random_int(-4 - distance_ratio - detection_ratio,
                                                                 4 + distance_ratio + detection_ratio), 1, vessel,
                             '#386e2c'])
                        # pygame.draw.circle(self.window, '#386e2c', (zero + rel_x*scale, 30), 5)
                    else:
                        rel_x = p2_sonar_start + (p2_sonar_end - p2_sonar_start) / 2 + bearing
                        rel_x -= (p2_sonar_start + (p2_sonar_end - p2_sonar_start) / 2)
                        zero = p2_sonar_start + (p2_sonar_end - p2_sonar_start) / 2
                        self.PASSIVE_SONAR_DISPLAY_CONTACTS.append(
                            [(zero + rel_x * scale) + random_int(-4 - distance_ratio - detection_ratio,
                                                                 4 + distance_ratio + detection_ratio), 1, vessel,
                             '#386e2c'])
            if self.OBJECTS[vessel][5] > 1.5 or (vessel == 'Enemy' and self.ENEMY_SONAR >= 1 and distance <= 150):
                if not self.PASSIVE_SONAR_FREEZE:
                    if self.OBJECTS[vessel][0][3] < self.LOCAL_POSITION[4]:
                        rel_x = p1_sonar_start + (p1_sonar_end - p1_sonar_start) / 2 + bearing
                        rel_x -= (p1_sonar_start + (p1_sonar_end - p1_sonar_start) / 2)
                        zero = p1_sonar_start + (p1_sonar_end - p1_sonar_start) / 2
                        self.PASSIVE_SONAR_DISPLAY_CONTACTS.append(
                            [(zero + rel_x * scale) + random_int(-distance_ratio, distance_ratio), 1, 'sonar',
                             'yellow'])
                        # pygame.draw.circle(self.window, '#386e2c', (zero + rel_x*scale, 30), 5)
                    else:
                        rel_x = p2_sonar_start + (p2_sonar_end - p2_sonar_start) / 2 + bearing
                        rel_x -= (p2_sonar_start + (p2_sonar_end - p2_sonar_start) / 2)
                        zero = p2_sonar_start + (p2_sonar_end - p2_sonar_start) / 2
                        self.PASSIVE_SONAR_DISPLAY_CONTACTS.append(
                            [(zero + rel_x * scale) + random_int(-distance_ratio, distance_ratio), 1, 'sonar',
                             'yellow'])
            if vessel != 'Enemy':
                if self.OBJECTS[vessel][5] - 0.0167 > -25:
                    self.OBJECTS[vessel][5] -= 0.0167
                else:
                    self.OBJECTS[vessel][5] = -25
            else:
                if self.OBJECTS[vessel][5] >= 1:
                    self.ENEMY_SONAR += 0.0167
                    if self.ENEMY_SONAR > 2:
                        self.ENEMY_SONAR = 0

        for torpedo in self.TORPEDOES:
            torpedo = self.TORPEDOES[torpedo]
            rel_x = torpedo[0][0] - self.LOCAL_POSITION[0]
            rel_y = torpedo[0][1] - self.LOCAL_POSITION[1]
            distance = math.sqrt(rel_x * rel_x + rel_y * rel_y)
            bearing = calculate_bearing(rel_x, rel_y, distance)
            distance_ratio = (distance / PASSIVE_SONAR_RANGE) * 10
            if distance + ((1 - 0.6) * PASSIVE_SONAR_RANGE) <= PASSIVE_SONAR_RANGE:
                # Draw it on the passive sonar display
                # print(f"Angle: {angle} Local Angle: {local_position} "
                #       f"Bearing: {bearing}")
                if not self.PASSIVE_SONAR_FREEZE:
                    if torpedo[0][4] < self.LOCAL_POSITION[4]:
                        rel_x = p1_sonar_start + (p1_sonar_end - p1_sonar_start) / 2 + bearing
                        rel_x -= (p1_sonar_start + (p1_sonar_end - p1_sonar_start) / 2)
                        zero = p1_sonar_start + (p1_sonar_end - p1_sonar_start) / 2
                        self.PASSIVE_SONAR_DISPLAY_CONTACTS.append(
                            [(zero + rel_x * scale) + random_int(-1 - distance_ratio,
                                                                 1 + distance_ratio), 1, torpedo, '#2c6e5f'])
                        # pygame.draw.circle(self.window, '#386e2c', (zero + rel_x*scale, 30), 5)
                    else:
                        rel_x = p2_sonar_start + (p2_sonar_end - p2_sonar_start) / 2 + bearing
                        rel_x -= (p2_sonar_start + (p2_sonar_end - p2_sonar_start) / 2)
                        zero = p2_sonar_start + (p2_sonar_end - p2_sonar_start) / 2
                        self.PASSIVE_SONAR_DISPLAY_CONTACTS.append(
                            [(zero + rel_x * scale) + random_int(-1 - distance_ratio,
                                                                 1 + distance_ratio), 1, torpedo, '#2c6e5f'])
            if torpedo[5] > 1.5:
                if not self.PASSIVE_SONAR_FREEZE:
                    if torpedo[0][4] < self.LOCAL_POSITION[4]:
                        rel_x = p1_sonar_start + (p1_sonar_end - p1_sonar_start) / 2 + bearing
                        rel_x -= (p1_sonar_start + (p1_sonar_end - p1_sonar_start) / 2)
                        zero = p1_sonar_start + (p1_sonar_end - p1_sonar_start) / 2
                        self.PASSIVE_SONAR_DISPLAY_CONTACTS.append(
                            [(zero + rel_x * scale) + random_int(-distance_ratio, distance_ratio), 1, 'sonar',
                             'yellow'])
                        # pygame.draw.circle(self.window, '#386e2c', (zero + rel_x*scale, 30), 5)
                    else:
                        rel_x = p2_sonar_start + (p2_sonar_end - p2_sonar_start) / 2 + bearing
                        rel_x -= (p2_sonar_start + (p2_sonar_end - p2_sonar_start) / 2)
                        zero = p2_sonar_start + (p2_sonar_end - p2_sonar_start) / 2
                        self.PASSIVE_SONAR_DISPLAY_CONTACTS.append(
                            [(zero + rel_x * scale) + random_int(-distance_ratio, distance_ratio), 1, 'sonar',
                             'yellow'])
            if torpedo[5] - 0.0167 > -5:
                torpedo[5] -= 0.0167
            else:
                torpedo[5] = -5

        txtsurf = self.small_font.render('Above', True, "#b6b6d1")
        self.window.blit(txtsurf, (p1_sonar_start + (p1_sonar_end - p1_sonar_start) // 2 - txtsurf.get_width() // 2, 5))
        txtsurf = self.small_font.render('Below', True, "#b6b6d1")
        self.window.blit(txtsurf, (p2_sonar_start + (p2_sonar_end - p2_sonar_start) // 2 - txtsurf.get_width() // 2, 5))

        # Passive sonar contact identification
        txtsurf = self.middle_font.render("Passive sonar contact identification", True, '#b6b6d1')
        self.window.blit(txtsurf, (10, 420))
        txtsurf = self.middle_font.render("Type: ", True, '#b6b6d1')
        self.window.blit(txtsurf, (10, 450))
        txtsurf = self.middle_font.render("Bearing: ", True, '#b6b6d1')
        self.window.blit(txtsurf, (10, 480))
        txtsurf = self.middle_font.render("Speed: ", True, '#b6b6d1')
        self.window.blit(txtsurf, (10, 510))
        txtsurf = self.middle_font.render("Depth: ", True, '#b6b6d1')
        self.window.blit(txtsurf, (10, 540))
        txtsurf = self.middle_font.render("Distance: ", True, '#b6b6d1')
        self.window.blit(txtsurf, (10, 570))
        txtsurf = self.middle_font.render("Heading: ", True, '#b6b6d1')
        self.window.blit(txtsurf, (10, 600))

        if 4 >= self.identifying_delay > 0:
            self.identifying_delay += 0.0167 * self.fps / self.current_fps

        if self.PASSIVE_SONAR_BUTTON_HOVER:
            # >--- SELECT FOR IDENTIFICATION BUTTON ---< #
            pygame.draw.rect(self.window, 'white', (10, 650, 200, 40), width=2)
            txtsurf = self.middle_font.render("Select for identification", True, 'white')
            self.window.blit(txtsurf, (110 - txtsurf.get_width() // 2,
                                       670 - txtsurf.get_height() // 2))
            # <--- -------------------------------- ---> #
        else:
            # >--- SELECT FOR IDENTIFICATION BUTTON ---< #
            pygame.draw.rect(self.window, '#b6b6d1', (10, 650, 200, 40), width=2)
            txtsurf = self.middle_font.render("Select for identification", True, '#b6b6d1')
            self.window.blit(txtsurf, (110 - txtsurf.get_width() // 2,
                                       670 - txtsurf.get_height() // 2))
            # <--- -------------------------------- ---> #
        contact_type = None
        contact_bearing = 0
        contact_speed = 0
        contact_depth = 0
        contact_distance = 0
        contact_heading = 0
        if self.PASSIVE_SELECTED_CONTACT and self.PASSIVE_SELECTED_CONTACT[2] in list(self.OBJECTS):
            if self.identifying_delay <= 4:
                contact_type = 'Unidentified'
                if self.identifying_delay > 0:
                    contact_type = 'Identifying...'
                if self.PASSIVE_SELECTED_CONTACT[0] > p2_sonar_start:
                    contact_bearing = self.PASSIVE_SELECTED_CONTACT[0] - (p2_sonar_start + (
                            p2_sonar_end - p2_sonar_start) / 2)
                else:
                    contact_bearing = self.PASSIVE_SELECTED_CONTACT[0] - (p1_sonar_start + (
                            p1_sonar_end - p1_sonar_start) / 2)
                contact_bearing /= scale
                if contact_bearing < 0:
                    contact_bearing += 360
            elif not self.PASSIVE_SONAR_FREEZE:
                contact_type = self.OBJECTS[self.PASSIVE_SELECTED_CONTACT[2]][1]
                contact_speed = self.OBJECTS[self.PASSIVE_SELECTED_CONTACT[2]][2]
                contact_depth = self.OBJECTS[self.PASSIVE_SELECTED_CONTACT[2]][0][3]
                rel_x = self.OBJECTS[self.PASSIVE_SELECTED_CONTACT[2]][0][0] - self.LOCAL_POSITION[0]
                rel_y = self.OBJECTS[self.PASSIVE_SELECTED_CONTACT[2]][0][1] - self.LOCAL_POSITION[1]
                contact_distance = math.sqrt(rel_x * rel_x + rel_y * rel_y)
                contact_heading = self.OBJECTS[self.PASSIVE_SELECTED_CONTACT[2]][0][2]
                if contact_heading < 0:
                    contact_heading += 360
                contact_bearing = calculate_bearing(rel_x, rel_y, contact_distance)
                if contact_bearing < 0:
                    contact_bearing += 360
                if contact_distance > PASSIVE_SONAR_RANGE:
                    self.identifying_delay = 0
                    self.PASSIVE_SELECTED_CONTACT = None
        elif self.PASSIVE_SELECTED_CONTACT and self.PASSIVE_SELECTED_CONTACT[2] in list(self.TORPEDOES):
            if self.identifying_delay <= 2:
                contact_type = 'Unidentified'
                if self.identifying_delay > 0:
                    contact_type = 'Identifying...'
                if self.PASSIVE_SELECTED_CONTACT[0] > p2_sonar_start:
                    contact_bearing = self.PASSIVE_SELECTED_CONTACT[0] - (p2_sonar_start + (
                            p2_sonar_end - p2_sonar_start) / 2)
                else:
                    contact_bearing = self.PASSIVE_SELECTED_CONTACT[0] - (p1_sonar_start + (
                            p1_sonar_end - p1_sonar_start) / 2)
                contact_bearing /= scale
                if contact_bearing < 0:
                    contact_bearing += 360
            elif not self.PASSIVE_SONAR_FREEZE:
                torpedo = self.TORPEDOES[self.PASSIVE_SELECTED_CONTACT[2]]
                contact_type = 'Torpedo'
                contact_speed = torpedo[0][3]
                contact_depth = torpedo[0][4]
                rel_x = torpedo[0][0] - self.LOCAL_POSITION[0]
                rel_y = torpedo[0][1] - self.LOCAL_POSITION[1]
                contact_distance = math.sqrt(rel_x * rel_x + rel_y * rel_y)
                contact_heading = torpedo[0][2]
                if contact_heading < 0:
                    contact_heading += 360
                if contact_heading > 360:
                    contact_heading -= 360
                contact_bearing = calculate_bearing(rel_x, rel_y, contact_distance)
                if contact_bearing < 0:
                    contact_bearing += 360
                if contact_distance > PASSIVE_SONAR_RANGE:
                    self.identifying_delay = 0
                    self.PASSIVE_SELECTED_CONTACT = None
        if contact_type:
            txtsurf = self.middle_font.render(f"{contact_type}", True, '#b6b6d1')
        else:
            txtsurf = self.middle_font.render("Select a contact...", True, '#b6b6d1')
        self.window.blit(txtsurf, (110, 450))
        txtsurf = self.middle_font.render(f"{contact_bearing:.2f}", True, '#b6b6d1')
        self.window.blit(txtsurf, (110, 480))
        txtsurf = self.middle_font.render(f"{(contact_speed * 60) / 0.0193:.2f}km/h", True, '#b6b6d1')
        self.window.blit(txtsurf, (110, 510))
        txtsurf = self.middle_font.render(f"{contact_depth:.2f}m", True, '#b6b6d1')
        self.window.blit(txtsurf, (110, 540))
        txtsurf = self.middle_font.render(f"{contact_distance * 2.0923:.2f}km", True, '#b6b6d1')
        self.window.blit(txtsurf, (110, 570))
        txtsurf = self.middle_font.render(f"{contact_heading:.2f} (azimuth)", True, '#b6b6d1')
        self.window.blit(txtsurf, (110, 600))
        if self.sonar_cursor_position:
            if self.PASSIVE_SELECTED_CONTACT:
                pygame.draw.line(self.window, '#00ad06', (self.size[0] // 2, self.sonar_cursor_position[1]),
                                 self.sonar_cursor_position)
                pygame.draw.line(self.window, '#00ad06', (self.sonar_cursor_position[0], 30),
                                 self.sonar_cursor_position)
                pygame.draw.line(self.window, '#00ad06', (self.size[0] - 30, self.sonar_cursor_position[1]),
                                 self.sonar_cursor_position)
                pygame.draw.line(self.window, '#00ad06', (self.sonar_cursor_position[0], self.size[1]),
                                 self.sonar_cursor_position)
            else:
                pygame.draw.line(self.window, '#ad001d', (self.size[0] // 2, self.sonar_cursor_position[1]),
                                 self.sonar_cursor_position)
                pygame.draw.line(self.window, '#ad001d', (self.sonar_cursor_position[0], 30),
                                 self.sonar_cursor_position)
                pygame.draw.line(self.window, '#ad001d', (self.size[0] - 30, self.sonar_cursor_position[1]),
                                 self.sonar_cursor_position)
                pygame.draw.line(self.window, '#ad001d', (self.sonar_cursor_position[0], self.size[1]),
                                 self.sonar_cursor_position)

        if self.TRANSFER_CONTACT_INFO_P:
            self.bearing_var[1] = f"{float(contact_bearing):.2f}"
            self.depth_var[1] = f"{float(contact_depth):.2f}"
            self.distance_var[1] = f"{float(contact_distance) * 2.0923:.2f}"
            # self.TRANSFER_CONTACT_INFO_P = False

        # Position details
        txtsurf = self.middle_font.render(f"Submarine position:", True, '#b6b6d1')
        self.window.blit(txtsurf, (400, 420))
        speed = self.LOCAL_VELOCITY * self.fps
        txtsurf = self.middle_font.render(f"Speed: ", True, '#b6b6d1')
        self.window.blit(txtsurf, (400, 445))
        txtsurf = self.middle_font.render(f"Gear: ", True, '#b6b6d1')
        self.window.blit(txtsurf, (400, 470))
        txtsurf = self.middle_font.render(f"Depth: ", True, '#b6b6d1')
        self.window.blit(txtsurf, (400, 495))
        txtsurf = self.middle_font.render(f"Pitch: ", True, '#b6b6d1')
        self.window.blit(txtsurf, (400, 520))
        txtsurf = self.middle_font.render(f"Heading: ", True, '#b6b6d1')
        self.window.blit(txtsurf, (400, 545))
        txtsurf = self.middle_font.render(f"Ballast: ", True, '#b6b6d1')
        self.window.blit(txtsurf, (400, 570))
        txtsurf = self.middle_font.render(f"Health: ", True, '#b6b6d1')
        self.window.blit(txtsurf, (400, 595))

        txtsurf = self.middle_font.render(f"{speed / 0.0193:.2f}km/h", True, '#b6b6d1')
        self.window.blit(txtsurf, (480, 445))
        txtsurf = self.middle_font.render(f"{self.GEAR}", True, '#b6b6d1')
        self.window.blit(txtsurf, (480, 470))
        txtsurf = self.middle_font.render(f"{self.LOCAL_POSITION[4]:.2f}", True, '#b6b6d1')
        self.window.blit(txtsurf, (480, 495))
        txtsurf = self.middle_font.render(f"{self.LOCAL_POSITION[3]:.2f}", True, '#b6b6d1')
        self.window.blit(txtsurf, (480, 520))
        heading = self.LOCAL_POSITION[2]
        if heading < 0:
            heading += 360
        txtsurf = self.middle_font.render(f"{heading:.2f}", True, '#b6b6d1')
        self.window.blit(txtsurf, (480, 545))
        txtsurf = self.middle_font.render(f"{self.BALLAST:.2f}", True, '#b6b6d1')
        self.window.blit(txtsurf, (480, 570))
        txtsurf = self.middle_font.render(f"{self.HEALTH:.2f}", True, '#b6b6d1')
        self.window.blit(txtsurf, (480, 595))

        pygame.display.update()

    def start_hosting(self):
        server_api.remove_old_games()
        LISTENING_CHANNEL = None
        SENDING_CHANNEL = None
        rand_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        create_time = int(time.mktime(datetime.datetime.utcnow().timetuple()))
        if self.PLAYER_ID:
            enemy = 0
        else:
            enemy = 1
        LISTENING_CHANNEL = server_api.fetch_channel_object(
            server_api.create_channel(f"game{enemy}.{rand_id}-{create_time}"))
        SENDING_CHANNEL = server_api.fetch_channel_object(
            server_api.create_channel(f"game{self.PLAYER_ID}.{rand_id}-{create_time}"))

        server_api.LISTENING_CHANNEL = LISTENING_CHANNEL
        server_api.CHANNEL = SENDING_CHANNEL

        self.GAME_CODE = f"{rand_id}{enemy}"
        print("Waiting for enemy..")
        self.HOST_STATUS = 2
        self.must_update = True

        # Waiting until someone has joined the game
        msg = server_api.wait_for_message()
        if msg is None:  # Used to check if the player decided to abort the game
            server_api.ALLOW_WAIT = True
            return
        while msg['content'] != f"[{enemy}] Joined the game.":
            time.sleep(0.5)
            msg = server_api.wait_for_message()
            if msg is None:
                server_api.ALLOW_WAIT = True
                return
        print("SOMEONE JOINED THE GAME!")
        # Sending mission information
        server_api.SEND_INFO = f"MISSION-INFORMATION%!%{self.mission_name}"
        # Waiting for the other player to download mission info
        msg = server_api.wait_for_message()
        if msg is None:  # Used to check if the player decided to abort the game
            server_api.ALLOW_WAIT = True
            return
        while msg['content'] != f"[{enemy}] Mission loaded.":
            time.sleep(0.5)
            msg = server_api.wait_for_message()
            if msg is None:
                server_api.ALLOW_WAIT = True
                return
        print("Finished loading, ready to start.")
        self.HOST_STATUS = 3
        self.must_update = True

    def sync_time_start(self):
        self.clear_scene()
        self.game_init()
        self.GAME_OPEN = True
        self.GAME_INIT = True

    def host_game_screen_events(self, event):
        if self.starts_in is not None:
            self.must_update = True
            txtsurf = self.middle_font.render(f'Starting in {self.starts_in}', True, '#b6b6d1')
            self.window.blit(txtsurf, mid_rect((self.size[0] / 2 - 60, 31 * self.pos - 20, 120, 40), txtsurf))
        if not self.random_game_rect:  # Make sure the screen has been loaded first
            return
        pygame.mouse.set_cursor(*pygame.cursors.Cursor(pygame.SYSTEM_CURSOR_ARROW))
        if event.type == pygame.QUIT:
            self.running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and pygame.Rect(self.ru_team_box).collidepoint(pygame.mouse.get_pos()):
                self.team_selected = 0
            elif event.button == 1 and pygame.Rect(self.usa_team_box).collidepoint(pygame.mouse.get_pos()):
                self.team_selected = 1
            elif event.button == 1 and pygame.Rect(self.random_team_box).collidepoint(pygame.mouse.get_pos()):
                self.team_selected = 2
            elif event.button == 1 and pygame.Rect(self.back_box).collidepoint(pygame.mouse.get_pos()):
                self.clear_scene()
                self.MAIN_MENU_OPEN = True
            elif event.button == 1 and pygame.Rect(self.browse_game_rect).collidepoint(pygame.mouse.get_pos()):
                self.mission_name = prompt_file()
            elif event.button == 1 and pygame.Rect(self.random_game_rect).collidepoint(pygame.mouse.get_pos()):
                files = [f for f in os.listdir('.') if os.path.isfile(f)]
                choice = []
                for f in files:
                    if f.count('mission'):
                        choice.append(f)
                self.mission_name = random.choice(choice)
            elif event.button == 1 and pygame.Rect(self.host_game_box).collidepoint(pygame.mouse.get_pos()):
                print("Clicked on host game.")
                if self.mission_name and self.HOST_STATUS == 0:
                    if self.team_selected == 2:
                        self.PLAYER_ID = random_int(0, 1)
                        server_api.PLAYER = self.PLAYER_ID
                        print("Hosting...")
                        self.HOST_STATUS = 1
                        hosting_thread = threading.Thread(target=self.start_hosting)
                        hosting_thread.start()
                    else:
                        self.PLAYER_ID = self.team_selected
                        server_api.PLAYER = self.PLAYER_ID
                        print("Hosting...")
                        self.HOST_STATUS = 1
                        hosting_thread = threading.Thread(target=self.start_hosting)
                        hosting_thread.start()
                elif self.HOST_STATUS == 3:
                    server_api.SEND_INFO = f"[{self.PLAYER_ID}] Start the game."
                    while server_api.SEND_INFO:
                        pass
                    print("Starting the game!")
                    threading.Thread(target=self.sync_time_start).start()

            elif self.copy_box:
                if event.button == 1 and pygame.Rect(self.copy_box).collidepoint(pygame.mouse.get_pos()):
                    pyperclip.copy(self.GAME_CODE)
                    print("Copied!")
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F2:
                self.CHEATS = True
            elif event.key == pygame.K_F3:
                if self.mission_name and self.HOST_STATUS == 0 and self.CHEATS:
                    print("Forcefully starting game...")
                    if self.team_selected == 2:
                        self.PLAYER_ID = random_int(0, 1)
                        server_api.PLAYER = self.PLAYER_ID

                    else:
                        self.PLAYER_ID = self.team_selected
                        server_api.PLAYER = self.PLAYER_ID
                    print("Hosting...")
                    self.HOST_STATUS = 1
                    server_api.remove_old_games()
                    LISTENING_CHANNEL = None
                    SENDING_CHANNEL = None
                    rand_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                    create_time = int(time.mktime(datetime.datetime.utcnow().timetuple()))
                    if self.PLAYER_ID:
                        enemy = 0
                    else:
                        enemy = 1
                    LISTENING_CHANNEL = server_api.fetch_channel_object(
                        server_api.create_channel(f"game{enemy}.{rand_id}-{create_time}"))
                    SENDING_CHANNEL = server_api.fetch_channel_object(
                        server_api.create_channel(f"game{self.PLAYER_ID}.{rand_id}-{create_time}"))
                    server_api.LISTENING_CHANNEL = LISTENING_CHANNEL
                    server_api.CHANNEL = SENDING_CHANNEL
                    self.GAME_CODE = f"{rand_id}{enemy}"
                    print("Finished loading, ready to start.")
                    self.clear_scene()
                    self.game_init()
                    self.GAME_OPEN = True
                    self.GAME_INIT = True

        if pygame.Rect(self.browse_game_rect).collidepoint(pygame.mouse.get_pos()):
            pygame.mouse.set_cursor(*pygame.cursors.Cursor(pygame.SYSTEM_CURSOR_HAND))
            pygame.draw.rect(self.window, 'white', self.browse_game_rect, width=2, border_radius=2)
            txtsurf = self.middle_font.render('Browse', True, 'white')
            self.window.blit(txtsurf, mid_rect(self.browse_game_rect, txtsurf))
        elif pygame.Rect(self.random_game_rect).collidepoint(pygame.mouse.get_pos()):
            pygame.mouse.set_cursor(*pygame.cursors.Cursor(pygame.SYSTEM_CURSOR_HAND))
            pygame.draw.rect(self.window, 'white', self.random_game_rect, width=2, border_radius=2)
            txtsurf = self.middle_font.render('Random', True, 'white')
            self.window.blit(txtsurf, mid_rect(self.random_game_rect, txtsurf))
        elif pygame.Rect(self.ru_team_box).collidepoint(pygame.mouse.get_pos()):
            pygame.mouse.set_cursor(*pygame.cursors.Cursor(pygame.SYSTEM_CURSOR_HAND))
        elif pygame.Rect(self.usa_team_box).collidepoint(pygame.mouse.get_pos()):
            pygame.mouse.set_cursor(*pygame.cursors.Cursor(pygame.SYSTEM_CURSOR_HAND))
        elif pygame.Rect(self.random_team_box).collidepoint(pygame.mouse.get_pos()):
            pygame.mouse.set_cursor(*pygame.cursors.Cursor(pygame.SYSTEM_CURSOR_HAND))
        elif pygame.Rect(self.host_game_box).collidepoint(pygame.mouse.get_pos()):
            pygame.mouse.set_cursor(*pygame.cursors.Cursor(pygame.SYSTEM_CURSOR_HAND))
            pygame.draw.rect(self.window, '#DBFFD6', self.host_game_box, width=2, border_radius=2,
                             border_top_left_radius=0,
                             border_bottom_left_radius=0)
            if self.HOST_STATUS == 1:
                txtsurf = self.middle_font.render('Loading...', True, '#DBFFD6')
            elif self.HOST_STATUS == 2:
                txtsurf = self.middle_font.render('Waiting...', True, '#DBFFD6')
            elif self.HOST_STATUS == 3:
                txtsurf = self.middle_font.render('Start', True, '#DBFFD6')
            else:
                txtsurf = self.middle_font.render('Host', True, '#DBFFD6')
            self.window.blit(txtsurf, mid_rect(self.host_game_box, txtsurf))
        elif pygame.Rect(self.back_box).collidepoint(pygame.mouse.get_pos()):
            pygame.mouse.set_cursor(*pygame.cursors.Cursor(pygame.SYSTEM_CURSOR_HAND))
            pygame.draw.rect(self.window, '#FFDBDB', self.back_box, width=2, border_radius=2, border_top_left_radius=0,
                             border_bottom_left_radius=0)
            txtsurf = self.middle_font.render('Back', True, '#FFDBDB')
            self.window.blit(txtsurf, mid_rect(self.back_box, txtsurf))
        elif self.copy_box:
            if pygame.Rect(self.copy_box).collidepoint(pygame.mouse.get_pos()):
                pygame.mouse.set_cursor(*pygame.cursors.Cursor(pygame.SYSTEM_CURSOR_HAND))
                pygame.draw.rect(self.window, 'white', self.copy_box, width=2, border_radius=2,
                                 border_top_left_radius=0,
                                 border_bottom_left_radius=0)
                txtsurf = self.middle_font.render('Copy', True, 'white')
                self.window.blit(txtsurf, mid_rect(self.copy_box, txtsurf))

        pygame.display.update()

    def host_game_render(self):
        self.window.fill("#021019")
        if self.HOST_STATUS == 3:
            txtsurf = self.middle_font.render(f'Player joined the game!', True, '#B7FFB7')
            self.window.blit(txtsurf, mid_rect((self.size[0] / 2 - 60, 31 * self.pos - 20, 120, 40), txtsurf))
        chunk = 33
        self.pos = self.size[1] / chunk
        txtsurf = self.big_font.render('Host a game', True, '#b6b6d1')
        self.window.blit(txtsurf, (self.size[0] / 2 - txtsurf.get_width() / 2, 4 * self.pos))

        self.browse_game_rect = (self.size[0] / 2 - 65 - 90 - 10, 8 * self.pos - 20, 90, 40)
        pygame.draw.rect(self.window, '#b6b6d1', self.browse_game_rect, width=2, border_radius=2)
        txtsurf = self.middle_font.render('Browse', True, '#b6b6d1')
        self.window.blit(txtsurf, mid_rect(self.browse_game_rect, txtsurf))
        self.mission_name_box = (self.size[0] / 2 - 65, 8 * self.pos - 20, 130, 40)
        pygame.draw.rect(self.window, '#b6b6d1', self.mission_name_box, width=2, border_radius=2)

        if self.mission_name:
            name = self.mission_name.split("/")
            if len(name) == 1:
                txtsurf = self.middle_font.render(f'Random', True, '#b6b6d1')
            else:
                txtsurf = self.middle_font.render(f'{name[-1]}', True, '#b6b6d1')
        else:
            txtsurf = self.middle_font.render(f'None', True, '#b6b6d1')
        self.window.blit(txtsurf, mid_rect(self.mission_name_box, txtsurf))
        self.random_game_rect = (self.size[0] / 2 + 65 + 10, 8 * self.pos - 20, 90, 40)
        pygame.draw.rect(self.window, '#b6b6d1', self.random_game_rect, width=2, border_radius=2)
        txtsurf = self.middle_font.render('Random', True, '#b6b6d1')
        self.window.blit(txtsurf, mid_rect(self.random_game_rect, txtsurf))

        if self.team_selected == 0:
            self.ru_team_box = (self.size[0] / 2 - 53 - 90, 12 * self.pos - 20, 90, 40)
            pygame.draw.rect(self.window, '#b6b6d1', self.ru_team_box, border_radius=2, border_top_right_radius=0,
                             border_bottom_right_radius=0)
            txtsurf = self.middle_font.render('RU', True, '#021019')
            self.window.blit(txtsurf, mid_rect(self.ru_team_box, txtsurf))
        else:
            self.ru_team_box = (self.size[0] / 2 - 53 - 90, 12 * self.pos - 20, 90, 40)
            pygame.draw.rect(self.window, '#b6b6d1', self.ru_team_box, width=2, border_radius=2,
                             border_top_right_radius=0,
                             border_bottom_right_radius=0)
            txtsurf = self.middle_font.render('RU', True, '#b6b6d1')
            self.window.blit(txtsurf, mid_rect(self.ru_team_box, txtsurf))
        if self.team_selected == 2:
            self.random_team_box = (self.size[0] / 2 - 55, 12 * self.pos - 20, 110, 40)
            pygame.draw.rect(self.window, '#b6b6d1', self.random_team_box, border_radius=0)
            txtsurf = self.middle_font.render('Random', True, '#021019')
            self.window.blit(txtsurf, mid_rect(self.random_team_box, txtsurf))
        else:
            self.random_team_box = (self.size[0] / 2 - 55, 12 * self.pos - 20, 110, 40)
            pygame.draw.rect(self.window, '#b6b6d1', self.random_team_box, width=2, border_radius=0)
            txtsurf = self.middle_font.render('Random', True, '#b6b6d1')
            self.window.blit(txtsurf, mid_rect(self.random_team_box, txtsurf))
        if self.team_selected == 1:
            self.usa_team_box = (self.size[0] / 2 + 53, 12 * self.pos - 20, 90, 40)
            pygame.draw.rect(self.window, '#b6b6d1', self.usa_team_box, border_radius=2, border_top_left_radius=0,
                             border_bottom_left_radius=0)
            txtsurf = self.middle_font.render('USA', True, '#021019')
            self.window.blit(txtsurf, mid_rect(self.usa_team_box, txtsurf))
        else:
            self.usa_team_box = (self.size[0] / 2 + 53, 12 * self.pos - 20, 90, 40)
            pygame.draw.rect(self.window, '#b6b6d1', self.usa_team_box, width=2, border_radius=2,
                             border_top_left_radius=0,
                             border_bottom_left_radius=0)
            txtsurf = self.middle_font.render('USA', True, '#b6b6d1')
            self.window.blit(txtsurf, mid_rect(self.usa_team_box, txtsurf))

        self.host_game_box = (self.size[0] / 2 - 60, 16 * self.pos - 20, 120, 40)
        pygame.draw.rect(self.window, '#b6b6d1', self.host_game_box, width=2, border_radius=2, border_top_left_radius=0,
                         border_bottom_left_radius=0)
        if self.HOST_STATUS == 1:
            txtsurf = self.middle_font.render('Loading...', True, '#b6b6d1')
        elif self.HOST_STATUS == 2:
            txtsurf = self.middle_font.render('Waiting...', True, '#b6b6d1')
        elif self.HOST_STATUS == 3:
            txtsurf = self.middle_font.render('Start', True, '#b6b6d1')
        else:
            txtsurf = self.middle_font.render('Host', True, '#b6b6d1')
        self.window.blit(txtsurf, mid_rect(self.host_game_box, txtsurf))

        self.back_box = (self.size[0] / 2 - 60, 29 * self.pos - 20, 120, 40)
        pygame.draw.rect(self.window, '#b6b6d1', self.back_box, width=2, border_radius=2, border_top_left_radius=0,
                         border_bottom_left_radius=0)
        txtsurf = self.middle_font.render('Back', True, '#b6b6d1')
        self.window.blit(txtsurf, mid_rect(self.back_box, txtsurf))

        if self.GAME_CODE:
            txtsurf = self.middle_font.render(f'Join code: {self.GAME_CODE}', True, '#DBFFD6')
            self.window.blit(txtsurf,
                             (self.size[0] / 2 - txtsurf.get_width() / 2, 20 * self.pos - txtsurf.get_height() / 2))
            self.copy_box = (self.size[0] / 2 - 30, 24 * self.pos - 15, 60, 30)
            pygame.draw.rect(self.window, '#b6b6d1', self.copy_box, width=2, border_radius=2, border_top_left_radius=0,
                             border_bottom_left_radius=0)
            txtsurf = self.middle_font.render('Copy', True, '#b6b6d1')
            self.window.blit(txtsurf, mid_rect(self.copy_box, txtsurf))
        if self.must_update:
            self.must_update = False
            pygame.display.update()

    def start_joining(self):
        flag = 0
        if self.PLAYER_ID:
            enemy = 0
        else:
            enemy = 1
        for channel in server_api.get_all_channel_names():
            if channel.name.count(f"{self.PLAYER_ID}{self.GAME_CODE_VAR[1][:-1].lower()}"):
                print("Sending channel found!")
                server_api.CHANNEL = channel
                flag += 1
            elif channel.name.count(f"{enemy}{self.GAME_CODE_VAR[1][:-1].lower()}"):
                print("Listening channel found!")
                server_api.LISTENING_CHANNEL = channel
                flag += 1
        if flag >= 2:
            print("Connected!")
            server_api.SEND_INFO = f"[{self.PLAYER_ID}] Joined the game."
            # Waiting for mission information
            msg = server_api.wait_for_message()
            if msg is None:  # Used to check if the player decided to abort the game
                server_api.ALLOW_WAIT = True
                return
            while not msg['content'].count("MISSION-INFORMATION"):
                time.sleep(0.5)
                msg = server_api.wait_for_message()
                if msg is None:
                    server_api.ALLOW_WAIT = True
                    return
            print("Received mission information!", msg['content'])
            info = json.loads(eval(msg['content'].replace("MISSION-INFORMATION", "")))
            json_object = json.dumps(info, indent=4)
            with open("TEMP.json", "w", encoding="utf-8") as temp_file:
                temp_file.write(json_object)
            self.mission_name = 'TEMP.json'
            server_api.SEND_INFO = f"[{self.PLAYER_ID}] Mission loaded."
            self.JOIN_STATUS = 2
            self.must_update = True
            # Waiting for start
            msg = server_api.wait_for_message()
            if msg is None:  # Used to check if the player decided to abort the game
                server_api.ALLOW_WAIT = True
                return
            while msg['content'] != f"[{enemy}] Start the game.":
                time.sleep(0.5)
                msg = server_api.wait_for_message()
                if msg is None:
                    server_api.ALLOW_WAIT = True
                    return
            print("Starting the game!")
            threading.Thread(target=self.sync_time_start).start()
        else:
            print("Join failed.")
            self.JOIN_STATUS = 3
            self.must_update = True

    def join_game_screen_events(self, event):
        if self.starts_in is not None:
            txtsurf = self.middle_font.render(f'Starting in {self.starts_in}', True, '#b6b6d1')
            self.window.blit(txtsurf, mid_rect((self.size[0] / 2 - 60, 25 * self.pos - 20, 120, 40), txtsurf))
        if not self.game_code_box:  # Make sure the screen has been loaded first
            return
        pygame.mouse.set_cursor(*pygame.cursors.Cursor(pygame.SYSTEM_CURSOR_ARROW))
        if event.type == pygame.QUIT:
            self.running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and pygame.Rect(self.game_code_box).collidepoint(pygame.mouse.get_pos()):
                self.GAME_CODE_VAR[0] = True
                self.GAME_CODE_VAR[1] = ""
            elif event.button == 1 and pygame.Rect(self.join_game_box).collidepoint(pygame.mouse.get_pos()):
                print("Clicked on join game.")
                if self.JOIN_STATUS == 0:
                    if self.GAME_CODE_VAR[1] != "" and self.GAME_CODE_VAR[1] != "Game code" and \
                            self.GAME_CODE_VAR[1][-1].isnumeric():
                        self.PLAYER_ID = int(self.GAME_CODE_VAR[1][-1])
                        server_api.PLAYER = self.PLAYER_ID
                        print("Joining...")
                        self.JOIN_STATUS = 1
                        self.must_update = True
                        joining_thread = threading.Thread(target=self.start_joining)
                        joining_thread.start()
                    else:
                        print("Wrong code!")
                        self.JOIN_STATUS = 3
                        self.must_update = True
            elif event.button == 1 and pygame.Rect(self.back_box_join).collidepoint(pygame.mouse.get_pos()):
                self.clear_scene()
                self.MAIN_MENU_OPEN = True
            else:
                self.GAME_CODE_VAR[0] = False
                if self.GAME_CODE_VAR[1] == "":
                    self.GAME_CODE_VAR[1] = "Game code"
        elif event.type == pygame.KEYDOWN:
            if self.GAME_CODE_VAR[0]:
                if event.key == pygame.K_BACKSPACE:
                    self.GAME_CODE_VAR[1] = self.GAME_CODE_VAR[1][:-1]
                elif (event.key == pygame.K_v) and (event.mod & pygame.KMOD_CTRL):
                    self.GAME_CODE_VAR[1] = pyperclip.paste()
                    if len(self.GAME_CODE_VAR[1]) > 15:
                        self.GAME_CODE_VAR[1] = self.GAME_CODE_VAR[1][:15]
                elif len(self.GAME_CODE_VAR[1]) < 15:
                    k = str(pygame.key.name(event.key))
                    if len(k) == 1 and k.isascii():
                        self.GAME_CODE_VAR[1] += k.upper()
            elif event.key == pygame.K_F2:
                self.CHEATS = True

        if pygame.Rect(self.game_code_box).collidepoint(pygame.mouse.get_pos()):
            pygame.mouse.set_cursor(*pygame.cursors.Cursor(pygame.SYSTEM_CURSOR_IBEAM))
            pygame.draw.rect(self.window, 'white', self.game_code_box, width=2, border_radius=2)
            txtsurf = self.middle_font.render(f'{self.GAME_CODE_VAR[1]}', True, 'white')
            self.window.blit(txtsurf, mid_rect(self.game_code_box, txtsurf))
        elif pygame.Rect(self.join_game_box).collidepoint(pygame.mouse.get_pos()):
            pygame.mouse.set_cursor(*pygame.cursors.Cursor(pygame.SYSTEM_CURSOR_HAND))
            pygame.draw.rect(self.window, '#DBFFD6', self.join_game_box, width=2, border_radius=2,
                             border_top_left_radius=0,
                             border_bottom_left_radius=0)
            if self.JOIN_STATUS == 1:
                txtsurf = self.middle_font.render('Joining...', True, '#DBFFD6')
            elif self.JOIN_STATUS == 2:
                txtsurf = self.middle_font.render('Ready...', True, '#DBFFD6')
            elif self.JOIN_STATUS == 3:
                txtsurf = self.middle_font.render('Wrong code!', True, '#DBFFD6')
            else:
                txtsurf = self.middle_font.render('Join', True, '#DBFFD6')
            self.window.blit(txtsurf, mid_rect(self.join_game_box, txtsurf))
        elif pygame.Rect(self.back_box_join).collidepoint(pygame.mouse.get_pos()):
            pygame.mouse.set_cursor(*pygame.cursors.Cursor(pygame.SYSTEM_CURSOR_HAND))
            pygame.draw.rect(self.window, '#FFDBDB', self.back_box_join, width=2, border_radius=2,
                             border_top_left_radius=0,
                             border_bottom_left_radius=0)
            txtsurf = self.middle_font.render('Back', True, '#FFDBDB')
            self.window.blit(txtsurf, mid_rect(self.back_box_join, txtsurf))

        pygame.display.update()

    def join_game_render(self):
        if self.JOIN_STATUS == 3 and self.ERROR_DELAY == 0:
            self.ERROR_DELAY = 3
        if self.ERROR_DELAY:
            self.ERROR_DELAY -= 0.0167 * (self.fps / self.current_fps)
            if self.ERROR_DELAY < 0 or self.ERROR_DELAY == 0:
                self.ERROR_DELAY = 0
                self.JOIN_STATUS = 0
                self.must_update = True
        self.window.fill("#021019")
        if self.starts_in is not None:
            self.must_update = True
            txtsurf = self.middle_font.render(f'Starting in {self.starts_in}', True, '#b6b6d1')
            self.window.blit(txtsurf, mid_rect((self.size[0] / 2 - 60, 25 * self.pos - 20, 120, 40), txtsurf))
        chunk = 33
        self.pos = self.size[1] / chunk
        txtsurf = self.big_font.render('Join a game', True, '#b6b6d1')
        self.window.blit(txtsurf, (self.size[0] / 2 - txtsurf.get_width() / 2, 4 * self.pos))

        self.game_code_box = (self.size[0] / 2 - 105, 12 * self.pos - 15, 210, 30)
        if self.GAME_CODE_VAR[0]:
            pygame.draw.rect(self.window, 'white', self.game_code_box, width=2, border_radius=2)
            txtsurf = self.middle_font.render(f'{self.GAME_CODE_VAR[1]}', True, 'white')
        else:
            pygame.draw.rect(self.window, '#b6b6d1', self.game_code_box, width=2, border_radius=2)
            txtsurf = self.middle_font.render(f'{self.GAME_CODE_VAR[1]}', True, '#b6b6d1')
        self.window.blit(txtsurf, mid_rect(self.game_code_box, txtsurf))

        self.join_game_box = (self.size[0] / 2 - 60, 16 * self.pos - 20, 120, 40)
        pygame.draw.rect(self.window, '#b6b6d1', self.join_game_box, width=2, border_radius=2, border_top_left_radius=0,
                         border_bottom_left_radius=0)
        if self.JOIN_STATUS == 1:
            txtsurf = self.middle_font.render('Joining...', True, '#b6b6d1')
        elif self.JOIN_STATUS == 2:
            txtsurf = self.middle_font.render('Joined.', True, '#b6b6d1')
        elif self.JOIN_STATUS == 3:
            txtsurf = self.middle_font.render('Wrong code!', True, '#b6b6d1')
        else:
            txtsurf = self.middle_font.render('Join', True, '#b6b6d1')
        self.window.blit(txtsurf, mid_rect(self.join_game_box, txtsurf))

        self.back_box_join = (self.size[0] / 2 - 60, 29 * self.pos - 20, 120, 40)
        pygame.draw.rect(self.window, '#b6b6d1', self.back_box_join, width=2, border_radius=2, border_top_left_radius=0,
                         border_bottom_left_radius=0)
        txtsurf = self.middle_font.render('Back', True, '#b6b6d1')
        self.window.blit(txtsurf, mid_rect(self.back_box_join, txtsurf))

        if self.must_update:
            self.must_update = False
            pygame.display.update()

    def win_screen_render(self):
        self.window.fill("#021019")
        chunk = 33
        self.pos = self.size[1] / chunk
        txtsurf = self.big_font.render('You won!', True, 'green')
        self.window.blit(txtsurf, (self.size[0] / 2 - txtsurf.get_width() / 2, 16 * self.pos))
        txtsurf = self.middle_font.render(f'Your score: {self.LOCAL_SCORE}', True, 'green')
        self.window.blit(txtsurf, (self.size[0] / 2 - txtsurf.get_width() / 2, 20 * self.pos))
        txtsurf = self.middle_font.render(f'Enemy score: {self.ENEMY_SCORE}', True, 'green')
        self.window.blit(txtsurf, (self.size[0] / 2 - txtsurf.get_width() / 2, 24 * self.pos))

        pygame.display.update()

    def loss_screen_render(self):
        self.window.fill("#021019")
        chunk = 33
        self.pos = self.size[1] / chunk
        txtsurf = self.big_font.render('You lost!', True, 'red')
        self.window.blit(txtsurf, (self.size[0] / 2 - txtsurf.get_width() / 2, 16 * self.pos))
        txtsurf = self.middle_font.render(f'Your score: {self.LOCAL_SCORE}', True, 'red')
        self.window.blit(txtsurf, (self.size[0] / 2 - txtsurf.get_width() / 2, 20 * self.pos))
        txtsurf = self.middle_font.render(f'Enemy score: {self.ENEMY_SCORE}', True, 'red')
        self.window.blit(txtsurf, (self.size[0] / 2 - txtsurf.get_width() / 2, 24 * self.pos))
        if self.HEALTH <= 0:
            txtsurf = self.middle_font.render(f'You died!', True, 'red')
            self.window.blit(txtsurf, (self.size[0] / 2 - txtsurf.get_width() / 2, 28 * self.pos))

        pygame.display.update()

    def scoreboard_render(self):
        self.window.fill("#021019")
        self.render_notifications()
        sb_grid = (self.size[0] - 200) / 4

        self.score_board_rect = (100, 100, self.size[0] - 200, self.size[1] - 200)
        pygame.draw.rect(self.window, '#b6b6d1', self.score_board_rect, width=2, border_radius=2)
        pygame.draw.line(self.window, '#b6b6d1', (100, 150), (self.size[0] - 101, 150), width=2)
        # Scoreboard information tab
        txtsurf = self.middle_font.render('Player', True, "#b6b6d1")
        self.window.blit(txtsurf,
                         (100 + (sb_grid * 0 + sb_grid / 2 - txtsurf.get_width() / 2), 125 - txtsurf.get_height() / 2))
        txtsurf = self.middle_font.render('Ships destroyed', True, "#b6b6d1")
        self.window.blit(txtsurf,
                         (100 + (sb_grid * 1 + sb_grid / 2 - txtsurf.get_width() / 2), 125 - txtsurf.get_height() / 2))
        txtsurf = self.middle_font.render('Targets destroyed', True, "#b6b6d1")
        self.window.blit(txtsurf,
                         (100 + (sb_grid * 2 + sb_grid / 2 - txtsurf.get_width() / 2), 125 - txtsurf.get_height() / 2))
        txtsurf = self.middle_font.render('Score', True, "#b6b6d1")
        self.window.blit(txtsurf,
                         (100 + (sb_grid * 3 + sb_grid / 2 - txtsurf.get_width() / 2), 125 - txtsurf.get_height() / 2))
        if self.LOCAL_SCORE > self.ENEMY_SCORE:
            p = 0
            e = 1
        else:
            p = 1
            e = 0
        txtsurf = self.middle_font.render('You', True, "#b6b6d1")
        self.window.blit(txtsurf,
                         (100 + (sb_grid * 0 + sb_grid / 2 - txtsurf.get_width() / 2),
                          175 + p * 50 - txtsurf.get_height() / 2))
        txtsurf = self.middle_font.render(f'{self.SHIPS_DESTROYED}', True, "#b6b6d1")
        self.window.blit(txtsurf,
                         (100 + (sb_grid * 1 + sb_grid / 2 - txtsurf.get_width() / 2),
                          175 + p * 50 - txtsurf.get_height() / 2))
        txtsurf = self.middle_font.render(f'{self.TARGETS_DESTROYED}', True, "#b6b6d1")
        self.window.blit(txtsurf,
                         (100 + (sb_grid * 2 + sb_grid / 2 - txtsurf.get_width() / 2),
                          175 + p * 50 - txtsurf.get_height() / 2))
        txtsurf = self.middle_font.render(f'{self.LOCAL_SCORE}', True, "#b6b6d1")
        self.window.blit(txtsurf,
                         (100 + (sb_grid * 3 + sb_grid / 2 - txtsurf.get_width() / 2),
                          175 + p * 50 - txtsurf.get_height() / 2))
        # Enemy
        txtsurf = self.middle_font.render('Enemy', True, "#b6b6d1")
        self.window.blit(txtsurf,
                         (100 + (sb_grid * 0 + sb_grid / 2 - txtsurf.get_width() / 2),
                          175 + e * 50 - txtsurf.get_height() / 2))
        txtsurf = self.middle_font.render(f'{self.SHIPS_DESTROYED_ENEMY}', True, "#b6b6d1")
        self.window.blit(txtsurf,
                         (100 + (sb_grid * 1 + sb_grid / 2 - txtsurf.get_width() / 2),
                          175 + e * 50 - txtsurf.get_height() / 2))
        txtsurf = self.middle_font.render(f'{self.TARGETS_DESTROYED_ENEMY}', True, "#b6b6d1")
        self.window.blit(txtsurf,
                         (100 + (sb_grid * 2 + sb_grid / 2 - txtsurf.get_width() / 2),
                          175 + e * 50 - txtsurf.get_height() / 2))
        txtsurf = self.middle_font.render(f'{self.ENEMY_SCORE}', True, "#b6b6d1")
        self.window.blit(txtsurf,
                         (100 + (sb_grid * 3 + sb_grid / 2 - txtsurf.get_width() / 2),
                          175 + e * 50 - txtsurf.get_height() / 2))
        pygame.display.update()

    def scoreboard_events(self, event):
        pygame.mouse.set_cursor(*pygame.cursors.Cursor(pygame.SYSTEM_CURSOR_ARROW))
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                flag = 0
                if self.MAP_OPEN:
                    flag = 1
                self.clear_scene()
                if not flag:
                    self.GAME_OPEN = True
                else:
                    self.MAP_OPEN = True

        pygame.display.update()


def start_the_game():
    pygame.init()
    app = App()
    app.on_execute()


if __name__ == "__main__":
    threading.Thread(target=start_the_game).start()
    asyncio.run(server_api.start_bot())
