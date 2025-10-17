"""
test_game.py
Script de test pour vérifier que tous les composants fonctionnent
"""

import sys


def test_imports():
    """Test que tous les modules peuvent être importés"""
    print("🧪 Test des imports...")
    try:
        import pygame
        print("  ✅ pygame importé")
    except ImportError as e:
        print(f"  ❌ Erreur pygame: {e}")
        print("  💡 Installez avec: pip install pygame")
        return False

    try:
        from objects import Ingredient, Tool, Dish, Station
        print("  ✅ objects.py importé")
    except ImportError as e:
        print(f"  ❌ Erreur objects: {e}")
        return False

    try:
        from recipes import recipes, get_all_recipe_names, parse_ingredient_requirement
        print("  ✅ recipes.py importé")
    except ImportError as e:
        print(f"  ❌ Erreur recipes: {e}")
        return False

    try:
        from kitchen import Kitchen
        print("  ✅ kitchen.py importé")
    except ImportError as e:
        print(f"  ❌ Erreur cuisine: {e}")
        return False

    try:
        from agent import Agent
        print("  ✅ agent.py importé")
    except ImportError as e:
        print(f"  ❌ Erreur agent: {e}")
        return False

    return True


def test_objects():
    """Test la création d'objets"""
    print("\n🧪 Test des objets...")
    from objects import Ingredient, Tool, Dish

    # Test Ingredient
    tomato = Ingredient("tomate", "cru")
    print(f"  ✅ Ingrédient créé: {tomato}")

    tomato.cut()
    assert tomato.state == "coupe", "La découpe ne fonctionne pas"
    print(f"  ✅ Découpe fonctionne: {tomato.state}")

    # Test Tool
    cutting_board = Tool("planche", (1, 1))
    print(f"  ✅ Outil créé: {cutting_board}")

    # Test Dish
    dish = Dish("burger", [tomato])
    print(f"  ✅ Plat créé: {dish}")

    return True


def test_recipes():
    """Test le système de recettes"""
    print("\n🧪 Test des recettes...")
    from recipes import recipes, get_all_recipe_names, parse_ingredient_requirement

    recipe_names = get_all_recipe_names()
    print(f"  ✅ {len(recipe_names)} recettes trouvées: {recipe_names}")

    for name in recipe_names:
        recipe = recipes[name]
        print(f"  📋 {name}: {len(recipe['ingredients'])} ingrédients")

    # Test du parsing
    base, state = parse_ingredient_requirement("tomate_coupe")
    assert base == "tomate" and state == "coupe"
    print(f"  ✅ Parsing fonctionne: tomate_coupe -> {base}, {state}")

    return True


def test_kitchen():
    """Test la création de la cuisine"""
    print("\n🧪 Test de la cuisine...")
    from kitchen import Kitchen

    try:
        kitchen = Kitchen(width=10, height=8, cell_size=80)
        print(f"  ✅ Cuisine créée: {kitchen.width}x{kitchen.height}")
        print(f"  ✅ {len(kitchen.stations)} stations")
        print(f"  ✅ {len(kitchen.tools)} outils")
        print(f"  ✅ {len(kitchen.ingredients_available)} ingrédients")

        # Ferme la fenêtre pygame
        import pygame
        pygame.quit()

        return True
    except Exception as e:
        print(f"  ❌ Erreur: {e}")
        return False


def test_agent():
    """Test la création de l'agent"""
    print("\n🧪 Test de l'agent...")
    from kitchen import Kitchen
    from agent import Agent
    from recipes import recipes
    import pygame

    try:
        kitchen = Kitchen(width=10, height=8, cell_size=80)
        agent = Agent(position=[5, 5], kitchen=kitchen)
        print(f"  ✅ Agent créé à la position {agent.position}")

        # Test la configuration d'une recette
        agent.set_recipe("burger", recipes["burger"])
        print(f"  ✅ Recette configurée: {len(agent.task_queue)} tâches")

        pygame.quit()
        return True
    except Exception as e:
        print(f"  ❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Execute tous les tests"""
    print("=" * 60)
    print("🧪 TESTS DU JEU OVERCOOKED")
    print("=" * 60)

    tests = [
        ("Imports", test_imports),
        ("Objets", test_objects),
        ("Recettes", test_recipes),
        ("Cuisine", test_kitchen),
        ("Agent", test_agent)
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"  ⚠️ Test {name} échoué")
        except Exception as e:
            failed += 1
            print(f"  ❌ Test {name} a planté: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print(f"📊 RÉSULTATS: {passed}/{len(tests)} tests réussis")
    if failed == 0:
        print("✅ Tous les tests sont passés!")
        print("💡 Vous pouvez lancer le jeu avec: python main.py")
    else:
        print(f"❌ {failed} test(s) échoué(s)")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)