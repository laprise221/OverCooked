"""
agent.py
Définit le comportement de l'agent autonome
"""

import math
from collections import deque
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

    def set_recipe(self, recipe_name, recipe_data):
        """
        Configure une nouvelle recette à préparer
        """
        print(f"\n🍳 Nouvelle commande: {recipe_name}")
        print(f"Ingrédients requis: {recipe_data['ingredients']}")

        self.assembled_ingredients = []
        self.task_queue = []

        # Crée les tâches pour chaque ingrédient
        for ingredient_req in recipe_data['ingredients']:
            base_name, required_state = parse_ingredient_requirement(ingredient_req)
            config = get_ingredient_config(base_name)

            # Crée la séquence de tâches pour cet ingrédient
            tasks = []

            # 1. Aller chercher l'ingrédient
            tasks.append({
                'type': 'pickup',
                'ingredient': base_name,
                'target_state': required_state
            })

            # 2. Traiter l'ingrédient si nécessaire
            if required_state == 'coupe' and config['needs_cutting']:
                tasks.append({
                    'type': 'cut',
                    'ingredient': base_name
                })
            elif required_state == 'cuit' and config['needs_cooking']:
                tasks.append({
                    'type': 'cook',
                    'ingredient': base_name
                })

            # 3. Apporter à la table d'assemblage
            tasks.append({
                'type': 'bring_to_assembly',
                'ingredient': base_name
            })

            self.task_queue.extend(tasks)

        # Tâche finale: déposer le plat
        self.task_queue.append({
            'type': 'deliver',
            'recipe_name': recipe_name,
            'required_ingredients': recipe_data['ingredients']
        })

        print(f"📋 {len(self.task_queue)} tâches planifiées")

    def update(self):
        """
        Met à jour l'état de l'agent (appelé à chaque frame)
        """
        # Si l'agent attend la fin d'une action (découpe, cuisson, etc.)
        if self.action_timer > 0:
            self.action_timer -= 1
            if self.action_timer <= 0:
                print("✅ Action terminée !")
            return  # ⚠️ on sort mais on ne perd pas la tâche courante

        # Si aucune tâche en cours
        if not self.task_queue and not self.current_task:
            self.current_action = "Terminé!"
            return

        # Si pas de tâche active, on en prend une nouvelle
        if not self.current_task and self.task_queue:
            self.current_task = self.task_queue.pop(0)
            print(f"\n➡️ Nouvelle tâche: {self.current_task['type']}")

        # Exécution de la tâche courante
        if self.current_task:
            task_complete = self._execute_task()
            if task_complete:
                self.current_task = None

    def _execute_task(self):
        """
        Execute la tâche actuelle
        Retourne True si la tâche est terminée
        """
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

    def _do_pickup(self, ingredient_name):
        """Ramasse un ingrédient"""
        if self.holding:
            return True  # Déjà en train de porter quelque chose

        # Trouve l'ingrédient
        target_ingredient = None
        for ing in self.kitchen.ingredients_available:
            if ing.name == ingredient_name and ing.state == "cru":
                target_ingredient = ing
                break

        if not target_ingredient:
            print(f"❌ Ingrédient {ingredient_name} non trouvé!")
            return True

        # Se déplace vers l'ingrédient
        if self.position != list(target_ingredient.position):
            self._move_towards(target_ingredient.position)
            self.current_action = f"Va chercher {ingredient_name}"
            return False

        # Ramasse l'ingrédient
        print(f"✅ Ramassé: {ingredient_name}")
        self.holding = Ingredient(ingredient_name, "cru")
        self.current_action = f"Porte {ingredient_name}"
        return True

    def _do_cut(self):
        """Découpe l'ingrédient porté"""
        if not self.holding:
            return True

        # Trouve une planche disponible
        cutting_board = self.kitchen.get_available_tool('planche')
        if not cutting_board:
            print("⏳ Attente d'une planche...")
            self.current_action = "Attente planche"
            return False

        # Se déplace vers la planche
        if self.position != list(cutting_board.position):
            self._move_towards(cutting_board.position)
            self.current_action = f"Va vers planche"
            return False

        # Utilise la planche
        if cutting_board.use(self.holding):
            print(f"🔪 Découpe {self.holding.name}...")
            self.current_action = f"Découpe {self.holding.name}"
            self.action_timer = 20  # Temps de découpe
            self.holding = cutting_board.release()
            self.holding.state = "coupe"

            return True

        return False

    def _do_cook(self):
        """Cuit l'ingrédient porté"""
        if not self.holding:
            return True

        # Trouve une poêle disponible
        stove = self.kitchen.get_available_tool('poele')
        if not stove:
            print("⏳ Attente d'une poêle...")
            self.current_action = "Attente poêle"
            return False

        # Se déplace vers la poêle
        if self.position != list(stove.position):
            self._move_towards(stove.position)
            self.current_action = f"Va vers poêle"
            return False

        # Utilise la poêle
        if stove.use(self.holding):
            print(f"🍳 Cuisson {self.holding.name}...")
            self.current_action = f"Cuit {self.holding.name}"
            self.action_timer = 30  # Temps de cuisson
            self.holding = stove.release()
            self.holding.state = "cuit"
            return True

        return False

    def _do_bring_to_assembly(self):
        """Apporte l'ingrédient à la table d'assemblage"""
        if not self.holding:
            return True

        # Position cible: centre de la table d'assemblage
        target_pos = (4, 4)

        # Se déplace vers la table
        if self.position != list(target_pos):
            self._move_towards(target_pos)
            self.current_action = "Va vers table"
            return False

        # Dépose l'ingrédient
        print(f"📦 Déposé sur table: {self.holding.get_full_name()}")
        self.assembled_ingredients.append(self.holding)
        self.holding = None
        self.current_action = "Dépose ingrédient"
        return True

    def _do_deliver(self, recipe_name, required_ingredients):
        """Assemble puis livre le plat final"""
        assembled_names = [ing.get_full_name() for ing in self.assembled_ingredients]

        # Vérifie que tous les ingrédients nécessaires sont présents
        if sorted(assembled_names) != sorted(required_ingredients):
            print(f"❌ Ingrédients manquants!")
            print(f"Requis: {required_ingredients}")
            print(f"Assemblés: {assembled_names}")
            return True

        # Étape 1 : assemblage du plat
        if not self.holding or not isinstance(self.holding, Dish):
            print(f"🍽️ Assemblage du {recipe_name}...")
            self.holding = Dish(recipe_name, self.assembled_ingredients)
            self.current_action = f"Assemble {recipe_name}"
            self.kitchen.spawn_dish_image(recipe_name, position=(4, 4))
            self.action_timer = 15  # on attend un peu
            return False  # ⏳ on laisse le temps s’écouler

        # Étape 2 : déplacement vers le comptoir
        target_pos = (2, 6)
        if self.position != list(target_pos):
            self._move_towards(target_pos)
            # 🔁 déplace aussi l’image du plat visuellement
            self.kitchen.move_dish_image(self.position)
            self.current_action = "Va livrer le plat"
            return False

        # Étape 3 : livraison finale
        print(f"✨ Plat livré: {recipe_name} !")
        self.holding = None
        self.assembled_ingredients = []
        self.current_action = f"Livré {recipe_name} !"
        self.kitchen.remove_dish_image()

        return True

    """def _move_towards(self, target):
        tx, ty = target
        cx, cy = self.position

        # Calcule les déplacements possibles
        moves = []
        if cx < tx:
            moves.append((cx + 1, cy, abs(tx - cx - 1) + abs(ty - cy)))
        if cx > tx:
            moves.append((cx - 1, cy, abs(tx - cx + 1) + abs(ty - cy)))
        if cy < ty:
            moves.append((cx, cy + 1, abs(tx - cx) + abs(ty - cy - 1)))
        if cy > ty:
            moves.append((cx, cy - 1, abs(tx - cx) + abs(ty - cy + 1)))

        # Filtre les mouvements valides et choisit le meilleur
        valid_moves = [
            (x, y, dist) for x, y, dist in moves
            if self.kitchen.is_walkable((x, y))
        ]

        if valid_moves:
            # Choisit le mouvement qui rapproche le plus de la cible
            valid_moves.sort(key=lambda m: m[2])
            next_x, next_y, _ = valid_moves[0]
            self.position = [next_x, next_y]"""


    def _move_towards(self, target):
        """
        Déplace l'agent d'une case vers la cible en évitant les obstacles (BFS)
        """
        tx, ty = target
        cx, cy = self.position
        if (cx, cy) == (tx, ty):
            return

        # Recherche BFS
        queue = deque([(cx, cy)])
        visited = {(cx, cy): None}
        found = False

        while queue:
            x, y = queue.popleft()
            if (x, y) == (tx, ty):
                found = True
                break
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx, ny = x + dx, y + dy
                if (nx, ny) not in visited and self.kitchen.is_walkable((nx, ny)):
                    visited[(nx, ny)] = (x, y)
                    queue.append((nx, ny))

        if not found:
            return  # Aucun chemin trouvé

        # Retrace le chemin jusqu'au prochain pas
        path = []
        node = (tx, ty)
        while node and node != (cx, cy):
            path.append(node)
            node = visited[node]
        if path:
            next_x, next_y = path[-1]
            self.position = [next_x, next_y]

    def __repr__(self):
        return f"Agent(pos={self.position}, holding={self.holding})"