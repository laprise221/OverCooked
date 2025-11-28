import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

"""
Task Market - Système d'allocation dynamique des tâches pour multi-agents coopératifs

Principe du Task Market:
- Pool partagé de tâches disponibles
- Chaque agent évalue le coût de chaque tâche (bidding)
- L'agent avec le coût le plus faible obtient la tâche
- Prévention des conflits via réservation de ressources

Objectif: Maximiser la performance globale du système (non compétitif)
"""

from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import time
from multi_agent.planning.strips import Action, ActionType, WorldState


class TaskStatus(Enum):
    """Statut d'une tâche dans le market"""
    AVAILABLE = "available"      # Disponible pour allocation
    CLAIMED = "claimed"          # Réservée par un agent
    IN_PROGRESS = "in_progress"  # En cours d'exécution
    COMPLETED = "completed"      # Terminée
    BLOCKED = "blocked"          # Bloquée (dépendances non satisfaites)


@dataclass
class Task:
    """
    Tâche atomique dans le task market
    """
    task_id: int
    action_type: ActionType
    parameters: Dict[str, any]
    dependencies: List[int]  # IDs des tâches dont celle-ci dépend
    estimated_duration: float
    priority: int  # Plus faible = plus prioritaire
    status: TaskStatus = TaskStatus.AVAILABLE
    assigned_agent: Optional[int] = None
    start_time: Optional[float] = None
    completion_time: Optional[float] = None

    def is_ready(self, completed_tasks: Set[int]) -> bool:
        """Vérifie si toutes les dépendances sont satisfaites"""
        return all(dep in completed_tasks for dep in self.dependencies)

    def __repr__(self) -> str:
        return f"Task(id={self.task_id}, type={self.action_type.value}, status={self.status.value})"


@dataclass
class Bid:
    """
    Enchère d'un agent pour une tâche
    """
    agent_id: int
    task_id: int
    cost: float  # Coût estimé (distance + durée)
    timestamp: float

    def __lt__(self, other):
        """Pour tri par coût croissant"""
        return self.cost < other.cost


