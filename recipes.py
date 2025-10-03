from typing import List, Dict, Tuple, Optional

class RecipeManager:
    def __init__(self):
        # Recettes : nom -> liste d'étapes (chaque étape est un dict avec ingredient + action optionnelle)
        self.recipes: Dict[str, List[Dict[str, str]]] = {
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
                {"ingredient": "fromage", "action": "couper"},
                {"ingredient": "tomate", "action": "couper"},
                {"ingredient": "oignon", "action": "cuire"},
            ],
            "burger": [
                {"ingredient": "pain"},
                {"ingredient": "viande", "action": "cuire"},
                {"ingredient": "fromage", "action": "couper"},
                {"ingredient": "salade", "action": "couper"},
            ],
        }

        # paramètres de score
        self.score = 0
        self.score_per_dish = 10
        self.penalty_burn = 5

    # ---------- utilitaires (venant du 1er code) ----------
    def get_recipe(self, name: str) -> List[Dict[str, str]]:
        """Retourne la liste d'étapes de la recette"""
        return self.recipes.get(name, [])

    def ingredients_for(self, dish_name: str) -> List[str]:
        """
        Retourne la liste simple des ingrédients (sans tenir compte des actions),
        utile si tu veux juste voir de quoi est composée une recette.
        """
        steps = self.recipes.get(dish_name, [])
        return [s["ingredient"] for s in steps]

    def reset(self):
        """Réinitialise le score"""
        self.score = 0

    def get_score(self) -> int:
        return self.score

    # ---------- validation (check_delivery avancé) ----------
    def check_delivery(self, delivered_items: List[str], recipe_name: str) -> bool:
        """
        Vérifie si les items livrés correspondent exactement à la recette (avec actions).
        Exemple attendu: ["pain", "viande_cuit", "salade_coupé"]
        """
        expected_steps = self.recipes.get(recipe_name, [])
        expected = []
        for step in expected_steps:
            ing = step["ingredient"]
            action = step.get("action")
            if action == "couper":
                expected.append(f"{ing}_coupé")
            elif action == "cuire":
                expected.append(f"{ing}_cuit")
            else:
                expected.append(ing)

        if sorted(expected) == sorted(delivered_items):
            print(f"✅ Recette {recipe_name} livrée avec succès ! +{self.score_per_dish} points")
            self.score += self.score_per_dish
            return True
        else:
            print(f"❌ Mauvais plat livré.\nAttendu: {expected}\nReçu: {delivered_items}")
            return False

    # ---------- extension ----------
    def register_recipes(self, extra: Dict[str, List[Dict[str, str]]]):
        """
        Ajoute de nouvelles recettes sans modifier le code de base.
        Exemple:
            rm.register_recipes({
                "tacos": [
                    {"ingredient":"pain"},
                    {"ingredient":"poulet","action":"cuire"},
                    {"ingredient":"salade","action":"couper"},
                    {"ingredient":"tomate","action":"couper"},
                ]
            })
        """
        self.recipes.update(extra)
