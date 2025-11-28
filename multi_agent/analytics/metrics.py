import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

"""
Système de métriques pour évaluer la performance globale du système multi-agents

Métriques clés pour la coopération:
- Temps total de complétion des commandes
- Taux d'utilisation des ressources (cutting board, stove)
- Distance totale parcourue par tous les agents
- Temps d'inactivité des agents
- Throughput (commandes/minute)
"""

import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class OrderMetrics:
    """Métriques pour une commande individuelle"""
    order_id: int
    recipe_name: str
    start_time: float
    completion_time: Optional[float] = None
    agents_involved: List[int] = field(default_factory=list)
    tasks_count: int = 0

    @property
    def duration(self) -> float:
        """Durée de la commande en secondes"""
        if self.completion_time:
            return self.completion_time - self.start_time
        return time.time() - self.start_time

    @property
    def is_completed(self) -> bool:
        return self.completion_time is not None


@dataclass
class ResourceUtilization:
    """Suivi de l'utilisation d'une ressource"""
    resource_name: str
    total_time: float = 0.0
    busy_time: float = 0.0
    last_check_time: float = field(default_factory=time.time)
    is_busy: bool = False

    def update(self, currently_busy: bool):
        """Met à jour l'état d'utilisation"""
        current_time = time.time()
        elapsed = current_time - self.last_check_time

        self.total_time += elapsed
        if self.is_busy:
            self.busy_time += elapsed

        self.is_busy = currently_busy
        self.last_check_time = current_time

    @property
    def utilization_rate(self) -> float:
        """Taux d'utilisation (0.0 à 1.0)"""
        if self.total_time == 0:
            return 0.0
        return self.busy_time / self.total_time


