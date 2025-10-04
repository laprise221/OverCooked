import pygame


class Screen:

    def __init__(self):
        self.display = pygame.display.set_mode((625, 480))
        pygame.display.set_caption('OverCooked')
        self.clock = pygame.time.Clock()
        self.framerate = 60

    def update(self):
        pygame.display.flip()
        pygame.display.update()
        self.clock.tick(self.framerate)
        self.display.fill((0, 0, 0))

    def get_size(self):
        return self.display.get_size()

    def get_display(self):
        return self.display
