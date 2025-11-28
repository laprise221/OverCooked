"""
objects.py
Définit les classes pour tous les objets du jeu : ingrédients, outils, plats
"""

class Ingredient:
    """
    Représente un ingrédient avec son état actuel
    """

    def __init__(self, name, state="crue", position=None):
        self.name = name
        self.state = state
        self.position = position

    def transform(self, new_state):
        """Change l'état visuel de l'ingrédient"""
        self.state = new_state

    def _get_image_path(self):
        """Retourne le chemin de l'image selon l'état"""
        if self.state == "coupe":
            return f"images/{self.name}_coupe.png"
        elif self.state == "cuit":
            return f"images/{self.name}_cuit.png"
        else:
            return f"images/{self.name}.png"

    def cut(self):
        """Change l'état de l'ingrédient en 'coupe'."""
        if self.state in ["crue", "cru", "raw"]:
            self.state = "coupe"

    def cook(self):
        """Change l'état de l'ingrédient en 'cuit'."""
        if self.state in ["crue", "cru", "raw", "coupe", "cut"]:
            self.state = "cuit"

    def get_full_name(self):
        """Retourne le nom complet avec l'état"""
        if self.state == "coupe":
            return f"{self.name}_coupe"
        elif self.state == "cuit":
            return f"{self.name}_cuit"
        return self.name

    def __repr__(self):
        return f"Ingredient({self.name}, {self.state})"


# ----------------------------------------------------------------------
class Tool:
    """Représente un outil (planche à découper, poêle)"""

    def __init__(self, tool_type, position):
        self.tool_type = tool_type  # "planche", "poele"
        self.position = position
        self.occupied = False
        self.current_item = None
        self.image_path = f"images/{tool_type}.png"

    def use(self, ingredient):
        """Utilise l'outil sur un ingrédient"""
        if self.occupied:
            return False

        self.occupied = True
        self.current_item = ingredient

        if self.tool_type == "planche":
            ingredient.cut()
        elif self.tool_type == "poele":
            ingredient.cook()

        print(f"✅ {ingredient.name} est maintenant {ingredient.state}")
        return True

    def release(self):
        """Libère l'outil et retourne l'ingrédient traité"""
        if self.current_item:
            item = self.current_item
            self.current_item = None
            self.occupied = False
            return item
        return None

    def __repr__(self):
        return f"Tool({self.tool_type}, occupied={self.occupied})"


# ----------------------------------------------------------------------
class Dish:
    """Représente un plat assemblé"""

    def __init__(self, recipe_name, ingredients):
        self.recipe_name = recipe_name
        self.ingredients = ingredients  # Liste d'objets Ingredient
        self.completed = False
        self.image_path = f"images/{recipe_name}.png"
        self.position = None

    def is_complete(self, required_ingredients):
        """Vérifie si le plat contient tous les ingrédients requis"""
        current_ingredients = [ing.get_full_name() for ing in self.ingredients]
        return sorted(current_ingredients) == sorted(required_ingredients)

    def __repr__(self):
        return f"Dish({self.recipe_name}, {len(self.ingredients)} ingredients)"


# ----------------------------------------------------------------------
class Station:
    """Représente une station de travail (zone ingrédients, table, comptoir)"""

    def __init__(self, station_type, position, size=(1, 1)):
        self.station_type = station_type
        self.position = position  # (x, y)
        self.size = size  # (width, height)
        self.items = []  # Liste d'objets présents

    def add_item(self, item):
        """Ajoute un objet à la station"""
        self.items.append(item)
        item.position = self.position

    def remove_item(self, item):
        """Retire un objet de la station"""
        if item in self.items:
            self.items.remove(item)
            return True
        return False

    def get_items(self):
        """Retourne tous les objets présents"""
        return self.items

    def __repr__(self):
        return f"Station({self.station_type}, {len(self.items)} items)"
