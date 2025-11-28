"""
multi_agent/kitchen.py
Version Debug & Robuste
"""

import sys
import os
import pygame
import random
import math

# Permet d'importer depuis le dossier parent (common.*)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.kitchen_base import Kitchen as KitchenBase
from common.objects import Ingredient, Tool

# === THEME VISUEL ===
GRID_BG = (246, 244, 235)
GRID_ALT_BG = (238, 236, 222)
GRID_LINE = (220, 215, 200)
UI_BG = (252, 252, 248)
UI_BORDER = (210, 210, 200)
TEXT_MAIN = (40, 40, 40)
TEXT_MUTED = (110, 110, 110)
SCORE_GREEN = (20, 140, 60)


class Kitchen(KitchenBase):
    def __init__(self, width=16, height=16, cell_size=50):
        super().__init__(width, height, cell_size)

        self.resource_locks = {
            'cutting_board': set(),
            'stove': set(),
            'assembly': set(),
            'counter': set()
        }
        self.resource_capacity = {
            'cutting_board': 0,
            'stove': 0,
            'assembly': 1,
            'counter': 1
        }
        self.shared_assembly_table = []

        if hasattr(self, "colors"):
            self.colors.setdefault("floor", GRID_BG)
            self.colors.setdefault("agent", (0, 100, 255))

        print("🔒 Kitchen multi-agent initialisée.")
        self._compute_resource_capacity()

    # ------------------------------------------------------------------
    # 1. Génération Robustifiée
    # ------------------------------------------------------------------

    def generate_dynamic_kitchen(self, nb_assembly=1, nb_stoves=2, nb_cutting_boards=2):
        """
        Génération qui force la présence des outils même si la map de base est vide.
        Garantit 1 seule table de livraison (counter).
        """
        # 1. Identifier les candidats (Comptoirs ou vides sur les bords)
        candidates = []
        existing_tools = {
            'stove': [], 
            'cutting_board': [], 
            'assembly_table': [],
            'counter': []
        }

        # Scan de la grille actuelle
        for y in range(self.height):
            for x in range(self.width):
                cell = self.grid[y][x]

                # Est-ce un outil déjà là ?
                if isinstance(cell, Tool):
                    # Normalisation des noms d'outil pour éviter les alias
                    tool_type = cell.tool_type
                    if tool_type == 'planche':
                        tool_type = 'cutting_board'
                    elif tool_type == 'poele':
                        tool_type = 'stove'
                    if tool_type in existing_tools:
                        existing_tools[tool_type].append((x, y))
                elif cell == 'assembly_table':
                    existing_tools['assembly_table'].append((x, y))
                elif cell == 'counter':
                    existing_tools['counter'].append((x, y))

                # Est-ce un emplacement libre pour construire ?
                # On accepte 'counter', None (vide), ou 'X' (mur générique) si c'est sur les bords
                is_edge = (x == 0 or x == self.width - 1 or y == 0 or y == self.height - 1)
                is_counter = (cell == 'counter')
                is_empty = (cell is None)

                if is_counter or (is_edge and is_empty):
                    # On évite les coins (souvent bloqués)
                    if not ((x == 0 and y == 0) or (x == self.width - 1 and y == 0) or
                            (x == 0 and y == self.height - 1) or (x == self.width - 1 and y == self.height - 1)):
                        candidates.append((x, y))

        # Si on a peu de candidats (map vide), on force les bords
        if len(candidates) < 5:
            print("⚠️ Map vide détectée, utilisation des bordures par défaut.")
            for x in range(1, self.width - 1):
                candidates.append((x, 0))  # Haut
                candidates.append((x, self.height - 1))  # Bas

        random.shuffle(candidates)

        # 2. Fonction de placement
        def place_items(type_name, count, current_list, is_tool_obj=True):
            # Enlever le surplus
            while len(current_list) > count:
                cx, cy = current_list.pop()
                self.grid[cy][cx] = None  # Revert to floor (was 'counter')

            # Ajouter le manquant
            while len(current_list) < count and candidates:
                cx, cy = candidates.pop()
                if is_tool_obj:
                    # Création explicite de l'objet Tool
                    actual_tool_type = type_name
                    if type_name == 'cutting_board':
                        actual_tool_type = 'planche'
                    elif type_name == 'stove':
                        actual_tool_type = 'poele'
                    self.grid[cy][cx] = Tool(actual_tool_type, (cx, cy))
                else:
                    self.grid[cy][cx] = type_name  # String (ex: assembly_table)
                current_list.append((cx, cy))

        # 3. Application
        place_items('stove', nb_stoves, existing_tools['stove'], True)
        place_items('cutting_board', nb_cutting_boards, existing_tools['cutting_board'], True)
        place_items('assembly_table', nb_assembly, existing_tools['assembly_table'], False)
        
        # Placement explicite d'UN SEUL comptoir de livraison
        place_items('counter', 1, existing_tools['counter'], False)

        # Note: On NE remplit PLUS le reste avec des counters.
        # Les candidats non utilisés restent tels quels (None/Vide ou ce qu'ils étaient).

        self._compute_resource_capacity()
        print(f"🏗️ Cuisine générée: {nb_stoves} poêles, {nb_cutting_boards} planches, 1 comptoir.")

    def _compute_resource_capacity(self):
        """Compte le nombre de stations disponibles par type."""
        counts = {'cutting_board': 0, 'stove': 0, 'assembly': 0, 'counter': 0}
        for y in range(self.height):
            for x in range(self.width):
                cell = self.grid[y][x]
                if isinstance(cell, Tool):
                    tool_type = cell.tool_type
                    if tool_type == 'planche':
                        counts['cutting_board'] += 1
                    elif tool_type == 'poele':
                        counts['stove'] += 1
                elif isinstance(cell, str):
                    if cell == 'assembly_table':
                        counts['assembly'] += 1
                    elif cell == 'counter':
                        counts['counter'] += 1
        # Fallback à 1 pour éviter division par 0
        for key in counts:
            counts[key] = max(1, counts[key])
        self.resource_capacity.update(counts)
        # Réinitialiser les locks si structure changée
        for k in self.resource_locks:
            self.resource_locks[k] = set()

    # ------------------------------------------------------------------
    # 2. Intelligence Artificielle (CORRECTION ICI)
    # ------------------------------------------------------------------

    def get_best_available_resource(self, resource_type, agent_pos):
        """
        Recherche tolérante de ressources.
        Accepte 'cutting_board' même si la grille contient 'planche'.
        Privilégie les outils non occupés physiquement.
        """
        candidates = []

        # Liste d'alias pour être sûr de trouver
        aliases = [resource_type]
        if resource_type == 'cutting_board':
            aliases.extend(['planche', 'board', 'cutting'])
        elif resource_type == 'stove':
            aliases.extend(['poele', 'cooker', 'oven'])

        for y in range(self.height):
            for x in range(self.width):
                cell = self.grid[y][x]
                is_target = False
                is_occupied = False

                # Cas 1: C'est un objet Tool
                if isinstance(cell, Tool):
                    if cell.tool_type in aliases:
                        is_target = True
                        is_occupied = cell.occupied

                # Cas 2: C'est une string (ex: 'assembly_table')
                elif isinstance(cell, str):
                    if cell in aliases:
                        is_target = True

                if is_target:
                    candidates.append({'pos': (x, y), 'occupied': is_occupied})

        if not candidates:
            # DEBUG IMPORTANT : Regarde ta console quand ça arrive !
            # print(f"⚠️ DEBUG: Aucune ressource '{resource_type}' trouvée dans la grille !")
            return None

        # Trier par :
        # 1. Disponibilité (False < True, donc non occupé en premier)
        # 2. Distance
        ax, ay = agent_pos
        candidates.sort(key=lambda c: (c['occupied'], abs(c['pos'][0] - ax) + abs(c['pos'][1] - ay)))

        return candidates[0]['pos']

    # ------------------------------------------------------------------
    # 3. Locks & Render (Inchangés mais inclus pour copier-coller)
    # ------------------------------------------------------------------

    def try_lock_resource(self, resource_name: str, agent_id: int) -> bool:
        if resource_name not in self.resource_locks: 
            return True
        capacity = self.resource_capacity.get(resource_name, 1)
        holders = self.resource_locks[resource_name]
        if agent_id in holders:
            return True
        if len(holders) < capacity:
            holders.add(agent_id)
            return True
        return False

    def unlock_resource(self, resource_name: str, agent_id: int):
        if resource_name in self.resource_locks:
            self.resource_locks[resource_name].discard(agent_id)

    def is_resource_available(self, resource_name: str) -> bool:
        """Retourne True si la ressource n'est pas verrouillée"""
        if resource_name not in self.resource_locks:
            return True
        capacity = self.resource_capacity.get(resource_name, 1)
        return len(self.resource_locks[resource_name]) < capacity

    def get_resource_owner(self, resource_name: str):
        """Renvoie l'agent propriétaire du lock, None sinon"""
        if resource_name not in self.resource_locks:
            return None
        holders = self.resource_locks[resource_name]
        if not holders:
            return None
        if len(holders) == 1:
            return next(iter(holders))
        return holders

    def _draw_background(self):
        self.screen.fill(GRID_BG)
        for y in range(self.height):
            for x in range(self.width):
                if (x + y) % 2 != 0:
                    r = pygame.Rect(x * self.cell_size, y * self.cell_size, self.cell_size, self.cell_size)
                    pygame.draw.rect(self.screen, GRID_ALT_BG, r)

        w_px = self.width * self.cell_size
        h_px = self.height * self.cell_size
        for x in range(self.width + 1):
            px = x * self.cell_size
            pygame.draw.line(self.screen, GRID_LINE, (px, 0), (px, h_px), 1)
        for y in range(self.height + 1):
            py = y * self.cell_size
            pygame.draw.line(self.screen, GRID_LINE, (0, py), (w_px, py), 1)

    def draw(self, agents=None, current_order=None, score=0, show_buttons=False):
        if agents and not isinstance(agents, list): agents = [agents]
        self._draw_background()

        # Grille
        for y in range(self.height):
            for x in range(self.width):
                cell = self.grid[y][x]
                if cell is None: continue

                rect = pygame.Rect(x * self.cell_size, y * self.cell_size, self.cell_size, self.cell_size)

                if isinstance(cell, str):
                    img = self.images.get(cell)
                    if img:
                        self.screen.blit(img, img.get_rect(center=rect.center))
                    else:
                        c = (200, 190, 180) if cell == 'counter' else (200, 180, 100)
                        pygame.draw.rect(self.screen, c, rect.inflate(-4, -4), border_radius=4)

                elif isinstance(cell, Tool):
                    pygame.draw.rect(self.screen, (220, 215, 210), rect.inflate(-2, -2), border_radius=4)
                    # Essayer le nom anglais ET français pour l'image
                    img = self.images.get(cell.tool_type)
                    if not img and cell.tool_type == 'cutting_board': img = self.images.get('planche')
                    if not img and cell.tool_type == 'stove': img = self.images.get('poele')

                    if img:
                        self.screen.blit(img, img.get_rect(center=rect.center))
                    else:
                        # Debug visuel : Carré rouge si image manquante
                        pygame.draw.rect(self.screen, (200, 100, 100), rect.inflate(-10, -10))

                elif isinstance(cell, Ingredient):
                    pygame.draw.rect(self.screen, (230, 230, 230), rect.inflate(-8, -8), border_radius=6)
                    
                    # Mapping des états STRIPS vers les suffixes de fichiers (FR)
                    state_map = {
                        "cut": "coupe", 
                        "cooked": "cuit", 
                        "raw": "crue", 
                        "cru": "crue", 
                        "coupe": "coupe", 
                        "cuit": "cuit"
                    }
                    suffix = state_map.get(cell.state, cell.state)
                    k = f"{cell.name}_{suffix}"
                    
                    img = self.images.get(k)
                    if img: self.screen.blit(img, img.get_rect(center=rect.center))

        # Shared Assembly
        if self.shared_assembly_table:
            for idx, ing in enumerate(self.shared_assembly_table):
                if ing.position:
                    ix, iy = ing.position
                    
                    state_map = {"cut": "coupe", "cooked": "cuit", "raw": "crue"}
                    suffix = state_map.get(ing.state, "crue")
                    k = f"{ing.name}_{suffix}"
                    
                    img = self.images.get(k)
                    if img:
                        small = pygame.transform.smoothscale(img, (25, 25))
                        dest = (ix * self.cell_size + 12 + (idx % 2) * 5, iy * self.cell_size + 12 + (idx // 2) * 5)
                        self.screen.blit(small, dest)

        # Plats comptoir
        for d in self.counter_dishes:
            dx, dy = d['position']
            r = pygame.Rect(dx * self.cell_size, dy * self.cell_size, self.cell_size, self.cell_size)
            if d['image']: self.screen.blit(d['image'], d['image'].get_rect(center=r.center))

        # Agents
        if agents:
            colors = [(0, 100, 255), (255, 130, 60), (120, 60, 200), (50, 180, 50)]
            for idx, ag in enumerate(agents):
                ax, ay = ag.position
                rect = pygame.Rect(ax * self.cell_size, ay * self.cell_size, self.cell_size, self.cell_size)

                # Ombre
                s = pygame.Rect(0, 0, int(self.cell_size * 0.6), 10)
                s.center = (rect.centerx, rect.bottom - 5)
                pygame.draw.ellipse(self.screen, (100, 100, 100, 100), s)

                img_k = f"agent_{ag.direction}"
                img = self.images.get(img_k)
                if img:
                    self.screen.blit(img, img.get_rect(center=rect.center))
                else:
                    pygame.draw.circle(self.screen, colors[idx % 4], rect.center, 20)

                # Holding
                if hasattr(ag, 'holding') and ag.holding:
                    if isinstance(ag.holding, Ingredient):
                        state_map = {"cut": "coupe", "cooked": "cuit", "raw": "crue", "cru": "crue"}
                        suffix = state_map.get(ag.holding.state, ag.holding.state)
                        k = f"{ag.holding.name}_{suffix}"
                        
                        i_img = self.images.get(k)
                        if i_img:
                            s = pygame.transform.smoothscale(i_img, (30, 30))
                            self.screen.blit(s, s.get_rect(midbottom=(rect.centerx, rect.top + 5)))
                    elif isinstance(ag.holding, Tool):  # Plat
                        p = self.images.get("plate")
                        if p: self.screen.blit(p, p.get_rect(midbottom=(rect.centerx, rect.top + 5)))

        # UI Bas
        ui_y = self.height * self.cell_size
        pygame.draw.rect(self.screen, UI_BG, (0, ui_y, self.width * self.cell_size, 200))
        pygame.draw.line(self.screen, UI_BORDER, (0, ui_y), (self.width * self.cell_size, ui_y), 2)

        sc = self.font.render(f"Score: {score}", True, SCORE_GREEN)
        self.screen.blit(sc, (15, ui_y + 15))

        # Commande actuelle (à droite de Score)
        if current_order:
            if isinstance(current_order, str):
                order_text = current_order
            else:
                order_text = f"Commande: {current_order}"
            text_order = self.font.render(order_text, True, (30, 60, 160))
            self.screen.blit(text_order, (350, ui_y + 10))

        # Actions des agents (juste en dessous)
        if agents:
            action_y = ui_y + 40   # 2e ligne
            for idx, agent in enumerate(agents):
                txt = self.small_font.render(
                    f"Agent {idx + 1}: {getattr(agent, 'current_action', 'En attente')}",
                    True,
                    TEXT_MAIN,
                )
                self.screen.blit(txt, (10, action_y + idx * 20))

        # IMPORTANT : plus de show_buttons ici, plus de flip ici
        return []



