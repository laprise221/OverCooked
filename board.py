# board.py
class GameBoard:
    def __init__(self, width=10, height=10):
        self.width = width
        self.height = height
        # 0 = vide, 1 = mur, 2 = tomate, 5 = salade, 6 = oignon, 4 = assiette
        self.grid = [[0 for _ in range(width)] for _ in range(height)]

        # 🍅 Tomate
        self.grid[2][2] = 2
        # 🥬 Salade
        self.grid[3][2] = 5
        # 🧅 Oignon
        self.grid[4][2] = 6

        # 🍽️ Assiette (sortie)
        self.grid[6][6] = 4

    def is_walkable(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height and self.grid[y][x] != 1

    def get_cell(self, x, y):
        return self.grid[y][x]

    def set_cell(self, x, y, value):
        self.grid[y][x] = value
