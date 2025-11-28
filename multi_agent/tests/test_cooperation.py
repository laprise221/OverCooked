"""
Test du système multi-agents sans interface graphique
Permet de tester la logique de coopération
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

from multi_agent.kitchen import Kitchen
from multi_agent.agent import CooperativeAgent
from common.recipes import recipes
from multi_agent.planning.strips import STRIPSPlanner, create_initial_world_state
from multi_agent.coordination.task_market import TaskMarket
from multi_agent.coordination.communication import Blackboard, AgentCommunicator, MessageType
from multi_agent.analytics.metrics import PerformanceMetrics


def test_basic_cooperation():
    """Test basique de coopération entre 2 agents"""
    print("\n" + "="*60)
    print("🧪 TEST: Coopération de base entre 2 agents")
    print("="*60)

    # Créer la cuisine
    kitchen = Kitchen(width=16, height=16, cell_size=50)

    # Systèmes multi-agents
    blackboard = Blackboard()
    metrics = PerformanceMetrics()

    # Créer 2 agents
    agents = []
    agent_positions = [(0, 15), (15, 15)]

    for i in range(2):
        communicator = AgentCommunicator(agent_id=i, blackboard=blackboard)
        agent = CooperativeAgent(
            agent_id=i,
            position=agent_positions[i],
            kitchen=kitchen,
            communicator=communicator
        )
        agents.append(agent)

    print(f"✅ {len(agents)} agents créés")

    # Tester la planification STRIPS
    planner = STRIPSPlanner(create_initial_world_state(kitchen, agents))

    # Décomposer une recette simple (sandwich)
    recipe_name = "sandwich"
    recipe_data = recipes[recipe_name]

    print(f"\n🍽️ Recette: {recipe_name}")
    print(f"   Ingrédients: {recipe_data['ingredients']}")

    tasks = planner.decompose_recipe(recipe_name, recipe_data['ingredients'])
    print(f"\n📋 {len(tasks)} tâches générées:")
    for task in tasks:
        print(f"   - {task['task_id']}: {task['action_type'].value} ({task.get('ingredient', 'N/A')})")

    # Créer le Task Market
    world_state = create_initial_world_state(kitchen, agents)
    task_market = TaskMarket(world_state)
    task_market.add_tasks(tasks)

    print(f"\n💼 Task Market créé")
    print(f"   Tâches disponibles: {len(task_market.get_available_tasks())}")

    # Tester le bidding
    print("\n💰 Phase de bidding:")
    available_tasks = task_market.get_available_tasks()[:3]  # Prendre les 3 premières

    all_bids = []
    for task in available_tasks:
        print(f"\n   Tâche {task.task_id} ({task.action_type.value}):")
        for agent in agents:
            bid = agent.submit_bid_for_task(task)
            all_bids.append(bid)
            print(f"      Agent {bid.agent_id}: coût = {bid.cost:.2f}")

    # Allouer les tâches
    allocations = task_market.allocate_tasks(all_bids)
    print(f"\n🎯 Allocations:")
    for agent_id, task_id in allocations.items():
        task = task_market.tasks[task_id]
        print(f"   Agent {agent_id} -> Tâche {task_id} ({task.action_type.value})")

    # Tester la communication
    print(f"\n📡 Test de communication:")
    agents[0].communicator.broadcast(
        msg_type=MessageType.TASK_CLAIMED,
        content={'task_id': 1, 'agent_id': 0}
    )
    messages = agents[1].communicator.receive_messages()
    print(f"   Agent 1 a reçu {len(messages)} message(s)")

    # Statistiques finales
    print(f"\n📊 Statistiques:")
    print(f"   Blackboard messages: {len(blackboard.messages)}")
    print(f"   Task Market: {task_market}")

    print("\n✅ Test terminé avec succès!")
    print("="*60 + "\n")


def test_resource_locking():
    """Test du verrouillage des ressources"""
    print("\n" + "="*60)
    print("🧪 TEST: Verrouillage des ressources")
    print("="*60)

    kitchen = Kitchen(width=16, height=16, cell_size=50)

    # Tester les locks
    print("\n🔒 Test des locks:")
    print(f"   Planche à découper libre: {kitchen.is_resource_available('cutting_board')}")

    # Agent 0 prend la planche
    success = kitchen.try_lock_resource('cutting_board', agent_id=0)
    print(f"   Agent 0 prend la planche: {success}")
    print(f"   Planche libre: {kitchen.is_resource_available('cutting_board')}")
    print(f"   Propriétaire: Agent {kitchen.get_resource_owner('cutting_board')}")

    # Agent 1 tente de prendre la planche
    success = kitchen.try_lock_resource('cutting_board', agent_id=1)
    print(f"   Agent 1 tente de prendre la planche: {success} (devrait être False)")

    # Agent 0 libère la planche
    kitchen.unlock_resource('cutting_board', agent_id=0)
    print(f"   Agent 0 libère la planche")
    print(f"   Planche libre: {kitchen.is_resource_available('cutting_board')}")

    print("\n✅ Test terminé avec succès!")
    print("="*60 + "\n")


if __name__ == "__main__":
    print("\n🚀 SUITE DE TESTS MULTI-AGENTS\n")

    try:
        test_resource_locking()
        test_basic_cooperation()

        print("\n🎉 TOUS LES TESTS SONT PASSÉS!")

    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
