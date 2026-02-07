"""Main game entry point."""
import pygame
from entities.player import Player
from entities.enemy import Slime
from config.settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, PLAYER_ATTACK_DAMAGE

# Initialize pygame
pygame.init()

# Create scaled window
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Die Insel - Pygame")

clock = pygame.time.Clock()
running = True

# Create player at center of screen
player = Player(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)

# Create enemies
enemies = pygame.sprite.Group()
slime = Slime(600, 300)
slime.set_target(player)
enemies.add(slime)

# Create another slime
slime2 = Slime(200, 150)
slime2.set_target(player)
enemies.add(slime2)

# Create sprite group for rendering (ordered by y-position)
all_sprites = pygame.sprite.Group()
all_sprites.add(player)
all_sprites.add(slime)
all_sprites.add(slime2)

def check_combat():
    """Check for combat interactions."""
    # Check if player attack hits enemies
    attack_hitbox = player.get_attack_hitbox()
    if attack_hitbox:
        for enemy in enemies:
            if enemy.is_alive:
                enemy_hitbox = enemy.get_hitbox()
                if attack_hitbox.colliderect(enemy_hitbox):
                    enemy.take_damage(PLAYER_ATTACK_DAMAGE)

def draw_health_bar(surface, x, y, health, max_health, width=50, height=5):
    """Draw a health bar."""
    health_ratio = health / max_health
    # Background (red)
    pygame.draw.rect(surface, (100, 0, 0), (x - width/2, y, width, height))
    # Health (green)
    pygame.draw.rect(surface, (0, 200, 0), (x - width/2, y, width * health_ratio, height))

def y_sort_key(sprite):
    """Key function for Y-sorting sprites."""
    return sprite.pos.y

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
            # Debug: press R to respawn
            if event.key == pygame.K_r:
                player.respawn(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
            # Debug: press E to spawn new enemy
            if event.key == pygame.K_e:
                new_slime = Slime(player.pos.x + 100, player.pos.y)
                new_slime.set_target(player)
                enemies.add(new_slime)
                all_sprites.add(new_slime)
    
    # Get continuous key state for movement
    keys = pygame.key.get_pressed()
    player.handle_input(keys)
    
    # Update player
    player.update(dt)
    
    # Clamp player to screen
    player.pos.x = max(24, min(SCREEN_WIDTH - 24, player.pos.x))
    player.pos.y = max(24, min(SCREEN_HEIGHT - 24, player.pos.y))
    
    # Update enemies
    for enemy in enemies:
        enemy.update(dt)
        # Clamp enemy to screen
        enemy.pos.x = max(16, min(SCREEN_WIDTH - 16, enemy.pos.x))
        enemy.pos.y = max(16, min(SCREEN_HEIGHT - 16, enemy.pos.y))
    
    # Check combat
    check_combat()
    
    # Clean up dead enemies that finished death animation
    for enemy in list(enemies):
        if not enemy.is_alive and enemy.is_animation_finished():
            enemies.remove(enemy)
            all_sprites.remove(enemy)
    
    # Draw
    screen.fill((34, 45, 35))  # Dark green background
    
    # Y-sort and draw sprites
    sorted_sprites = sorted(all_sprites, key=y_sort_key)
    for sprite in sorted_sprites:
        screen.blit(sprite.image, sprite.rect)
    
    # Draw attack hitbox (debug)
    hitbox = player.get_attack_hitbox()
    if hitbox:
        pygame.draw.rect(screen, (255, 100, 100), hitbox, 2)
    
    # Draw health bars
    draw_health_bar(screen, player.pos.x, player.pos.y - 35, player.health, player.max_health)
    
    for enemy in enemies:
        if enemy.is_alive:
            draw_health_bar(screen, enemy.pos.x, enemy.pos.y - 25, enemy.health, enemy.max_health, width=30, height=4)
            # Draw detection radius (debug)
            # pygame.draw.circle(screen, (255, 255, 0), (int(enemy.pos.x), int(enemy.pos.y)), enemy.detection_radius, 1)
    
    # Debug info
    font = pygame.font.Font(None, 24)
    state_text = font.render(f"State: {player.state} | Dir: {player.direction} | HP: {player.health}", True, (255, 255, 255))
    screen.blit(state_text, (10, 10))
    
    controls_text = font.render("WASD/Arrows: Move | Space: Attack | R: Respawn | E: Spawn Enemy", True, (200, 200, 200))
    screen.blit(controls_text, (10, SCREEN_HEIGHT - 25))
    
    enemy_count = len([e for e in enemies if e.is_alive])
    enemy_text = font.render(f"Enemies: {enemy_count}", True, (255, 255, 255))
    screen.blit(enemy_text, (10, 35))
    
    pygame.display.flip()

pygame.quit()
