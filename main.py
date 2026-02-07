import pygame
from entities.player import Player

# pygame setup
pygame.init()
screen = pygame.display.set_mode((1280, 720))
clock = pygame.time.Clock()
running = True
dt = 0

# Create player
player = Player(screen.get_width() / 2, screen.get_height() / 2, screen.get_width(), screen.get_height())

while running:
    # poll for events
    # pygame.QUIT event means the user clicked X to close your window
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            player.handle_keydown(event.key)
        elif event.type == pygame.KEYUP:
            player.handle_keyup(event.key)

    # fill the screen with a color to wipe away anything from last frame
    screen.fill("purple")

    # Update and draw player
    player.update(dt)
    player.draw(screen)

    # flip() the display to put your work on screen
    pygame.display.flip()

    # limits FPS to 60
    # dt is delta time in seconds since last frame, used for framerate-
    # independent physics.
    dt = clock.tick(60) / 1000

pygame.quit()
