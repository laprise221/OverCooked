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
    2: (255, 0, 0),       # tomate - rouge
    5: (0, 255, 0),       # salade - vert
    6: (255, 255, 0),     # oignon - jaune
    4: (255, 255, 255),       # assiette - blanc
}


def draw(board, players, recipe_manager):
    for y in range(board.height):
        for x in range(board.width):
            cell = board.get_cell(x, y)
            pygame.draw.rect(WINDOW, COLORS.get(cell, (255, 255, 255)),
                             (x*CELL_SIZE, y*CELL_SIZE, CELL_SIZE, CELL_SIZE))

    for i, p in enumerate(players):
        color = (0, 0, 150)  # joueur IA en bleu foncé

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
    player = PlayerAI(0, 0)

    # 🟢 Demande les ingrédients à l'utilisateur au démarrage
    ingredients = input("Entrez les ingrédients à livrer (ex: salade tomate oignon) : ").split()
    player.enqueue_ingredients(ingredients)

    running = True
    while running:
        clock.tick(10)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        result = player.update(board)
        if result and result[0] == "deliver":
            recipe_manager.check_delivery(result[1])

        draw(board, [player], recipe_manager)

    pygame.quit()

if __name__ == "__main__":
    main()
