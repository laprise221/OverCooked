"""
main_multi_agents.py
Système multi-agents coopératif avec allocation dynamique de tâches

Architecture:
- 2 agents coopératifs
- Task Market pour allocation dynamique
- Blackboard pour communication
- STRIPS pour planification
- Métriques de performance
"""

import pygame
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multi_agent.kitchen import Kitchen
from multi_agent.agent import CooperativeAgent
from common.recipes import recipes, get_all_recipe_names
from multi_agent.planning.strips import STRIPSPlanner, create_initial_world_state
from multi_agent.coordination.task_market import TaskMarket
from multi_agent.coordination.communication import Blackboard, AgentCommunicator, MessageType
from multi_agent.analytics.metrics import PerformanceMetrics

pygame.init()


class MultiAgentOvercookedGame:
    """
    Jeu Overcooked avec système multi-agents coopératif
    """

    def __init__(self, num_agents=2):
        # Environnement
        self.kitchen = Kitchen(width=16, height=16, cell_size=50)

        # Systèmes multi-agents
        self.blackboard = Blackboard()
        self.metrics = PerformanceMetrics()

        # Créer les agents
        self.agents = []
        agent_start_positions = [(0, 15), (15, 15)]  # Coins opposés

        for i in range(num_agents):
            communicator = AgentCommunicator(agent_id=i, blackboard=self.blackboard)
            agent = CooperativeAgent(
                agent_id=i,
                position=agent_start_positions[i],
                kitchen=self.kitchen,
                communicator=communicator
            )
            self.agents.append(agent)
            self.blackboard.global_state['active_agents'].add(i)

        # Planification et allocation de tâches
        self.planner = STRIPSPlanner(create_initial_world_state(self.kitchen, self.agents))
        self.task_market = None

        # État du jeu
        self.order_queue = []
        self.current_order = None
        self.current_order_id = None
        self.pending_orders = []
        self.score = 0
        self.running = True
        self.awaiting_recipe_choice = True

        # UI
        self.recipe_buttons = []
        self.send_button = None
        self.clear_button = None

        print(f"\n🎮 Système multi-agents initialisé avec {num_agents} agents")

    # ----------------------------------------------------------------------
    # Gestion des commandes
    # ----------------------------------------------------------------------

    def add_recipe_to_order(self, recipe_name):
        """Ajoute une recette à la liste des commandes en attente"""
        if recipe_name not in recipes:
            print(f"❌ Recette inconnue: {recipe_name}")
            return
        self.pending_orders.append(recipe_name)
        print(f"➕ Ajouté: {recipe_name} (Total: {len(self.pending_orders)} plats)")

    def send_orders(self):
        """Envoie les commandes en attente au système multi-agents"""
        if not self.pending_orders:
            print("⚠️ Aucune commande à envoyer!")
            return

        self.order_queue.extend(self.pending_orders)
        print(f"\n📤 ENVOI DE LA COMMANDE: {len(self.pending_orders)} plat(s)")
        for i, r in enumerate(self.pending_orders, 1):
            print(f"  {i}. {r.capitalize()}")

        self.pending_orders = []
        self.awaiting_recipe_choice = False

        if not self.current_order and self.order_queue:
            self._start_next_order()

    def clear_pending_orders(self):
        """Efface les commandes en attente"""
        self.pending_orders = []
        print("🗑️ Commandes en attente effacées")

    def _start_next_order(self):
        """Démarre la préparation de la prochaine commande"""
        if not self.order_queue:
            return

        recipe_name = self.order_queue.pop(0)
        recipe_data = recipes[recipe_name]
        self.current_order = recipe_name

        print(f"\n{'='*60}")
        print(f"🍽️ NOUVELLE COMMANDE: {recipe_name.upper()}")
        print(f"{'='*60}")

        # Décomposer la recette en tâches atomiques avec STRIPS
        tasks = self.planner.decompose_recipe(recipe_name, recipe_data['ingredients'])
        print(f"📋 {len(tasks)} tâches identifiées pour cette commande")

        # Créer un nouveau Task Market pour cette commande
        world_state = create_initial_world_state(self.kitchen, self.agents)
        self.task_market = TaskMarket(world_state)
        self.task_market.add_tasks(tasks)

        # Démarrer le suivi des métriques
        self.current_order_id = self.metrics.start_order(recipe_name, len(tasks))

        # Notifier le blackboard
        self.blackboard.post_message(
            msg_type=MessageType.ORDER_RECEIVED,
            sender_id=None,
            receiver_id=None,
            content={'recipe': recipe_name, 'tasks_count': len(tasks)}
        )

    # ----------------------------------------------------------------------
    # Allocation de tâches (Task Market)
    # ----------------------------------------------------------------------

    def allocate_tasks_to_agents(self):
        """
        Alloue les tâches disponibles aux agents via le Task Market
        Utilise un système d'enchères (bidding)

        STRATÉGIE: Allouer seulement aux agents qui n'ont RIEN dans les mains
        pour respecter la contrainte "1 ingrédient à la fois"
        """
        if not self.task_market:
            return

        # Obtenir les tâches disponibles
        available_tasks = self.task_market.get_available_tasks()

        if not available_tasks:
            return

        # Trouver les agents disponibles (pas de tâche en cours)
        # Note: Un agent peut avoir quelque chose dans les mains (après PICKUP)
        # et être prêt pour CUT/COOK/BRING
        available_agents = [agent for agent in self.agents
                          if agent.current_task is None]

        if not available_agents:
            return

        # Collecter les enchères (bids) en priorisant les tâches utiles
        all_bids = []
        tasks_with_candidates = 0
        max_tasks = len(available_agents)
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
            if tasks_with_candidates >= max_tasks:
                break

        if not all_bids:
            return

        # Allouer les tâches selon les enchères
        allocations = self.task_market.allocate_tasks(all_bids)

        # Assigner les tâches aux agents
        for agent_id, task_id in allocations.items():
            agent = self.agents[agent_id]
            task = self.task_market.tasks[task_id]
            agent.assign_task(task)
            self.task_market.start_task(task_id)

    # ----------------------------------------------------------------------
    # Boucle de jeu principale
    # ----------------------------------------------------------------------

    def update(self):
        """Met à jour le système multi-agents"""
        if self.awaiting_recipe_choice:
            return

        # Allouer les tâches disponibles
        self.allocate_tasks_to_agents()

        # Mettre à jour tous les agents
        for agent in self.agents:
            agent.update(self.task_market)

        # Mettre à jour les métriques
        self._update_metrics()

        # Vérifier si la commande est terminée
        if self.task_market and not self.task_market.has_pending_tasks():
            self._complete_current_order()

    def _update_metrics(self):
        """Met à jour les métriques de performance"""
        # Mettre à jour les stats des agents
        for agent in self.agents:
            stats = agent.get_performance_stats()
            self.metrics.update_agent_stats(agent.id, stats)

        # Mettre à jour l'utilisation des ressources
        self.metrics.update_resource_usage(self.kitchen.resource_locks)

    def _complete_current_order(self):
        """Termine la commande actuelle"""
        print(f"\n✅ Commande {self.current_order} TERMINÉE!")

        # Compléter les métriques
        agents_involved = [agent.id for agent in self.agents if agent.tasks_completed > 0]
        self.metrics.complete_order(self.current_order_id, agents_involved)

        # Augmenter le score
        self.score += 10
        print(f"💰 Score: {self.score}")

        # Afficher les statistiques
        if self.task_market:
            stats = self.task_market.get_completion_stats()
            print(f"📊 Statistiques: {stats}")

        # Réinitialiser pour la prochaine commande
        self.current_order = None
        self.task_market = None

        # Passer à la commande suivante ou revenir au menu
        if self.order_queue:
            self._start_next_order()
        else:
            print("\n🎉 Toutes les commandes sont terminées!")
            self.awaiting_recipe_choice = True
            self.metrics.print_summary()

    # ----------------------------------------------------------------------
    # Interface utilisateur
    # ----------------------------------------------------------------------

    def handle_button_click(self, mouse_pos):
        """Gère les clics sur les boutons"""
        if self.send_button and self.send_button.collidepoint(mouse_pos):
            self.send_orders()
            return True
        if self.clear_button and self.clear_button.collidepoint(mouse_pos):
            self.clear_pending_orders()
            return True
        for button_rect, recipe_name in self.recipe_buttons:
            if button_rect.collidepoint(mouse_pos):
                self.add_recipe_to_order(recipe_name)
                return True
        return False

    def draw_game(self):
        """Dessine tout le jeu"""
        if self.awaiting_recipe_choice:
            current_display = f"{len(self.pending_orders)} plat(s) sélectionné(s)"
        else:
            current_display = f"{self.current_order} ({len(self.order_queue)} en attente)"

        # Dessine la cuisine avec tous les agents
        _ = self.kitchen.draw(
            agents=self.agents,
            current_order=current_display,
            score=self.score,
            show_buttons=False   # <-- IMPORTANT : toujours False ici
        )

        # Dessine l'interface de commandes si nécessaire
        if self.awaiting_recipe_choice:
            self.recipe_buttons, self.send_button, self.clear_button = self._draw_order_interface()

        pygame.display.flip()


    def _draw_order_interface(self):
        """Dessine l'interface de sélection des commandes"""
        recipes_list = get_all_recipe_names()

        # haut du panneau bas
        ui_top = self.kitchen.height * self.kitchen.cell_size  # 800

        # --- Boutons de recettes ---
        button_width = 150
        button_height = 40
        button_spacing = 20
        recipe_buttons = []

        # on les place vers le milieu du panneau bas
        recipes_y = ui_top + 80   # 880 → 920

        for i, recipe_name in enumerate(recipes_list):
            button_x = 10 + i * (button_width + button_spacing)
            button_rect = pygame.Rect(button_x, recipes_y, button_width, button_height)

            # Couleur selon si sélectionné
            color = (100, 150, 255) if recipe_name not in self.pending_orders else (50, 200, 50)

            pygame.draw.rect(self.kitchen.screen, color, button_rect)
            pygame.draw.rect(self.kitchen.screen, (0, 0, 0), button_rect, 2)

            button_text = self.kitchen.small_font.render(recipe_name.capitalize(), True, (255, 255, 255))
            text_rect = button_text.get_rect(center=button_rect.center)
            self.kitchen.screen.blit(button_text, text_rect)

            recipe_buttons.append((button_rect, recipe_name))

        # --- Bouton "Envoyer" ---
        send_y = ui_top + 130  # 930 → 970, bien visible
        send_button_rect = pygame.Rect(10, send_y, 150, 40)
        send_color = (50, 200, 50) if self.pending_orders else (150, 150, 150)
        pygame.draw.rect(self.kitchen.screen, send_color, send_button_rect)
        pygame.draw.rect(self.kitchen.screen, (0, 0, 0), send_button_rect, 2)
        send_text = self.kitchen.small_font.render("Envoyer", True, (255, 255, 255))
        send_text_rect = send_text.get_rect(center=send_button_rect.center)
        self.kitchen.screen.blit(send_text, send_text_rect)

        # --- Bouton "Effacer" ---
        clear_button_rect = pygame.Rect(180, send_y, 150, 40)
        pygame.draw.rect(self.kitchen.screen, (200, 50, 50), clear_button_rect)
        pygame.draw.rect(self.kitchen.screen, (0, 0, 0), clear_button_rect, 2)
        clear_text = self.kitchen.small_font.render("Effacer", True, (255, 255, 255))
        clear_text_rect = clear_text.get_rect(center=clear_button_rect.center)
        self.kitchen.screen.blit(clear_text, clear_text_rect)

        return recipe_buttons, send_button_rect, clear_button_rect


    def run(self):
        """Boucle principale du jeu"""
        print("\n🎮 Démarrage du jeu multi-agents...")
        print("Cliquez sur les recettes pour composer votre commande")
        print("Puis cliquez sur 'Envoyer' pour lancer la préparation")
        print("Appuyez sur Q pour quitter\n")

        while self.running:
            # Gestion des événements
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_button_click(event.pos)

            # Mise à jour du jeu
            self.update()

            # Affichage
            self.draw_game()

            # Limitation FPS
            self.kitchen.clock.tick(10)

        # Afficher le rapport final
        print("\n" + "="*60)
        print("🏁 FIN DE LA SESSION")
        print("="*60)
        self.metrics.print_summary()

        pygame.quit()
        sys.exit()


# ----------------------------------------------------------------------
# Point d'entrée
# ----------------------------------------------------------------------

if __name__ == "__main__":
    game = MultiAgentOvercookedGame(num_agents=2)
    game.run()
