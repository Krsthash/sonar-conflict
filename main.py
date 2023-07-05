# Example file showing a basic pygame "game loop"
import pygame

FPS = 60
WIDTH, HEIGHT = 1280, 720

# pygame setup
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill("purple")

   

    pygame.display.flip()

    clock.tick(FPS)

pygame.quit()