# game.py
import pygame
from board import GameBoard
from player import Player
from recipes import RecipeManager

pygame.init()

CELL_SIZE = 50
WIDTH, HEIGHT = 10, 10
WINDOW = pygame.display.set_mode((WIDTH * CELL_SIZE, HEIGHT * CELL_SIZE))
pygame.display.set_caption("Overcooked - Mini")

COLORS = {
    0: (200, 200, 200),
    1: (50, 50, 50),
    2: (0, 200, 0),
    4: (0, 0, 200),
}

def draw(board, players, recipe_manager):
    for y in range(board.height):
        for x in range(board.width):
            cell = board.get_cell(x, y)
            pygame.draw.rect(WINDOW, COLORS.get(cell, (255, 255, 255)),
                             (x*CELL_SIZE, y*CELL_SIZE, CELL_SIZE, CELL_SIZE))

    for i, p in enumerate(players):
        color = (200, 0, 0) if i == 0 else (0, 200, 200)
        pygame.draw.rect(WINDOW, color,
                         (p.x*CELL_SIZE, p.y*CELL_SIZE, CELL_SIZE, CELL_SIZE))

    font = pygame.font.SysFont(None, 30)
    score_text = font.render(f"Score: {recipe_manager.score}", True, (0, 0, 0))
    WINDOW.blit(score_text, (10, 10))

    pygame.display.update()

def main():
    clock = pygame.time.Clock()
    board = GameBoard()
    recipe_manager = RecipeManager()

    player1 = Player(0, 0, {"up": pygame.K_z, "down": pygame.K_s,
                            "left": pygame.K_q, "right": pygame.K_d,
                            "action": pygame.K_e})
    player2 = Player(9, 9, {"up": pygame.K_UP, "down": pygame.K_DOWN,
                            "left": pygame.K_LEFT, "right": pygame.K_RIGHT,
                            "action": pygame.K_m})

    players = [player1, player2]

    running = True
    while running:
        clock.tick(10)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        for p in players:
            if keys[p.controls["up"]]: p.move(0, -1, board)
            if keys[p.controls["down"]]: p.move(0, 1, board)
            if keys[p.controls["left"]]: p.move(-1, 0, board)
            if keys[p.controls["right"]]: p.move(1, 0, board)
            if keys[p.controls["action"]]:
                result = p.interact(board)
                if result and result[0] == "deliver":
                    recipe_manager.check_delivery(result[1])

        draw(board, players, recipe_manager)

    pygame.quit()

if __name__ == "__main__":
    main()
