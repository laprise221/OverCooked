import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

"""
Module de planification STRIPS pour système multi-agents coopératif
Basé sur les cours IntroPlanning.pdf et DeductiveAgents.pdf

STRIPS (Stanford Research Institute Problem Solver):
- États: Ensemble de prédicats logiques
- Actions: Préconditions, Delete List, Add List
- Planification: Recherche d'une séquence d'actions menant au but
"""

from typing import Dict, Set, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class ActionType(Enum):
    """Types d'actions atomiques dans la cuisine"""
    PICKUP = "pickup"
    CUT = "cut"
    COOK = "cook"
    BRING_TO_ASSEMBLY = "bring_to_assembly"
    DELIVER = "deliver"
    WAIT = "wait"  # Attendre libération d'une ressource


@dataclass
class WorldState:
    """
    Représentation symbolique de l'état du monde
    Conforme à l'approche STRIPS: ensemble de prédicats
    """
    # Position des agents
    agent_positions: Dict[int, Tuple[int, int]] = field(default_factory=dict)

    # Inventaire des agents (ce qu'ils portent)
    agent_inventory: Dict[int, Optional[str]] = field(default_factory=dict)

    # État des ingrédients (raw, cut, cooked)
    ingredient_states: Dict[str, str] = field(default_factory=dict)

    # Disponibilité des stations (True = libre, False = occupée)
    station_availability: Dict[str, bool] = field(default_factory=dict)

    # Ingrédients sur la table d'assemblage
    assembly_table: Set[str] = field(default_factory=set)

    # Commandes en cours
    pending_orders: List[str] = field(default_factory=list)

    # Commandes complétées
    completed_orders: List[str] = field(default_factory=list)

    def copy(self) -> 'WorldState':
        """Crée une copie profonde de l'état"""
        return WorldState(
            agent_positions=self.agent_positions.copy(),
            agent_inventory=self.agent_inventory.copy(),
            ingredient_states=self.ingredient_states.copy(),
            station_availability=self.station_availability.copy(),
            assembly_table=self.assembly_table.copy(),
            pending_orders=self.pending_orders.copy(),
            completed_orders=self.completed_orders.copy()
        )

    def satisfies(self, conditions: Dict[str, Any]) -> bool:
        """Vérifie si l'état satisfait un ensemble de conditions"""
        for key, value in conditions.items():
            if key.startswith("agent_has_"):
                agent_id = int(key.split("_")[-1])
                if self.agent_inventory.get(agent_id) != value:
                    return False
            elif key.startswith("station_"):
                station = key.replace("station_", "")
                if self.station_availability.get(station) != value:
                    return False
            elif key.startswith("ingredient_state_"):
                ingredient = key.replace("ingredient_state_", "")
                if self.ingredient_states.get(ingredient) != value:
                    return False
            elif key == "assembly_has":
                if isinstance(value, (list, tuple, set)):
                    if not all(item in self.assembly_table for item in value):
                        return False
                else:
                    if value not in self.assembly_table:
                        return False
        return True


@dataclass
class Action:
    """
    Représentation STRIPS d'une action

    Selon le cours:
    - name: Nom de l'action avec paramètres
    - preconditions: Conditions nécessaires pour exécuter l'action
    - delete_list: Prédicats qui deviennent faux après l'action
    - add_list: Prédicats qui deviennent vrais après l'action
    """
    name: str
    action_type: ActionType
    agent_id: int
    parameters: Dict[str, Any]
    preconditions: Dict[str, Any]
    delete_list: Dict[str, Any]
    add_list: Dict[str, Any]
    estimated_duration: float  # En secondes

    def is_applicable(self, state: WorldState) -> bool:
        """Vérifie si l'action peut être exécutée dans l'état donné"""
        return state.satisfies(self.preconditions)

    def apply(self, state: WorldState) -> WorldState:
        """
        Applique l'action à l'état et retourne le nouvel état
        Implémente la sémantique STRIPS: (State - DeleteList) ∪ AddList
        """
        new_state = state.copy()

        # Delete List: Retirer les prédicats
        for key, value in self.delete_list.items():
            if key.startswith("agent_has_"):
                agent_id = int(key.split("_")[-1])
                new_state.agent_inventory[agent_id] = None
            elif key.startswith("station_"):
                station = key.replace("station_", "")
                new_state.station_availability[station] = False
            elif key.startswith("ingredient_state_"):
                ingredient = key.replace("ingredient_state_", "")
                if ingredient in new_state.ingredient_states:
                    del new_state.ingredient_states[ingredient]
            elif key == "assembly_has":
                items = value if isinstance(value, (list, tuple, set)) else [value]
                for item in items:
                    new_state.assembly_table.discard(item)

        # Add List: Ajouter les nouveaux prédicats
        for key, value in self.add_list.items():
            if key.startswith("agent_has_"):
                agent_id = int(key.split("_")[-1])
                new_state.agent_inventory[agent_id] = value
            elif key.startswith("station_"):
                station = key.replace("station_", "")
                new_state.station_availability[station] = value
            elif key.startswith("ingredient_state_"):
                ingredient = key.replace("ingredient_state_", "")
                new_state.ingredient_states[ingredient] = value
            elif key == "assembly_has":
                items = value if isinstance(value, (list, tuple, set)) else [value]
                for item in items:
                    new_state.assembly_table.add(item)
            elif key == "order_completed":
                new_state.completed_orders.append(value)
                if value in new_state.pending_orders:
                    new_state.pending_orders.remove(value)

        return new_state

    def __repr__(self) -> str:
        return f"Action({self.name}, agent={self.agent_id}, params={self.parameters})"


