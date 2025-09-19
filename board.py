class GameBoard:
    # Constantes pour les types de cases
    EMPTY = 0
    WALL = 1
    TOMATE = 2
    OIGNON = 3
    SALADE = 4
    VIANDE = 5
    PAIN = 6
    PATE = 7
    PLANCH_COUPE = 8
    POELE = 9
    ASSEMBLAGE = 10
    SORTIE = 11
    FROMAGE = 12

    def __init__(self, width=10, height=10):
        self.width = width
        self.height = height
        self.grid = [[self.EMPTY for _ in range(width)] for _ in range(height)]

        # Ligne du haut (y = 0) — Ingrédients
        self.grid[0][0] = self.SALADE
        self.grid[0][1] = self.TOMATE
        self.grid[0][2] = self.OIGNON
        self.grid[0][3] = self.VIANDE
        self.grid[0][4] = self.PAIN
        self.grid[0][5] = self.PATE
        self.grid[0][6] = self.FROMAGE

        # Colonne de gauche — Outils
        self.grid[2][0] = self.POELE
        self.grid[4][0] = self.PLANCH_COUPE

        # Colonne de droite — Assemblage et Sortie
        self.grid[4][9] = self.ASSEMBLAGE
        self.grid[9][9] = self.SORTIE

    def is_walkable(self, x, y):
        """Vérifie si la case est traversable (pas un mur)"""
        return 0 <= x < self.width and 0 <= y < self.height and self.grid[y][x] != self.WALL

    def get_cell(self, x, y):
        """Retourne la valeur de la case"""
        return self.grid[y][x]

    def set_cell(self, x, y, value):
        """Modifie la valeur de la case"""
        self.grid[y][x] = value

    def remove_ingredient(self, x, y):
        """Enlève un ingrédient ou objet de la case"""
        if self.grid[y][x] in [self.SALADE, self.TOMATE, self.OIGNON,
                               self.VIANDE, self.PAIN, self.PATE, self.FROMAGE]:
            self.grid[y][x] = self.EMPTY

    def place_ingredient(self, x, y, ingredient_value):
        """Place un ingrédient sur une case vide"""
        if self.grid[y][x] == self.EMPTY and ingredient_value in [
            self.SALADE, self.TOMATE, self.OIGNON,
            self.VIANDE, self.PAIN, self.PATE, self.FROMAGE
        ]:
            self.grid[y][x] = ingredient_value
