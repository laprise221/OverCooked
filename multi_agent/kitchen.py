"""
Kitchen avec fonctionnalités multi-agent
Ajoute: resource locks et shared assembly table
+ design graphique amélioré (damier, panneau bas, etc.)
"""

import sys
import os
import pygame

# Permet d'importer depuis le dossier parent (common.*)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.kitchen_base import Kitchen as KitchenBase
from common.objects import Ingredient, Tool

# === THEME VISUEL DE LA CUISINE ===
GRID_BG      = (246, 244, 235)
GRID_ALT_BG  = (238, 236, 222)
GRID_LINE    = (220, 215, 200)

UI_BG        = (252, 252, 248)
UI_BORDER    = (210, 210, 200)

TEXT_MAIN    = (40, 40, 40)
TEXT_MUTED   = (110, 110, 110)
SCORE_GREEN  = (20, 140, 60)


class Kitchen(KitchenBase):
    """
    Kitchen étendue avec support multi-agent:
    - Resource locking (cutting_board, stove, assembly, counter)
    - Shared assembly table
    - Design graphique amélioré
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

        # Ajuste quelques couleurs de base si présentes
        if hasattr(self, "colors"):
            self.colors.setdefault("floor", GRID_BG)
            self.colors.setdefault("agent", (0, 100, 255))

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

    def get_resource_owner(self, resource_name: str):
        """Retourne l'ID de l'agent qui possède la ressource (ou None)"""
        return self.resource_locks.get(resource_name)

    # ------------------------------------------------------------------
    # Helpers graphiques
    # ------------------------------------------------------------------

    def _draw_background(self):
        """Dessine le sol de la cuisine (damier + lignes de grille)."""
        for y in range(self.height):
            for x in range(self.width):
                rect = pygame.Rect(
                    x * self.cell_size,
                    y * self.cell_size,
                    self.cell_size,
                    self.cell_size,
                )
                color = GRID_BG if (x + y) % 2 == 0 else GRID_ALT_BG
                pygame.draw.rect(self.screen, color, rect)

        width_px = self.width * self.cell_size
        height_px = self.height * self.cell_size

        for x in range(self.width + 1):
            px = x * self.cell_size
            pygame.draw.line(self.screen, GRID_LINE, (px, 0), (px, height_px), 1)

        for y in range(self.height + 1):
            py = y * self.cell_size
            pygame.draw.line(self.screen, GRID_LINE, (0, py), (width_px, py), 1)

    # ------------------------------------------------------------------
    # Override draw pour supporter plusieurs agents + nouveau design
    # ------------------------------------------------------------------

    def draw(self, agents=None, current_order=None, score=0, show_buttons=False):
        """
        Dessine la cuisine avec support multi-agent

        Args:
            agents: Liste d'agents ou agent unique (compatibilité)
            current_order: Commande en cours (texte ou objet)
            score: Score actuel
            show_buttons: Afficher les boutons de sélection (si dispo dans la base)
        """
        # Support pour agent unique (compatibilité)
        if agents is not None and not isinstance(agents, list):
            agents = [agents]

        # Fond général
        self.screen.fill(UI_BG)

        # --- Zone cuisine (haut) ---
        self._draw_background()

        # --- Grille et éléments fixes ---
        for y in range(self.height):
            for x in range(self.width):
                rect = pygame.Rect(
                    x * self.cell_size,
                    y * self.cell_size,
                    self.cell_size,
                    self.cell_size,
                )
                cell = self.grid[y][x]

                if cell is None:
                    # Rien, le fond damier est déjà là
                    continue

                if isinstance(cell, Ingredient):
                    tile_rect = rect.inflate(-10, -10)
                    pygame.draw.rect(self.screen, (230, 230, 230), tile_rect, border_radius=8)

                    key = f"{cell.name}_{cell.state}" if cell.state != "cru" else f"{cell.name}_crue"
                    img = self.images.get(key)
                    if img:
                        img_rect = img.get_rect(center=rect.center)
                        self.screen.blit(img, img_rect.topleft)

                elif isinstance(cell, Tool):
                    img = self.images.get(cell.tool_type)
                    if img:
                        img_rect = img.get_rect(center=rect.center)
                        self.screen.blit(img, img_rect.topleft)
                    else:
                        tile_rect = rect.inflate(-10, -10)
                        pygame.draw.rect(self.screen, (170, 170, 170), tile_rect, border_radius=8)

                elif isinstance(cell, str):
                    img_key = None
                    if cell == "assembly_table":
                        img_key = "assembly_table"
                    elif cell == "counter":
                        img_key = "counter"

                    if img_key:
                        img = self.images.get(img_key)
                        if img:
                            img_rect = img.get_rect(center=rect.center)
                            self.screen.blit(img, img_rect.topleft)
                        else:
                            pygame.draw.rect(
                                self.screen,
                                (180, 170, 150),
                                rect.inflate(-8, -8),
                                border_radius=6,
                            )

        # --- Ingrédients sur la table d'assemblage partagée ---
        if self.shared_assembly_table and not (self.current_dish_image and self.current_dish_pos):
            for idx, ingredient in enumerate(self.shared_assembly_table):
                if ingredient.position:
                    ix, iy = ingredient.position
                    key = (
                        f"{ingredient.name}_{ingredient.state}"
                        if ingredient.state != "cru"
                        else f"{ingredient.name}_crue"
                    )
                    img = self.images.get(key)
                    if img:
                        small_img = pygame.transform.smoothscale(img, (25, 25))
                        base_x = ix * self.cell_size + self.cell_size // 2
                        base_y = iy * self.cell_size + self.cell_size // 2

                        offset_x = (idx % 3 - 1) * 10
                        offset_y = (idx // 3 - 1) * 10
                        self.screen.blit(
                            small_img,
                            (base_x + offset_x - 12, base_y + offset_y - 12),
                        )

        # --- Plats sur le comptoir ---
        for dish_data in self.counter_dishes:
            dish_img = dish_data['image']
            dx, dy = dish_data['position']
            offset = dish_data.get('offset', 0)

            rect = pygame.Rect(
                dx * self.cell_size,
                dy * self.cell_size,
                self.cell_size,
                self.cell_size,
            )
            img_rect = dish_img.get_rect(center=rect.center)
            img_rect.x += offset
            self.screen.blit(dish_img, img_rect.topleft)

        # --- Agents ---
        if agents:
            agent_colors = [(0, 100, 255), (255, 130, 60), (120, 60, 200)]

            for idx, agent in enumerate(agents):
                ax, ay = agent.position
                rect = pygame.Rect(
                    ax * self.cell_size,
                    ay * self.cell_size,
                    self.cell_size,
                    self.cell_size,
                )

                # ombre sous le cuisinier
                shadow_rect = pygame.Rect(
                    0, 0,
                    int(self.cell_size * 0.6),
                    int(self.cell_size * 0.22),
                )
                shadow_rect.center = (rect.centerx, rect.bottom - 5)
                pygame.draw.ellipse(self.screen, (180, 180, 180), shadow_rect)

                agent_img_key = f"agent_{agent.direction}"
                agent_img = self.images.get(agent_img_key)

                if agent_img:
                    img_rect = agent_img.get_rect(center=rect.center)
                    self.screen.blit(agent_img, img_rect.topleft)
                else:
                    # Fallback: cercle coloré
                    color = agent_colors[idx % len(agent_colors)]
                    radius = self.cell_size // 3
                    pygame.draw.circle(self.screen, color, rect.center, radius)

                # Ingrédient porté
                if hasattr(agent, 'holding') and agent.holding and isinstance(agent.holding, Ingredient):
                    key = (
                        f"{agent.holding.name}_{agent.holding.state}"
                        if agent.holding.state != "cru"
                        else f"{agent.holding.name}_crue"
                    )
                    ing_img = self.images.get(key)
                    if ing_img:
                        small_img = pygame.transform.smoothscale(ing_img, (30, 30))
                        img_rect = small_img.get_rect(midbottom=(rect.centerx, rect.top - 2))
                        self.screen.blit(small_img, img_rect.topleft)

        # --- Plat en transit ---
        if self.current_dish_image and self.current_dish_pos:
            x, y = self.current_dish_pos
            rect = pygame.Rect(
                x * self.cell_size,
                y * self.cell_size,
                self.cell_size,
                self.cell_size,
            )
            img_rect = self.current_dish_image.get_rect(center=rect.center)
            self.screen.blit(self.current_dish_image, img_rect.topleft)

        # --- Interface bas ---
        ui_y = self.height * self.cell_size
        ui_rect = pygame.Rect(0, ui_y, self.width * self.cell_size, 200)
        pygame.draw.rect(self.screen, UI_BG, ui_rect)
        pygame.draw.line(self.screen, UI_BORDER, (0, ui_y), (ui_rect.width, ui_y), 2)

        font = self.font
        small_font = self.small_font

        # Score
        score_text = font.render(f"Score: {score}", True, SCORE_GREEN)
        self.screen.blit(score_text, (10, ui_y + 10))

        # Actions des agents
        if agents:
            action_y = ui_y + 45
            for idx, agent in enumerate(agents):
                txt = small_font.render(
                    f"Agent {idx + 1}: {getattr(agent, 'current_action', 'En attente')}",
                    True,
                    TEXT_MAIN,
                )
                self.screen.blit(txt, (10, action_y + idx * 22))

        # Commande actuelle (texte simplifié)
        if current_order:
            if isinstance(current_order, str):
                order_text = current_order
            else:
                order_text = f"Commande: {current_order}"
            text_order = font.render(order_text, True, (30, 60, 160))
            self.screen.blit(text_order, (350, ui_y + 10))

        # Instructions
        instructions_text = small_font.render(
            "Cliquez sur un bouton pour choisir une recette | Q = Quitter",
            True,
            TEXT_MUTED,
        )
        self.screen.blit(instructions_text, (10, ui_y + 120))

        # Boutons (si le parent en fournit)
        if show_buttons and hasattr(self, "_draw_recipe_buttons_internal"):
            return self._draw_recipe_buttons_internal()

        pygame.display.flip()
        return []
