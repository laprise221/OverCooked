class PlayerAI:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.holding = None
        self.order = None
        self.path = []
        self.target = None
        self.current_ingredient = None
        self.current_action = None
        self.recipe_name = ""
        self.recipe_steps = []
        self.current_step_index = 0
        self.processed_ingredients = []

    def set_order(self, order, board=None, ingredient=None):
        self.order = order
        if ingredient:
            self.current_ingredient = ingredient

        if board is None:
            # Si pas de board fourni, on ne peut pas avancer (sécurité)
            return

        if order == "fetch_ingredient":
            self.find_and_go_to_ingredient(board, ingredient)
        elif order == "cut_ingredient":
            self.find_and_go_to(board, 7)  # planche
        elif order == "cook_ingredient":
            self.find_and_go_to(board, 8)  # poêle
        elif order == "assemble":
            self.find_and_go_to(board, 9)  # table assemblage
        elif order == "deliver_plate":
            self.find_and_go_to(board, 4)  # sortie / assiette

    def find_and_go_to_ingredient(self, board, ingredient):
        codes = {
            "tomate": 2,
            "salade": 5,
            "oignon": 6,
            "viande": 10,
            "pain": 11
        }
        code = codes.get(ingredient)
        if code is None:
            print(f"Ingrédient inconnu : {ingredient}")
            return
        for y in range(board.height):
            for x in range(board.width):
                if board.get_cell(x, y) == code:
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
        # Avancer sur le chemin si possible
        if self.path:
            next_x, next_y = self.path[0]
            if board.is_walkable(next_x, next_y):
                self.x, self.y = next_x, next_y
                self.path.pop(0)
            return None

        cell = board.get_cell(self.x, self.y)

        if self.order == "fetch_ingredient":
            ingredient_codes = {
                "tomate": 2,
                "salade": 5,
                "oignon": 6,
                "viande": 10,
                "pain": 11
            }
            expected_code = ingredient_codes.get(self.current_ingredient)
            if expected_code and cell == expected_code:
                print(f"{self.current_ingredient} ramassé")
                self.holding = self.current_ingredient
                # On ne supprime pas l'ingrédient de la grille

                if self.current_action == "couper":
                    self.set_order("cut_ingredient", board)
                elif self.current_action == "cuire":
                    self.set_order("cook_ingredient", board)
                else:
                    self.processed_ingredients.append(self.holding)
                    self.holding = None
                    self.current_step_index += 1
                    self.process_next_step(board)
            return None

        elif self.order == "cut_ingredient" and cell == 7:
            print(f"{self.holding} coupé")
            self.processed_ingredients.append(f"{self.holding}_coupé")
            self.holding = None
            self.current_step_index += 1
            self.process_next_step(board)
            return None

        elif self.order == "cook_ingredient" and cell == 8:
            print(f"{self.holding} cuit")
            self.processed_ingredients.append(f"{self.holding}_cuit")
            self.holding = None
            self.current_step_index += 1
            self.process_next_step(board)
            return None
        
        elif self.order == "assemble":
            if cell == 9:  # Table assemblage
                print("Assemblage du plat")
                self.processed_ingredients = [ing + "_assemble" for ing in self.processed_ingredients]
                self.current_step_index = len(self.recipe_steps) + 1  # On dépasse la fin
                self.process_next_step(board)  # Cela doit lancer la livraison
            else:
                self.find_and_go_to(board, 9)
            return None


        elif self.order == "deliver_plate" and cell == 4:
            delivered = self.processed_ingredients
            self.processed_ingredients = []
            self.order = None
            self.recipe_steps = []
            print(f"📦 Plat livré : {delivered}")
            return ("deliver", delivered, self.recipe_name)

        return None

    def start_recipe(self, recipe_name, steps, board):
        self.recipe_name = recipe_name
        self.recipe_steps = steps
        self.current_step_index = 0
        self.processed_ingredients = []
        self.process_next_step(board)

    def process_next_step(self, board):
        if self.current_step_index >= len(self.recipe_steps) and self.order != "assemble" and self.order != "deliver_plate":
            # Recette terminée : passer à l'assemblage puis à la livraison
            if self.order != "assemble":
                self.set_order("assemble", board)
            else:
                self.set_order("deliver_plate", board)
            return

        if self.current_step_index >= len(self.recipe_steps) and self.order == "assemble":
            # Après assemblage, passer à la livraison
            self.set_order("deliver_plate", board)
            return

        if self.current_step_index < len(self.recipe_steps):
            step = self.recipe_steps[self.current_step_index]
            self.current_ingredient = step["ingredient"]
            self.current_action = step.get("action")
            self.set_order("fetch_ingredient", board, self.current_ingredient)

