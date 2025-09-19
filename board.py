# board.py
class GameBoard:
    def __init__(self, width=10, height=10):
        self.width = width
        self.height = height
        # matrice : 0 = vide, 1 = mur, 2 = ingrédient, 3 = planche, 4 = assiette
        self.grid = [[0 for _ in range(width)] for _ in range(height)]

        # exemple : placer un ingrédient et une assiette
        self.grid[2][2] = 2  # ingrédient
        self.grid[4][4] = 4  # assiette

    def is_walkable(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height and self.grid[y][x] != 1

    def get_cell(self, x, y):
        return self.grid[y][x]

    def set_cell(self, x, y, value):
        self.grid[y][x] = value
