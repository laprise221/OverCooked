import pygame
from tool import Tool
import random


class Entity(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.spritesheet = pygame.image.load('assets/player/arenspace-playerupscaled.png').convert_alpha()

        # Dictionnaire d’animations (3 frames pour chaque direction)
        self.animations = {
            "down": [Tool.split_image(self.spritesheet, 24, 56, 24, 28),
                     Tool.split_image(self.spritesheet, 133, 56, 24, 28),
                     Tool.split_image(self.spritesheet, 133, 165, 24, 28)],

            "up": [Tool.split_image(self.spritesheet, 24, 0, 24, 28),
                   Tool.split_image(self.spritesheet, 133, 0, 24, 28),
                   Tool.split_image(self.spritesheet, 133, 109, 24, 28)],

            "left": [Tool.split_image(self.spritesheet, 0, 28, 24, 28),
                     Tool.split_image(self.spritesheet, 109, 28, 24, 28),
                     Tool.split_image(self.spritesheet, 109, 137, 24, 28)],

            "right": [Tool.split_image(self.spritesheet, 48, 28, 24, 28),
                      Tool.split_image(self.spritesheet, 157, 28, 24, 28),
                      Tool.split_image(self.spritesheet, 157, 137, 24, 28)],

            # Exemple diagonales (à adapter selon ton spritesheet)
            "down_left": [Tool.split_image(self.spritesheet, 0, 56, 24, 28),
                          Tool.split_image(self.spritesheet, 109, 56, 24, 28),
                          Tool.split_image(self.spritesheet, 109, 165, 24, 28)],

            "down_right": [Tool.split_image(self.spritesheet, 48, 56, 24, 28),
                           Tool.split_image(self.spritesheet, 157, 56, 24, 28),
                           Tool.split_image(self.spritesheet, 157, 165, 24, 28)],

            "up_left": [Tool.split_image(self.spritesheet, 0, 0, 24, 28),
                        Tool.split_image(self.spritesheet, 109, 0, 24, 28),
                        Tool.split_image(self.spritesheet, 109, 109, 24, 28)],

            "up_right": [Tool.split_image(self.spritesheet, 48, 0, 24, 28),
                         Tool.split_image(self.spritesheet, 157, 109, 24, 28),
                         Tool.split_image(self.spritesheet, 157, 109, 24, 28)]
        }

        self.position = pygame.Vector2(200, 200)
        self.rect: pygame.Rect = self.animations["down"][0].get_rect(topleft=(200, 200))

        # Animation
        self.image = self.animations["down"][0]
        self.frame_index = 0
        self.animation_speed = 0.15
        self.current_animation = "down"

        # Déplacement automatique
        self.direction = pygame.Vector2(0, 0)
        self.timer = 0
        self.speed = 2

    def update(self):
        # Déplacement
        self.position += self.direction * self.speed

        # Empêche de sortir de l'écran (625x480)
        screen_width, screen_height = 285, 185
        if self.position.x < 0:
            self.position.x = 0
        if self.position.y < 50:
            self.position.y = 50
        if self.position.x + self.rect.width > screen_width:
            self.position.x = screen_width - self.rect.width
        if self.position.y + self.rect.height > screen_height:
            self.position.y = screen_height - self.rect.height

        # Mise à jour du rect
        self.rect.topleft = self.position

        # Changer d’animation selon la direction
        self.set_animation()

        # Mettre à jour l’image courante
        self.frame_index += self.animation_speed
        if self.frame_index >= len(self.animations[self.current_animation]):
            self.frame_index = 0
        self.image = self.animations[self.current_animation][int(self.frame_index)]

        # Timer pour changer de direction (bot)
        self.timer += 1
        if self.timer > 60:
            self.timer = 0
            self.choose_random_direction()


    def set_animation(self):
        if self.direction == (0, 0):
            return  # Pas de changement si le joueur ne bouge pas

        dx, dy = self.direction.x, self.direction.y

        if dx > 0 and dy == 0:
            self.current_animation = "right"
        elif dx < 0 and dy == 0:
            self.current_animation = "left"
        elif dy > 0 and dx == 0:
            self.current_animation = "down"
        elif dy < 0 and dx == 0:
            self.current_animation = "up"
        elif dx > 0 and dy > 0:
            self.current_animation = "down_right"
        elif dx < 0 and dy > 0:
            self.current_animation = "down_left"
        elif dx > 0 and dy < 0:
            self.current_animation = "up_right"
        elif dx < 0 and dy < 0:
            self.current_animation = "up_left"

    def choose_random_direction(self):
        directions = [
            pygame.Vector2(-1, 0),
            pygame.Vector2(1, 0),
            pygame.Vector2(0, -1),
            pygame.Vector2(0, 1),
            pygame.Vector2(-1, -1),
            pygame.Vector2(1, -1),
            pygame.Vector2(-1, 1),
            pygame.Vector2(1, 1),
            pygame.Vector2(0, 0)  # ne bouge pas
        ]
        self.direction = random.choice(directions)
