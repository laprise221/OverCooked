import heapq
from kitchen import Kitchen
from objects import Ingredient, Dish
from recipes import parse_ingredient_requirement, get_ingredient_config

class Agent:
    """
    Agent autonome qui prépare les plats
    """

    def __init__(self, position, kitchen):
        self.position = list(position)  # case logique [x, y]
        self.pixel_pos = [position[0] * kitchen.cell_size,
                          position[1] * kitchen.cell_size]  # position en pixels
        self.kitchen = kitchen
        self.holding = None
        self.current_task = None
        self.task_queue = []
        self.assembled_ingredients = []
        self.current_action = "En attente"
        self.action_timer = 0
        self.speed = 50 # pixels par frame

    # ----------------------------------------------------------------------
    def _move_towards(self, target):
        tx, ty = target
        target_px = tx * self.kitchen.cell_size
        target_py = ty * self.kitchen.cell_size

        dx = target_px - self.pixel_pos[0]
        dy = target_py - self.pixel_pos[1]

        # Déterminer la direction pour changer l'image
        if abs(dx) > abs(dy):
            self.direction = "CD" if dx > 0 else "CG"
        else:
            self.direction = "CF" if dy > 0 else "CDR"

        # Déplacement pixel par pixel
        step_x = min(self.speed, abs(dx)) * (1 if dx > 0 else -1 if dx < 0 else 0)
        step_y = min(self.speed, abs(dy)) * (1 if dy > 0 else -1 if dy < 0 else 0)
        self.pixel_pos[0] += step_x
        self.pixel_pos[1] += step_y

        # Mettre à jour la position logique seulement si l'agent a atteint la cellule
        if abs(self.pixel_pos[0] - target_px) < 1 and abs(self.pixel_pos[1] - target_py) < 1:
            self.position = [tx, ty]
            self.pixel_pos = [target_px, target_py]

    # ----------------------------------------------------------------------
    def update(self):
        if self.action_timer > 0:
            self.action_timer -= 1
            return

        if not self.task_queue and not self.current_task:
            self.current_action = "Terminé!"
            return

        if not self.current_task and self.task_queue:
            self.current_task = self.task_queue.pop(0)

        if self.current_task:
            task_complete = self._execute_task()
            if task_complete:
                self.current_task = None
    # ----------------------------------------------------------------------
    def _execute_task(self):
        task_type = self.current_task['type']

        if task_type == 'pickup':
            return self._do_pickup(self.current_task['ingredient'])
        elif task_type == 'cut':
            return self._do_cut()
        elif task_type == 'cook':
            return self._do_cook()
        elif task_type == 'bring_to_assembly':
            return self._do_bring_to_assembly()
        elif task_type == 'deliver':
            return self._do_deliver(self.current_task['recipe_name'],
                                    self.current_task['required_ingredients'])
        return False

    # ----------------------------------------------------------------------
    def _do_pickup(self, ingredient_name):
        if self.holding:
            return True

        target_ingredient = next((ing for ing in self.kitchen.ingredients_available
                                  if ing.name == ingredient_name and ing.state == "cru"), None)
        if not target_ingredient:
            return True

        if self.position != list(target_ingredient.position):
            self._move_towards(target_ingredient.position)
            self.current_action = f"Va chercher {ingredient_name}"
            return False

        self.holding = Ingredient(ingredient_name, "cru")
        self.current_action = f"Porte {ingredient_name}"
        return True

    # ----------------------------------------------------------------------
    def _do_cut(self):
        if not self.holding:
            return True

        cutting_board = self.kitchen.get_available_tool('planche')
        if not cutting_board:
            self.current_action = "Attente planche"
            return False

        if self.position != list(cutting_board.position):
            self._move_towards(cutting_board.position)
            self.current_action = "Va vers planche"
            return False

        if cutting_board.use(self.holding):
            self.action_timer = 20
            self.holding = cutting_board.release()
            self.holding.state = "coupe"
            self.current_action = f"Découpe {self.holding.name}"
            return True
        return False

    # ----------------------------------------------------------------------
    def _do_cook(self):
        if not self.holding:
            return True

        stove = self.kitchen.get_available_tool('poele')
        if not stove:
            self.current_action = "Attente poêle"
            return False

        if self.position != list(stove.position):
            self._move_towards(stove.position)
            self.current_action = "Va vers poêle"
            return False

        if stove.use(self.holding):
            self.action_timer = 30
            self.holding = stove.release()
            self.holding.state = "cuit"
            self.current_action = f"Cuit {self.holding.name}"
            return True
        return False

    # ----------------------------------------------------------------------
    def _do_bring_to_assembly(self):
        if not self.holding:
            return True

        target_pos = (4, 4)
        if self.position != list(target_pos):
            self._move_towards(target_pos)
            self.current_action = "Va vers table"
            return False

        self.assembled_ingredients.append(self.holding)
        self.holding = None
        self.current_action = "Dépose ingrédient"
        return True

    # ----------------------------------------------------------------------
    def _do_deliver(self, recipe_name, required_ingredients):
        assembled_names = [ing.get_full_name() for ing in self.assembled_ingredients]
        if sorted(assembled_names) != sorted(required_ingredients):
            return True

        if not self.holding or not isinstance(self.holding, Dish):
            self.holding = Dish(recipe_name, self.assembled_ingredients)
            self.current_action = f"Assemble {recipe_name}"
            self.kitchen.spawn_dish_image(recipe_name, position=(4, 4))
            self.action_timer = 15
            return False

        target_pos = (2, 6)
        if self.position != list(target_pos):
            self._move_towards(target_pos)
            self.kitchen.move_dish_image(self.pixel_pos)
            self.current_action = "Va livrer le plat"
            return False

        self.holding = None
        self.assembled_ingredients = []
        self.current_action = f"Livré {recipe_name} !"
        self.kitchen.remove_dish_image()
        return True

    # ----------------------------------------------------------------------
    def set_recipe(self, recipe_name, recipe_data):
        self.assembled_ingredients = []
        self.task_queue = []

        for ingredient_req in recipe_data['ingredients']:
            base_name, required_state = parse_ingredient_requirement(ingredient_req)
            config = get_ingredient_config(base_name)
            tasks = []

            tasks.append({'type': 'pickup', 'ingredient': base_name, 'target_state': required_state})
            if required_state == 'coupe' and config['needs_cutting']:
                tasks.append({'type': 'cut', 'ingredient': base_name})
            elif required_state == 'cuit' and config['needs_cooking']:
                tasks.append({'type': 'cook', 'ingredient': base_name})

            tasks.append({'type': 'bring_to_assembly', 'ingredient': base_name})
            self.task_queue.extend(tasks)

        self.task_queue.append({
            'type': 'deliver',
            'recipe_name': recipe_name,
            'required_ingredients': recipe_data['ingredients']
        })

    # ----------------------------------------------------------------------
    def __repr__(self):
        return f"Agent(pos={self.position}, holding={self.holding})"
