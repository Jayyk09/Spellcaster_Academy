"""Main game entry point."""
import pygame
from entities.player import Player
from config.settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, SCALE

# Initialize pygame
pygame.init()

# Create scaled window
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Die Insel - Pygame")

clock = pygame.time.Clock()
running = True

# Create player at center of screen
player = Player(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)

# Create sprite group for rendering
all_sprites = pygame.sprite.Group()
all_sprites.add(player)

# Game loop
while running:
    dt = clock.tick(FPS) / 1000  # Delta time in seconds
    
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            player.handle_attack_input(event.key)
            if event.key == pygame.K_ESCAPE:
                running = False
    
    # Get continuous key state for movement
    keys = pygame.key.get_pressed()
    player.handle_input(keys)
    
    # Update
    player.update(dt)
    
    # Draw
    screen.fill((34, 45, 35))  # Dark green background
    
    # Draw all sprites
    all_sprites.draw(screen)
    
    # Debug: Draw attack hitbox
    hitbox = player.get_attack_hitbox()
    if hitbox:
        pygame.draw.rect(screen, (255, 0, 0), hitbox, 2)
    
    # Debug: Draw collision rect
    collision_rect = player.get_collision_rect()
    pygame.draw.rect(screen, (0, 255, 0), collision_rect, 1)
    
    # Debug: Draw health bar
    health_bar_width = 50
    health_bar_height = 5
    health_ratio = player.health / player.max_health
    health_bar_x = player.pos.x - health_bar_width / 2
    health_bar_y = player.pos.y - 30
    
    # Background (red)
    pygame.draw.rect(screen, (100, 0, 0), 
                     (health_bar_x, health_bar_y, health_bar_width, health_bar_height))
    # Health (green)
    pygame.draw.rect(screen, (0, 200, 0), 
                     (health_bar_x, health_bar_y, health_bar_width * health_ratio, health_bar_height))
    
    # Debug: Display state info
    font = pygame.font.Font(None, 24)
    state_text = font.render(f"State: {player.state} | Dir: {player.direction} | HP: {player.health}", True, (255, 255, 255))
    screen.blit(state_text, (10, 10))
    
    pygame.display.flip()

pygame.quit()
