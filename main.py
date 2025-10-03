import pygame
from game import Game

pygame.init()

if __name__ == '__main__':
    game = Game()
    game.run()
    screen = pygame.display.set_mode((625, 480))