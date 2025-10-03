class GameBoard:
    # Codes des cases (constantes)
    EMPTY = 0
    WALL = 1
    TOMATE = 2
    OIGNON = 3
    SALADE = 4
    VIANDE = 5
    PAIN = 6
    PATE = 7
    PLANCHE = 8
    POELE = 9
    ASSEMBLAGE = 10
    SORTIE = 11
    FROMAGE = 12

    # mapping nom → code (utile pour extensions)
    NAME_TO_CODE = {
        "tomate": TOMATE,
        "oignon": OIGNON,
        "salade": SALADE,
        "viande": VIANDE,
        "pain": PAIN,
        "pate": PATE,
        "fromage": FROMAGE,
    }

    def __init__(self, width=10, height=10):
        self.width = width
        self.height = height
        self.grid = [[self.EMPTY for _ in range(width)] for _ in range(height)]

        # ➡️ Exemple de placement d’ingrédients (tu peux modifier)
        self.grid[0][0] = self.SALADE
        self.grid[0][1] = self.TOMATE
        self.grid[0][2] = self.OIGNON
        self.grid[0][3] = self.VIANDE
        self.grid[0][4] = self.PAIN
        self.grid[0][5] = self.PATE
        self.grid[0][6] = self.FROMAGE

        # ➡️ Outils
        self.grid[2][0] = self.POELE
        self.grid[4][0] = self.PLANCHE

        # ➡️ Assemblage et sortie
        self.grid[4][9] = self.ASSEMBLAGE
        self.grid[9][9] = self.SORTIE

    # --- Utilitaires ---
    def is_walkable(self, x, y):
        """Vérifie si la case est traversable (pas un mur)."""
        return 0 <= x < self.width and 0 <= y < self.height and self.grid[y][x] != self.WALL

    def get_cell(self, x, y):
        """Retourne la valeur de la case."""
        return self.grid[y][x]

    def set_cell(self, x, y, value):
        """Modifie la valeur d’une case."""
        self.grid[y][x] = value

    def remove_ingredient(self, x, y):
        """Enlève un ingrédient (remet la case à vide)."""
        if self.grid[y][x] in [
            self.SALADE, self.TOMATE, self.OIGNON,
            self.VIANDE, self.PAIN, self.PATE, self.FROMAGE
        ]:
            self.grid[y][x] = self.EMPTY

    def place_ingredient(self, x, y, ingredient_value):
        """Place un ingrédient si la case est vide."""
        if self.grid[y][x] == self.EMPTY and ingredient_value in [
            self.SALADE, self.TOMATE, self.OIGNON,
            self.VIANDE, self.PAIN, self.PATE, self.FROMAGE
        ]:
            self.grid[y][x] = ingredient_value

    def place_by_name(self, x, y, name: str):
        """Place un ingrédient via son nom (plus pratique)."""
        code = self.NAME_TO_CODE.get(name)
        if code is not None:
            self.grid[y][x] = code
