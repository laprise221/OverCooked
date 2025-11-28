"""
main_multi_agents.py
Système multi-agents coopératif avec allocation dynamique de tâches
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

# ----------------------------------------------------------------------
# MENU DE CONFIGURATION (Isolé)
# ----------------------------------------------------------------------
def run_configuration_menu():
    width, height = 800, 600
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Configuration Overcooked")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 40)
    title_font = pygame.font.Font(None, 60)

    config = {
        'nb_agents': 2,
        'nb_stoves': 2,
        'nb_boards': 2,
        'nb_assembly': 1
    }

    # Layout
    center_x = width // 2
    params = [
        ("Agents", 'nb_agents', 1, 4),
        ("Poêles", 'nb_stoves', 1, 6),
        ("Planches", 'nb_boards', 1, 6),
        ("Tables Assemblage", 'nb_assembly', 1, 4)
    ]

    start_btn = pygame.Rect(center_x - 100, height - 100, 200, 60)

    running = True
    while running:
        screen.fill((246, 244, 235))

        # Titre
        t = title_font.render("Paramètres de la Cuisine", True, (40,40,40))
        screen.blit(t, (center_x - t.get_width()//2, 40))

        mouse_pos = pygame.mouse.get_pos()
        clicked = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                clicked = True

        # Dessin des contrôles
        start_y = 140
        for i, (label, key, vmin, vmax) in enumerate(params):
            y = start_y + i * 80
            val = config[key]

            # Label
            lbl = font.render(f"{label}: {val}", True, (60,60,60))
            screen.blit(lbl, (center_x - 120, y))

            # Boutons - / +
            r_minus = pygame.Rect(center_x + 140, y - 5, 40, 40)
            r_plus = pygame.Rect(center_x + 200, y - 5, 40, 40)

            # Dessin boutons
            pygame.draw.rect(screen, (200,80,80), r_minus, border_radius=5)
            pygame.draw.rect(screen, (80,200,80), r_plus, border_radius=5)

            screen.blit(font.render("-", True, (255,255,255)), (r_minus.x+13, r_minus.y+8))
            screen.blit(font.render("+", True, (255,255,255)), (r_plus.x+11, r_plus.y+8))

            # Interaction
            if clicked:
                if r_minus.collidepoint(mouse_pos) and val > vmin:
                    config[key] -= 1
                if r_plus.collidepoint(mouse_pos) and val < vmax:
                    config[key] += 1

        # Bouton Start
        c_btn = (50, 150, 255) if not start_btn.collidepoint(mouse_pos) else (80, 180, 255)
        pygame.draw.rect(screen, c_btn, start_btn, border_radius=10)
        st_txt = font.render("LANCER", True, (255,255,255))
        screen.blit(st_txt, st_txt.get_rect(center=start_btn.center))

        if clicked and start_btn.collidepoint(mouse_pos):
            running = False

        pygame.display.flip()
        clock.tick(30)

    return config

# ----------------------------------------------------------------------
# JEU PRINCIPAL
# ----------------------------------------------------------------------

class MultiAgentOvercookedGame:
    def __init__(self, config):
        self.num_agents = config['nb_agents']

        # 1. Créer la cuisine (charge la carte par défaut via super())
        self.kitchen = Kitchen(width=16, height=16, cell_size=50)

        # 2. Appliquer la mutation (modifier poêles/planches sans casser les ingrédients)
        self.kitchen.generate_dynamic_kitchen(
            nb_assembly=config['nb_assembly'],
            nb_stoves=config['nb_stoves'],
            nb_cutting_boards=config['nb_boards']
        )

        self.blackboard = Blackboard()
        self.metrics = PerformanceMetrics()

        # Agents
        self.agents = []
        starts = [(1, 1), (14, 14), (1, 14), (14, 1)] # Coins

        for i in range(self.num_agents):
            pos = starts[i % len(starts)]
            comm = AgentCommunicator(agent_id=i, blackboard=self.blackboard)
            agent = CooperativeAgent(
                agent_id=i,
                position=pos,
                kitchen=self.kitchen,
                communicator=comm
            )
            self.agents.append(agent)
            self.blackboard.global_state['active_agents'].add(i)

        self.planner = STRIPSPlanner(create_initial_world_state(self.kitchen, self.agents))
        self.task_market = None
        self.order_queue = []
        self.current_order = None
        self.current_order_id = None
        self.pending_orders = []
        self.score = 0
        self.running = True
        self.awaiting_recipe_choice = True
        self.recipe_buttons = []
        self.send_button = None
        self.clear_button = None

        print(f"\n🎮 Jeu lancé : {self.num_agents} agents, Config: {config}")

    # ... (Le reste des méthodes est identique, je remets juste les cruciales) ...

    def add_recipe_to_order(self, recipe_name):
        if recipe_name in recipes:
            self.pending_orders.append(recipe_name)
            print(f"➕ {recipe_name}")

    def send_orders(self):
        if self.pending_orders:
            self.order_queue.extend(self.pending_orders)
            self.pending_orders = []
            self.awaiting_recipe_choice = False
            if not self.current_order: self._start_next_order()

    def clear_pending_orders(self):
        self.pending_orders = []

    def _start_next_order(self):
        if not self.order_queue: return
        recipe_name = self.order_queue.pop(0)
        self.current_order = recipe_name
        tasks = self.planner.decompose_recipe(recipe_name, recipes[recipe_name]['ingredients'])

        ws = create_initial_world_state(self.kitchen, self.agents)
        self.task_market = TaskMarket(ws)
        self.task_market.add_tasks(tasks)

        self.current_order_id = self.metrics.start_order(recipe_name, len(tasks))
        self.blackboard.post_message(MessageType.ORDER_RECEIVED, None, None, {'recipe': recipe_name})

    def allocate_tasks_to_agents(self):
        if not self.task_market: return
        avail_tasks = self.task_market.get_available_tasks()
        if not avail_tasks: return

        avail_agents = [a for a in self.agents if a.current_task is None]
        if not avail_agents: return

        all_bids = []
        # Logique d'enchères simple
        for task in avail_tasks:
            for agent in avail_agents:
                bid = agent.submit_bid_for_task(task)
                if bid.cost < float('inf'):
                    all_bids.append(bid)

        if all_bids:
            allocs = self.task_market.allocate_tasks(all_bids)
            for aid, tid in allocs.items():
                self.agents[aid].assign_task(self.task_market.tasks[tid])
                self.task_market.start_task(tid)

    def update(self):
        if self.awaiting_recipe_choice: return
        self.allocate_tasks_to_agents()
        for agent in self.agents: agent.update(self.task_market)
        self._update_metrics()

        if self.task_market and not self.task_market.has_pending_tasks():
            self._complete_current_order()

    def _update_metrics(self):
        for agent in self.agents:
            self.metrics.update_agent_stats(agent.id, agent.get_performance_stats())
        self.metrics.update_resource_usage(self.kitchen.resource_locks)

    def _complete_current_order(self):
        print(f"✅ FINI: {self.current_order}")
        self.score += 10
        agents_involved = [a.id for a in self.agents if a.tasks_completed > 0]
        self.metrics.complete_order(self.current_order_id, agents_involved)
        self.current_order = None
        self.task_market = None

        if self.order_queue: self._start_next_order()
        else: self.awaiting_recipe_choice = True; self.metrics.print_summary()

    # --- UI ---

    def handle_button_click(self, pos):
        if self.send_button and self.send_button.collidepoint(pos):
            self.send_orders(); return True
        if self.clear_button and self.clear_button.collidepoint(pos):
            self.clear_pending_orders(); return True
        for rect, name in self.recipe_buttons:
            if rect.collidepoint(pos): self.add_recipe_to_order(name); return True
        return False

    def draw_game(self):
        txt = f"{len(self.pending_orders)} choix" if self.awaiting_recipe_choice else f"{self.current_order}"

        # Appel du dessin kitchen (SANS FLIP)
        self.kitchen.draw(self.agents, txt, self.score, self.awaiting_recipe_choice)

        if self.awaiting_recipe_choice:
            self.recipe_buttons, self.send_button, self.clear_button = self._draw_order_interface()

        # LE SEUL ET UNIQUE FLIP DE LA BOUCLE DE JEU
        pygame.display.flip()

    def _draw_order_interface(self):
        # ... (Identique à avant, juste pour le visuel des boutons) ...
        ui_y = self.kitchen.height * self.kitchen.cell_size + 130
        buttons = []
        names = get_all_recipe_names()

        for i, name in enumerate(names):
            r = pygame.Rect(10 + i*170, ui_y, 150, 40)
            col = (100, 150, 255) if name not in self.pending_orders else (50, 200, 50)
            pygame.draw.rect(self.kitchen.screen, col, r, border_radius=5)
            txt = self.kitchen.small_font.render(name.capitalize(), True, (255,255,255))
            self.kitchen.screen.blit(txt, txt.get_rect(center=r.center))
            buttons.append((r, name))

        bsend = pygame.Rect(10, ui_y + 50, 150, 40)
        pygame.draw.rect(self.kitchen.screen, (50, 200, 50), bsend, border_radius=5)
        t1 = self.kitchen.small_font.render("Envoyer", True, (255,255,255))
        self.kitchen.screen.blit(t1, t1.get_rect(center=bsend.center))

        bclear = pygame.Rect(180, ui_y + 50, 150, 40)
        pygame.draw.rect(self.kitchen.screen, (200, 50, 50), bclear, border_radius=5)
        t2 = self.kitchen.small_font.render("Effacer", True, (255,255,255))
        self.kitchen.screen.blit(t2, t2.get_rect(center=bclear.center))

        return buttons, bsend, bclear

    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: self.running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_q: self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN: self.handle_button_click(event.pos)

            self.update()
            self.draw_game()
            clock.tick(10) # FPS du jeu

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    # 1. Configuration
    user_config = run_configuration_menu()

    # 2. Jeu
    game = MultiAgentOvercookedGame(user_config)
    game.run()