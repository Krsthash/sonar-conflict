import os
import pygame



class App:
    def __init__(self):
        self.fps = 60
        self.mapsurface = None
        self.running = True
        self.size = (1280, 720)
        self.moving = False
        self.MAP_OPEN = False

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

    def open_map(self):
        # Uncomment to reset map's position
        # self.map_rect = self.map.get_rect(topleft=self.window.get_rect().topleft)
        self.blitmap()

    def blitmap(self):
        self.mapsurface = pygame.transform.smoothscale(self.map, self.map_rect.size)
        self.window.fill(0)
        self.window.blit(self.mapsurface, self.map_rect)

    def on_cleanup(self):
        pygame.quit()

    def open_main_menu(self):
        self.window.fill("#021019")
        font = pygame.font.Font('freesansbold.ttf', 32)
        txtsurf = font.render("Sonar Conflict", True, "white")
        self.window.blit(txtsurf, (self.size[0] // 2 - txtsurf.get_width() // 2,
                                   self.size[1] // 4 - txtsurf.get_height() // 2))

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
                self.MAP_OPEN = False
                self.open_main_menu()
                print("Closing the map...")

        pygame.display.update()

    def main_menu_events(self, event):
        if event.type == pygame.QUIT:
            self.running = False

        pygame.display.update()

    def on_execute(self):
        self.open_main_menu()
        while self.running:
            for event in pygame.event.get():
                if self.MAP_OPEN:
                    self.check_map_events(event)
                else:
                    self.main_menu_events(event)
            self.clock.tick(self.fps)
        self.on_cleanup()

pygame.init()
start = App()
start.on_execute()
