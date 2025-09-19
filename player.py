class PlayerAI:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.holding = None
        self.order = None
        self.path = []
        self.target = None
        self.ingredient = None
        self.ingredient_queue = []

    def enqueue_ingredients(self, ingredients):
        self.ingredient_queue.extend(ingredients)

    def set_order(self, order, board, ingredient=None):
        self.order = order
        self.ingredient = ingredient  # stocke l'ingrédient demandé

        if order == "fetch_ingredient":
            self.find_and_go_to_ingredient(board, ingredient)
        elif order == "deliver_item":
            self.find_and_go_to(board, 4)  # 4 = assiette

    def find_and_go_to_ingredient(self, board, ingredient):
        ingredient_codes = {
            "tomate": 2,
            "salade": 5,
            "oignon": 6,
        }

        target_code = ingredient_codes.get(ingredient)
        if target_code is None:
            print(f"Ingrédient inconnu : {ingredient}")
            return

        for y in range(board.height):
            for x in range(board.width):
                if board.get_cell(x, y) == target_code:
                    self.target = (x, y)
                    self.generate_path_to(x, y)
                    return
    def find_and_go_to(self, board, cell_value):
        for y in range(board.height):
            for x in range(board.width):
                if board.get_cell(x, y) == cell_value:
                    self.target = (x, y)
                    self.generate_path_to(x, y)
                    return


    def generate_path_to(self, target_x, target_y):
        self.path = []
        dx = 1 if target_x > self.x else -1
        for x in range(self.x, target_x, dx):
            self.path.append((x + dx, self.y))
        dy = 1 if target_y > self.y else -1
        for y in range(self.y, target_y, dy):
            self.path.append((target_x, y + dy))

    def update(self, board):
        if self.path:
            next_x, next_y = self.path[0]
            if board.is_walkable(next_x, next_y):
                self.x, self.y = next_x, next_y
                self.path.pop(0)
        elif self.order == "fetch_ingredient" and self.holding is None:
            cell = board.get_cell(self.x, self.y)
            ingredient_codes = {
                "tomate": 2,
                "salade": 5,
                "oignon": 6,
            }
            expected_code = ingredient_codes.get(self.ingredient)
            if cell == expected_code:
                self.holding = self.ingredient
                board.set_cell(self.x, self.y, 0)
                print(f"{self.ingredient} ramassé")
                self.set_order("deliver_item", board)
        elif self.order == "deliver_item" and self.holding:
            cell = board.get_cell(self.x, self.y)
            if cell == 4:
                item = self.holding
                self.holding = None
                self.order = None
                print(f"{item} livré")
                return ("deliver", item)

        # Si aucune commande, on envoie la suivante de la queue
        if self.order is None and self.ingredient_queue:
            next_ingredient = self.ingredient_queue.pop(0)
            self.set_order("fetch_ingredient", board, next_ingredient)

        return None
