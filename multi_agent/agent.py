"""
multi_agent.py
Agent coopératif pour système multi-agents avec allocation dynamique de tâches

Architecture:
- Intégration avec STRIPS pour planification
- Participation au Task Market pour allocation dynamique
- Communication via Blackboard
- Évaluation de coûts pour bidding
"""

import heapq
import sys
import os
from typing import Optional, Tuple, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.objects import Ingredient, Dish
from common.recipes import parse_ingredient_requirement, get_ingredient_config
from multi_agent.planning.strips import Action, ActionType, STRIPSPlanner, WorldState
from multi_agent.coordination.task_market import Task, TaskStatus, Bid
from multi_agent.coordination.communication import AgentCommunicator, MessageType


class CooperativeAgent:
    """
    Agent coopératif pour système multi-agents
    Utilise STRIPS pour la planification et Task Market pour l'allocation
    """

    def __init__(self, agent_id: int, position: Tuple[int, int], kitchen, communicator: AgentCommunicator):
        self.id = agent_id
        self.position = list(position)
        self.kitchen = kitchen
        self.communicator = communicator

        # État interne
        self.holding = None
        self.current_task: Optional[Task] = None
        self.current_action_strips: Optional[Action] = None
        self.assembled_ingredients = []
        self.current_action = "En attente"
        self.action_timer = 0
        self.direction = "CF"
        self.processing_action: Optional[str] = None
        self.active_tool = None

        # Performance tracking
        self.total_distance_traveled = 0
        self.tasks_completed = 0
        self.idle_time = 0

        print(f"🤖 Agent {self.id} initialisé à position {position}")

    # ----------------------------------------------------------------------
    # Méthodes pour Task Market - Bidding
    # ----------------------------------------------------------------------

    def evaluate_task_cost(self, task: Task) -> float:
        """
        Évalue le coût d'une tâche pour cet agent
        Coût = distance jusqu'à la ressource + durée estimée de l'action
        """
        # Vérifications de préconditions
        action_type = task.action_type
        ingredient_param = task.parameters.get('ingredient', '')

        # CUT/COOK : agent DOIT avoir l'ingrédient
        if action_type in [ActionType.CUT, ActionType.COOK]:
            if not self.holding:
                return float('inf')  # Impossible

            # Vérifier que c'est le bon ingrédient
            base_ing = ingredient_param.split('_')[0] if '_' in ingredient_param else ingredient_param
            if self.holding.name != base_ing:
                return float('inf')  # Mauvais ingrédient

        # BRING_TO_ASSEMBLY : agent DOIT avoir quelque chose
        if action_type == ActionType.BRING_TO_ASSEMBLY:
            if not self.holding:
                return float('inf')
            target_ingredient = task.parameters.get('ingredient', '')
            if not target_ingredient:
                return float('inf')
            base_target = target_ingredient.split('_')[0] if '_' in target_ingredient else target_ingredient
            required_state = target_ingredient.split('_')[1] if '_' in target_ingredient else 'cru'
            normalized_required = 'cru' if required_state in ('raw', 'cru') else required_state
            holding_state = self.holding.state
            if self.holding.name != base_target:
                return float('inf')
            if normalized_required == 'coupe' and holding_state != 'coupe':
                return float('inf')
            if normalized_required == 'cuit' and holding_state != 'cuit':
                return float('inf')

        # PICKUP : agent ne doit RIEN avoir
        if action_type == ActionType.PICKUP:
            if self.holding is not None:
                return float('inf')  # Déjà chargé

        # Obtenir la position cible en fonction du type de tâche
        target_position = self._get_task_target_position(task)

        if not target_position:
            return float('inf')  # Coût infini si impossible

        # Distance Manhattan
        distance = abs(self.position[0] - target_position[0]) + \
                   abs(self.position[1] - target_position[1])

        # Temps de déplacement (approximation: 0.1s par case)
        travel_time = distance * 0.1

        # Coût total = déplacement + exécution
        total_cost = travel_time + task.estimated_duration

        return total_cost

    def _get_task_target_position(self, task: Task) -> Optional[Tuple[int, int]]:
        """Détermine la position cible d'une tâche"""
        action_type = task.action_type
        ingredient = task.parameters.get('ingredient')

        if action_type == ActionType.PICKUP:
            # Position de l'ingrédient
            base_name = ingredient.split('_')[0] if '_' in ingredient else ingredient
            target_ing = next((ing for ing in self.kitchen.ingredients_available
                             if ing.name == base_name), None)
            return tuple(target_ing.position) if target_ing else None

        elif action_type == ActionType.CUT:
            # Position de la planche à découper
            cutting_board = self.kitchen.get_available_tool('planche')
            return tuple(cutting_board.position) if cutting_board else None

        elif action_type == ActionType.COOK:
            # Position de la cuisinière
            stove = self.kitchen.get_available_tool('poele')
            return tuple(stove.position) if stove else None

        elif action_type in [ActionType.BRING_TO_ASSEMBLY, ActionType.DELIVER]:
            # Position de la table d'assemblage ou comptoir
            if action_type == ActionType.BRING_TO_ASSEMBLY:
                return (8, 8)  # Table d'assemblage
            else:
                return (3, 12)  # Comptoir

        return None

    def submit_bid_for_task(self, task: Task) -> Bid:
        """Soumet une enchère pour une tâche"""
        cost = self.evaluate_task_cost(task)
        bid = Bid(
            agent_id=self.id,
            task_id=task.task_id,
            cost=cost,
            timestamp=0  # Sera rempli par le market
        )
        return bid

    # ----------------------------------------------------------------------
    # Exécution de tâches
    # ----------------------------------------------------------------------

    def assign_task(self, task: Task):
        """Assigne une tâche à cet agent"""
        self.current_task = task
        print(f"🎯 Agent {self.id} reçoit tâche {task.task_id}: {task.action_type.value}")
        self.communicator.notify_task_claimed(task.task_id)

    def update(self, task_market=None) -> bool:
        """
        Met à jour l'agent (appelé chaque frame)
        Retourne True si l'agent a terminé sa tâche actuelle
        """
        # Mettre à jour la position sur le blackboard
        self.communicator.update_position(self.position[0], self.position[1])

        # Gérer le timer d'action
        if self.action_timer > 0:
            self.action_timer -= 1
            if self.action_timer <= 0:
                print(f"✅ Agent {self.id}: Action terminée!")
            return False

        # Si pas de tâche, l'agent est idle
        if not self.current_task:
            self.current_action = "En attente"
            self.idle_time += 1
            self.communicator.notify_idle()
            return True

        # Exécuter la tâche actuelle
        task_complete = self._execute_current_task()

        if task_complete:
            # Notifier la complétion
            self.communicator.notify_task_completed(self.current_task.task_id)

            # Libérer les ressources si nécessaire
            self._release_resources()

            # Marquer comme complété dans le task market
            if task_market:
                task_market.complete_task(self.current_task.task_id)

            self.tasks_completed += 1
            self.current_task = None
            return True

        return False

    def _execute_current_task(self) -> bool:
        """Exécute la tâche actuelle selon son type"""
        task = self.current_task
        action_type = task.action_type

        if action_type == ActionType.PICKUP:
            ingredient = task.parameters['ingredient']
            return self._do_pickup(ingredient)

        elif action_type == ActionType.CUT:
            return self._do_cut()

        elif action_type == ActionType.COOK:
            return self._do_cook()

        elif action_type == ActionType.BRING_TO_ASSEMBLY:
            return self._do_bring_to_assembly()

        elif action_type == ActionType.DELIVER:
            recipe = task.parameters['recipe']
            ingredients = task.parameters['ingredients']
            return self._do_deliver(recipe, ingredients)

        return False

    def _release_resources(self):
        """Libère les ressources occupées par l'agent"""
        if self.current_task:
            action_type = self.current_task.action_type

            if action_type == ActionType.CUT:
                self.kitchen.unlock_resource('cutting_board', self.id)
                self.communicator.notify_resource_free('cutting_board')
            elif action_type == ActionType.COOK:
                self.kitchen.unlock_resource('stove', self.id)
                self.communicator.notify_resource_free('stove')
            elif action_type in [ActionType.BRING_TO_ASSEMBLY, ActionType.DELIVER]:
                self.kitchen.unlock_resource('assembly', self.id)
                self.communicator.notify_resource_free('assembly')

    # ----------------------------------------------------------------------
    # Actions atomiques (similaires à agent.py mais avec locks)
    # ----------------------------------------------------------------------

    def _do_pickup(self, ingredient_name: str) -> bool:
        """Ramasse un ingrédient"""
        if self.holding:
            self.current_action = "Doit déposer avant pickup"
            return False

        base_name = ingredient_name.split('_')[0] if '_' in ingredient_name else ingredient_name
        target_ingredient = next((ing for ing in self.kitchen.ingredients_available
                                  if ing.name == base_name and ing.state == "cru"), None)

        if not target_ingredient:
            print(f"❌ Agent {self.id}: Ingrédient {ingredient_name} non trouvé!")
            return True

        # Vérifie si on est adjacent
        if self._is_adjacent_to(tuple(self.position), tuple(target_ingredient.position)):
            print(f"✅ Agent {self.id}: Ramassé {ingredient_name}")
            self.holding = Ingredient(base_name, "cru")
            self.current_action = f"Porte {ingredient_name}"
            return True

        # Se déplacer vers l'ingrédient
        target_pos = self._find_nearest_accessible_position(target_ingredient.position)
        if not target_pos:
            print(f"❌ Agent {self.id}: Impossible d'accéder à {ingredient_name}!")
            return True

        if tuple(self.position) != target_pos:
            self._move_towards(target_pos)
            self.current_action = f"Va chercher {ingredient_name}"
            return False

        return False

    def _do_cut(self) -> bool:
        """Découpe un ingrédient"""
        if self.processing_action == 'cut':
            if self.action_timer > 0:
                return False
            processed = self.active_tool.release() if self.active_tool else None
            if processed:
                self.holding = processed
                self.current_action = f"Découpe terminée ({processed.name})"
            self.processing_action = None
            self.active_tool = None
            # CRITICAL: Libérer le resource lock après la découpe
            self.kitchen.unlock_resource('cutting_board', self.id)
            self.communicator.notify_resource_free('cutting_board')
            return True

        if not self.holding:
            needed = self.current_task.parameters.get('ingredient') if self.current_task else None
            if needed:
                acquired = self._do_pickup(needed)
                if not acquired:
                    return False
            else:
                self.current_action = "Ingrédient inconnu pour découpe"
                return False

        # Vérifier d'abord qu'il y a une planche disponible
        cutting_board = self.kitchen.get_available_tool('planche')
        if not cutting_board:
            self.current_action = "Attente planche"
            # Libérer le lock si on l'avait
            self.kitchen.unlock_resource('cutting_board', self.id)
            return False

        # Tenter de verrouiller la ressource
        if not self.kitchen.try_lock_resource('cutting_board', self.id):
            self.current_action = "Attente planche (occupée)"
            return False

        # Vérifie si on est adjacent
        if self._is_adjacent_to(tuple(self.position), tuple(cutting_board.position)):
            if cutting_board.use(self.holding):
                ingredient = self.holding
                self.holding = None
                self.active_tool = cutting_board
                self.processing_action = 'cut'
                self.action_timer = 20
                self.current_action = f"Découpe {ingredient.name}"
                self.communicator.notify_resource_locked('cutting_board')
            return False

        # Se déplacer vers la planche
        target_pos = self._find_nearest_accessible_position(cutting_board.position)
        if not target_pos:
            print(f"❌ Agent {self.id}: Impossible d'accéder à la planche!")
            self.kitchen.unlock_resource('cutting_board', self.id)
            return True

        self._move_towards(target_pos)
        self.current_action = "Va vers planche"
        return False

    def _do_cook(self) -> bool:
        """Cuit un ingrédient"""
        if self.processing_action == 'cook':
            if self.action_timer > 0:
                return False
            processed = self.active_tool.release() if self.active_tool else None
            if processed:
                self.holding = processed
                self.current_action = f"Cuisson terminée ({processed.name})"
            self.processing_action = None
            self.active_tool = None
            # CRITICAL: Libérer le resource lock après la cuisson
            self.kitchen.unlock_resource('stove', self.id)
            self.communicator.notify_resource_free('stove')
            return True

        if not self.holding:
            needed = self.current_task.parameters.get('ingredient') if self.current_task else None
            if needed:
                acquired = self._do_pickup(needed)
                if not acquired:
                    return False
            else:
                self.current_action = "Ingrédient inconnu pour cuisson"
                return False

        # Vérifier d'abord qu'il y a une poêle disponible
        stove = self.kitchen.get_available_tool('poele')
        if not stove:
            self.current_action = "Attente poêle"
            # Libérer le lock si on l'avait
            self.kitchen.unlock_resource('stove', self.id)
            return False

        # Tenter de verrouiller la ressource
        if not self.kitchen.try_lock_resource('stove', self.id):
            self.current_action = "Attente poêle (occupée)"
            return False

        # Vérifie si on est adjacent
        if self._is_adjacent_to(tuple(self.position), tuple(stove.position)):
            if stove.use(self.holding):
                ingredient = self.holding
                self.holding = None
                self.active_tool = stove
                self.processing_action = 'cook'
                self.action_timer = 30
                self.current_action = f"Cuit {ingredient.name}"
                self.communicator.notify_resource_locked('stove')
            return False

        # Se déplacer vers la poêle
        target_pos = self._find_nearest_accessible_position(stove.position)
        if not target_pos:
            print(f"❌ Agent {self.id}: Impossible d'accéder à la poêle!")
            self.kitchen.unlock_resource('stove', self.id)
            return True

        self._move_towards(target_pos)
        self.current_action = "Va vers poêle"
        return False

    def _do_bring_to_assembly(self) -> bool:
        """Amène un ingrédient à la table d'assemblage"""
        if not self.holding:
            print(f"⚠️  Agent {self.id}: bring_to_assembly mais rien dans les mains!")
            self.current_action = "En attente ingrédient"
            return False

        assembly_center = (8, 8)

        # Vérifie si on est adjacent
        if self._is_adjacent_to(tuple(self.position), assembly_center):
            self.holding.position = list(assembly_center)
            # Ajouter à la table partagée ET à la liste personnelle
            self.kitchen.shared_assembly_table.append(self.holding)
            # Nettoyer la liste locale pour éviter les résidus visuels
            self.assembled_ingredients.clear()
            print(f"✅ Agent {self.id}: Dépose {self.holding.get_full_name()} sur table")
            self.holding = None
            self.current_action = "Dépose ingrédient"
            return True

        # Se déplacer vers la table
        target_pos = self._find_nearest_accessible_position(assembly_center)
        if not target_pos:
            print(f"❌ Agent {self.id}: Impossible d'accéder à la table!")
            return True

        self._move_towards(target_pos)
        self.current_action = "Va vers table"
        return False

    def _do_deliver(self, recipe_name: str, required_ingredients: list) -> bool:
        """Livre le plat final"""
        # Utiliser la table d'assemblage partagée (effort collectif des 2 agents)
        assembled_names = [ing.get_full_name() for ing in self.kitchen.shared_assembly_table]

        if sorted(assembled_names) != sorted(required_ingredients):
            # Attendre que tous les ingrédients soient assemblés
            self.current_action = f"Attente ingrédients ({len(assembled_names)}/{len(required_ingredients)})"
            return False

        if not self.holding or not isinstance(self.holding, Dish):
            self.holding = Dish(recipe_name, self.kitchen.shared_assembly_table)
            self.current_action = f"Assemble {recipe_name}"
            self.kitchen.spawn_dish_image(recipe_name, position=(8, 8))
            self.action_timer = 15
            return False

        counter_center = (3, 12)

        # Vérifie si on est adjacent
        if self._is_adjacent_to(tuple(self.position), counter_center):
            self.kitchen.place_dish_on_counter(recipe_name, counter_center)
            self.holding = None
            # Nettoyer la table partagée et personnelle
            self.kitchen.shared_assembly_table = []
            self.assembled_ingredients = []
            self.current_action = f"Livré {recipe_name} !"
            return True

        # Se déplacer vers le comptoir
        target_pos = self._find_nearest_accessible_position(counter_center)
        if not target_pos:
            print(f"❌ Agent {self.id}: Impossible d'accéder au comptoir!")
            return True

        self._move_towards(target_pos)
        self.kitchen.move_dish_image(self.position)
        self.current_action = "Va livrer le plat"
        return False

    # ----------------------------------------------------------------------
    # Méthodes utilitaires (navigation et pathfinding)
    # ----------------------------------------------------------------------

    def _get_adjacent_positions(self, position):
        """Retourne les 4 positions adjacentes"""
        x, y = position
        return [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]

    def _is_adjacent_to(self, pos1, pos2):
        """Vérifie si deux positions sont adjacentes"""
        dx = abs(pos1[0] - pos2[0])
        dy = abs(pos1[1] - pos2[1])
        return (dx == 1 and dy == 0) or (dx == 0 and dy == 1)

    def _find_nearest_accessible_position(self, target_position):
        """Trouve la case accessible la plus proche d'une position cible"""
        adjacent_positions = self._get_adjacent_positions(target_position)
        accessible = [pos for pos in adjacent_positions if self.kitchen.is_walkable(pos)]

        if not accessible:
            return None

        current_pos = tuple(self.position)
        closest = min(accessible, key=lambda pos: abs(pos[0] - current_pos[0]) + abs(pos[1] - current_pos[1]))
        return closest

    def _update_direction(self, old_pos, new_pos):
        """Met à jour la direction de l'agent"""
        dx = new_pos[0] - old_pos[0]
        dy = new_pos[1] - old_pos[1]

        if dx > 0:
            self.direction = "CDR"
        elif dx < 0:
            self.direction = "CG"
        elif dy > 0:
            self.direction = "CF"
        elif dy < 0:
            self.direction = "CD"

    def _move_towards(self, target):
        """
        Déplace l'agent d'une case vers la cible avec A*
        Évite les collisions avec les autres agents
        """
        tx, ty = target
        cx, cy = self.position

        if (cx, cy) == (tx, ty):
            return

        # Vérifier les positions des autres agents pour éviter collisions
        other_positions = self.communicator.get_other_agents_positions()
        occupied_positions = set(other_positions.values())

        def heuristic(a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])

        def is_walkable_and_free(pos):
            """Vérifie si une position est accessible ET non occupée par un autre agent"""
            return self.kitchen.is_walkable(pos) and pos not in occupied_positions

        open_set = []
        heapq.heappush(open_set, (heuristic((cx, cy), target), 0, (cx, cy)))
        came_from = {}
        g_score = {(cx, cy): 0}

        while open_set:
            _, cost, current = heapq.heappop(open_set)
            if current == target:
                break

            x, y = current
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx, ny = x + dx, y + dy
                neighbor = (nx, ny)

                if not is_walkable_and_free(neighbor):
                    continue

                tentative_g = g_score[current] + 1
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score = tentative_g + heuristic(neighbor, target)
                    heapq.heappush(open_set, (f_score, tentative_g, neighbor))

        if target not in came_from:
            return  # Aucun chemin trouvé

        # Retrace le chemin
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
            self.total_distance_traveled += 1

    def get_performance_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de performance de l'agent"""
        return {
            'agent_id': self.id,
            'tasks_completed': self.tasks_completed,
            'distance_traveled': self.total_distance_traveled,
            'idle_time': self.idle_time,
            'current_action': self.current_action
        }

    def __repr__(self):
        return f"Agent{self.id}(pos={self.position}, action={self.current_action})"
