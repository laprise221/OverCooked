"""
main.py
Point d'entrée du jeu Overcooked avec agent autonome
"""

import pygame
import sys
from kitchen import Kitchen
from agent import Agent
from recipes import recipes, get_all_recipe_names

pygame.init()

class OvercookedGame:
    """
    Classe principale du jeu
    """
    def __init__(self):
        self.kitchen = Kitchen(width=16, height=16, cell_size=50)
        self.agent = Agent(position=[0, 15], kitchen=self.kitchen)
        self.current_order = None
        self.score = 0
        self.running = True
        self.recipe_buttons = []
        self.awaiting_recipe_choice = True

    def start_new_order(self, recipe_name):
        """
        Démarre une nouvelle commande
        """
        if recipe_name not in recipes:
            print(f"❌ Recette inconnue: {recipe_name}")
            return

        recipe_data = recipes[recipe_name]
        self.current_order = recipe_name
        self.agent.set_recipe(recipe_name, recipe_data)
        self.awaiting_recipe_choice = False

        print("\n" + "="*60)
        print(f"📋 NOUVELLE COMMANDE: {recipe_name.upper()}")
        print(f"📝 Description: {recipe_data['description']}")
        print("="*60)

    def handle_button_click(self, mouse_pos):
        """Gère les clics sur les boutons de recettes"""
        for button_rect, recipe_name in self.recipe_buttons:
            if button_rect.collidepoint(mouse_pos):
                self.start_new_order(recipe_name)
                return True
        return False

    def run(self):
        """
        Boucle principale du jeu
        """
        all_recipes = get_all_recipe_names()

        print("="*60)
        print("🍳 OVERCOOKED - AGENT AUTONOME")
        print("="*60)
        print("📋 Recettes disponibles:")
        for i, name in enumerate(all_recipes, 1):
            print(f"  {i}. {name.capitalize()}")
        print("="*60)
        print("💡 Cliquez sur un bouton pour choisir une recette")
        print("="*60)

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                        self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.awaiting_recipe_choice:
                        mouse_pos = pygame.mouse.get_pos()
                        self.handle_button_click(mouse_pos)

            # Met à jour l'agent si une commande est en cours
            if self.current_order and not self.awaiting_recipe_choice:
                self.agent.update()

                # Vérifie si la commande est terminée
                if (not self.agent.task_queue and
                    not self.agent.current_task and
                    self.agent.current_action.startswith("Livré")):

                    self.score += 10
                    print(f"\n🎉 Commande terminée! +10 points")
                    print(f"📊 Score total: {self.score}")
                    print("⏳ Nouvelle commande disponible...")
                    pygame.time.wait(2000)

                    self.current_order = None
                    self.awaiting_recipe_choice = True

            # Affiche la cuisine avec ou sans boutons
            self.recipe_buttons = self.kitchen.draw(
                self.agent,
                self.current_order,
                self.score,
                show_buttons=self.awaiting_recipe_choice
            )

            self.kitchen.update()

        pygame.quit()

def main():
    """
    Fonction principale
    """
    print("="*60)
    print("🍳 OVERCOOKED - AGENT AUTONOME")
    print("="*60)
    print("💡 Instructions:")
    print("  - Cliquez sur un bouton pour choisir une recette")
    print("  - L'agent travaille automatiquement")
    print("  - +10 points par recette terminée")
    print("  - Q ou ESC: Quitter")
    print("="*60)

    game = OvercookedGame()
    game.run()


if __name__ == "__main__":
    main()