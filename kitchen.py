import pygame
from objects import Ingredient, Tool, Station


class Kitchen:
    """
    Représente la cuisine complète avec toutes ses zones
    """

    def __init__(self, width=16, height=16, cell_size=50):
        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.grid = [[None for _ in range(width)] for _ in range(height)]
        self.current_dish_image = None
        self.current_dish_pos = None

        # Initialisation Pygame
        pygame.init()
        self.screen = pygame.display.set_mode((width * cell_size, height * cell_size + 200))
        pygame.display.set_caption("Overcooked - Agent Autonome")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 20)

        # Données internes
        self.ingredients_available = []
        self.tools = []
        self.stations = {}
        self.colors = {}

        # Configuration de la cuisine
        self._setup_kitchen()
        self._load_images()

        print(f"🍳 Kitchen initialisée ({width}x{height})")

    # ----------------------------------------------------------------------
    def _setup_kitchen(self):
        """Configure toutes les zones de la cuisine"""

        # Zone des ingrédients (haut gauche) - Grille 16x16
        self.stations['ingredients'] = Station('ingredients', (1, 1), (7, 3))

        ingredient_positions = [
            (1, 1, "salade"), (2, 1, "tomate"), (3, 1, "oignon"),
            (4, 1, "pain"), (5, 1, "viande"), (6, 1, "fromage"),
            (7, 1, "pate"),
        ]

        for x, y, name in ingredient_positions:
            ing = Ingredient(name, "cru", (x, y))
            self.ingredients_available.append(ing)
            self.grid[y][x] = ing

        # Zone de découpe (droite haut)
        self.stations['cutting'] = Station('cutting', (13, 1), (2, 1))
        for pos in [(13, 1), (14, 1)]:
            tool = Tool('planche', pos)
            self.tools.append(tool)
            self.grid[pos[1]][pos[0]] = tool

        # Zone de cuisson (droite milieu)
        self.stations['cooking'] = Station('cooking', (13, 4), (2, 1))
        for pos in [(13, 4), (14, 4)]:
            tool = Tool('poele', pos)
            self.tools.append(tool)
            self.grid[pos[1]][pos[0]] = tool

        # Table centrale (assemblage) - UNE SEULE CASE
        self.stations['assembly'] = Station('assembly', (8, 8), (1, 1))
        self.grid[8][8] = 'assembly_table'

        # Comptoir (livraison) - UNE SEULE CASE
        self.stations['counter'] = Station('counter', (3, 12), (1, 1))
        self.grid[12][3] = 'counter'

    # ----------------------------------------------------------------------
    def _load_images(self):
        """Charge toutes les images des ingrédients et outils"""
        import os

        base_path = os.path.join(os.path.dirname(__file__), "images")
        self.images = {}
        self.colors = {}

        def load(name):
            path = os.path.join(base_path, name)
            try:
                img = pygame.image.load(path).convert_alpha()
                return pygame.transform.smoothscale(img, (self.cell_size - 10, self.cell_size - 10))
            except FileNotFoundError:
                print(f"⚠️ Image manquante: {name}")
                return None

        # Ingrédients crus
        for name in ["salade", "tomate", "oignon", "viande", "pain", "fromage", "pate"]:
            self.images[f"{name}_crue"] = load(f"{name}_crue.png")

        # Ingrédients transformés
        self.images["salade_coupe"] = load("salade_coupe.png")
        self.images["tomate_coupe"] = load("tomate_coupe.png")
        self.images["oignon_coupe"] = load("oignon_coupe.png")
        self.images["viande_cuit"] = load("viande_cuit.png")

        # Outils et zones
        self.images["planche"] = load("planche.png")
        self.images["poele"] = load("poele.png")
        self.images["assembly_table"] = load("table.png")
        self.images["counter"] = load("counter.png")

        # Images de l'agent selon la direction
        self.images["agent_CD"] = load("agent_CD.png")  # Dos
        self.images["agent_CDR"] = load("agent_CDR.png")  # Droite
        self.images["agent_CF"] = load("agent_CF.png")  # Face
        self.images["agent_CG"] = load("agent_CG.png")  # Gauche

        # Couleurs de base
        self.colors["floor"] = (240, 240, 220)
        self.colors["agent"] = (0, 100, 255)

    # ----------------------------------------------------------------------
    def draw(self, agent, current_order=None, score=0, show_buttons=False):
        """Dessine toute la cuisine"""
        self.screen.fill((240, 240, 220))

        # Grille
        for y in range(self.height):
            for x in range(self.width):
                rect = pygame.Rect(x * self.cell_size, y * self.cell_size, self.cell_size, self.cell_size)
                cell = self.grid[y][x]

                if cell is None:
                    pygame.draw.rect(self.screen, self.colors['floor'], rect)
                elif isinstance(cell, Ingredient):
                    pygame.draw.rect(self.screen, (200, 200, 200), rect)
                    key = f"{cell.name}_{cell.state}" if cell.state != "cru" else f"{cell.name}_crue"
                    img = self.images.get(key)
                    if img:
                        offset = 5
                        self.screen.blit(img, (x * self.cell_size + offset, y * self.cell_size + offset))
                elif isinstance(cell, Tool):
                    img = self.images.get(cell.tool_type)
                    if img:
                        self.screen.blit(img, (x * self.cell_size + 5, y * self.cell_size + 5))
                    else:
                        pygame.draw.rect(self.screen, (150, 150, 150), rect)
                elif isinstance(cell, str):
                    # Affiche l'image de la table ou du comptoir
                    if cell == "assembly_table":
                        img = self.images.get("assembly_table")
                        if img:
                            self.screen.blit(img, (x * self.cell_size + 5, y * self.cell_size + 5))
                        else:
                            pygame.draw.rect(self.screen, (139, 90, 43), rect)
                    elif cell == "counter":
                        img = self.images.get("counter")
                        if img:
                            self.screen.blit(img, (x * self.cell_size + 5, y * self.cell_size + 5))
                        else:
                            pygame.draw.rect(self.screen, (180, 180, 160), rect)
                    else:
                        color = self.colors.get(cell, (200, 200, 200))
                        pygame.draw.rect(self.screen, color, rect)

                pygame.draw.rect(self.screen, (200, 200, 200), rect, 1)

        # Dessine les ingrédients assemblés sur la table (AVANT le plat)
        if not (self.current_dish_image and self.current_dish_pos):
            # N'affiche les ingrédients QUE si le plat n'est pas encore créé
            for ingredient in agent.assembled_ingredients:
                if ingredient.position:
                    ix, iy = ingredient.position
                    key = f"{ingredient.name}_{ingredient.state}" if ingredient.state != "cru" else f"{ingredient.name}_crue"
                    img = self.images.get(key)
                    if img:
                        # Réduit l'image pour les ingrédients sur la table
                        small_img = pygame.transform.scale(img, (25, 25))
                        # Décale légèrement pour éviter la superposition
                        idx = agent.assembled_ingredients.index(ingredient)
                        offset_x = (idx * 10) % 30
                        offset_y = (idx * 10) // 30 * 10
                        self.screen.blit(small_img,
                                         (ix * self.cell_size + 10 + offset_x, iy * self.cell_size + 10 + offset_y))

        # Agent - Utilise l'image selon la direction
        ax, ay = agent.position
        agent_img_key = f"agent_{agent.direction}"
        agent_img = self.images.get(agent_img_key)

        if agent_img:
            # Affiche l'image de l'agent
            self.screen.blit(agent_img, (ax * self.cell_size + 5, ay * self.cell_size + 5))
        else:
            # Fallback sur le cercle bleu si l'image n'existe pas
            agent_rect = pygame.Rect(ax * self.cell_size + 5, ay * self.cell_size + 5,
                                     self.cell_size - 10, self.cell_size - 10)
            pygame.draw.circle(self.screen, self.colors['agent'], agent_rect.center, self.cell_size // 4)

        # Dessine l'ingrédient porté par l'agent (si c'est un simple ingrédient)
        if agent.holding and isinstance(agent.holding, Ingredient):
            key = f"{agent.holding.name}_{agent.holding.state}" if agent.holding.state != "cru" else f"{agent.holding.name}_crue"
            ing_img = self.images.get(key)
            if ing_img:
                # Réduit l'image pour qu'elle soit plus petite
                small_img = pygame.transform.scale(ing_img, (30, 30))
                # Position au-dessus de l'agent
                img_x = ax * self.cell_size + self.cell_size // 2 - 15
                img_y = ay * self.cell_size + 5
                self.screen.blit(small_img, (img_x, img_y))

        # Interface en bas
        font = self.font
        ui_y = self.height * self.cell_size

        # Score
        score_text = font.render(f"Score: {score}", True, (0, 100, 0))
        self.screen.blit(score_text, (10, ui_y + 10))

        # Action
        text_action = font.render(f"Action: {agent.current_action}", True, (0, 0, 0))
        self.screen.blit(text_action, (10, ui_y + 40))

        # Commande actuelle
        if current_order:
            text_order = font.render(f"Commande: {current_order}", True, (0, 0, 150))
            self.screen.blit(text_order, (10, ui_y + 70))

        # Instructions
        instructions_text = self.small_font.render("Cliquez sur un bouton pour choisir une recette | Q = Quitter", True,
                                                   (0, 0, 0))
        self.screen.blit(instructions_text, (10, ui_y + 100))

        # Dessine le plat si présent
        if self.current_dish_image and self.current_dish_pos:
            x, y = self.current_dish_pos
            rect_x = x * self.cell_size + self.cell_size // 4
            rect_y = y * self.cell_size + self.cell_size // 4
            self.screen.blit(self.current_dish_image, (rect_x, rect_y))

        # Ne dessine les boutons que si demandé
        if show_buttons:
            return self._draw_recipe_buttons_internal()

        pygame.display.flip()
        return []

    # ----------------------------------------------------------------------
    def _draw_recipe_buttons_internal(self):
        """Dessine les boutons de sélection de recettes (interne)"""
        from recipes import get_all_recipe_names
        recipes_list = get_all_recipe_names()

        button_y = self.height * self.cell_size + 130
        button_width = 150
        button_height = 40
        button_spacing = 20
        buttons = []

        for i, recipe_name in enumerate(recipes_list):
            button_x = 10 + i * (button_width + button_spacing)
            button_rect = pygame.Rect(button_x, button_y, button_width, button_height)

            # Dessine le bouton
            pygame.draw.rect(self.screen, (100, 150, 255), button_rect)
            pygame.draw.rect(self.screen, (0, 0, 0), button_rect, 2)

            # Texte du bouton
            button_text = self.small_font.render(recipe_name.capitalize(), True, (255, 255, 255))
            text_rect = button_text.get_rect(center=button_rect.center)
            self.screen.blit(button_text, text_rect)

            buttons.append((button_rect, recipe_name))

        pygame.display.flip()
        return buttons

    # ----------------------------------------------------------------------
    def is_walkable(self, position):
        """Vérifie si une position est accessible"""
        x, y = position

        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return False
        cell = self.grid[y][x]
        if cell is None:
            return True
        if isinstance(cell, str) and cell in ("assembly_table", "counter"):
            return True
        # Les outils et ingrédients ne sont PAS marchables
        if isinstance(cell, (Tool, Ingredient)):
            return False
        return False

    # ----------------------------------------------------------------------
    def get_available_tool(self, tool_type):
        """Retourne un outil disponible d'un type donné"""
        for tool in self.tools:
            if tool.tool_type == tool_type and not tool.occupied:
                return tool
        return None

    # ----------------------------------------------------------------------
    def update(self):
        """Met à jour l'affichage"""
        self.clock.tick(10)  # 10 FPS pour bien voir les déplacements

    def spawn_dish_image(self, recipe_name, position):
        """Affiche le plat sur la table d'assemblage"""
        from recipes import recipes
        import os

        recipe_data = recipes.get(recipe_name)
        if not recipe_data or "image" not in recipe_data:
            return

        try:
            image_path = os.path.join(os.path.dirname(__file__), recipe_data["image"])
            self.current_dish_image = pygame.image.load(image_path)
            self.current_dish_image = pygame.transform.scale(self.current_dish_image, (40, 40))
            self.current_dish_pos = list(position)
            print(f"🍔 Image du plat {recipe_name} affichée sur la table !")
        except Exception as e:
            print(f"⚠️ Erreur chargement plat {recipe_name}: {e}")

    def remove_dish_image(self):
        """Supprime l'image du plat (après livraison)"""
        print("🧺 Plat retiré du comptoir")
        self.current_dish_image = None
        self.current_dish_pos = None

    def move_dish_image(self, new_position):
        """Déplace visuellement le plat si présent"""
        if self.current_dish_image and self.current_dish_pos:
            self.current_dish_pos = list(new_position)