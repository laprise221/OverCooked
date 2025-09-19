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
            ]
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
            print(f"✅ Recette {recipe_name} livrée avec succès ! +10 points")
            self.score += 10
            return True
        else:
            print(f"❌ Mauvais plat livré.\nAttendu: {expected}\nReçu: {delivered_items}")
            return False
