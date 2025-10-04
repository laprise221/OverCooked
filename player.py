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

    INGREDIENT_CODES = {
        "tomate": 2,
        "salade": 4,
        "oignon": 3,
        "viande": 5,
        "pain": 6,
        "pate": 7,
        "fromage": 12
    }

    def set_order(self, order, board=None, ingredient=None):
        self.order = order
        if ingredient:
            self.current_ingredient = ingredient

        if board is None:
            return

        if order == "fetch_ingredient":
            self.find_and_go_to_ingredient(board, ingredient)
        elif order == "cut_ingredient":
            self.find_and_go_to(board, 8)
        elif order == "cook_ingredient":
            self.find_and_go_to(board, 9)
        elif order == "assemble":
            self.find_and_go_to(board, 10)
        elif order == "deliver_plate":
            self.find_and_go_to(board, 11)

    def find_and_go_to_ingredient(self, board, ingredient):
        code = self.INGREDIENT_CODES.get(ingredient)
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
        step_x = 1 if target_x > self.x else -1
        for x in range(self.x, target_x, step_x):
            self.path.append((x + step_x, self.y))
        step_y = 1 if target_y > self.y else -1
        for y in range(self.y, target_y, step_y):
            self.path.append((target_x, y + step_y))

    def update(self, board):
        if self.path:
            next_x, next_y = self.path[0]
            if board.is_walkable(next_x, next_y):
                self.x, self.y = next_x, next_y
                self.path.pop(0)
            return None

        cell = board.get_cell(self.x, self.y)

        if self.order == "fetch_ingredient":
            expected_code = self.INGREDIENT_CODES.get(self.current_ingredient)
            if expected_code and cell == expected_code:
                self.holding = self.current_ingredient
                board.remove_ingredient(self.x, self.y)

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

        elif self.order == "cut_ingredient" and cell == 8:
            self.processed_ingredients.append(f"{self.holding}_coupé")
            self.holding = None
            self.current_step_index += 1
            self.process_next_step(board)
            return None

        elif self.order == "cook_ingredient" and cell == 9:
            self.processed_ingredients.append(f"{self.holding}_cuit")
            self.holding = None
            self.current_step_index += 1
            self.process_next_step(board)
            return None

        elif self.order == "assemble" and cell == 10:
            self.current_step_index = len(self.recipe_steps)
            self.process_next_step(board)
            return None

        elif self.order == "deliver_plate" and cell == 11:
            delivered = self.processed_ingredients
            self.processed_ingredients = []
            self.order = None
            self.recipe_steps = []
            return ("deliver", delivered, self.recipe_name)

        return None

    def start_recipe(self, recipe_name, steps, board):
        self.recipe_name = recipe_name
        self.recipe_steps = steps
        self.current_step_index = 0
        self.processed_ingredients = []
        self.process_next_step(board)

    def process_next_step(self, board):
        if self.current_step_index >= len(self.recipe_steps):
            if self.order != "assemble":
                self.set_order("assemble", board)
            else:
                self.set_order("deliver_plate", board)
            return

        step = self.recipe_steps[self.current_step_index]
        self.current_ingredient = step["ingredient"]
        self.current_action = step.get("action")
        self.set_order("fetch_ingredient", board, self.current_ingredient)
