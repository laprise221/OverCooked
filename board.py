class GameBoard:
    def __init__(self, width=10, height=10):
        self.width = width
        self.height = height
        self.grid = [[0 for _ in range(width)] for _ in range(height)]

        # Ligne du haut (y = 0) — Ingrédients
        self.grid[0][0] = 5   # Salade
        self.grid[0][1] = 2   # Tomate
        self.grid[0][2] = 6   # Oignon
        self.grid[0][3] = 10  # Viande
        self.grid[0][4] = 11  # Pain

        # Colonne de gauche — Outils
        self.grid[2][0] = 8   # Poêle
        self.grid[4][0] = 7   # Planche à découper

        # Colonne de droite — Assemblage et Sortie
        self.grid[4][9] = 9   # Assemblage
        self.grid[9][9] = 4   # Assiette / Sortie

    def is_walkable(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height and self.grid[y][x] != 1

    def get_cell(self, x, y):
        return self.grid[y][x]

    def set_cell(self, x, y, value):
        self.grid[y][x] = value
