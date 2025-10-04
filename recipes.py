class RecipeManager:
    def __init__(self):
        self.recipes = {
            "sandwich": [
                {"ingredient": "pain"},
                {"ingredient": "viande", "action": "cuire"},
                {"ingredient": "salade", "action": "couper"},
            ],
            "salade": [
                {"ingredient": "salade", "action": "couper"},
                {"ingredient": "tomate", "action": "couper"},
                {"ingredient": "oignon", "action": "couper"},
            ],
            "pizza": [
                {"ingredient": "pate"},
                {"ingredient": "fromage","action": "couper"},
                {"ingredient": "tomate", "action": "couper"},
                {"ingredient": "oignon", "action": "cuire"},
            ],
            "burger": [
                {"ingredient": "pain"},
                {"ingredient": "viande", "action": "cuire"},
                {"ingredient": "fromage","action": "couper"},
                {"ingredient": "salade", "action": "couper"},
            ],
        }

        # Points attribués par recette
        self.recipe_points = {
            "burger": 100,
            "pizza": 120,
            "salade": 80,
            "sandwich": 90
        }

        self.score = 0

    def get_recipe(self, name):
        return self.recipes.get(name, [])

    def check_delivery(self, delivered_items, recipe_name):
        expected_steps = self.recipes.get(recipe_name, [])
        expected = []
        for step in expected_steps:
            ingredient = step["ingredient"]
            action = step.get("action")
            if action == "couper":
                expected.append(f"{ingredient}_coupé")
            elif action == "cuire":
                expected.append(f"{ingredient}_cuit")
            else:
                expected.append(ingredient)

        if sorted(expected) == sorted(delivered_items):
            points = self.recipe_points.get(recipe_name, 100)
            print(f"✅ Recette {recipe_name} livrée avec succès ! +{points} points")
            self.score += points
            return True
        else:
            print(f"❌ Mauvais plat livré.\nAttendu: {expected}\nReçu: {delivered_items}")
            return False
