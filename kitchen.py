import pygame
from objects import Ingredient, Tool, Station

class Kitchen:
    def __init__(self, width=13, height=13, cell_size=60):
        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.grid = [[None for _ in range(width)] for _ in range(height)]
        self.current_dish_image = None
        self.current_dish_pos = None

        # Initialisation Pygame
        pygame.init()
        self.screen = pygame.display.set_mode((width * cell_size, height * cell_size + 100))
        pygame.display.set_caption("Overcooked - Agent Autonome")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 28)

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
        """Configure toutes les zones de la cuisine avec meilleure disposition"""
        # Zone des ingrédients
        self.stations['ingredients'] = Station('ingredients', (1, 0), (7, 0))
        ingredient_positions = [
            (1, 0, "salade"), (2, 0, "tomate"), (3, 0, "oignon"),
            (4, 0, "pain"), (5, 0, "viande"), (6, 0, "fromage"),
            (7, 0, "pate")
        ]
        for x, y, name in ingredient_positions:
            ing = Ingredient(name, "cru", (x, y))
            self.ingredients_available.append(ing)
            self.grid[y][x] = ing

        # Zone de découpe (planche)
        self.stations['cutting'] = Station('cutting', (10, 0), (2, 1))
        for pos in [(10, 0), (11, 0)]:
            tool = Tool('planche', pos)
            self.tools.append(tool)
            self.grid[pos[1]][pos[0]] = tool

        # Zone de cuisson (poêle)
        self.stations['cooking'] = Station('cooking', (11, 1), (1, 2))
        for pos in [(11, 1), (11, 2)]:
            tool = Tool('poele', pos)
            self.tools.append(tool)
            self.grid[pos[1]][pos[0]] = tool

        # Table centrale (assemblage)
        self.stations['assembly'] = Station('assembly', (4, 6), (2, 2))
        for y in range(6, 8):
            for x in range(4, 6):
                self.grid[y][x] = 'assembly_table'

        # Comptoir (livraison)
        self.stations['counter'] = Station('counter', (1, 10), (3, 1))
        for x in range(1, 4):
            self.grid[10][x] = 'counter'

    # ----------------------------------------------------------------------
    def _load_images(self):
        """Charge toutes les images des ingrédients, outils et agent"""
        import os

        base_path = os.path.join(os.path.dirname(__file__), "images")
        self.images = {}
        self.colors = {}

        def load(name):
            path = os.path.join(base_path, name)
            try:
                img = pygame.image.load(path).convert_alpha()
                return pygame.transform.smoothscale(img, (self.cell_size - 16, self.cell_size - 16))
            except FileNotFoundError:
                print(f"⚠️ Image manquante: {name}")
                return None

        # Ingrédients crus et transformés
        for name in ["salade", "tomate", "oignon", "viande","pain","fromage","pate"]:
            self.images[f"{name}_crue"] = load(f"{name}_crue.png")
        self.images["salade_coupe"] = load("salade_coupe.png")
        self.images["tomate_coupe"] = load("tomate_coupe.png")
        self.images["oignon_coupe"] = load("oignon_coupe.png")
        self.images["viande_cuit"] = load("viande_cuit.png")

        # Outils et zones
        self.images["planche"] = load("planche.png")
        self.images["poele"] = load("poele.png")
        self.images["assembly_table"] = load("table.png")
        self.images["counter"] = load("counter.png")

        # Images de l’agent selon la direction
        for dir in ["CD", "CDR", "CG", "CF"]:
            self.images[f"agent_{dir}"] = load(f"agent_{dir}.png")

        # Couleurs de base
        self.colors["floor"] = (240, 240, 220)
        self.colors["agent"] = (0, 100, 255)

    # ----------------------------------------------------------------------
    def draw(self, agent, current_order=None):
        """Dessine toute la cuisine"""
        self.screen.fill(self.colors["floor"])

        # Grille
        for y in range(self.height):
            for x in range(self.width):
                rect = pygame.Rect(x * self.cell_size, y * self.cell_size, self.cell_size, self.cell_size)
                cell = self.grid[y][x]

                if cell is None:
                    pygame.draw.rect(self.screen, self.colors['floor'], rect)
                elif isinstance(cell, Ingredient):
                    key = f"{cell.name}_{cell.state}" if cell.state != "cru" else f"{cell.name}_crue"
                    img = self.images.get(key)
                    if img:
                        self.screen.blit(img, (x * self.cell_size + 8, y * self.cell_size + 8))
                    else:
                        pygame.draw.rect(self.screen, (220, 220, 220), rect)
                elif isinstance(cell, Tool):
                    img = self.images.get(cell.tool_type)
                    if img:
                        self.screen.blit(img, (x * self.cell_size + 5, y * self.cell_size + 5))
                    else:
                        pygame.draw.rect(self.screen, (150, 150, 150), rect)
                elif isinstance(cell, str):
                    color = self.colors.get(cell, (200, 200, 200))
                    pygame.draw.rect(self.screen, color, rect)

                pygame.draw.rect(self.screen, (200, 200, 200), rect, 1)

        # Agent
        agent_img = self.images.get(f"agent_{getattr(agent, 'direction', 'CD')}")
        if agent_img:
            self.screen.blit(agent_img, agent.pixel_pos)
        else:
            pygame.draw.circle(self.screen, self.colors['agent'],
                            (int(agent.pixel_pos[0] + self.cell_size//2),
                                int(agent.pixel_pos[1] + self.cell_size//2)),
                            self.cell_size // 3)



        # Texte d'état
        font = self.font
        text_action = font.render(f"Action: {agent.current_action}", True, (0, 0, 0))
        self.screen.blit(text_action, (10, self.height * self.cell_size + 10))
        if current_order:
            text_order = font.render(f"Commande: {current_order}", True, (0, 0, 0))
            self.screen.blit(text_order, (300, self.height * self.cell_size + 10))
        choices_text = font.render("1 = Burger    2 = Sandwich    3 = Pizza    Q = Quitter", True, (0, 0, 0))
        self.screen.blit(choices_text, (10, self.height * self.cell_size + 50))

        # Plat sur table
        if self.current_dish_image and self.current_dish_pos:
            x, y = self.current_dish_pos
            self.screen.blit(self.current_dish_image,
                             (x * self.cell_size + self.cell_size//4,
                              y * self.cell_size + self.cell_size//4))

        pygame.display.flip()

    # ----------------------------------------------------------------------
    def is_walkable(self, position):
        x, y = position
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return False
        cell = self.grid[y][x]
        if cell is None:
            return True
        if isinstance(cell, str) and cell in ("assembly_table", "counter"):
            return True
        if isinstance(cell, Ingredient):
            return True
        if hasattr(cell, "occupied") and not cell.occupied:
            return True
        return False

    # ----------------------------------------------------------------------
    def get_available_tool(self, tool_type):
        for tool in self.tools:
            if tool.tool_type == tool_type and not tool.occupied:
                return tool
        return None

    # ----------------------------------------------------------------------
    def update(self):
        self.clock.tick(10)  # 10 FPS

    def spawn_dish_image(self, recipe_name, position):
        from recipes import recipes
        import os
        recipe_data = recipes.get(recipe_name)
        if not recipe_data or "image" not in recipe_data:
            return
        try:
            image_path = os.path.join(os.path.dirname(__file__), recipe_data["image"])
            self.current_dish_image = pygame.image.load(image_path)
            self.current_dish_image = pygame.transform.scale(self.current_dish_image, (60, 60))
            self.current_dish_pos = list(position)
        except Exception as e:
            print(f"⚠️ Erreur chargement plat {recipe_name}: {e}")

    def remove_dish_image(self):
        self.current_dish_image = None
        self.current_dish_pos = None

    def move_dish_image(self, new_position):
        if self.current_dish_image:
            self.current_dish_pos = list(new_position)
