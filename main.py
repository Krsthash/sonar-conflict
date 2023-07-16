import colorsys
import json
import math
import os
import random

import pygame


def random_int(low, high):
    return math.floor((high - low + 1) * random.random()) + low


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


class App:
    def __init__(self):
        self.FRIENDLY_TARGET_LOCATIONS = []
        self.ENEMY_TARGET_LOCATIONS = []
        self.HEALTH = 100
        self.TORPEDOES = []
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
        self.PLAYER_ID = 0
        self.ACTIVE_SONAR_SELECTED_CONTACT = None
        self.identifying_delay = 0
        self.PASSIVE_SELECTED_CONTACT = None
        self.PASSIVE_SONAR_FREEZE = False
        self.sonar_cursor_position = None
        self.OBJECTS = {}
        self.PASSIVE_SONAR_BUTTON_HOVER = False
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
        current_dir = os.path.dirname(os.path.realpath(__file__))
        self.map = pygame.image.load(current_dir + '/Assets/map.png')
        self.map_rect = self.map.get_rect(topleft=self.window.get_rect().topleft)

        # create window
        pygame.display.flip()

    def clear_scene(self):
        self.MAP_OPEN = False
        self.MAIN_MENU_OPEN = False
        self.JOIN_GAME_OPEN = False
        self.GAME_OPEN = False

    def open_map(self):
        # Uncomment to reset map's position
        # self.map_rect = self.map.get_rect(topleft=self.window.get_rect().topleft)
        self.blitmap()

    def blitmap(self):
        current_dir = os.path.dirname(os.path.realpath(__file__))
        self.map = pygame.image.load(current_dir + '/Assets/map.png')
        # Collision detection
        if self.map.get_at((int(self.LOCAL_POSITION[0]), int(self.LOCAL_POSITION[1])))[:3] != (2, 16, 25):
            print("COLLIDED WITH LAND.")
            self.LOCAL_VELOCITY = 0
            self.LOCAL_ACCELERATION = 0
        self.map_render()
        self.mapsurface = pygame.transform.smoothscale(self.map, self.map_rect.size)
        self.window.fill(0)
        self.window.blit(self.mapsurface, self.map_rect)
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

        # Port locations
        for port in self.FRIENDLY_PORT_LOCATIONS:
            pygame.draw.circle(self.map, 'green', (port[0], port[1]), 4)

        # Friendly target locations
        for target in self.FRIENDLY_TARGET_LOCATIONS:
            pygame.draw.circle(self.map, 'yellow', (target[0], target[1]), 2)
            txtsurf = self.small_font.render(f"{target[2]}%", True, 'gray')
            self.map.blit(txtsurf, (target[0], target[1]))

        # Enemy target locations
        for target in self.ENEMY_TARGET_LOCATIONS:
            pygame.draw.circle(self.map, 'orange', (target[0], target[1]), 2)
            txtsurf = self.small_font.render(f"{target[2]}%", True, 'gray')
            self.map.blit(txtsurf, (target[0], target[1]))

        # for torpedo in self.TORPEDOES:
        #     pygame.draw.circle(self.map, 'red', (torpedo[0][0], torpedo[0][1]), 2)

        pygame.display.update()

    def on_cleanup(self):
        pygame.quit()

    def open_main_menu(self):
        self.window.fill("#021019")
        font = pygame.font.Font('freesansbold.ttf', 32)
        txtsurf = font.render("Sonar Conflict", True, "#b6b6d1")
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
                print(pygame.mouse.get_pos())
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
            if event.key == pygame.K_m:
                self.clear_scene()
                self.GAME_OPEN = True
                self.start_game()
            elif event.key == pygame.K_LCTRL:
                if self.GEAR > -3:
                    self.GEAR -= 1
                print(self.GEAR)
            elif event.key == pygame.K_LSHIFT:
                if self.GEAR != 3:
                    self.GEAR += 1
                print(self.GEAR)

        pygame.display.update()

    def main_menu_events(self, event):
        pygame.mouse.set_cursor(*pygame.cursors.Cursor(pygame.SYSTEM_CURSOR_ARROW))
        if event.type == pygame.QUIT:
            self.running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.join_game_rect.collidepoint(pygame.mouse.get_pos()):
                self.clear_scene()
                self.GAME_OPEN = True
                self.GAME_INIT = True
                self.game_init()

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
        mission = None
        with open('mission1.json', 'r') as file:
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
                                 100, 0]
        # [x, y, azimuth, depth], type, velocity, detection_chance, HEALTH* ACTIVE_SONAR**
        i = 1
        for vessel in mission[code]['ships']:
            self.OBJECTS[f'Friendly_ship_{i}'] = [[vessel[0], vessel[1], vessel[2], vessel[3]],
                                                  vessel[4], vessel[5], vessel[6], vessel[7], 0]
            i += 1
        i = 1
        for vessel in mission[enemy_code]['ships']:
            self.OBJECTS[f'Enemy_ship_{i}'] = [[vessel[0], vessel[1], vessel[2], vessel[3]],
                                               vessel[4], vessel[5], vessel[6], vessel[7], 0]
            i += 1
        self.SONAR_SCREEN = True

    def start_game(self):
        self.window.fill('black')

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
                else:
                    self.ACTIVE_SONAR = True
                    self.ACTIVE_SONAR_PING_DELAY = 0
                    self.ACTIVE_SONAR_PING_RADIUS = 0
            elif event.key == pygame.K_f:
                if self.PASSIVE_SONAR_FREEZE:
                    self.PASSIVE_SONAR_FREEZE = False
                else:
                    self.PASSIVE_SONAR_FREEZE = True
            elif event.key == pygame.K_e:
                self.WEAPON_SCREEN = True
                self.SONAR_SCREEN = False

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
                                        and self.WEAPON_LAYOUT[self.SELECTED_WEAPON][0][1] != 0:
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
                    self.TRANSFER_CONTACT_INFO_A = True
                elif pygame.Rect(self.passive_transfer_box).collidepoint(pygame.mouse.get_pos()):
                    self.TRANSFER_CONTACT_INFO_P = True
                elif pygame.Rect(self.reset_box).collidepoint(pygame.mouse.get_pos()):
                    self.bearing_var[1] = ''
                    self.depth_var[1] = ''
                    self.distance_var[1] = ''
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
                            elif self.WEAPON_LAYOUT[self.SELECTED_WEAPON][0][0] == 1 and self.mode_var != -1:
                                print("ALLOWED")
                                flag = 1
                            elif self.WEAPON_LAYOUT[self.SELECTED_WEAPON][1] == 'UGM-84' and self.mode_var == -1 and \
                                    self.LOCAL_POSITION[4] < 60:
                                print("ALLOWED")
                                flag = 1
                            else:
                                print("NOT ALLOWED")
                        else:
                            print("NOT ALLOWED")
                    else:
                        print("NOT ALLOWED")
                    if flag:
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
                            speed = 2
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
                            sensor_range = 5
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
                            if random_int(0, 10) < 2:
                                destruction = 0
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
                            range = 70  # = 2500km  # = 140 km
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
                            sensor_range = 10
                            speed = 2.1
                            range = 70  # = 2500km  # = 140 km
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

    def weapon_screen_render(self):
        self.window.fill(0)

        # Splitter lines
        pygame.draw.line(self.window, '#b6b6d1', (300, 0), (300, self.size[1]))
        pygame.draw.line(self.window, '#b6b6d1', (300, 100), (self.size[0], 100))
        pygame.draw.line(self.window, '#b6b6d1', (0, 300), (300, 300))

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
        txtsurf = self.middle_font.render(f"X: ", True, '#b6b6d1')
        self.window.blit(txtsurf, (20, 180))
        txtsurf = self.middle_font.render(f"Y: ", True, '#b6b6d1')
        self.window.blit(txtsurf, (20, 205))

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
        txtsurf = self.middle_font.render(f"{self.LOCAL_POSITION[0]:.2f}", True, '#b6b6d1')
        self.window.blit(txtsurf, (100, 180))
        txtsurf = self.middle_font.render(f"{self.LOCAL_POSITION[1]:.2f}", True, '#b6b6d1')
        self.window.blit(txtsurf, (100, 205))

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
            # Torpedo tubes
            for i in range(10):
                rect = (640, 120 + i * 40, 50, 7)
                if rect not in list(self.WEAPON_LAYOUT):
                    self.WEAPON_LAYOUT[rect] = [(1, 0), '']
                if self.WEAPON_LAYOUT[rect][1] != '':
                    if self.WEAPON_LAYOUT[rect][1] == 'Futlyar':
                        pygame.draw.rect(self.window, '#263ded', rect, border_radius=5)
                    else:
                        pygame.draw.rect(self.window, '#ffff82', rect, border_radius=5)
                    txtsurf = self.small_font.render(self.WEAPON_LAYOUT[rect][1], True, '#b6b6d1')
                    self.window.blit(txtsurf, (rect[0], rect[1] + 10))
                pygame.draw.rect(self.window, 'red', rect, border_radius=5, width=1)
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
                    else:
                        pygame.draw.rect(self.window, '#ffff82', rect, border_radius=5)
                    txtsurf = self.small_font.render(self.WEAPON_LAYOUT[rect][1], True, '#b6b6d1')
                    self.window.blit(txtsurf, (rect[0], rect[1] + 10))
                pygame.draw.rect(self.window, 'red', rect, border_radius=5, width=1)
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
        pygame.draw.rect(self.window, 'green', self.active_transfer_box, border_radius=2)
        txtsurf = self.middle_font.render("A", True, 'black')
        self.window.blit(txtsurf, (320 + (10 - txtsurf.get_width() // 2), 70 + (10 - txtsurf.get_height() // 2)))

        self.passive_transfer_box = (350, 70, 20, 20)
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

        txtsurf = self.middle_font.render("Mode: ", True, 'white')
        self.window.blit(txtsurf, (620, 37.5 + (12.5 - txtsurf.get_height() // 2)))
        if self.mode_var == 1:
            txtsurf = self.middle_font.render("Active", True, 'white')
        elif self.mode_var == 0:
            txtsurf = self.middle_font.render("Passive", True, 'white')
        else:
            txtsurf = self.middle_font.render("Normal", True, 'white')
        self.window.blit(txtsurf, (680, 37.5 + (12.5 - txtsurf.get_height() // 2)))

        self.change_mode_box = (750, 37.5, 25, 25)
        pygame.draw.rect(self.window, '#b6b6d1', self.change_mode_box, border_radius=2)

        self.fire_box = (795, 37.5, 80, 25)
        pygame.draw.rect(self.window, 'red', self.fire_box, border_radius=2)
        txtsurf = self.middle_font.render("FIRE", True, 'white')
        self.window.blit(txtsurf, (795 + (40 - txtsurf.get_width() // 2), 37.5 + (12.5 - txtsurf.get_height() // 2)))

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
                # Checking if the player is alive
                if self.HEALTH <= 0:
                    print("PLAYER DIED.")

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

                self.LOCAL_POSITION[4] -= (self.LOCAL_VELOCITY * fps_d) * math.sin(math.radians(self.LOCAL_POSITION[3]))
                self.LOCAL_POSITION[4] += (self.BALLAST - 50) * 0.0008 * fps_d
                if self.LOCAL_POSITION[4] < 0:
                    self.LOCAL_POSITION[4] = 0
                elif self.LOCAL_POSITION[4] >= 700:
                    self.LOCAL_POSITION[4] = 700

                # Other vessel's simulation
                for vessel in self.OBJECTS:
                    if vessel != 'Enemy' and self.OBJECTS[vessel][2] != 0:
                        self.OBJECTS[vessel][0][0] += (self.OBJECTS[vessel][2] * fps_d) * math.cos(
                            math.radians(self.OBJECTS[vessel][0][2] - 90))
                        self.OBJECTS[vessel][0][1] += (self.OBJECTS[vessel][2] * fps_d) * math.sin(
                            math.radians(self.OBJECTS[vessel][0][2] - 90))

                # Land attack missile simulation:
                for missile in self.LAM_FIRED:
                    missile[0] -= 0.01667 * fps_d
                    if missile[0] <= 0:
                        if missile[1] and missile[2]:  # Will hit and has a target
                            print("TARGET HIT!")
                            missile[2][2] -= missile[5]
                            if missile[2][2] < 0:
                                missile[2][2] = 0
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
                                        self.OBJECTS.pop(ship)
                    if missile[0] < -5:
                        self.ASM_FIRED.remove(missile)

                # Enemy ships trying to detect/shoot simulation
                for ship in list(self.OBJECTS):
                    if ship.count("Enemy_ship"):
                        rel_x = self.OBJECTS[ship][0][0] - self.LOCAL_POSITION[0]
                        rel_y = self.OBJECTS[ship][0][1] - self.LOCAL_POSITION[1]
                        distance = math.sqrt(rel_x * rel_x + rel_y * rel_y)
                        # Ships could only really detect you from 50km in the worst case scenario (dc = 0.5)
                        if distance + ((1 - self.DETECTION_CHANCE) * 50) <= 50:
                            if self.OBJECTS[ship][5] <= 0:
                                self.OBJECTS[ship][5] = 2
                            # TODO: Ship relays your position to the enemy submarine
                        if self.OBJECTS[ship][5] > 0:
                            # [x, y, azimuth, velocity, depth], [destination x, destination y, depth], sensor on/off,
                            # timer, sender
                            flag = 0
                            for torpedo in self.TORPEDOES:
                                if torpedo[4] == ship and torpedo[3] > 10:
                                    flag = 1
                            if not flag and distance < 25:  # distance check redundant
                                # Leading the target
                                time = distance / 2.2
                                if time < 1:
                                    time = 1
                                dest_x = self.LOCAL_POSITION[0] + ((self.LOCAL_VELOCITY * fps_d) * math.cos(
                                    math.radians(self.LOCAL_POSITION[2] - 90))) * time * 60
                                dest_y = self.LOCAL_POSITION[1] + ((self.LOCAL_VELOCITY * fps_d) * math.sin(
                                    math.radians(self.LOCAL_POSITION[2] - 90))) * time * 60

                                print(self.LOCAL_POSITION[0], self.LOCAL_POSITION[1], dest_x, dest_y)

                                self.TORPEDOES.append([[self.OBJECTS[ship][0][0], self.OBJECTS[ship][0][1],
                                                        self.OBJECTS[ship][0][2], 0.0367, self.OBJECTS[ship][0][3]],
                                                       [dest_x, dest_y, self.LOCAL_POSITION[3]], False, 20, ship, 0,
                                                       True])

                # Enemy torpedo simulation
                for torpedo in list(self.TORPEDOES):
                    if torpedo[6]:  # If torpedo is in the active mode
                        if torpedo[5] <= 0:
                            torpedo[5] = 1
                    torpedo[3] -= 0.0167 * fps_d
                    if torpedo[3] <= 0:
                        self.TORPEDOES.remove(torpedo)
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
                        dive_rate = 0.42 * fps_d
                        depth = torpedo[1][2] - torpedo[0][4]
                        if dive_rate > depth:
                            dive_rate = depth
                        if depth > 0:
                            torpedo[0][4] += dive_rate
                        else:
                            torpedo[0][4] -= dive_rate
                        torpedo[0][0] += (torpedo[0][3] * fps_d) * math.cos(
                            math.radians(torpedo[0][2] - 90))
                        torpedo[0][1] += (torpedo[0][3] * fps_d) * math.sin(
                            math.radians(torpedo[0][2] - 90))
                        if -10 < distance < 10:
                            torpedo[2] = True
                    else:
                        # Go into seeking mode
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
                        depth = self.LOCAL_POSITION[3] - torpedo[0][4]
                        if distance < 10 and 150 > angle > -150 and -50 < depth < 50:
                            turn = 0.34 * fps_d
                            if turn > abs(angle):
                                turn = abs(angle)
                            if angle > 0:
                                torpedo[0][2] += turn
                            else:
                                torpedo[0][2] -= turn
                            dive_rate = 0.22 * fps_d
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
                            if -1 < distance < 1:
                                print("TORPEDO HIT!")
                                self.TORPEDOES.remove(torpedo)
                                self.HEALTH -= random_int(30, 50)
                        else:
                            # Updating torpedo's position
                            torpedo[0][0] += (torpedo[0][3] * fps_d) * math.cos(
                                math.radians(torpedo[0][2] - 90))
                            torpedo[0][1] += (torpedo[0][3] * fps_d) * math.sin(
                                math.radians(torpedo[0][2] - 90))
                            # TODO: MAKE TORPEDO'S ACTIVE PING VISIBLE

            if self.MAIN_MENU_OPEN:
                self.open_main_menu()
            elif self.GAME_OPEN:
                if self.SONAR_SCREEN:
                    self.sonar_screen_render()
                elif self.WEAPON_SCREEN:
                    self.weapon_screen_render()
            elif self.MAP_OPEN:
                map_delay += tick_time
                if map_delay > self.fps * 2:
                    self.blitmap()
                    map_delay = 0

            # Scene event checks
            for event in pygame.event.get():
                if self.MAP_OPEN:
                    self.check_map_events(event)
                elif self.MAIN_MENU_OPEN:
                    self.main_menu_events(event)
                elif self.SONAR_SCREEN:
                    self.game_events(event)
                elif self.WEAPON_SCREEN:
                    self.weapon_screen_events(event)

            if self.GAME_INIT:
                keys = pygame.key.get_pressed()
                if keys[pygame.K_a]:
                    if self.LOCAL_POSITION[2] > -360:
                        turn_rate = 0.5 * (1 - (abs(self.LOCAL_VELOCITY) / 0.3))
                        self.LOCAL_POSITION[2] -= turn_rate * fps_d
                    else:
                        self.LOCAL_POSITION[2] = 0
                elif keys[pygame.K_d]:
                    if self.LOCAL_POSITION[2] < 360:
                        turn_rate = 0.5 * (1 - (abs(self.LOCAL_VELOCITY) / 0.3))
                        self.LOCAL_POSITION[2] += turn_rate * fps_d
                    else:
                        self.LOCAL_POSITION[2] = 0
                elif keys[pygame.K_w]:
                    if self.LOCAL_POSITION[3] < 45:
                        pitch_rate = 0.2 * (1 - (abs(self.LOCAL_VELOCITY) / 0.09))
                        self.LOCAL_POSITION[3] += pitch_rate * fps_d
                elif keys[pygame.K_s]:
                    if self.LOCAL_POSITION[3] > -45:
                        pitch_rate = 0.2 * (1 - (abs(self.LOCAL_VELOCITY) / 0.09))
                        self.LOCAL_POSITION[3] -= pitch_rate * fps_d
                elif keys[pygame.K_UP]:
                    if self.depth_var[0]:
                        self.depth_var[1] = str(float(self.depth_var[1]) + 1)
                    elif self.bearing_var[0]:
                        self.bearing_var[1] = str(float(self.bearing_var[1]) + 1)
                    elif self.distance_var[0]:
                        self.distance_var[1] = str(float(self.distance_var[1]) + 1)
                    elif self.BALLAST < 100:
                        self.BALLAST += 0.5 * fps_d
                elif keys[pygame.K_DOWN]:
                    if self.depth_var[0]:
                        self.depth_var[1] = str(float(self.depth_var[1]) - 1)
                    elif self.bearing_var[0]:
                        self.bearing_var[1] = str(float(self.bearing_var[1]) - 1)
                    elif self.distance_var[0]:
                        self.distance_var[1] = str(float(self.distance_var[1]) - 1)
                    if self.BALLAST > 0:
                        self.BALLAST -= 0.5 * fps_d

        self.on_cleanup()

    def sonar_screen_render(self):
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
        self.window.fill('black')

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
                self.TRANSFER_CONTACT_INFO_A = False
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
        pygame.draw.rect(self.window, 'gray', (self.size[0] // 2 - 30, 0, self.size[0] // 2 + 30, self.size[1]),
                         width=2)
        pygame.draw.rect(self.window, 'gray', (self.size[0] // 2, 30, self.size[0] // 2 - 30, self.size[1]), width=2)
        pygame.draw.rect(self.window, 'gray', (self.size[0] // 2, 30, (self.size[0] // 2 - 30) // 2, self.size[1]),
                         width=2)
        txtsurf = self.small_font.render(f"Time", True, "#b6b6d1")
        txtsurf = pygame.transform.rotate(txtsurf, 90)
        self.window.blit(txtsurf, (self.size[0] // 2 + 15 - 30 - txtsurf.get_width() // 2,
                                   self.size[1] // 2 - txtsurf.get_height() // 2))
        labels = ['180', '270', '0', '90', '180']
        for i in range(5):
            x = self.size[0] / 2 + i * (((self.size[0] // 2 - 30) // 2) / 4 - 0.5)
            y = 30
            pygame.draw.line(self.window, 'gray', (x, y), (x, y - 5), width=1)
            txtsurf = self.small_font.render(f"{labels[i]}", True, "#b6b6d1")
            self.window.blit(txtsurf, (x - txtsurf.get_width() // 2,
                                       y - 10 - txtsurf.get_height() // 2))
        for i in range(5):
            x = self.size[0] / 2 + (self.size[0] // 2 - 30) // 2 + i * ((self.size[0] // 2 - 30) // 2) / 4 - 1
            y = 30
            pygame.draw.line(self.window, 'gray', (x, y), (x, y - 5), width=1)
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
            if self.OBJECTS[vessel][5] > 0.5:
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
            if self.OBJECTS[vessel][5] - 0.0167 > 0:
                self.OBJECTS[vessel][5] -= 0.0167
            else:
                self.OBJECTS[vessel][5] = 0

        for torpedo in self.TORPEDOES:
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
            if torpedo[5] > 0.5:
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
            if torpedo[5] - 0.0167 > 0:
                torpedo[5] -= 0.0167
            else:
                torpedo[5] = 0

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
                contact_bearing = calculate_bearing(rel_x, rel_y, contact_distance)
                if contact_bearing < 0:
                    contact_bearing += 360
                if contact_distance > PASSIVE_SONAR_RANGE:
                    self.identifying_delay = 0
                    self.PASSIVE_SELECTED_CONTACT = None
        elif self.PASSIVE_SELECTED_CONTACT and self.PASSIVE_SELECTED_CONTACT[2] in self.TORPEDOES:
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
                torpedo = self.TORPEDOES[self.TORPEDOES.index(self.PASSIVE_SELECTED_CONTACT[2])]
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
            self.TRANSFER_CONTACT_INFO_P = False

        pygame.display.update()


pygame.init()
start = App()
start.on_execute()