class TaskMarket:
    """
    Marché de tâches pour allocation dynamique entre agents coopératifs

    Algorithme:
    1. Les agents annoncent leur disponibilité
    2. Pour chaque tâche disponible, les agents soumettent des enchères (bids)
    3. L'agent avec le coût le plus faible obtient la tâche
    4. Les ressources sont réservées pour éviter les conflits
    """

    def __init__(self, world_state: WorldState):
        self.world_state = world_state
        self.tasks: Dict[int, Task] = {}
        self.completed_tasks: Set[int] = set()
        self.resource_locks: Dict[str, Optional[int]] = {
            'cutting_board': None,
            'stove': None,
            'assembly': None
        }

    def add_tasks(self, tasks: List[Dict[str, any]]):
        """Ajoute des tâches au market"""
        for task_data in tasks:
            task = Task(
                task_id=task_data['task_id'],
                action_type=task_data['action_type'],
                parameters={'ingredient': task_data.get('ingredient'),
                          'recipe': task_data.get('recipe'),
                          'ingredients': task_data.get('ingredients')},
                dependencies=task_data.get('dependencies', []),
                estimated_duration=task_data['estimated_duration'],
                priority=task_data['priority']
            )
            self.tasks[task.task_id] = task

    def get_available_tasks(self) -> List[Task]:
        """
        Retourne les tâches disponibles pour allocation
        Une tâche est disponible si:
        - Son statut est AVAILABLE
        - Ses dépendances sont satisfaites
        - Les ressources nécessaires sont disponibles
        """
        available = []
        for task in self.tasks.values():
            if task.status == TaskStatus.AVAILABLE and task.is_ready(self.completed_tasks):
                # Vérifier si les ressources nécessaires sont disponibles
                if self._check_resource_availability(task):
                    available.append(task)
                else:
                    task.status = TaskStatus.BLOCKED
        return available

    def _check_resource_availability(self, task: Task) -> bool:
        """Vérifie si les ressources nécessaires pour une tâche sont disponibles"""
        if task.action_type == ActionType.CUT:
            return self.resource_locks['cutting_board'] is None
        elif task.action_type == ActionType.COOK:
            return self.resource_locks['stove'] is None
        elif task.action_type in [ActionType.BRING_TO_ASSEMBLY, ActionType.DELIVER]:
            return self.resource_locks['assembly'] is None
        return True  # PICKUP et WAIT n'ont pas besoin de ressources spécifiques

    def submit_bid(self, agent_id: int, task_id: int, cost: float) -> Bid:
        """Un agent soumet une enchère pour une tâche"""
        return Bid(
            agent_id=agent_id,
            task_id=task_id,
            cost=cost,
            timestamp=time.time()
        )

    def allocate_tasks(self, bids: List[Bid]) -> Dict[int, int]:
        """
        Alloue les tâches aux agents selon les enchères (bids)
        Retourne un dictionnaire {agent_id: task_id}

        Algorithme:
        1. Grouper les enchères par tâche
        2. Pour chaque tâche, sélectionner l'agent avec le coût le plus faible
        3. Réserver les ressources nécessaires
        """
        allocations = {}
        tasks_by_bid: Dict[int, List[Bid]] = {}

        # Grouper les enchères par tâche (FILTRER cost=inf)
        for bid in bids:
            # IMPORTANT: Ignorer les bids impossibles (cost infini)
            if bid.cost == float('inf'):
                continue
            if bid.task_id not in tasks_by_bid:
                tasks_by_bid[bid.task_id] = []
            tasks_by_bid[bid.task_id].append(bid)

        # Trier les tâches par priorité
        sorted_tasks = sorted(tasks_by_bid.keys(),
                            key=lambda tid: self.tasks[tid].priority)

        # Allouer chaque tâche à l'agent avec le coût le plus faible
        allocated_agents = set()
        for task_id in sorted_tasks:
            task_bids = sorted(tasks_by_bid[task_id])  # Tri par coût croissant

            # Trouver le premier agent disponible
            for bid in task_bids:
                if bid.agent_id not in allocated_agents:
                    # Allouer la tâche
                    allocations[bid.agent_id] = task_id
                    allocated_agents.add(bid.agent_id)

                    # Réserver la ressource
                    self._lock_resource(task_id, bid.agent_id)

                    # Mettre à jour le statut de la tâche
                    self.tasks[task_id].status = TaskStatus.CLAIMED
                    self.tasks[task_id].assigned_agent = bid.agent_id
                    break

        return allocations

    def _lock_resource(self, task_id: int, agent_id: int):
        """Réserve une ressource pour un agent"""
        task = self.tasks[task_id]
        if task.action_type == ActionType.CUT:
            self.resource_locks['cutting_board'] = agent_id
        elif task.action_type == ActionType.COOK:
            self.resource_locks['stove'] = agent_id
        elif task.action_type in [ActionType.BRING_TO_ASSEMBLY, ActionType.DELIVER]:
            self.resource_locks['assembly'] = agent_id

    def _unlock_resource(self, task_id: int):
        """Libère une ressource après utilisation"""
        task = self.tasks[task_id]
        if task.action_type == ActionType.CUT:
            self.resource_locks['cutting_board'] = None
        elif task.action_type == ActionType.COOK:
            self.resource_locks['stove'] = None
        elif task.action_type in [ActionType.BRING_TO_ASSEMBLY, ActionType.DELIVER]:
            self.resource_locks['assembly'] = None

    def start_task(self, task_id: int):
        """Marque une tâche comme commencée"""
        if task_id in self.tasks:
            self.tasks[task_id].status = TaskStatus.IN_PROGRESS
            self.tasks[task_id].start_time = time.time()

    def complete_task(self, task_id: int):
        """Marque une tâche comme terminée et libère les ressources"""
        if task_id in self.tasks:
            self.tasks[task_id].status = TaskStatus.COMPLETED
            self.tasks[task_id].completion_time = time.time()
            self.completed_tasks.add(task_id)

            # Libérer les ressources
            self._unlock_resource(task_id)

            # Débloquer les tâches dépendantes
            self._unblock_dependent_tasks(task_id)

    def _unblock_dependent_tasks(self, completed_task_id: int):
        """Débloque les tâches qui dépendaient de la tâche complétée"""
        for task in self.tasks.values():
            if task.status == TaskStatus.BLOCKED and task.is_ready(self.completed_tasks):
                task.status = TaskStatus.AVAILABLE

    def cancel_task(self, task_id: int):
        """Annule une tâche et libère les ressources"""
        if task_id in self.tasks:
            self.tasks[task_id].status = TaskStatus.AVAILABLE
            self.tasks[task_id].assigned_agent = None
            self._unlock_resource(task_id)

    def get_task_status(self, task_id: int) -> Optional[TaskStatus]:
        """Retourne le statut d'une tâche"""
        return self.tasks[task_id].status if task_id in self.tasks else None

    def get_agent_task(self, agent_id: int) -> Optional[Task]:
        """Retourne la tâche actuellement assignée à un agent"""
        for task in self.tasks.values():
            if task.assigned_agent == agent_id and task.status in [TaskStatus.CLAIMED, TaskStatus.IN_PROGRESS]:
                return task
        return None

    def get_completion_stats(self) -> Dict[str, any]:
        """Retourne des statistiques sur l'état d'avancement"""
        total = len(self.tasks)
        completed = len(self.completed_tasks)
        in_progress = sum(1 for t in self.tasks.values() if t.status == TaskStatus.IN_PROGRESS)
        available = sum(1 for t in self.tasks.values() if t.status == TaskStatus.AVAILABLE)
        blocked = sum(1 for t in self.tasks.values() if t.status == TaskStatus.BLOCKED)

        return {
            'total': total,
            'completed': completed,
            'in_progress': in_progress,
            'available': available,
            'blocked': blocked,
            'progress_percent': (completed / total * 100) if total > 0 else 0
        }

    def estimate_remaining_time(self) -> float:
        """Estime le temps restant pour terminer toutes les tâches"""
        remaining_tasks = [t for t in self.tasks.values() if t.status != TaskStatus.COMPLETED]
        if not remaining_tasks:
            return 0.0

        # Approximation: somme des durées estimées des tâches restantes
        # divisée par le nombre d'agents (parallélisation)
        total_duration = sum(t.estimated_duration for t in remaining_tasks)
        # Supposons 2 agents en parallèle
        return total_duration / 2

    def get_resource_utilization(self) -> Dict[str, float]:
        """
        Calcule le taux d'utilisation des ressources
        Utile pour optimiser la performance globale
        """
        utilization = {}
        for resource, locked_by in self.resource_locks.items():
            utilization[resource] = 1.0 if locked_by is not None else 0.0
        return utilization

    def has_pending_tasks(self) -> bool:
        """Vérifie s'il reste des tâches à effectuer"""
        return any(t.status != TaskStatus.COMPLETED for t in self.tasks.values())

    def __repr__(self) -> str:
        stats = self.get_completion_stats()
        return f"TaskMarket(total={stats['total']}, completed={stats['completed']}, " \
               f"in_progress={stats['in_progress']}, available={stats['available']})"
