"""
agent.py
Définit le comportement de l'agent autonome avec recherche de chemin A*
"""

import heapq
from objects import Ingredient, Dish
from recipes import parse_ingredient_requirement, get_ingredient_config

class Agent:
    """
    Agent autonome qui prépare les plats
    """
    def __init__(self, position, kitchen):
        self.position = list(position)  # [x, y]
        self.kitchen = kitchen
        self.holding = None  # Objet actuellement porté
        self.current_task = None  # Tâche en cours
        self.task_queue = []  # File de tâches à accomplir
        self.assembled_ingredients = []  # Ingrédients pour le plat en cours
        self.current_action = "En attente"
        self.action_timer = 0

    # ----------------------------------------------------------------------
    def set_recipe(self, recipe_name, recipe_data):
        """
        Configure une nouvelle recette à préparer
        """
        print(f"\n🍳 Nouvelle commande: {recipe_name}")
        print(f"Ingrédients requis: {recipe_data['ingredients']}")

        self.assembled_ingredients = []
        self.task_queue = []

        for ingredient_req in recipe_data['ingredients']:
            base_name, required_state = parse_ingredient_requirement(ingredient_req)
            config = get_ingredient_config(base_name)
            tasks = []

            # Aller chercher l'ingrédient
            tasks.append({'type': 'pickup', 'ingredient': base_name, 'target_state': required_state})

            # Traiter l'ingrédient si nécessaire
            if required_state == 'coupe' and config['needs_cutting']:
                tasks.append({'type': 'cut', 'ingredient': base_name})
            elif required_state == 'cuit' and config['needs_cooking']:
                tasks.append({'type': 'cook', 'ingredient': base_name})

            # Apporter à la table d'assemblage
            tasks.append({'type': 'bring_to_assembly', 'ingredient': base_name})
            self.task_queue.extend(tasks)

        # Tâche finale: déposer le plat
        self.task_queue.append({
            'type': 'deliver',
            'recipe_name': recipe_name,
            'required_ingredients': recipe_data['ingredients']
        })

        print(f"📋 {len(self.task_queue)} tâches planifiées")

    # ----------------------------------------------------------------------
    def update(self):
        """
        Met à jour l'état de l'agent (appelé à chaque frame)
        """
        if self.action_timer > 0:
            self.action_timer -= 1
            if self.action_timer <= 0:
                print("✅ Action terminée !")
            return

        if not self.task_queue and not self.current_task:
            self.current_action = "Terminé!"
            return

        if not self.current_task and self.task_queue:
            self.current_task = self.task_queue.pop(0)
            print(f"\n➡️ Nouvelle tâche: {self.current_task['type']}")

        if self.current_task:
            task_complete = self._execute_task()
            if task_complete:
                self.current_task = None

    # ----------------------------------------------------------------------
    def _execute_task(self):
        task = self.current_task
        task_type = task['type']

        if task_type == 'pickup':
            return self._do_pickup(task['ingredient'])
        elif task_type == 'cut':
            return self._do_cut()
        elif task_type == 'cook':
            return self._do_cook()
        elif task_type == 'bring_to_assembly':
            return self._do_bring_to_assembly()
        elif task_type == 'deliver':
            return self._do_deliver(task['recipe_name'], task['required_ingredients'])
        return False

    # ----------------------------------------------------------------------
    def _do_pickup(self, ingredient_name):
        if self.holding:
            return True

        target_ingredient = next((ing for ing in self.kitchen.ingredients_available
                                  if ing.name == ingredient_name and ing.state == "cru"), None)
        if not target_ingredient:
            print(f"❌ Ingrédient {ingredient_name} non trouvé!")
            return True

        if self.position != list(target_ingredient.position):
            self._move_towards(target_ingredient.position)
            self.current_action = f"Va chercher {ingredient_name}"
            return False

        print(f"✅ Ramassé: {ingredient_name}")
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
            print(f"❌ Ingrédients manquants!")
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
            self.kitchen.move_dish_image(self.position)
            self.current_action = "Va livrer le plat"
            return False

        self.holding = None
        self.assembled_ingredients = []
        self.current_action = f"Livré {recipe_name} !"
        self.kitchen.remove_dish_image()
        return True

    # ----------------------------------------------------------------------
    def _move_towards(self, target):
        """
        Déplace l'agent d'une case vers la cible en évitant les obstacles (A*).
        """
        tx, ty = target
        cx, cy = self.position
        if (cx, cy) == (tx, ty):
            return

        def heuristic(a, b):
            return abs(a[0]-b[0]) + abs(a[1]-b[1])

        open_set = []
        heapq.heappush(open_set, (heuristic((cx, cy), target), 0, (cx, cy)))
        came_from = {}
        g_score = {(cx, cy): 0}

        while open_set:
            _, cost, current = heapq.heappop(open_set)
            if current == target:
                break

            x, y = current
            for dx, dy in [(1,0), (-1,0), (0,1), (0,-1)]:
                nx, ny = x+dx, y+dy
                neighbor = (nx, ny)
                if not self.kitchen.is_walkable(neighbor):
                    continue
                tentative_g = g_score[current]+1
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score = tentative_g + heuristic(neighbor, target)
                    heapq.heappush(open_set, (f_score, tentative_g, neighbor))

        if target not in came_from:
            return  # Aucun chemin trouvé

        # Retrace le chemin jusqu'au prochain pas
        path = []
        node = target
        while node != (cx, cy):
            path.append(node)
            node = came_from[node]
        if path:
            next_x, next_y = path[-1]
            self.position = [next_x, next_y]

    # ----------------------------------------------------------------------
    def __repr__(self):
        return f"Agent(pos={self.position}, holding={self.holding})"
