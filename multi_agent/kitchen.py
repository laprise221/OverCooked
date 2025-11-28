"""
Kitchen avec fonctionnalités multi-agent
Ajoute: resource locks et shared assembly table
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.kitchen_base import Kitchen as KitchenBase


class Kitchen(KitchenBase):
    """
    Kitchen étendue avec support multi-agent:
    - Resource locking (cutting_board, stove, assembly)
    - Shared assembly table
    """

    def __init__(self, width=16, height=16, cell_size=50):
        super().__init__(width, height, cell_size)

        # Resource locks pour synchronisation multi-agent
        self.resource_locks = {
            'cutting_board': None,  # None ou agent_id
            'stove': None,
            'assembly': None,
            'counter': None
        }

        # Table d'assemblage partagée entre agents
        self.shared_assembly_table = []

        print("🔒 Kitchen multi-agent avec resource locks activée")

    # ------------------------------------------------------------------
    # Resource Locking pour coordination multi-agent
    # ------------------------------------------------------------------

    def try_lock_resource(self, resource_name: str, agent_id: int) -> bool:
        """
        Tente de verrouiller une ressource pour un agent
        Retourne True si succès, False si déjà occupée
        """
        if resource_name not in self.resource_locks:
            return True  # Ressource non lockable

        current_owner = self.resource_locks[resource_name]

        # Si déjà possédée par cet agent, OK
        if current_owner == agent_id:
            return True

        # Si libre, on la prend
        if current_owner is None:
            self.resource_locks[resource_name] = agent_id
            return True

        # Sinon, occupée par un autre agent
        return False

    def unlock_resource(self, resource_name: str, agent_id: int):
        """
        Libère une ressource si elle appartient à cet agent
        """
        if resource_name not in self.resource_locks:
            return

        if self.resource_locks[resource_name] == agent_id:
            self.resource_locks[resource_name] = None

    def is_resource_available(self, resource_name: str) -> bool:
        """Vérifie si une ressource est disponible"""
        if resource_name not in self.resource_locks:
            return True
        return self.resource_locks[resource_name] is None

    def get_resource_owner(self, resource_name: str) -> int:
        """Retourne l'ID de l'agent qui possède la ressource"""
        return self.resource_locks.get(resource_name)

    # ------------------------------------------------------------------
    # Override draw pour supporter plusieurs agents
    # ------------------------------------------------------------------

    def draw(self, agents=None, current_order=None, score=0, show_buttons=False):
        """
        Dessine la cuisine avec support multi-agent

        Args:
            agents: Liste d'agents ou agent unique (compatibilité)
            current_order: Commande en cours
            score: Score actuel
            show_buttons: Afficher les boutons de sélection
        """
        import pygame
        from common.objects import Ingredient, Tool

        # Support pour agent unique (compatibilité)
        if agents is not None and not isinstance(agents, list):
            agents = [agents]

        self.screen.fill((240, 240, 220))

        # Dessiner la grille
        for y in range(self.height):
            for x in range(self.width):
                rect = pygame.Rect(x * self.cell_size, y * self.cell_size,
                                 self.cell_size, self.cell_size)
                cell = self.grid[y][x]

                if cell is None:
                    pygame.draw.rect(self.screen, self.colors['floor'], rect)
                elif isinstance(cell, Ingredient):
                    pygame.draw.rect(self.screen, (200, 200, 200), rect)
                    key = f"{cell.name}_{cell.state}" if cell.state != "cru" else f"{cell.name}_crue"
                    img = self.images.get(key)
                    if img:
                        offset = 5
                        self.screen.blit(img, (x * self.cell_size + offset,
                                             y * self.cell_size + offset))
                elif isinstance(cell, Tool):
                    img = self.images.get(cell.tool_type)
                    if img:
                        self.screen.blit(img, (x * self.cell_size + 5,
                                             y * self.cell_size + 5))
                    else:
                        pygame.draw.rect(self.screen, (150, 150, 150), rect)
                elif isinstance(cell, str):
                    if cell == "assembly_table":
                        img = self.images.get("assembly_table")
                        if img:
                            self.screen.blit(img, (x * self.cell_size + 5,
                                                 y * self.cell_size + 5))
                        else:
                            pygame.draw.rect(self.screen, (139, 90, 43), rect)
                    elif cell == "counter":
                        img = self.images.get("counter")
                        if img:
                            self.screen.blit(img, (x * self.cell_size + 5,
                                                 y * self.cell_size + 5))
                        else:
                            pygame.draw.rect(self.screen, (180, 180, 160), rect)
                    else:
                        color = self.colors.get(cell, (200, 200, 200))
                        pygame.draw.rect(self.screen, color, rect)

                pygame.draw.rect(self.screen, (200, 200, 200), rect, 1)

        # Dessiner les ingrédients sur la table partagée
        if self.shared_assembly_table and not (self.current_dish_image and self.current_dish_pos):
            for idx, ingredient in enumerate(self.shared_assembly_table):
                if ingredient.position:
                    ix, iy = ingredient.position
                    key = f"{ingredient.name}_{ingredient.state}" if ingredient.state != "cru" else f"{ingredient.name}_crue"
                    img = self.images.get(key)
                    if img:
                        small_img = pygame.transform.scale(img, (25, 25))
                        offset_x = (idx * 10) % 30
                        offset_y = (idx * 10) // 30 * 10
                        self.screen.blit(small_img,
                                       (ix * self.cell_size + 10 + offset_x,
                                        iy * self.cell_size + 10 + offset_y))

        # Dessiner les plats sur le comptoir
        for dish_data in self.counter_dishes:
            dish_img = dish_data['image']
            dx, dy = dish_data['position']
            offset = dish_data.get('offset', 0)
            rect_x = dx * self.cell_size + 5 + offset
            rect_y = dy * self.cell_size + 5
            self.screen.blit(dish_img, (rect_x, rect_y))

        # Dessiner tous les agents
        if agents:
            agent_colors = [(0, 100, 255), (255, 100, 0)]  # Bleu, Orange

            for idx, agent in enumerate(agents):
                ax, ay = agent.position
                agent_img_key = f"agent_{agent.direction}"
                agent_img = self.images.get(agent_img_key)

                if agent_img:
                    self.screen.blit(agent_img, (ax * self.cell_size + 5,
                                                ay * self.cell_size + 5))
                else:
                    # Fallback: cercle avec couleur différente par agent
                    color = agent_colors[idx % len(agent_colors)]
                    agent_rect = pygame.Rect(ax * self.cell_size + 5,
                                            ay * self.cell_size + 5,
                                            self.cell_size - 10,
                                            self.cell_size - 10)
                    pygame.draw.circle(self.screen, color, agent_rect.center,
                                     self.cell_size // 4)

                # Dessiner l'ingrédient porté
                if hasattr(agent, 'holding') and agent.holding and isinstance(agent.holding, Ingredient):
                    key = f"{agent.holding.name}_{agent.holding.state}" if agent.holding.state != "cru" else f"{agent.holding.name}_crue"
                    ing_img = self.images.get(key)
                    if ing_img:
                        small_img = pygame.transform.scale(ing_img, (30, 30))
                        img_x = ax * self.cell_size + self.cell_size // 2 - 15
                        img_y = ay * self.cell_size + 5
                        self.screen.blit(small_img, (img_x, img_y))

        # Dessiner le plat en transit
        if self.current_dish_image and self.current_dish_pos:
            x, y = self.current_dish_pos
            rect_x = x * self.cell_size + self.cell_size // 4
            rect_y = y * self.cell_size + self.cell_size // 4
            self.screen.blit(self.current_dish_image, (rect_x, rect_y))

        # Interface en bas
        font = self.font
        ui_y = self.height * self.cell_size

        # Score
        score_text = font.render(f"Score: {score}", True, (0, 100, 0))
        self.screen.blit(score_text, (10, ui_y + 10))

        # Actions des agents
        if agents:
            action_y = ui_y + 40
            for idx, agent in enumerate(agents):
                text_action = self.small_font.render(
                    f"Agent {idx}: {agent.current_action}", True, (0, 0, 0))
                self.screen.blit(text_action, (10, action_y + idx * 20))

        # Commande actuelle
        if current_order:
            text_order = font.render(f"Commande: {current_order}", True, (0, 0, 150))
            self.screen.blit(text_order, (10, ui_y + 90))

        # Instructions
        instructions_text = self.small_font.render(
            "Cliquez sur un bouton pour choisir une recette | Q = Quitter",
            True, (0, 0, 0))
        self.screen.blit(instructions_text, (10, ui_y + 120))

        pygame.display.flip()
        return []
