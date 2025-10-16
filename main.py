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
        self.agent = Agent(position=[5, 5], kitchen=self.kitchen)
        self.current_order = None
        self.orders_completed = 0
        self.running = True

    def start_new_order(self):
        """
        Démarre une nouvelle commande aléatoire
        """
        recipe_name = random.choice(get_all_recipe_names())
        recipe_data = recipes[recipe_name]

        self.current_order = recipe_name
        self.agent.set_recipe(recipe_name, recipe_data)

        print("\n" + "="*60)
        print(f"📋 NOUVELLE COMMANDE: {recipe_name.upper()}")
        print(f"📝 Description: {recipe_data['description']}")
        print("="*60)

    def run(self):
        """
        Boucle principale du jeu
        """
        # Démarre la première commande
        self.start_new_order()

        # Boucle de jeu
        while self.running:
            # Gestion des événements
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_SPACE:
                        # Démarre une nouvelle commande (pour tester)
                        if not self.agent.task_queue and not self.agent.current_task:
                            self.start_new_order()

            # Met à jour l'agent
            self.agent.update()

            # Vérifie si la commande est terminée
            if (not self.agent.task_queue and
                not self.agent.current_task and
                self.agent.current_action.startswith("Livré")):

                self.orders_completed += 1
                print(f"\n🎉 Commande terminée! Total: {self.orders_completed}")
                print("⏳ Prochaine commande dans 3 secondes...")
                print("💡 Appuyez sur ESPACE pour une nouvelle commande immédiate")

                pygame.time.wait(3000)
                self.start_new_order()

            # Affiche la cuisine
            self.kitchen.draw(self.agent, self.current_order)
            self.kitchen.update()

        # Fermeture propre
        pygame.quit()
        print(f"\n🎮 Jeu terminé! Commandes complétées: {self.orders_completed}")


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