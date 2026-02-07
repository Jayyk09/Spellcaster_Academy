import pygame
import os

class Player:
    def __init__(self, x, y, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.speed = 300
        
        # Load player image
        image_path = os.path.join('assets', 'sprites', 'Gemini_Generated_Image_6q1sja6q1sja6q1s-removebg-preview.png')
        try:
            self.image = pygame.image.load(image_path).convert_alpha()
            # Scale down the image to a reasonable size
            self.image = pygame.transform.scale(self.image, (64, 64))
        except pygame.error as e:
            print(f"Error loading image: {e}")
            # Create a fallback surface if image fails to load
            self.image = pygame.Surface((64, 64), pygame.SRCALPHA)
            pygame.draw.circle(self.image, (255, 0, 0), (32, 32), 32)
        
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.pos = pygame.Vector2(x, y)
        
        # Track active movement keys
        self.active_keys = set()
    
    def handle_keydown(self, key):
        """Call this when a key is pressed."""
        if key in (pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d):
            self.active_keys.add(key)
    
    def handle_keyup(self, key):
        """Call this when a key is released."""
        if key in self.active_keys:
            self.active_keys.discard(key)
    
    def update(self, dt):
        # Calculate movement based on active keys
        dx, dy = 0, 0
        
        if pygame.K_w in self.active_keys:
            dy -= 1
        if pygame.K_s in self.active_keys:
            dy += 1
        if pygame.K_a in self.active_keys:
            dx -= 1
        if pygame.K_d in self.active_keys:
            dx += 1
        
        # Normalize diagonal movement so speed is consistent
        if dx != 0 and dy != 0:
            dx *= 0.707  # 1/sqrt(2)
            dy *= 0.707
        
        # Apply movement
        self.pos.x += dx * self.speed * dt
        self.pos.y += dy * self.speed * dt
        
        # Keep player on screen
        self.pos.x = max(self.rect.width / 2, min(self.screen_width - self.rect.width / 2, self.pos.x))
        self.pos.y = max(self.rect.height / 2, min(self.screen_height - self.rect.height / 2, self.pos.y))
        
        self.rect.center = self.pos
    
    def draw(self, surface):
        surface.blit(self.image, self.rect)
