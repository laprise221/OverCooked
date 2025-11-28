"""Test simulation complète sans interface graphique"""

import sys
import os

# Désactiver pygame display
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

# Ajouter la racine du projet pour les imports absolus
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from multi_agent.kitchen import Kitchen
from multi_agent.agent import CooperativeAgent
from common.recipes import recipes
from multi_agent.planning.strips import STRIPSPlanner, create_initial_world_state
from multi_agent.coordination.task_market import TaskMarket
from multi_agent.coordination.communication import Blackboard, AgentCommunicator
from multi_agent.analytics.metrics import PerformanceMetrics

def simulate_order(recipe_name, max_iterations=1500):
    """Simule complètement une commande"""
    print(f"\n{'='*60}")
    print(f"🍽️ SIMULATION: {recipe_name.upper()}")
    print(f"{'='*60}")

    # Setup
    kitchen = Kitchen(width=16, height=16, cell_size=50)
    blackboard = Blackboard()
    metrics = PerformanceMetrics()

    # Agents
    agents = []
    for i in range(2):
        communicator = AgentCommunicator(agent_id=i, blackboard=blackboard)
        agent = CooperativeAgent(
            agent_id=i,
            position=[(0, 15), (15, 15)][i],
            kitchen=kitchen,
            communicator=communicator
        )
        agents.append(agent)

    # Planning
    planner = STRIPSPlanner(create_initial_world_state(kitchen, agents))
    recipe_data = recipes[recipe_name]
    tasks = planner.decompose_recipe(recipe_name, recipe_data['ingredients'])

    print(f"📋 {len(tasks)} tâches planifiées")

    # Task Market
    world_state = create_initial_world_state(kitchen, agents)
    task_market = TaskMarket(world_state)
    task_market.add_tasks(tasks)

    order_id = metrics.start_order(recipe_name, len(tasks))

    # Boucle de simulation
    iteration = 0
    while task_market.has_pending_tasks() and iteration < max_iterations:
        iteration += 1

        # Allocation - gérer plusieurs tâches à la fois
        available_tasks = task_market.get_available_tasks()
        available_agents = [a for a in agents if a.current_task is None]

        if available_tasks and available_agents:
            # Permettre l'allocation de plusieurs tâches (1 par agent disponible)
            all_bids = []
            tasks_with_candidates = 0
            sorted_tasks = sorted(
                available_tasks,
                key=lambda t: (t.priority, t.task_id)
            )
            for task in sorted_tasks:
                task_has_bid = False
                for agent in available_agents:
                    bid = agent.submit_bid_for_task(task)
                    if bid.cost < float('inf'):
                        all_bids.append(bid)
                        task_has_bid = True
                if task_has_bid:
                    tasks_with_candidates += 1
                if tasks_with_candidates >= len(available_agents):
                    break

            if all_bids:
                allocations = task_market.allocate_tasks(all_bids)
                for agent_id, task_id in allocations.items():
                    agents[agent_id].assign_task(task_market.tasks[task_id])
                    task_market.start_task(task_id)

        # Update agents (appeler plusieurs fois si timer actif)
        for agent in agents:
            # Si l'agent a un timer, continuer à update jusqu'à ce qu'il termine
            for _ in range(20):  # Max 20 updates par iteration pour gérer les timers
                agent.update(task_market)
                if agent.action_timer == 0 and agent.current_task is None:
                    break

        # Update metrics
        for agent in agents:
            metrics.update_agent_stats(agent.id, agent.get_performance_stats())
        metrics.update_resource_usage(kitchen.resource_locks)

    # Completion
    stats = task_market.get_completion_stats()
    agents_involved = [a.id for a in agents if a.tasks_completed > 0]
    metrics.complete_order(order_id, agents_involved)

    print(f"\n✅ COMMANDE TERMINÉE!")
    print(f"   Iterations: {iteration}")
    print(f"   Tâches complétées: {stats['completed']}/{stats['total']}")
    print(f"   Agent 0: {agents[0].tasks_completed} tâches, {agents[0].total_distance_traveled} cases")
    print(f"   Agent 1: {agents[1].tasks_completed} tâches, {agents[1].total_distance_traveled} cases")

    return metrics, stats['completed'] == stats['total']

# Tests
if __name__ == "__main__":
    print("\n🚀 SIMULATION MULTI-AGENTS - CONDITIONS RÉELLES\n")

    results = {}

    for recipe in ["sandwich", "burger", "pizza"]:
        try:
            metrics, success = simulate_order(recipe)
            results[recipe] = {"success": success, "metrics": metrics}

            if not success:
                print(f"❌ ÉCHEC: {recipe}")
        except Exception as e:
            print(f"❌ ERREUR {recipe}: {e}")
            import traceback
            traceback.print_exc()
            results[recipe] = {"success": False, "error": str(e)}

    # Résumé
    print(f"\n{'='*60}")
    print("📊 RÉSUMÉ FINAL")
    print(f"{'='*60}")

    for recipe, data in results.items():
        status = "✅ SUCCÈS" if data.get("success") else "❌ ÉCHEC"
        print(f"{recipe.capitalize():15} : {status}")

        if data.get("success") and "metrics" in data:
            report = data["metrics"].generate_report()
            print(f"                  Temps moyen: {report['performance']['average_completion_time']:.1f}s")
            print(f"                  Équilibrage: {report['workload_balance']*100:.1f}%")

    print(f"{'='*60}\n")

    # Success?
    all_success = all(r.get("success", False) for r in results.values())
    if all_success:
        print("🎉 TOUS LES TESTS RÉUSSIS!")
    else:
        print("⚠️  CERTAINS TESTS ONT ÉCHOUÉ")
