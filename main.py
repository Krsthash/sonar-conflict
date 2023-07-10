import colorsys
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


class App:
    def __init__(self):
        self.identifying_delay = 0
        self.PASSIVE_SELECTED_CONTACT = None
        self.PASSIVE_SONAR_FREEZE = False
        self.sonar_cursor_position = None
        self.OBJECTS = {}
        self.PASSIVE_SONAR_BUTTON_HOVER = False
        self.middle_font = pygame.font.Font('freesansbold.ttf', 15)
        self.small_font = pygame.font.Font('freesansbold.ttf', 10)
        self.PASSIVE_SONAR_DISPLAY_CONTACTS = []
        self.ENEMY_DETECTION_CHANCE = 0
        self.ACTIVE_SONAR_CONTACTS = {}
        self.ACTIVE_SONAR_PING_DELAY = 0
        self.ACTIVE_SONAR_PING_RADIUS = 0
        self.ACTIVE_SONAR = False
        self.BALLAST = 50
        self.GEAR = 0
        self.LOCAL_ACCELERATION = 0
        self.LOCAL_VELOCITY = 0
        self.ENEMY_POSITION = None
        self.LOCAL_POSITION = None
        self.G_SPAWN_POSITIONS = None
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

    def map_render(self):
        # Location marker rendering
        width = 10
        height = 10
        point1 = (self.LOCAL_POSITION[0] + width * math.cos(math.radians(self.LOCAL_POSITION[2] - 90)),
                  self.LOCAL_POSITION[1] + height * math.sin(math.radians(self.LOCAL_POSITION[2] - 90)))
        # point2 = (self.LOCAL_POSITION[0] + width//2 * math.cos(math.radians(self.LOCAL_POSITION[2] - 180)),
        #           self.LOCAL_POSITION[1] + height//2 * math.sin(math.radians(self.LOCAL_POSITION[2] - 180)))
        #
        # point3 = (self.LOCAL_POSITION[0] + width//2 * math.cos(math.radians(self.LOCAL_POSITION[2])),
        #           self.LOCAL_POSITION[1] + height//2 * math.sin(math.radians(self.LOCAL_POSITION[2])))
        # pygame.draw.polygon(self.map, 'red', (point1, point2, point3), width=1)
        pygame.draw.aaline(self.map, 'red', (self.LOCAL_POSITION[0], self.LOCAL_POSITION[1]), point1)
        pygame.draw.circle(self.map, 'green', (self.LOCAL_POSITION[0], self.LOCAL_POSITION[1]), 2)
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
            elif event.button == 4 or event.button == 5:
                zoom = 1.2 if event.button == 4 else 0.8
                mx, my = event.pos
                left = mx + (self.map_rect.left - mx) * zoom
                right = mx + (self.map_rect.right - mx) * zoom
                top = my + (self.map_rect.top - my) * zoom
                bottom = my + (self.map_rect.bottom - my) * zoom
                if left > 0 or right < 1306 or top > 0 or bottom < self.size[1]:
                    left = 0
                    right = 1306
                    top = 0
                    bottom = 720
                elif right > 3000 and bottom > 2000:
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
                self.game_init(0)

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

    def game_init(self, player_id):
        self.G_SPAWN_POSITIONS = [(400, 100, 150, 400), (400, 150, 0, 400)]
        # x, y, azimuth, depth
        self.LOCAL_POSITION = [self.G_SPAWN_POSITIONS[player_id][0], self.G_SPAWN_POSITIONS[player_id][1],
                               self.G_SPAWN_POSITIONS[player_id][2], 0, self.G_SPAWN_POSITIONS[player_id][3]]
        # x, y, azimuth, pitch, depth
        if player_id:
            self.ENEMY_POSITION = [self.G_SPAWN_POSITIONS[0][0], self.G_SPAWN_POSITIONS[0][1],
                                   self.G_SPAWN_POSITIONS[0][2], self.G_SPAWN_POSITIONS[0][3]]
            self.OBJECTS['Enemy'] = [self.ENEMY_POSITION, 'Submarine', 0, 1]
        else:
            self.ENEMY_POSITION = [self.G_SPAWN_POSITIONS[1][0], self.G_SPAWN_POSITIONS[1][1],
                                   self.G_SPAWN_POSITIONS[1][2], self.G_SPAWN_POSITIONS[1][3]]
            self.OBJECTS['Enemy'] = [self.ENEMY_POSITION, 'Submarine', 0, 1]
            # [x, y, azimuth, depth], type, velocity, detection_chance
        self.SONAR_SCREEN = True
        self.ENEMY_DETECTION_CHANCE = 1

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
                            flag = 1
                    if not flag:
                        self.PASSIVE_SELECTED_CONTACT = None
                        self.identifying_delay = 0
                elif pygame.Rect(10, 650, 200, 40).collidepoint(pygame.mouse.get_pos()):
                    self.identifying_delay = 0.0167

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

        elif pygame.Rect(10, 650, 200, 40).collidepoint(pygame.mouse.get_pos()):
            self.PASSIVE_SONAR_BUTTON_HOVER = True
            pygame.mouse.set_cursor(*pygame.cursors.Cursor(pygame.SYSTEM_CURSOR_HAND))

        elif pygame.Rect(self.size[0] // 2, 30,
                         self.size[0] // 2 - 30, self.size[1] - 30).collidepoint(pygame.mouse.get_pos()):
            mouse_pos = pygame.mouse.get_pos()
            self.sonar_cursor_position = mouse_pos

    def on_execute(self):
        WATER_DRAG = 0.0002
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
                # Movement calculations
                if self.GEAR == 1:
                    ratio = 1.2 - self.LOCAL_VELOCITY / 0.05
                    self.LOCAL_ACCELERATION = 0.0007 * ratio
                elif self.GEAR == 2:
                    ratio = 1 - self.LOCAL_VELOCITY / 0.08
                    self.LOCAL_ACCELERATION = 0.0008 * ratio
                elif self.GEAR == 3:
                    ratio = 1 - self.LOCAL_VELOCITY / 0.10
                    self.LOCAL_ACCELERATION = 0.0009 * ratio
                elif self.GEAR == 0:
                    self.LOCAL_ACCELERATION = 0
                elif self.GEAR == -1:
                    ratio = 1.2 + self.LOCAL_VELOCITY / 0.05
                    self.LOCAL_ACCELERATION = -0.0007 * ratio
                elif self.GEAR == -2:
                    ratio = 1 + self.LOCAL_VELOCITY / 0.08
                    self.LOCAL_ACCELERATION = -0.0008 * ratio
                elif self.GEAR == -3:
                    ratio = 1 + self.LOCAL_VELOCITY / 0.10
                    self.LOCAL_ACCELERATION = -0.0009 * ratio

                self.LOCAL_VELOCITY += self.LOCAL_ACCELERATION

                if self.LOCAL_VELOCITY - WATER_DRAG >= 0 and self.LOCAL_ACCELERATION >= 0:
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
            if self.MAIN_MENU_OPEN:
                self.open_main_menu()
            elif self.GAME_OPEN:
                if self.SONAR_SCREEN:
                    self.sonar_screen_render()
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
                elif self.GAME_OPEN:
                    self.game_events(event)

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
                    if self.BALLAST < 100:
                        self.BALLAST += 0.5 * fps_d
                elif keys[pygame.K_DOWN]:
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

        ACTIVE_SONAR_RANGE = 300
        PASSIVE_SONAR_RANGE = 300
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

        for contact in list(self.ACTIVE_SONAR_CONTACTS):
            self.ACTIVE_SONAR_CONTACTS[contact][2] -= 0.016 * self.fps / self.current_fps
            if self.ACTIVE_SONAR_CONTACTS[contact][2] > 0:
                pygame.draw.circle(self.window, darken(self.ACTIVE_SONAR_CONTACTS[contact][2] + 1, '#00ff00'),
                                   (self.ACTIVE_SONAR_CONTACTS[contact][0],
                                    self.ACTIVE_SONAR_CONTACTS[contact][1]), 5)
            else:
                self.ACTIVE_SONAR_CONTACTS.pop(contact)

        if self.ACTIVE_SONAR:
            if self.ACTIVE_SONAR_PING_RADIUS >= 180:
                self.ACTIVE_SONAR_PING_RADIUS = 0
                self.ACTIVE_SONAR_PING_DELAY += 0.017 * self.fps / self.current_fps
            if self.ACTIVE_SONAR_PING_DELAY == 0:
                pygame.draw.circle(self.window, 'white', (200, 200), self.ACTIVE_SONAR_PING_RADIUS, width=1)
                self.ACTIVE_SONAR_PING_RADIUS += 1.5 * self.fps / self.current_fps
                # Make the coordinates relative:
                rel_x = self.ENEMY_POSITION[0] - self.LOCAL_POSITION[0]
                rel_y = self.ENEMY_POSITION[1] - self.LOCAL_POSITION[1]
                distance = math.sqrt(rel_x * rel_x + rel_y * rel_y)
                if self.ACTIVE_SONAR_PING_RADIUS < distance * 0.6 < self.ACTIVE_SONAR_PING_RADIUS + 5:
                    # Draw it on the sonar display
                    rel_x = rel_x * 0.6 + 200
                    rel_y = rel_y * 0.6 + 200
                    pygame.draw.circle(self.window, '#386e2c', (rel_x, rel_y), 5)
                    self.ACTIVE_SONAR_CONTACTS['Enemy'] = [rel_x, rel_y, 4]
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
            pygame.draw.circle(self.window, '#386e2c', (contact[0], 30 + contact[1]), 1)

        # Make the coordinates relative:
        rel_x = self.ENEMY_POSITION[0] - self.LOCAL_POSITION[0]
        rel_y = self.ENEMY_POSITION[1] - self.LOCAL_POSITION[1]
        distance = math.sqrt(rel_x * rel_x + rel_y * rel_y)
        if distance <= PASSIVE_SONAR_RANGE:
            # Draw it on the passive sonar display
            bearing = calculate_bearing(rel_x, rel_y, distance)

            # print(f"Angle: {angle} Local Angle: {local_position} "
            #       f"Bearing: {bearing}")
            if not self.PASSIVE_SONAR_FREEZE:
                if self.ENEMY_POSITION[3] < self.LOCAL_POSITION[4]:
                    rel_x = p1_sonar_start + (p1_sonar_end - p1_sonar_start) / 2 + bearing
                    rel_x -= (p1_sonar_start + (p1_sonar_end - p1_sonar_start) / 2)
                    zero = p1_sonar_start + (p1_sonar_end - p1_sonar_start) / 2
                    self.PASSIVE_SONAR_DISPLAY_CONTACTS.append([(zero + rel_x * scale) + random_int(-4, 4), 1, 'Enemy'])
                    # pygame.draw.circle(self.window, '#386e2c', (zero + rel_x*scale, 30), 5)
                else:
                    rel_x = p2_sonar_start + (p2_sonar_end - p2_sonar_start) / 2 + bearing
                    rel_x -= (p2_sonar_start + (p2_sonar_end - p2_sonar_start) / 2)
                    zero = p2_sonar_start + (p2_sonar_end - p2_sonar_start) / 2
                    self.PASSIVE_SONAR_DISPLAY_CONTACTS.append([(zero + rel_x * scale) + random_int(-4, 4), 1, 'Enemy'])

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
        contact_bearing = None
        contact_speed = None
        contact_depth = None
        contact_distance = None
        contact_heading = None
        if self.PASSIVE_SELECTED_CONTACT:
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
            else:
                contact_type = self.OBJECTS[self.PASSIVE_SELECTED_CONTACT[2]][1]
                contact_speed = self.OBJECTS[self.PASSIVE_SELECTED_CONTACT[2]][2]
                contact_depth = self.OBJECTS[self.PASSIVE_SELECTED_CONTACT[2]][0][3]
                rel_x = self.OBJECTS[self.PASSIVE_SELECTED_CONTACT[2]][0][0] - self.LOCAL_POSITION[0]
                rel_y = self.OBJECTS[self.PASSIVE_SELECTED_CONTACT[2]][0][1] - self.LOCAL_POSITION[1]
                contact_distance = math.sqrt(rel_x * rel_x + rel_y * rel_y)
                contact_heading = self.OBJECTS[self.PASSIVE_SELECTED_CONTACT[2]][0][2]
                contact_bearing = calculate_bearing(rel_x, rel_y, distance)
                if contact_bearing < 0:
                    contact_bearing += 360
        if contact_type:
            txtsurf = self.middle_font.render(f"{contact_type}", True, '#b6b6d1')
        else:
            txtsurf = self.middle_font.render("Select a contact...", True, '#b6b6d1')
        self.window.blit(txtsurf, (110, 450))
        txtsurf = self.middle_font.render(f"{contact_bearing}", True, '#b6b6d1')
        self.window.blit(txtsurf, (110, 480))
        txtsurf = self.middle_font.render(f"{contact_speed}", True, '#b6b6d1')
        self.window.blit(txtsurf, (110, 510))
        txtsurf = self.middle_font.render(f"{contact_depth}", True, '#b6b6d1')
        self.window.blit(txtsurf, (110, 540))
        txtsurf = self.middle_font.render(f"{contact_distance}", True, '#b6b6d1')
        self.window.blit(txtsurf, (110, 570))
        txtsurf = self.middle_font.render(f"{contact_heading} (azimuth)", True, '#b6b6d1')
        self.window.blit(txtsurf, (110, 600))
        if self.sonar_cursor_position:
            if self.PASSIVE_SELECTED_CONTACT:
                pygame.draw.line(self.window, '#00ad06', (self.size[0] // 2, self.sonar_cursor_position[1]),
                                 self.sonar_cursor_position)
                pygame.draw.line(self.window, '#00ad06', (self.sonar_cursor_position[0], 30),
                                 self.sonar_cursor_position)
                pygame.draw.line(self.window, '#00ad06', (self.size[0], self.sonar_cursor_position[1]),
                                 self.sonar_cursor_position)
                pygame.draw.line(self.window, '#00ad06', (self.sonar_cursor_position[0], self.size[1] - 30),
                                 self.sonar_cursor_position)
            else:
                pygame.draw.line(self.window, '#ad001d', (self.size[0] // 2, self.sonar_cursor_position[1]),
                                 self.sonar_cursor_position)
                pygame.draw.line(self.window, '#ad001d', (self.sonar_cursor_position[0], 30),
                                 self.sonar_cursor_position)
                pygame.draw.line(self.window, '#ad001d', (self.size[0], self.sonar_cursor_position[1]),
                                 self.sonar_cursor_position)
                pygame.draw.line(self.window, '#ad001d', (self.sonar_cursor_position[0], self.size[1] - 30),
                                 self.sonar_cursor_position)
        pygame.display.update()


pygame.init()
start = App()
start.on_execute()
