import os
import pygame
import math


class App:
    def __init__(self):
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
        self.mapsurface = None
        self.running = True
        self.size = (1280, 720)
        self.moving = False
        self.MAP_OPEN = False
        self.MAIN_MENU_OPEN = True
        self.JOIN_GAME_OPEN = False
        self.GAME_OPEN = False
        self.GAME_INIT = False

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
        self.window.blit(txtsurf, (self.join_game_rect.left+(
                (self.join_game_rect.right-self.join_game_rect.left)-txtsurf.get_width())//2,
                                   self.join_game_rect.top+(
                (self.join_game_rect.bottom-self.join_game_rect.top)-txtsurf.get_height())//2,
                                   self.join_game_rect.right-(
                (self.join_game_rect.bottom-self.join_game_rect.top)-txtsurf.get_height())//2,
                                   self.join_game_rect.bottom-(
                (self.join_game_rect.bottom-self.join_game_rect.top)-txtsurf.get_height())//2))
        self.host_game_rect = pygame.Rect(self.size[0] // 2 - width // 2, self.size[1] // 2.3 - height // 2, width,
                                          height)
        pygame.draw.rect(self.window, '#b6b6d1', self.host_game_rect, width=2)
        txtsurf = font.render("Host a game", True, "#b6b6d1")
        self.window.blit(txtsurf, (self.host_game_rect.left + (
                (self.host_game_rect.right - self.host_game_rect.left) - txtsurf.get_width()) // 2,
                                   self.host_game_rect.top + (
                (self.host_game_rect.bottom - self.host_game_rect.top) - txtsurf.get_height()) // 2,
                                   self.host_game_rect.right - (
                (self.host_game_rect.bottom - self.host_game_rect.top) - txtsurf.get_height()) // 2,
                                   self.host_game_rect.bottom - (
                (self.host_game_rect.bottom - self.host_game_rect.top) - txtsurf.get_height()) // 2))
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

        elif event.type == pygame.MOUSEBUTTONUP:
            self.moving = False

        elif event.type == pygame.MOUSEMOTION and self.moving:
            if self.map_rect.left + event.rel[0] > 0 or self.map_rect.right + event.rel[0] < \
                    1306 or self.map_rect.top + event.rel[1] > 0 or self.map_rect.bottom + event.rel[1] < self.size[1]:
                return
            self.map_rect.move_ip(event.rel)

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
        if event.type == pygame.QUIT:
            self.running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.join_game_rect.collidepoint(pygame.mouse.get_pos()):
                self.clear_scene()
                self.GAME_OPEN = True
                self.GAME_INIT = True
                self.game_init(0)

        if self.join_game_rect.collidepoint(pygame.mouse.get_pos()):
            pygame.draw.rect(self.window, 'white', self.join_game_rect, width=2)
            font = pygame.font.Font('freesansbold.ttf', 28)
            txtsurf = font.render("Join a game", True, "white")
            self.window.blit(txtsurf, (self.join_game_rect.left + (
                    (self.join_game_rect.right - self.join_game_rect.left) - txtsurf.get_width()) // 2,
                                       self.join_game_rect.top + (
                    (self.join_game_rect.bottom - self.join_game_rect.top) - txtsurf.get_height()) // 2,
                                       self.join_game_rect.right - (
                    (self.join_game_rect.bottom - self.join_game_rect.top) - txtsurf.get_height()) // 2,
                                       self.join_game_rect.bottom - (
                    (self.join_game_rect.bottom - self.join_game_rect.top) - txtsurf.get_height()) // 2))
        elif self.host_game_rect.collidepoint(pygame.mouse.get_pos()):
            pygame.draw.rect(self.window, 'white', self.host_game_rect, width=2)
            font = pygame.font.Font('freesansbold.ttf', 28)
            txtsurf = font.render("Host a game", True, "white")
            self.window.blit(txtsurf, (self.host_game_rect.left + (
                    (self.host_game_rect.right - self.host_game_rect.left) - txtsurf.get_width()) // 2,
                                       self.host_game_rect.top + (
                    (self.host_game_rect.bottom - self.host_game_rect.top) - txtsurf.get_height()) // 2,
                                       self.host_game_rect.right - (
                    (self.host_game_rect.bottom - self.host_game_rect.top) - txtsurf.get_height()) // 2,
                                       self.host_game_rect.bottom - (
                    (self.host_game_rect.bottom - self.host_game_rect.top) - txtsurf.get_height()) // 2))
        elif self.quit_rect.collidepoint(pygame.mouse.get_pos()):
            pygame.draw.rect(self.window, 'white', self.quit_rect, width=2)
            font = pygame.font.Font('freesansbold.ttf', 28)
            txtsurf = font.render("Quit", True, "white")
            self.window.blit(txtsurf, (self.quit_rect.left + (
                    (self.quit_rect.right - self.quit_rect.left) - txtsurf.get_width()) // 2,
                                       self.quit_rect.top + (
                    (self.quit_rect.bottom - self.quit_rect.top) - txtsurf.get_height()) // 2,
                                       self.quit_rect.right - (
                    (self.quit_rect.bottom - self.quit_rect.top) - txtsurf.get_height()) // 2,
                                       self.quit_rect.bottom - (
                    (self.quit_rect.bottom - self.quit_rect.top) - txtsurf.get_height()) // 2))
        pygame.display.update()

    def game_init(self, player_id):
        self.G_SPAWN_POSITIONS = [(400, 100, 150), (400, 400, 0)]
        # Y, X, AZIMUTH, PITCH_ANGLE
        self.LOCAL_POSITION = [self.G_SPAWN_POSITIONS[player_id][0], self.G_SPAWN_POSITIONS[player_id][1],
                               self.G_SPAWN_POSITIONS[player_id][2], 0]
        if player_id:
            self.ENEMY_POSITION = self.G_SPAWN_POSITIONS[0]
        else:
            self.ENEMY_POSITION = self.G_SPAWN_POSITIONS[1]

    def start_game(self):
        self.window.fill('black')

    def game_events(self, event):
        if event.type == pygame.QUIT:
            self.running = False

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

        pygame.display.update()

    def on_execute(self):
        WATER_DRAG = 0.0006
        self.open_main_menu()
        while self.running:
            # Scene checks
            if self.GAME_INIT:
                # Movement calculations
                if self.GEAR == 1:
                    ratio = 1.2 - self.LOCAL_VELOCITY / 0.05
                    self.LOCAL_ACCELERATION = 0.0008 * ratio
                elif self.GEAR == 2:
                    ratio = 1 - self.LOCAL_VELOCITY / 0.12
                    self.LOCAL_ACCELERATION = 0.0014 * ratio
                elif self.GEAR == 3:
                    ratio = 1 - self.LOCAL_VELOCITY / 0.15
                    self.LOCAL_ACCELERATION = 0.0016 * ratio
                elif self.GEAR == 0:
                    self.LOCAL_ACCELERATION = 0
                elif self.GEAR == -1:
                    ratio = 1.2 + self.LOCAL_VELOCITY / 0.05
                    self.LOCAL_ACCELERATION = -0.0008 * ratio
                elif self.GEAR == -2:
                    ratio = 1 + self.LOCAL_VELOCITY / 0.12
                    self.LOCAL_ACCELERATION = -0.0014 * ratio
                elif self.GEAR == -3:
                    ratio = 1 + self.LOCAL_VELOCITY / 0.15
                    self.LOCAL_ACCELERATION = -0.0016 * ratio

                self.LOCAL_VELOCITY += self.LOCAL_ACCELERATION

                if self.LOCAL_VELOCITY - WATER_DRAG >= 0 and self.LOCAL_ACCELERATION >= 0:
                    self.LOCAL_VELOCITY -= WATER_DRAG
                elif self.LOCAL_VELOCITY + WATER_DRAG <= 0:
                    self.LOCAL_VELOCITY += WATER_DRAG
                else:
                    self.LOCAL_VELOCITY = 0

                print(f"Acceleration: {self.LOCAL_ACCELERATION} Velocity: {self.LOCAL_VELOCITY}")

                self.LOCAL_POSITION[0] += self.LOCAL_VELOCITY * math.cos(math.radians(self.LOCAL_POSITION[2] - 90))
                self.LOCAL_POSITION[1] += self.LOCAL_VELOCITY * math.sin(math.radians(self.LOCAL_POSITION[2] - 90))
            if self.MAIN_MENU_OPEN:
                self.open_main_menu()
            elif self.GAME_OPEN:
                self.start_game()
            elif self.MAP_OPEN:
                self.blitmap()

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
                    turn_rate = 0.5 * (1 - (self.LOCAL_VELOCITY / 0.3))
                    self.LOCAL_POSITION[2] -= turn_rate
                elif keys[pygame.K_d]:
                    turn_rate = 0.5 * (1 - (self.LOCAL_VELOCITY / 0.3))
                    self.LOCAL_POSITION[2] += turn_rate

            self.clock.tick(self.fps)

        self.on_cleanup()


pygame.init()
start = App()
start.on_execute()
