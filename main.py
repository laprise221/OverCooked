"""
main.py
Point d'entrée du jeu Overcooked avec agent autonome
"""

import pygame
import random
import sys
from kitchen import Kitchen
from agent import Agent
from recipes import recipes, get_all_recipe_names

pygame.init()
pygame.display.set_mode((800, 600))
pygame.display.set_caption("Overcooked - Agent autonome")

class OvercookedGame:
    """
    Classe principale du jeu
    """
    def __init__(self):
        self.kitchen = Kitchen(width=10, height=8, cell_size=80)
        self.agent = Agent(position=[0, 7], kitchen=self.kitchen)
        self.current_order = None
        self.orders_completed = 0
        self.running = True

    def start_new_order(self, recipe_index=None):
        """
        Démarre une nouvelle commande
        Si recipe_index est None, on attend que le joueur choisisse via le clavier
        """
        all_recipes = get_all_recipe_names()

        if recipe_index is None:
            # Affiche les recettes sur l'écran
            print("\n📋 Recettes disponibles :")
            for i, name in enumerate(all_recipes, 1):
                print(f"{i}. {name} - {recipes[name]['description']}")

            self.current_order = None  # On attend le choix
            self.awaiting_choice = True
            return

        # Choix fait
        recipe_name = all_recipes[recipe_index]
        recipe_data = recipes[recipe_name]
        self.current_order = recipe_name
        self.agent.set_recipe(recipe_name, recipe_data)

        print("\n" + "="*60)
        print(f"📋 NOUVELLE COMMANDE: {recipe_name.upper()}")
        print(f"📝 Description: {recipe_data['description']}")
        print("="*60)
        self.awaiting_choice = False

# -------------------------------------------------------
    def run(self):
        """
        Boucle principale du jeu
        """
        self.start_new_order()  # Affiche les recettes pour choix

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                        self.running = False
                    elif event.key == pygame.K_SPACE:
                        # Démarre nouvelle commande si aucune tâche
                        if not self.agent.task_queue and not self.agent.current_task:
                            self.start_new_order()
                    elif self.awaiting_choice:
                        # Choix de la recette avec touches 1,2,…
                        if pygame.K_1 <= event.key <= pygame.K_9:
                            index = event.key - pygame.K_1
                            all_recipes = get_all_recipe_names()
                            if index < len(all_recipes):
                                self.start_new_order(recipe_index=index)

            # Met à jour l'agent si une commande est en cours
            if self.current_order:
                self.agent.update()

                # Vérifie si la commande est terminée
                if (not self.agent.task_queue and
                    not self.agent.current_task and
                    self.agent.current_action.startswith("Livré")):

                    self.orders_completed += 1
                    print(f"\n🎉 Commande terminée! Total: {self.orders_completed}")
                    print("⏳ Prochaine commande dans 3 secondes...")
                    pygame.time.wait(3000)
                    self.start_new_order()  # Affiche choix pour nouvelle commande

            # Affiche la cuisine
            self.kitchen.draw(self.agent, self.current_order)
            self.kitchen.update()

def main():
    """
    Fonction principale
    """
    print("="*60)
    print("🍳 OVERCOOKED - AGENT AUTONOME")
    print("="*60)
    print("💡 Instructions:")
    print("  - L'agent travaille automatiquement")
    print("  - ESC: Quitter")
    print("  - ESPACE: Nouvelle commande (après la fin d'une commande)")
    print("="*60)

    game = OvercookedGame()
    game.run()


if __name__ == "__main__":
    main()