class STRIPSPlanner:
    """
    Planificateur STRIPS pour générer des plans d'actions
    Utilise une approche de planification en avant (forward search)
    """

    def __init__(self, initial_state: WorldState):
        self.initial_state = initial_state

    def decompose_recipe(self, recipe_name: str, recipe_ingredients: List[str]) -> List[Dict[str, Any]]:
        """
        Décompose une recette en tâches atomiques indépendantes
        Retourne une liste de tâches qui peuvent être allouées dynamiquement
        """
        from common.recipes import get_ingredient_config

        tasks = []
        task_id = 0

        for ingredient in recipe_ingredients:
            base_ingredient = ingredient.split('_')[0]
            required_state = ingredient.split('_')[1] if '_' in ingredient else 'raw'

            # Tâche 1: Pickup de l'ingrédient
            pickup_task = {
                'task_id': task_id,
                'action_type': ActionType.PICKUP,
                'ingredient': base_ingredient,
                'dependencies': [],
                'estimated_duration': 2.0,
                'priority': 1
            }
            tasks.append(pickup_task)
            pickup_task_id = task_id
            task_id += 1

            # Tâche 2: Processing si nécessaire (cut ou cook)
            config = get_ingredient_config(base_ingredient)
            if required_state == 'coupe' and config.get('needs_cutting', False):
                cut_task = {
                    'task_id': task_id,
                    'action_type': ActionType.CUT,
                    'ingredient': base_ingredient,
                    'dependencies': [pickup_task_id],
                    'estimated_duration': 2.0,
                    'priority': 2
                }
                tasks.append(cut_task)
                process_task_id = task_id
                task_id += 1
            elif required_state == 'cuit' and config.get('needs_cooking', False):
                cook_task = {
                    'task_id': task_id,
                    'action_type': ActionType.COOK,
                    'ingredient': base_ingredient,
                    'dependencies': [pickup_task_id],
                    'estimated_duration': 3.0,
                    'priority': 2
                }
                tasks.append(cook_task)
                process_task_id = task_id
                task_id += 1
            else:
                process_task_id = pickup_task_id

            # Tâche 3: Amener à la table d'assemblage
            bring_task = {
                'task_id': task_id,
                'action_type': ActionType.BRING_TO_ASSEMBLY,
                'ingredient': base_ingredient + '_' + required_state,
                'dependencies': [process_task_id],
                'estimated_duration': 2.0,
                'priority': 3
            }
            tasks.append(bring_task)
            task_id += 1

        # Tâche finale: Livraison
        delivery_task = {
            'task_id': task_id,
            'action_type': ActionType.DELIVER,
            'recipe': recipe_name,
            'ingredients': recipe_ingredients,
            'dependencies': [t['task_id'] for t in tasks if t['action_type'] == ActionType.BRING_TO_ASSEMBLY],
            'estimated_duration': 2.0,
            'priority': 4
        }
        tasks.append(delivery_task)

        return tasks

    def create_action(self, task: Dict[str, Any], agent_id: int) -> Action:
        """
        Crée une action STRIPS à partir d'une tâche et d'un agent
        """
        action_type = task['action_type']

        if action_type == ActionType.PICKUP:
            ingredient = task['ingredient']
            return Action(
                name=f"PICKUP({ingredient}, agent{agent_id})",
                action_type=ActionType.PICKUP,
                agent_id=agent_id,
                parameters={'ingredient': ingredient},
                preconditions={
                    f'agent_has_{agent_id}': None,  # Agent n'a rien dans les mains
                },
                delete_list={},
                add_list={
                    f'agent_has_{agent_id}': ingredient,
                },
                estimated_duration=task['estimated_duration']
            )

        elif action_type == ActionType.CUT:
            ingredient = task['ingredient']
            return Action(
                name=f"CUT({ingredient}, agent{agent_id})",
                action_type=ActionType.CUT,
                agent_id=agent_id,
                parameters={'ingredient': ingredient},
                preconditions={
                    f'agent_has_{agent_id}': ingredient,
                    'station_cutting_board': True,  # Station libre
                    f'ingredient_state_{ingredient}': 'raw'
                },
                delete_list={
                    f'ingredient_state_{ingredient}': 'raw',
                    'station_cutting_board': True
                },
                add_list={
                    f'ingredient_state_{ingredient}': 'cut',
                    'station_cutting_board': True  # Libérer après usage
                },
                estimated_duration=task['estimated_duration']
            )

        elif action_type == ActionType.COOK:
            ingredient = task['ingredient']
            return Action(
                name=f"COOK({ingredient}, agent{agent_id})",
                action_type=ActionType.COOK,
                agent_id=agent_id,
                parameters={'ingredient': ingredient},
                preconditions={
                    f'agent_has_{agent_id}': ingredient,
                    'station_stove': True,  # Station libre
                    f'ingredient_state_{ingredient}': 'raw'
                },
                delete_list={
                    f'ingredient_state_{ingredient}': 'raw',
                    'station_stove': True
                },
                add_list={
                    f'ingredient_state_{ingredient}': 'cooked',
                    'station_stove': True  # Libérer après usage
                },
                estimated_duration=task['estimated_duration']
            )

        elif action_type == ActionType.BRING_TO_ASSEMBLY:
            ingredient = task['ingredient']
            return Action(
                name=f"BRING_TO_ASSEMBLY({ingredient}, agent{agent_id})",
                action_type=ActionType.BRING_TO_ASSEMBLY,
                agent_id=agent_id,
                parameters={'ingredient': ingredient},
                preconditions={
                    f'agent_has_{agent_id}': ingredient,
                },
                delete_list={
                    f'agent_has_{agent_id}': ingredient,
                },
                add_list={
                    'assembly_has': ingredient,
                },
                estimated_duration=task['estimated_duration']
            )

        elif action_type == ActionType.DELIVER:
            recipe = task['recipe']
            return Action(
                name=f"DELIVER({recipe}, agent{agent_id})",
                action_type=ActionType.DELIVER,
                agent_id=agent_id,
                parameters={'recipe': recipe, 'ingredients': task['ingredients']},
                preconditions={
                    'assembly_has': task['ingredients']
                },
                delete_list={
                    'assembly_has': task['ingredients']
                },
                add_list={
                    'order_completed': recipe
                },
                estimated_duration=task['estimated_duration']
            )

        else:
            raise ValueError(f"Unknown action type: {action_type}")

    def estimate_action_cost(self, action: Action, agent_position: Tuple[int, int],
                            target_position: Tuple[int, int]) -> float:
        """
        Estime le coût d'une action pour un agent
        Coût = distance Manhattan + durée estimée de l'action
        """
        distance = abs(agent_position[0] - target_position[0]) + \
                   abs(agent_position[1] - target_position[1])

        # Coût temporel = déplacement (0.1s par case) + action
        travel_time = distance * 0.1
        total_cost = travel_time + action.estimated_duration

        return total_cost


def create_initial_world_state(kitchen, agents: List[Any]) -> WorldState:
    """
    Crée l'état initial du monde à partir de la cuisine et des agents
    """
    state = WorldState()

    # Positions des agents
    for i, agent in enumerate(agents):
        agent_id = agent.id if hasattr(agent, 'id') else i
        position = tuple(agent.position) if hasattr(agent, 'position') else (0, 0)
        state.agent_positions[agent_id] = position
        state.agent_inventory[agent_id] = None

    # Disponibilité des stations
    state.station_availability['cutting_board'] = True
    state.station_availability['stove'] = True
    state.station_availability['assembly'] = True
    state.station_availability['counter'] = True

    # Table d'assemblage vide
    state.assembly_table = set()

    return state