class PerformanceMetrics:
    """
    Système de suivi des performances globales

    Objectif: Mesurer l'efficacité de la coopération entre agents
    """

    def __init__(self):
        self.start_time = time.time()
        self.orders: List[OrderMetrics] = []
        self.order_counter = 0

        # Métriques par agent
        self.agent_stats: Dict[int, Dict[str, Any]] = {}

        # Utilisation des ressources
        self.resource_utilization: Dict[str, ResourceUtilization] = {
            'cutting_board': ResourceUtilization('cutting_board'),
            'stove': ResourceUtilization('stove'),
            'assembly': ResourceUtilization('assembly'),
            'counter': ResourceUtilization('counter')
        }

        # Métriques globales
        self.total_tasks_completed = 0
        self.total_distance_traveled = 0
        self.total_idle_time = 0

    # ----------------------------------------------------------------------
    # Gestion des commandes
    # ----------------------------------------------------------------------

    def start_order(self, recipe_name: str, tasks_count: int) -> int:
        """Démarre le suivi d'une nouvelle commande"""
        order = OrderMetrics(
            order_id=self.order_counter,
            recipe_name=recipe_name,
            start_time=time.time(),
            tasks_count=tasks_count
        )
        self.orders.append(order)
        self.order_counter += 1
        return order.order_id

    def complete_order(self, order_id: int, agents_involved: List[int]):
        """Marque une commande comme terminée"""
        for order in self.orders:
            if order.order_id == order_id:
                order.completion_time = time.time()
                order.agents_involved = agents_involved
                print(f"📊 Commande {order_id} complétée en {order.duration:.2f}s par agents {agents_involved}")
                break

    def get_order_metrics(self, order_id: int) -> Optional[OrderMetrics]:
        """Récupère les métriques d'une commande"""
        for order in self.orders:
            if order.order_id == order_id:
                return order
        return None

    # ----------------------------------------------------------------------
    # Métriques par agent
    # ----------------------------------------------------------------------

    def update_agent_stats(self, agent_id: int, stats: Dict[str, Any]):
        """Met à jour les statistiques d'un agent"""
        if agent_id not in self.agent_stats:
            self.agent_stats[agent_id] = {}
        self.agent_stats[agent_id].update(stats)

    def get_agent_stats(self, agent_id: int) -> Dict[str, Any]:
        """Récupère les statistiques d'un agent"""
        return self.agent_stats.get(agent_id, {})

    # ----------------------------------------------------------------------
    # Utilisation des ressources
    # ----------------------------------------------------------------------

    def update_resource_usage(self, resource_locks: Dict[str, Optional[int]]):
        """Met à jour l'utilisation des ressources"""
        for resource_name, locked_by in resource_locks.items():
            if resource_name in self.resource_utilization:
                is_busy = locked_by is not None
                self.resource_utilization[resource_name].update(is_busy)

    def get_resource_utilization(self, resource_name: str) -> float:
        """Retourne le taux d'utilisation d'une ressource"""
        if resource_name in self.resource_utilization:
            return self.resource_utilization[resource_name].utilization_rate
        return 0.0

    # ----------------------------------------------------------------------
    # Métriques globales
    # ----------------------------------------------------------------------

    def get_average_completion_time(self) -> float:
        """Temps moyen de complétion des commandes"""
        completed_orders = [o for o in self.orders if o.is_completed]
        if not completed_orders:
            return 0.0
        return sum(o.duration for o in completed_orders) / len(completed_orders)

    def get_throughput(self) -> float:
        """Nombre de commandes complétées par minute"""
        elapsed_time = time.time() - self.start_time
        if elapsed_time == 0:
            return 0.0
        completed_count = sum(1 for o in self.orders if o.is_completed)
        return (completed_count / elapsed_time) * 60  # Par minute

    def get_total_distance_traveled(self) -> int:
        """Distance totale parcourue par tous les agents"""
        return sum(stats.get('distance_traveled', 0) for stats in self.agent_stats.values())

    def get_total_idle_time(self) -> int:
        """Temps d'inactivité total de tous les agents"""
        return sum(stats.get('idle_time', 0) for stats in self.agent_stats.values())

    def get_agent_workload_distribution(self) -> Dict[int, int]:
        """Distribution de la charge de travail entre agents"""
        return {
            agent_id: stats.get('tasks_completed', 0)
            for agent_id, stats in self.agent_stats.items()
        }

    # ----------------------------------------------------------------------
    # Rapport de performance
    # ----------------------------------------------------------------------

    def generate_report(self) -> Dict[str, Any]:
        """Génère un rapport complet de performance"""
        elapsed_time = time.time() - self.start_time
        completed_orders = [o for o in self.orders if o.is_completed]
        pending_orders = [o for o in self.orders if not o.is_completed]

        report = {
            'session': {
                'duration': elapsed_time,
                'total_orders': len(self.orders),
                'completed_orders': len(completed_orders),
                'pending_orders': len(pending_orders)
            },
            'performance': {
                'average_completion_time': self.get_average_completion_time(),
                'throughput': self.get_throughput(),
                'total_distance': self.get_total_distance_traveled(),
                'total_idle_time': self.get_total_idle_time()
            },
            'resources': {
                resource_name: {
                    'utilization_rate': util.utilization_rate,
                    'busy_time': util.busy_time,
                    'total_time': util.total_time
                }
                for resource_name, util in self.resource_utilization.items()
            },
            'agents': {
                agent_id: {
                    'tasks_completed': stats.get('tasks_completed', 0),
                    'distance_traveled': stats.get('distance_traveled', 0),
                    'idle_time': stats.get('idle_time', 0),
                    'current_action': stats.get('current_action', 'unknown')
                }
                for agent_id, stats in self.agent_stats.items()
            },
            'workload_balance': self.get_workload_balance_score()
        }

        return report

    def get_workload_balance_score(self) -> float:
        """
        Score d'équilibrage de charge (0.0 à 1.0)
        1.0 = parfaitement équilibré, 0.0 = très déséquilibré
        """
        workload = self.get_agent_workload_distribution()
        if not workload or len(workload) < 2:
            return 1.0

        tasks_list = list(workload.values())
        if sum(tasks_list) == 0:
            return 1.0

        avg_tasks = sum(tasks_list) / len(tasks_list)
        variance = sum((t - avg_tasks) ** 2 for t in tasks_list) / len(tasks_list)
        std_dev = variance ** 0.5

        # Normaliser: écart-type faible = bon équilibrage
        if avg_tasks == 0:
            return 1.0
        normalized_std = std_dev / avg_tasks
        balance_score = max(0.0, 1.0 - normalized_std)

        return balance_score

    def print_summary(self):
        """Affiche un résumé des performances"""
        report = self.generate_report()

        print("\n" + "="*60)
        print("📊 RAPPORT DE PERFORMANCE MULTI-AGENTS")
        print("="*60)

        print(f"\n⏱️  SESSION:")
        print(f"  Durée: {report['session']['duration']:.1f}s")
        print(f"  Commandes: {report['session']['completed_orders']}/{report['session']['total_orders']} complétées")

        print(f"\n🎯 PERFORMANCE GLOBALE:")
        print(f"  Temps moyen/commande: {report['performance']['average_completion_time']:.2f}s")
        print(f"  Throughput: {report['performance']['throughput']:.2f} commandes/min")
        print(f"  Distance totale: {report['performance']['total_distance']} cases")
        print(f"  Temps d'inactivité total: {report['performance']['total_idle_time']} frames")

        print(f"\n🔧 UTILISATION DES RESSOURCES:")
        for resource, data in report['resources'].items():
            print(f"  {resource}: {data['utilization_rate']*100:.1f}% ({data['busy_time']:.1f}s/{data['total_time']:.1f}s)")

        print(f"\n🤖 STATISTIQUES PAR AGENT:")
        for agent_id, stats in report['agents'].items():
            print(f"  Agent {agent_id}:")
            print(f"    Tâches: {stats['tasks_completed']}")
            print(f"    Distance: {stats['distance_traveled']} cases")
            print(f"    Inactivité: {stats['idle_time']} frames")

        print(f"\n⚖️  ÉQUILIBRAGE DE CHARGE: {report['workload_balance']*100:.1f}%")
        print("="*60 + "\n")

    def export_to_csv(self, filename: str = "metrics.csv"):
        """Exporte les métriques au format CSV"""
        import csv

        report = self.generate_report()

        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)

            # En-tête
            writer.writerow(['Metric', 'Value'])

            # Session
            writer.writerow(['Duration (s)', report['session']['duration']])
            writer.writerow(['Total Orders', report['session']['total_orders']])
            writer.writerow(['Completed Orders', report['session']['completed_orders']])

            # Performance
            writer.writerow(['Avg Completion Time (s)', report['performance']['average_completion_time']])
            writer.writerow(['Throughput (orders/min)', report['performance']['throughput']])
            writer.writerow(['Total Distance', report['performance']['total_distance']])
            writer.writerow(['Total Idle Time', report['performance']['total_idle_time']])

            # Resources
            for resource, data in report['resources'].items():
                writer.writerow([f'{resource} Utilization', f"{data['utilization_rate']*100:.1f}%"])

            # Agents
            for agent_id, stats in report['agents'].items():
                writer.writerow([f'Agent {agent_id} Tasks', stats['tasks_completed']])
                writer.writerow([f'Agent {agent_id} Distance', stats['distance_traveled']])

            writer.writerow(['Workload Balance', f"{report['workload_balance']*100:.1f}%"])

        print(f"✅ Métriques exportées vers {filename}")
