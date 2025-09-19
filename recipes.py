# recipes.py
class RecipeManager:
    def __init__(self):
        self.recipes = {
            "salade": ["tomate"]
        }
        self.score = 0

    def check_delivery(self, item):
        for recipe, ingredients in self.recipes.items():
            if item in ingredients:
                self.score += 10
                print(f"Plat {recipe} réussi ! +10 points")
                return True
        print("Plat incorrect : 0 point")
        return False
