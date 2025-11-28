"""
main.py
Point d'entrée du jeu Overcooked avec agent autonome et commandes multiples
"""

import pygame
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from single_agent.kitchen import Kitchen
from single_agent.agent import Agent
from common.recipes import recipes, get_all_recipe_names

pygame.init()

class OvercookedGame:
    """
    Classe principale du jeu
    """
    def __init__(self):
        self.kitchen = Kitchen(width=16, height=16, cell_size=50)
        self.agent = Agent(position=[0, 15], kitchen=self.kitchen)
        self.order_queue = []
        self.current_order = None
        self.pending_orders = []
        self.score = 0
        self.running = True
        self.recipe_buttons = []
        self.send_button = None
        self.clear_button = None
        self.awaiting_recipe_choice = True

    def add_recipe_to_order(self, recipe_name):
        if recipe_name not in recipes:
            print(f"❌ Recette inconnue: {recipe_name}")
            return
        self.pending_orders.append(recipe_name)
        print(f"➕ Ajouté: {recipe_name} (Total: {len(self.pending_orders)} plats)")

    def send_orders(self):
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
        self.pending_orders = []
        print("🗑️ Commandes en attente effacées")

    def _start_next_order(self):
        if not self.order_queue:
            return
        recipe_name = self.order_queue.pop(0)
        recipe_data = recipes[recipe_name]
        self.current_order = recipe_name
        self.agent.set_recipe(recipe_name, recipe_data)
        print(f"\n🍽️ PRÉPARATION: {recipe_name.upper()}")

    def handle_button_click(self, mouse_pos):
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
        """Dessine tout le jeu (cuisine + interface + boutons)"""

        # Texte affichage
        if self.awaiting_recipe_choice:
            current_display = f"{len(self.pending_orders)} plat(s) sélectionné(s)"
        else:
            current_display = f"{self.current_order} ({len(self.order_queue)} en attente)"

        # Dessine la cuisine (grille + agent)
        self.kitchen.draw(self.agent, current_display, self.score)

        # Dessine l'interface de commandes si nécessaire
        if self.awaiting_recipe_choice:
            self._draw_order_interface()

        # Rafraîchissement UNE SEULE FOIS par frame
        pygame.display.flip()

    def _draw_order_interface(self):
        """Dessine l'interface de sélection des commandes PAR-DESSUS la cuisine"""
        recipes_list = get_all_recipe_names()
        ui_y = self.kitchen.height * self.kitchen.cell_size
        button_width = 120
        button_height = 35
        button_spacing = 15

        # Fond interface
        interface_rect = pygame.Rect(0, ui_y + 95,
                                     self.kitchen.width * self.kitchen.cell_size, 105)
        pygame.draw.rect(self.kitchen.screen, (250, 250, 240), interface_rect)

        # Titre
        title = self.kitchen.font.render("🍽️ COMPOSER UNE COMMANDE", True, (0, 0, 0))
        self.kitchen.screen.blit(title, (10, ui_y + 100))

        # Recettes sélectionnées
        if self.pending_orders:
            pending_text = f"Sélection: {', '.join([r.capitalize() for r in self.pending_orders])}"
            pending_surface = self.kitchen.small_font.render(pending_text, True, (0, 100, 0))
            self.kitchen.screen.blit(pending_surface, (10, ui_y + 130))
        else:
            help_text = "Cliquez sur les recettes pour composer votre commande"
            help_surface = self.kitchen.small_font.render(help_text, True, (100, 100, 100))
            self.kitchen.screen.blit(help_surface, (10, ui_y + 130))

        # Boutons recettes
        button_y = ui_y + 155
        self.recipe_buttons = []

        for i, recipe_name in enumerate(recipes_list):
            button_x = 10 + i * (button_width + button_spacing)
            button_rect = pygame.Rect(button_x, button_y, button_width, button_height)

            pygame.draw.rect(self.kitchen.screen, (100, 150, 255), button_rect)
            pygame.draw.rect(self.kitchen.screen, (0, 0, 0), button_rect, 2)

            text = self.kitchen.small_font.render(recipe_name.capitalize(), True, (255, 255, 255))
            text_rect = text.get_rect(center=button_rect.center)
            self.kitchen.screen.blit(text, text_rect)

            self.recipe_buttons.append((button_rect, recipe_name))

        # Bouton "Envoyer"
        send_button_x = 550
        send_button_y = button_y
        self.send_button = pygame.Rect(send_button_x, send_button_y, 130, button_height)
        send_color = (50, 200, 50) if self.pending_orders else (150, 150, 150)
        pygame.draw.rect(self.kitchen.screen, send_color, self.send_button)
        pygame.draw.rect(self.kitchen.screen, (0, 0, 0), self.send_button, 2)
        send_text = self.kitchen.small_font.render("📤 Envoyer", True, (255, 255, 255))
        pygame.draw.rect(self.kitchen.screen, send_color, self.send_button)
        self.kitchen.screen.blit(send_text, send_text.get_rect(center=self.send_button.center))

        # Bouton "Effacer"
        clear_button_x = send_button_x + 140
        self.clear_button = pygame.Rect(clear_button_x, send_button_y, 110, button_height)
        clear_color = (200, 50, 50) if self.pending_orders else (150, 150, 150)
        pygame.draw.rect(self.kitchen.screen, clear_color, self.clear_button)
        pygame.draw.rect(self.kitchen.screen, (0, 0, 0), self.clear_button, 2)
        clear_text = self.kitchen.small_font.render("🗑️ Effacer", True, (255, 255, 255))
        self.kitchen.screen.blit(clear_text, clear_text.get_rect(center=self.clear_button.center))

    def run(self):
        """Boucle principale"""
        all_recipes = get_all_recipe_names()
        print("🍳 OVERCOOKED - AGENT AUTONOME")
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_q):
                        self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.awaiting_recipe_choice:
                        self.handle_button_click(pygame.mouse.get_pos())

            # Mise à jour agent si commande en cours
            if self.current_order and not self.awaiting_recipe_choice:
                self.agent.update()
                if (not self.agent.task_queue and
                    not self.agent.current_task and
                    self.agent.current_action.startswith("Livré")):

                    self.score += 10
                    print(f"🎉 Commande {self.current_order} terminée! +10 points")
                    self.current_order = None
                    if self.order_queue:
                        pygame.time.wait(1000)
                        self._start_next_order()
                    else:
                        pygame.time.wait(2000)
                        self.awaiting_recipe_choice = True
                        self.kitchen.clear_counter()

            # Dessin centralisé
            self.draw_game()
            self.kitchen.update()


def main():
    print("🍳 OVERCOOKED - AGENT AUTONOME")
    game = OvercookedGame()
    game.run()
    pygame.quit()


if __name__ == "__main__":
    main()
