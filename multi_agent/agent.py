"""
multi_agent/agent.py
Agent coopératif corrigé et stabilisé
"""

import heapq
import sys
import os
import math
from typing import Optional, Tuple, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.objects import Ingredient, Dish, Tool
from multi_agent.planning.strips import Action, ActionType
from multi_agent.coordination.task_market import Task, Bid
from multi_agent.coordination.communication import AgentCommunicator

class CooperativeAgent:
    def __init__(self, agent_id: int, position: Tuple[int, int], kitchen, communicator: AgentCommunicator):
        self.id = agent_id
        self.position = list(position)
        self.kitchen = kitchen
        self.communicator = communicator

        # État interne
        self.holding = None
        self.current_task: Optional[Task] = None
        self.current_action = "En attente"
        self.action_timer = 0
        self.direction = "CF"
        self.action_complete = False

        # État pour actions longues
        self.processing_action: Optional[str] = None
        self.target_tool_pos = None

        # Performance tracking
        self.total_distance_traveled = 0
        self.tasks_completed = 0
        self.idle_time = 0

        print(f"🤖 Agent {self.id} initialisé à position {position}")

    # ----------------------------------------------------------------------
    # 1. Évaluation et Bidding (Intelligence)
    # ----------------------------------------------------------------------

    def evaluate_task_cost(self, task: Task) -> float:
        """Calcule le coût en fonction de la distance réelle vers l'outil le plus proche"""
        # Vérifications de base (Holding)
        if task.action_type in [ActionType.CUT, ActionType.COOK, ActionType.BRING_TO_ASSEMBLY]:
            if not self.holding: return float('inf')
        if task.action_type == ActionType.PICKUP and self.holding:
            return float('inf')

        # Trouver la cible optimale
        target_pos = self._get_smart_target(task)
        if not target_pos:
            return float('inf')

        # Distance Manhattan
        dist = abs(self.position[0] - target_pos[0]) + abs(self.position[1] - target_pos[1])
        return (dist * 0.5) + task.estimated_duration

    def submit_bid_for_task(self, task: Task) -> Bid:
        return Bid(self.id, task.task_id, self.evaluate_task_cost(task), 0)

    def assign_task(self, task: Task):
        self.current_task = task
        self.communicator.notify_task_claimed(task.task_id)

    # ----------------------------------------------------------------------
    # 2. Boucle de mise à jour (Update)
    # ----------------------------------------------------------------------

    def update(self, task_market=None) -> bool:
        """Appelé à chaque frame"""
        self.communicator.update_position(self.position[0], self.position[1])

        # Gestion du timer (Action en cours)
        if self.action_timer > 0:
            self.action_timer -= 1
            if self.action_timer <= 0:
                self._finish_action()
            return False

        finished = False

        # Action longue qui vient juste de se terminer (cut/cook)
        if self.action_complete and self.current_task and \
           self.current_task.action_type in [ActionType.CUT, ActionType.COOK]:
            self.action_complete = False
            finished = True
        else:
            if not self.current_task:
                self.current_action = "En attente"
                self.idle_time += 1
                return True

            # Exécution de la tâche
            finished = self._execute_task()

        if finished:
            self.communicator.notify_task_completed(self.current_task.task_id)
            if task_market:
                task_market.complete_task(self.current_task.task_id)
            self.tasks_completed += 1
            self.current_task = None
            self.target_tool_pos = None
            return True

        return False

    def _finish_action(self):
        """Finalise une action (Cut/Cook)"""
        # On récupère le résultat de l'outil
        if self.target_tool_pos:
            tx, ty = self.target_tool_pos
            cell = self.kitchen.grid[ty][tx]
            if isinstance(cell, Tool):
                res = cell.release()
                if res:
                    self.holding = res

        self.processing_action = None
        self.target_tool_pos = None
        self.action_complete = True

        # Déverrouillage propre des ressources
        if self.current_task.action_type == ActionType.CUT:
            self.kitchen.unlock_resource('cutting_board', self.id)
        elif self.current_task.action_type == ActionType.COOK:
            self.kitchen.unlock_resource('stove', self.id)

    # ----------------------------------------------------------------------
    # 3. Exécution des Tâches
    # ----------------------------------------------------------------------

    def _execute_task(self) -> bool:
        task = self.current_task
        if task.action_type == ActionType.PICKUP:
            return self._do_pickup(task.parameters['ingredient'])
        elif task.action_type == ActionType.CUT:
            return self._do_tool_action('cutting_board', 'cut', 20)
        elif task.action_type == ActionType.COOK:
            return self._do_tool_action('stove', 'cook', 40)
        elif task.action_type == ActionType.BRING_TO_ASSEMBLY:
            return self._do_bring_assembly()
        elif task.action_type == ActionType.DELIVER:
            return self._do_deliver(task.parameters['recipe'])
        return False

    def _do_pickup(self, ing_name) -> bool:
        if self.holding: return False

        base_name = ing_name.split('_')[0]
        target = self._get_smart_target(self.current_task)

        if not target:
            self.current_action = f"Cherche {base_name}..."
            return False

        if self._is_adjacent(target):
            # Création de l'ingrédient
            self.holding = Ingredient(base_name, "cru")
            self.current_action = f"Porte {base_name}"
            return True

        self._move_towards(target)
        self.current_action = f"Va chercher {base_name}"
        return False

    def _do_tool_action(self, tool_type, action_verb, duration) -> bool:
        """Gère Cut et Cook de manière dynamique"""
        if self.processing_action == action_verb:
            return False # En cours (timer géré dans update)

        if not self.holding: return False

        # 1. Trouver l'outil le plus proche
        # Note : On passe self.position pour avoir le plus proche
        target = self.kitchen.get_best_available_resource(tool_type, self.position)

        if not target:
            self.current_action = f"Attente {tool_type}..."
            return False

        # 2. Vérifier si on est à côté
        if self._is_adjacent(target):
            # Tenter de verrouiller (Optionnel selon ta Kitchen, mais mieux pour éviter conflit)
            # Ici on bypass le lock global strict pour permettre le multi-outil,
            # on fait confiance à l'intelligence spatiale

            tool = self.kitchen.grid[target[1]][target[0]]
            if isinstance(tool, Tool) and tool.use(self.holding):
                self.holding = None
                self.processing_action = action_verb
                self.target_tool_pos = target
                self.action_timer = duration
                self.current_action = f"{action_verb.capitalize()}..."
                return False

        # 3. Se déplacer
        self._move_towards(target)
        self.current_action = f"Va vers {tool_type}"
        return False

    def _do_bring_assembly(self) -> bool:
        if not self.holding: return False

        target = self.kitchen.get_best_available_resource('assembly_table', self.position)
        if not target: return False

        if self._is_adjacent(target):
            self.holding.position = list(target)
            self.kitchen.shared_assembly_table.append(self.holding)
            self.holding = None
            return True

        self._move_towards(target)
        self.current_action = "Vers assemblage"
        return False

    def _do_deliver(self, recipe) -> bool:
        # Logique simplifiée : Si pas de plat, aller chercher à l'assemblage
        if not self.holding:
            target = self.kitchen.get_best_available_resource('assembly_table', self.position)
            if not target: return False

            if self._is_adjacent(target):
                # Simule assemblage final
                items = [i for i in self.kitchen.shared_assembly_table]
                self.holding = Dish(recipe, items)
                self.kitchen.shared_assembly_table = []
                return False
            else:
                self._move_towards(target)
                self.current_action = "Récupère plat"
                return False

        # Si plat en main, aller au comptoir
        target = self.kitchen.get_best_available_resource('counter', self.position)
        # Fallback si pas de comptoir trouvé via get_best
        if not target: target = (3, 0)

        if self._is_adjacent(target):
            self.kitchen.place_dish_on_counter(recipe, target)
            self.holding = None
            return True

        self._move_towards(target)
        self.current_action = "Livraison"
        return False

    # ----------------------------------------------------------------------
    # 4. Helpers & Navigation (Le Vrai Pathfinding A*)
    # ----------------------------------------------------------------------

    def _get_smart_target(self, task) -> Optional[Tuple[int, int]]:
        """Wrappe la recherche de cible"""
        ttype = task.action_type
        if ttype == ActionType.PICKUP:
            name = task.parameters['ingredient'].split('_')[0]
            # Chercher dans la grille
            best = None
            min_d = 999
            for y in range(self.kitchen.height):
                for x in range(self.kitchen.width):
                    obj = self.kitchen.grid[y][x]
                    # Check Caisse (Ingredient) ou Item au sol
                    if isinstance(obj, Ingredient) and obj.name == name:
                        d = abs(x-self.position[0]) + abs(y-self.position[1])
                        if d < min_d:
                            min_d = d
                            best = (x, y)
            return best

        elif ttype == ActionType.CUT:
            return self.kitchen.get_best_available_resource('cutting_board', self.position)
        elif ttype == ActionType.COOK:
            return self.kitchen.get_best_available_resource('stove', self.position)
        elif ttype == ActionType.BRING_TO_ASSEMBLY:
            return self.kitchen.get_best_available_resource('assembly_table', self.position)
        elif ttype == ActionType.DELIVER:
            # Aller vers le comptoir de livraison
            return self.kitchen.get_best_available_resource('counter', self.position) or (3, 0)

        return None

    def _is_adjacent(self, target):
        return abs(self.position[0] - target[0]) + abs(self.position[1] - target[1]) == 1

    def _move_towards(self, target):
        """
        Algorithme A* complet et robuste (celui qui marchait).
        Évite les murs et les autres agents.
        """
        if not target: return
        start = tuple(self.position)
        goal = tuple(target)

        if start == goal: return

        # Obstacles = autres agents
        obstacles = set()
        others = self.communicator.get_other_agents_positions()
        for pos in others.values():
            obstacles.add(pos)

        def heuristic(a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])

        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from = {}
        g_score = {start: 0}

        found = False
        closest_node = start
        min_h = heuristic(start, goal)

        while open_set:
            current = heapq.heappop(open_set)[1]

            # Si on est adjacent au but (et que le but est un obstacle/outil), on s'arrête
            if heuristic(current, goal) == 1:
                found = True
                break

            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                neighbor = (current[0] + dx, current[1] + dy)

                # Vérif limites et murs
                if not self.kitchen.is_walkable(neighbor):
                    continue
                # Vérif agents
                if neighbor in obstacles:
                    continue

                new_g = g_score[current] + 1
                if neighbor not in g_score or new_g < g_score[neighbor]:
                    g_score[neighbor] = new_g
                    h = heuristic(neighbor, goal)
                    f = new_g + h
                    heapq.heappush(open_set, (f, neighbor))
                    came_from[neighbor] = current

                    if h < min_h:
                        min_h = h
                        closest_node = neighbor

        # Reconstruction du chemin
        # Si pas trouvé chemin complet, on va vers le noeud le plus proche (Best Effort)
        target_node = current if found else closest_node

        path = []
        while target_node in came_from:
            path.append(target_node)
            target_node = came_from[target_node]

        if path:
            next_step = path[-1] # Le premier pas après start
            self.position = list(next_step)
            self.total_distance_traveled += 1

            # Mise à jour direction visuelle
            dx = next_step[0] - start[0]
            dy = next_step[1] - start[1]
            if dx > 0: self.direction = "CD"
            elif dx < 0: self.direction = "CG"
            elif dy > 0: self.direction = "CF"
            else: self.direction = "CD"

    def get_performance_stats(self) -> Dict[str, Any]:
        return {
            'agent_id': self.id,
            'tasks_completed': self.tasks_completed,
            'distance_traveled': self.total_distance_traveled,
            'idle_time': self.idle_time,
            'current_action': self.current_action
        }

    def __repr__(self):
        return f"Agent{self.id}(pos={self.position}, action={self.current_action})"
