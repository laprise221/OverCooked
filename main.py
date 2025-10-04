import pygame
from game import main

pygame.init()

if __name__ == '__main__':
    game = main()
    game.run()
    screen = pygame.display.set_mode((625, 480))