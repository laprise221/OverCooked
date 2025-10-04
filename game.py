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
    0: (200, 200, 200), 1: (50, 50, 50), 2: (255, 0, 0), 3: (255, 255, 0),
    4: (0, 255, 0), 5: (150, 75, 0), 6: (255, 228, 181), 7: (255, 160, 122),
    8: (139, 69, 19), 9: (100, 100, 100), 10: (150, 150, 255),
    11: (255, 255, 255), 12: (255, 192, 203)
}

def draw(board, players, recipe_manager, countdown=None):
    WINDOW.fill((200, 200, 200))
    for y in range(board.height):
        for x in range(board.width):
            cell = board.get_cell(x, y)
            pygame.draw.rect(WINDOW, COLORS.get(cell, (255, 255, 255)),
                             (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))

    for p in players:
        pygame.draw.rect(WINDOW, (0, 0, 150),
                         (p.x * CELL_SIZE, p.y * CELL_SIZE, CELL_SIZE, CELL_SIZE))
        if p.holding:
            font = pygame.font.SysFont(None, 20)
            text = font.render(p.holding, True, (0, 0, 0))
            WINDOW.blit(text, (p.x * CELL_SIZE + 2, p.y * CELL_SIZE + 2))

    font = pygame.font.SysFont(None, 30)
    score_text = font.render(f"Score: {recipe_manager.score}", True, (0, 0, 0))
    WINDOW.blit(score_text, (10, 10))

    instr_font = pygame.font.SysFont(None, 20)
    instructions = "1=burger 2=salade 3=sandwich 4=pizza q=quit"
    text_instr = instr_font.render(instructions, True, (0, 0, 0))
    WINDOW.blit(text_instr, (10, HEIGHT*CELL_SIZE - 25))

    if countdown is not None:
        font_count = pygame.font.SysFont(None, 40)
        text_count = font_count.render(f"⏳ {countdown}", True, (255, 0, 0))
        WINDOW.blit(text_count, (WIDTH*CELL_SIZE//2 - 20, HEIGHT*CELL_SIZE//2 - 20))

    pygame.display.update()

def main():
    clock = pygame.time.Clock()
    board = GameBoard()
    recipe_manager = RecipeManager()
    player = PlayerAI(5, 5)
    current_recipe = None
    preparing = False
    running = True

    countdown_active = False
    countdown_start_time = 0
    countdown_seconds = 5

    while running:
        dt = clock.tick(30)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    running = False
                elif not countdown_active:
                    if event.key == pygame.K_1:
                        current_recipe = "burger"
                    elif event.key == pygame.K_2:
                        current_recipe = "salade"
                    elif event.key == pygame.K_3:
                        current_recipe = "sandwich"
                    elif event.key == pygame.K_4:
                        current_recipe = "pizza"

                    if current_recipe:
                        steps = recipe_manager.get_recipe(current_recipe)
                        player.start_recipe(current_recipe, steps, board)
                        preparing = True

        if preparing:
            result = player.update(board)
            if result and result[0] == "deliver":
                recipe_manager.check_delivery(result[1], result[2])
                preparing = False
                countdown_active = True
                countdown_start_time = pygame.time.get_ticks()

                player.holding = None
                player.current_ingredient = None
                player.current_action = None
                player.recipe_name = ""
                player.recipe_steps = []
                player.current_step_index = 0
                player.processed_ingredients = []
                player.path = []
                current_recipe = None

        countdown = None
        if countdown_active:
            elapsed = (pygame.time.get_ticks() - countdown_start_time) / 1000
            remaining = countdown_seconds - int(elapsed)
            if remaining > 0:
                countdown = remaining
            else:
                countdown_active = False
                board.regenerate_ingredients()

        draw(board, [player], recipe_manager, countdown=countdown)

    pygame.quit()

if __name__ == "__main__":
    main()
