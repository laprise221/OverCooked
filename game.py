import pygame
from board import GameBoard
from player import PlayerAI
from recipes import RecipeManager

pygame.init()

CELL_SIZE = 50
WIDTH, HEIGHT = 10, 10
WINDOW = pygame.display.set_mode((WIDTH * CELL_SIZE, HEIGHT * CELL_SIZE))
pygame.display.set_caption("Overcooked - Mini")

COLORS = {
    0: (200, 200, 200),   # sol vide
    1: (50, 50, 50),      # mur
    2: (255, 0, 0),       # tomate
    5: (0, 255, 0),       # salade
    6: (255, 255, 0),     # oignon
    10: (150, 75, 0),     # viande
    11: (255, 228, 181),  # pain
    4: (255, 255, 255),   # assiette (sortie)
    7: (139, 69, 19),     # planche
    8: (100, 100, 100),   # poêle
    9: (150, 150, 255),   # table assemblage
}

def draw(board, players, recipe_manager):
    for y in range(board.height):
        for x in range(board.width):
            cell = board.get_cell(x, y)
            pygame.draw.rect(WINDOW, COLORS.get(cell, (255, 255, 255)),
                             (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))

    for p in players:
        pygame.draw.rect(WINDOW, (0, 0, 150),
                         (p.x * CELL_SIZE, p.y * CELL_SIZE, CELL_SIZE, CELL_SIZE))

    font = pygame.font.SysFont(None, 30)
    score_text = font.render(f"Score: {recipe_manager.score}", True, (0, 0, 0))
    WINDOW.blit(score_text, (10, 10))

    pygame.display.update()

def main():
    clock = pygame.time.Clock()
    board = GameBoard()
    recipe_manager = RecipeManager()
    player = PlayerAI(5, 5)

    recipe_name = input("Quel plat souhaitez-vous préparer ? ").strip().lower()
    steps = recipe_manager.get_recipe(recipe_name)

    if not steps:
        print(f"❌ Recette '{recipe_name}' introuvable.")
        return

    player.start_recipe(recipe_name, steps, board)

    running = True
    while running:
        clock.tick(10)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        result = player.update(board)
        if result and result[0] == "deliver":
            delivered_items = result[1]
            recipe_name = result[2]
            recipe_manager.check_delivery(delivered_items, recipe_name)

        draw(board, [player], recipe_manager)

    pygame.quit()

if __name__ == "__main__":
    main()
