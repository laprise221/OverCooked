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
        self.direction = "CF"  # Direction par défaut (face)

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
            self.current_action = "En attente"
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
    def _get_adjacent_positions(self, position):
        """Retourne les 4 positions adjacentes (haut, bas, gauche, droite)"""
        x, y = position
        return [
            (x + 1, y),  # droite
            (x - 1, y),  # gauche
            (x, y + 1),  # bas
            (x, y - 1)   # haut
        ]

    # ----------------------------------------------------------------------
    def _is_adjacent_to(self, pos1, pos2):
        """Vérifie si deux positions sont adjacentes (4 directions uniquement)"""
        dx = abs(pos1[0] - pos2[0])
        dy = abs(pos1[1] - pos2[1])
        return (dx == 1 and dy == 0) or (dx == 0 and dy == 1)

    # ----------------------------------------------------------------------
    def _find_nearest_accessible_position(self, target_position):
        """Trouve la case accessible la plus proche d'une position cible"""
        adjacent_positions = self._get_adjacent_positions(target_position)

        # Filtre les positions accessibles
        accessible = [pos for pos in adjacent_positions if self.kitchen.is_walkable(pos)]

        if not accessible:
            return None

        # Retourne la position la plus proche de l'agent
        current_pos = tuple(self.position)
        closest = min(accessible, key=lambda pos: abs(pos[0] - current_pos[0]) + abs(pos[1] - current_pos[1]))
        return closest

    # ----------------------------------------------------------------------
    def _do_pickup(self, ingredient_name):
        if self.holding:
            return True

        target_ingredient = next((ing for ing in self.kitchen.ingredients_available
                                  if ing.name == ingredient_name and ing.state == "cru"), None)
        if not target_ingredient:
            print(f"❌ Ingrédient {ingredient_name} non trouvé!")
            return True

        # Vérifie si on est déjà adjacent à l'ingrédient
        if self._is_adjacent_to(tuple(self.position), tuple(target_ingredient.position)):
            print(f"✅ Ramassé: {ingredient_name}")
            self.holding = Ingredient(ingredient_name, "cru")
            self.current_action = f"Porte {ingredient_name}"
            return True

        # Trouve une position accessible adjacent à l'ingrédient
        target_pos = self._find_nearest_accessible_position(target_ingredient.position)

        if not target_pos:
            print(f"❌ Impossible d'accéder à {ingredient_name}!")
            return True

        # Se déplace vers cette position
        if tuple(self.position) != target_pos:
            self._move_towards(target_pos)
            self.current_action = f"Va chercher {ingredient_name}"
            return False

        return False

    # ----------------------------------------------------------------------
    def _do_cut(self):
        if not self.holding:
            return True

        cutting_board = self.kitchen.get_available_tool('planche')
        if not cutting_board:
            self.current_action = "Attente planche"
            return False

        # Vérifie si on est adjacent à la planche
        if self._is_adjacent_to(tuple(self.position), tuple(cutting_board.position)):
            if cutting_board.use(self.holding):
                self.action_timer = 20
                self.holding = cutting_board.release()
                self.holding.state = "coupe"
                self.current_action = f"Découpe {self.holding.name}"
                return True
            return False

        # Trouve une position adjacente à la planche
        target_pos = self._find_nearest_accessible_position(cutting_board.position)
        if not target_pos:
            print("❌ Impossible d'accéder à la planche!")
            return True

        self._move_towards(target_pos)
        self.current_action = "Va vers planche"
        return False

    # ----------------------------------------------------------------------
    def _do_cook(self):
        if not self.holding:
            return True

        stove = self.kitchen.get_available_tool('poele')
        if not stove:
            self.current_action = "Attente poêle"
            return False

        # Vérifie si on est adjacent à la poêle
        if self._is_adjacent_to(tuple(self.position), tuple(stove.position)):
            if stove.use(self.holding):
                self.action_timer = 30
                self.holding = stove.release()
                self.holding.state = "cuit"
                self.current_action = f"Cuit {self.holding.name}"
                return True
            return False

        # Trouve une position adjacente à la poêle
        target_pos = self._find_nearest_accessible_position(stove.position)
        if not target_pos:
            print("❌ Impossible d'accéder à la poêle!")
            return True

        self._move_towards(target_pos)
        self.current_action = "Va vers poêle"
        return False

    # ----------------------------------------------------------------------
    def _do_bring_to_assembly(self):
        if not self.holding:
            return True

        # Position centrale de la table d'assemblage
        assembly_center = (8, 8)

        # Vérifie si on est adjacent à la table
        if self._is_adjacent_to(tuple(self.position), assembly_center):
            # Dépose l'ingrédient sur la table avec sa position
            self.holding.position = list(assembly_center)
            self.assembled_ingredients.append(self.holding)
            self.holding = None
            self.current_action = "Dépose ingrédient"
            return True

        # Trouve une position adjacente à la table
        target_pos = self._find_nearest_accessible_position(assembly_center)
        if not target_pos:
            print("❌ Impossible d'accéder à la table!")
            return True

        self._move_towards(target_pos)
        self.current_action = "Va vers table"
        return False

    # ----------------------------------------------------------------------
    def _do_deliver(self, recipe_name, required_ingredients):
        assembled_names = [ing.get_full_name() for ing in self.assembled_ingredients]
        if sorted(assembled_names) != sorted(required_ingredients):
            print(f"❌ Ingrédients manquants!")
            return True

        if not self.holding or not isinstance(self.holding, Dish):
            self.holding = Dish(recipe_name, self.assembled_ingredients)
            self.current_action = f"Assemble {recipe_name}"
            self.kitchen.spawn_dish_image(recipe_name, position=(8, 8))
            self.action_timer = 15
            return False

        # Position centrale du comptoir
        counter_center = (3, 12)

        # Vérifie si on est adjacent au comptoir
        if self._is_adjacent_to(tuple(self.position), counter_center):
            self.holding = None
            self.assembled_ingredients = []
            self.current_action = f"Livré {recipe_name} !"
            self.kitchen.remove_dish_image()
            return True

        # Trouve une position adjacente au comptoir
        target_pos = self._find_nearest_accessible_position(counter_center)
        if not target_pos:
            print("❌ Impossible d'accéder au comptoir!")
            return True

        self._move_towards(target_pos)
        self.kitchen.move_dish_image(self.position)
        self.current_action = "Va livrer le plat"
        return False

    # ----------------------------------------------------------------------
    def _update_direction(self, old_pos, new_pos):
        """Met à jour la direction de l'agent selon son déplacement"""
        dx = new_pos[0] - old_pos[0]
        dy = new_pos[1] - old_pos[1]

        # Détermine la direction
        if dx > 0:
            self.direction = "CDR"  # Droite
        elif dx < 0:
            self.direction = "CG"   # Gauche
        elif dy > 0:
            self.direction = "CF"   # Face (bas)
        elif dy < 0:
            self.direction = "CD"   # Dos (haut)

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
            old_pos = self.position.copy()
            self.position = [next_x, next_y]
            self._update_direction(old_pos, self.position)

    # ----------------------------------------------------------------------
    def __repr__(self):
        return f"Agent(pos={self.position}, holding={self.holding}, direction={self.direction})"
