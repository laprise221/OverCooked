"""
test_comprehensive.py
Tests complets pour vérifier tous les composants du jeu
"""

import sys
import os

def test_imports():
    """Test que tous les modules peuvent être importés"""
    print("\n" + "="*60)
    print("🧪 TEST 1: IMPORTS")
    print("="*60)

    try:
        import pygame
        print("  ✅ pygame importé")
    except ImportError as e:
        print(f"  ❌ Erreur pygame: {e}")
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
        print(f"  ❌ Erreur kitchen: {e}")
        return False

    try:
        from agent import Agent
        print("  ✅ agent.py importé")
    except ImportError as e:
        print(f"  ❌ Erreur agent: {e}")
        return False

    return True


def test_ingredient_states():
    """Test les transformations d'ingrédients"""
    print("\n" + "="*60)
    print("🧪 TEST 2: ÉTATS DES INGRÉDIENTS")
    print("="*60)

    from objects import Ingredient

    # Test découpe
    tomato = Ingredient("tomate", "cru")
    print(f"  État initial: {tomato.state}")
    tomato.cut()
    assert tomato.state == "coupe", "❌ La découpe ne fonctionne pas"
    print(f"  ✅ Après découpe: {tomato.state}")

    # Test cuisson
    meat = Ingredient("viande", "cru")
    meat.cook()
    assert meat.state == "cuit", "❌ La cuisson ne fonctionne pas"
    print(f"  ✅ Après cuisson: {meat.state}")

    # Test get_full_name
    assert tomato.get_full_name() == "tomate_coupe"
    assert meat.get_full_name() == "viande_cuit"
    print(f"  ✅ get_full_name fonctionne correctement")

    return True


def test_tools():
    """Test le fonctionnement des outils"""
    print("\n" + "="*60)
    print("🧪 TEST 3: OUTILS")
    print("="*60)

    from objects import Tool, Ingredient

    # Test planche à découper
    cutting_board = Tool("planche", (1, 1))
    assert not cutting_board.occupied, "❌ L'outil ne devrait pas être occupé"
    print(f"  ✅ Planche créée: {cutting_board}")

    tomato = Ingredient("tomate", "cru")
    result = cutting_board.use(tomato)
    assert result, "❌ L'utilisation de l'outil a échoué"
    assert cutting_board.occupied, "❌ L'outil devrait être occupé"
    print(f"  ✅ Utilisation de la planche: {tomato.state}")

    released = cutting_board.release()
    assert released == tomato, "❌ La libération de l'outil a échoué"
    assert not cutting_board.occupied, "❌ L'outil devrait être libre"
    print(f"  ✅ Libération de l'outil réussie")

    # Test poêle
    stove = Tool("poele", (2, 2))
    meat = Ingredient("viande", "cru")
    stove.use(meat)
    assert meat.state == "cuit", "❌ La cuisson n'a pas fonctionné"
    print(f"  ✅ Cuisson sur poêle: {meat.state}")

    return True


def test_recipes():
    """Test le système de recettes"""
    print("\n" + "="*60)
    print("🧪 TEST 4: RECETTES")
    print("="*60)

    from recipes import recipes, get_all_recipe_names, parse_ingredient_requirement, get_ingredient_config

    recipe_names = get_all_recipe_names()
    print(f"  ✅ {len(recipe_names)} recettes trouvées: {recipe_names}")

    # Vérifier que toutes les recettes ont les champs requis
    for name in recipe_names:
        recipe = recipes[name]
        assert "ingredients" in recipe, f"❌ Recette {name} manque 'ingredients'"
        assert "image" in recipe, f"❌ Recette {name} manque 'image'"
        assert "description" in recipe, f"❌ Recette {name} manque 'description'"
        print(f"  ✅ {name}: {len(recipe['ingredients'])} ingrédients - {recipe['description'][:40]}...")

    # Test du parsing
    base, state = parse_ingredient_requirement("tomate_coupe")
    assert base == "tomate" and state == "coupe", "❌ Parsing tomate_coupe échoué"
    print(f"  ✅ Parsing 'tomate_coupe': base={base}, state={state}")

    base, state = parse_ingredient_requirement("viande_cuit")
    assert base == "viande" and state == "cuit", "❌ Parsing viande_cuit échoué"
    print(f"  ✅ Parsing 'viande_cuit': base={base}, state={state}")

    base, state = parse_ingredient_requirement("pain")
    assert base == "pain" and state == "cru", "❌ Parsing pain échoué"
    print(f"  ✅ Parsing 'pain': base={base}, state={state}")

    # Test configuration ingrédients
    config = get_ingredient_config("tomate")
    assert config["needs_cutting"], "❌ Tomate devrait nécessiter découpe"
    print(f"  ✅ Config tomate: needs_cutting={config['needs_cutting']}")

    config = get_ingredient_config("viande")
    assert config["needs_cooking"], "❌ Viande devrait nécessiter cuisson"
    print(f"  ✅ Config viande: needs_cooking={config['needs_cooking']}")

    return True


def test_kitchen_creation():
    """Test la création de la cuisine"""
    print("\n" + "="*60)
    print("🧪 TEST 5: CRÉATION DE LA CUISINE")
    print("="*60)

    from kitchen import Kitchen
    import pygame

    try:
        kitchen = Kitchen(width=16, height=16, cell_size=50)
        print(f"  ✅ Cuisine créée: {kitchen.width}x{kitchen.height}")
        print(f"  ✅ Taille cellule: {kitchen.cell_size}px")
        print(f"  ✅ {len(kitchen.stations)} stations")
        print(f"  ✅ {len(kitchen.tools)} outils")
        print(f"  ✅ {len(kitchen.ingredients_available)} ingrédients")

        pygame.quit()
        return True
    except Exception as e:
        print(f"  ❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_kitchen_grid():
    """Test la grille de la cuisine"""
    print("\n" + "="*60)
    print("🧪 TEST 6: GRILLE DE LA CUISINE")
    print("="*60)

    from kitchen import Kitchen
    from objects import Ingredient, Tool
    import pygame

    kitchen = Kitchen(width=16, height=16, cell_size=50)

    # Vérifier les stations
    stations = kitchen.stations
    assert "ingredients" in stations, "❌ Station ingrédients manquante"
    assert "cutting" in stations, "❌ Station découpe manquante"
    assert "cooking" in stations, "❌ Station cuisson manquante"
    assert "assembly" in stations, "❌ Station assemblage manquante"
    assert "counter" in stations, "❌ Station comptoir manquante"
    print(f"  ✅ Toutes les stations présentes: {list(stations.keys())}")

    # Vérifier la zone d'ingrédients
    ingredient_count = 0
    for y in range(16):
        for x in range(16):
            cell = kitchen.grid[y][x]
            if isinstance(cell, Ingredient):
                ingredient_count += 1
                print(f"  ✅ Ingrédient trouvé: {cell.name} à ({x}, {y})")

    assert ingredient_count > 0, "❌ Aucun ingrédient trouvé dans la grille"
    print(f"  ✅ {ingredient_count} ingrédients placés dans la grille")

    # Vérifier les outils
    tool_count = 0
    for y in range(16):
        for x in range(16):
            cell = kitchen.grid[y][x]
            if isinstance(cell, Tool):
                tool_count += 1
                print(f"  ✅ Outil trouvé: {cell.tool_type} à ({x}, {y})")

    assert tool_count > 0, "❌ Aucun outil trouvé dans la grille"
    print(f"  ✅ {tool_count} outils placés dans la grille")

    # Vérifier la table d'assemblage - UNE SEULE CASE
    cell = kitchen.grid[8][8]
    assert cell == "assembly_table", "❌ Table d'assemblage non trouvée à (8, 8)!"
    print(f"  ✅ Table d'assemblage trouvée à (8, 8)")

    # Vérifier le comptoir - UNE SEULE CASE
    cell = kitchen.grid[12][3]
    assert cell == "counter", "❌ Comptoir non trouvé à (3, 12)!"
    print(f"  ✅ Comptoir trouvé à (3, 12)")

    pygame.quit()
    return True


def test_walkability():
    """Test les zones marchables"""
    print("\n" + "="*60)
    print("🧪 TEST 7: ZONES MARCHABLES")
    print("="*60)

    from kitchen import Kitchen
    import pygame

    kitchen = Kitchen(width=16, height=16, cell_size=50)

    # Test cases vides (doivent être marchables)
    assert kitchen.is_walkable((0, 0)), "❌ Case vide devrait être marchable"
    print(f"  ✅ Case vide (0, 0) est marchable")

    # Test table d'assemblage (doit être marchable)
    assert kitchen.is_walkable((8, 8)), "❌ Table d'assemblage devrait être marchable"
    print(f"  ✅ Table d'assemblage (8, 8) est marchable")

    # Test comptoir (doit être marchable)
    assert kitchen.is_walkable((2, 12)), "❌ Comptoir devrait être marchable"
    print(f"  ✅ Comptoir (2, 12) est marchable")

    # Test outils (NE doivent PAS être marchables)
    assert not kitchen.is_walkable((13, 1)), "❌ Planche ne devrait PAS être marchable"
    print(f"  ✅ Planche (13, 1) n'est PAS marchable")

    assert not kitchen.is_walkable((13, 4)), "❌ Poêle ne devrait PAS être marchable"
    print(f"  ✅ Poêle (13, 4) n'est PAS marchable")

    # Test ingrédients (NE doivent PAS être marchables)
    assert not kitchen.is_walkable((1, 1)), "❌ Ingrédient ne devrait PAS être marchable"
    print(f"  ✅ Ingrédient (1, 1) n'est PAS marchable")

    # Test hors limites
    assert not kitchen.is_walkable((-1, 0)), "❌ Hors limites devrait être non marchable"
    assert not kitchen.is_walkable((20, 20)), "❌ Hors limites devrait être non marchable"
    print(f"  ✅ Cases hors limites ne sont pas marchables")

    pygame.quit()
    return True


def test_images():
    """Test le chargement des images"""
    print("\n" + "="*60)
    print("🧪 TEST 8: CHARGEMENT DES IMAGES")
    print("="*60)

    from kitchen import Kitchen
    import pygame
    import os

    kitchen = Kitchen(width=16, height=16, cell_size=50)

    # Vérifier que les images sont chargées
    required_images = [
        "salade_crue", "tomate_crue", "oignon_crue", "viande_crue", "pain_crue", "fromage_crue", "pate_crue",
        "salade_coupe", "tomate_coupe", "oignon_coupe", "viande_cuit",
        "planche", "poele", "assembly_table", "counter"
    ]

    missing_images = []
    for img_name in required_images:
        if img_name not in kitchen.images or kitchen.images[img_name] is None:
            missing_images.append(img_name)
            print(f"  ⚠️  Image manquante: {img_name}")
        else:
            print(f"  ✅ Image chargée: {img_name}")

    if missing_images:
        print(f"  ⚠️  {len(missing_images)} images manquantes (le jeu peut fonctionner avec des couleurs)")
    else:
        print(f"  ✅ Toutes les images sont chargées!")

    # Vérifier que le dossier images existe
    image_path = os.path.join(os.path.dirname(__file__), "images")
    if os.path.exists(image_path):
        print(f"  ✅ Dossier images trouvé: {image_path}")
        files = os.listdir(image_path)
        print(f"  ✅ {len(files)} fichiers dans le dossier images")
    else:
        print(f"  ⚠️  Dossier images non trouvé: {image_path}")

    pygame.quit()
    return True


def test_agent_creation():
    """Test la création de l'agent"""
    print("\n" + "="*60)
    print("🧪 TEST 9: CRÉATION DE L'AGENT")
    print("="*60)

    from kitchen import Kitchen
    from agent import Agent
    import pygame

    kitchen = Kitchen(width=16, height=16, cell_size=50)
    agent = Agent(position=[0, 15], kitchen=kitchen)

    assert agent.position == [0, 15], "❌ Position initiale incorrecte"
    print(f"  ✅ Agent créé à la position {agent.position}")

    assert agent.holding is None, "❌ Agent ne devrait rien porter au départ"
    print(f"  ✅ Agent ne porte rien au départ")

    assert len(agent.task_queue) == 0, "❌ File de tâches devrait être vide"
    print(f"  ✅ File de tâches vide")

    assert agent.current_action == "En attente", "❌ Action initiale incorrecte"
    print(f"  ✅ Action initiale: {agent.current_action}")

    pygame.quit()
    return True


def test_agent_recipe():
    """Test la configuration d'une recette pour l'agent"""
    print("\n" + "="*60)
    print("🧪 TEST 10: CONFIGURATION RECETTE AGENT")
    print("="*60)

    from kitchen import Kitchen
    from agent import Agent
    from recipes import recipes
    import pygame

    kitchen = Kitchen(width=16, height=16, cell_size=50)
    agent = Agent(position=[0, 15], kitchen=kitchen)

    # Test avec le burger
    agent.set_recipe("burger", recipes["burger"])
    print(f"  ✅ Recette 'burger' configurée")
    print(f"  ✅ {len(agent.task_queue)} tâches générées")

    # Vérifier qu'il y a des tâches
    assert len(agent.task_queue) > 0, "❌ Aucune tâche générée"

    # Afficher les types de tâches
    task_types = [task['type'] for task in agent.task_queue]
    print(f"  ✅ Types de tâches: {set(task_types)}")

    # Vérifier qu'il y a une tâche de livraison à la fin
    assert agent.task_queue[-1]['type'] == 'deliver', "❌ Dernière tâche devrait être 'deliver'"
    print(f"  ✅ Dernière tâche est bien 'deliver'")

    # Test avec sandwich (plus simple)
    agent2 = Agent(position=[0, 15], kitchen=kitchen)
    agent2.set_recipe("sandwich", recipes["sandwich"])
    print(f"  ✅ Recette 'sandwich' configurée avec {len(agent2.task_queue)} tâches")

    pygame.quit()
    return True


def test_pathfinding():
    """Test l'algorithme A* de recherche de chemin"""
    print("\n" + "="*60)
    print("🧪 TEST 11: RECHERCHE DE CHEMIN (A*)")
    print("="*60)

    from kitchen import Kitchen
    from agent import Agent
    import pygame

    kitchen = Kitchen(width=16, height=16, cell_size=50)
    agent = Agent(position=[0, 15], kitchen=kitchen)

    initial_pos = agent.position.copy()
    print(f"  Position initiale: {initial_pos}")

    # Test déplacement vers une position accessible
    target = (5, 10)
    print(f"  Cible: {target}")

    # Effectuer plusieurs déplacements
    for i in range(10):
        old_pos = agent.position.copy()
        agent._move_towards(target)
        if agent.position != old_pos:
            print(f"  ✅ Déplacement {i+1}: {old_pos} -> {agent.position}")
        if tuple(agent.position) == target:
            print(f"  ✅ Cible atteinte en {i+1} mouvements!")
            break

    # Vérifier que l'agent s'est déplacé
    assert agent.position != initial_pos, "❌ Agent ne s'est pas déplacé"
    print(f"  ✅ Agent s'est bien déplacé")

    pygame.quit()
    return True


def test_adjacent_positions():
    """Test la détection des positions adjacentes"""
    print("\n" + "="*60)
    print("🧪 TEST 12: POSITIONS ADJACENTES")
    print("="*60)

    from kitchen import Kitchen
    from agent import Agent
    import pygame

    kitchen = Kitchen(width=16, height=16, cell_size=50)
    agent = Agent(position=[5, 5], kitchen=kitchen)

    # Test positions adjacentes
    test_cases = [
        ((5, 6), True, "en dessous"),
        ((5, 4), True, "au dessus"),
        ((6, 5), True, "à droite"),
        ((4, 5), True, "à gauche"),
        ((6, 6), True, "diagonale"),
        ((5, 5), False, "même position"),
        ((7, 7), False, "trop loin"),
        ((10, 10), False, "très loin")
    ]

    for pos, expected, description in test_cases:
        result = agent._is_adjacent_to((5, 5), pos)
        status = "✅" if result == expected else "❌"
        print(f"  {status} Position {pos} ({description}): {result} (attendu: {expected})")
        assert result == expected, f"❌ Test adjacence échoué pour {pos}"

    # Test recherche de position accessible
    target = (8, 8)  # Centre de la table d'assemblage
    accessible_pos = agent._find_nearest_accessible_position(target)
    assert accessible_pos is not None, "❌ Aucune position accessible trouvée"
    print(f"  ✅ Position accessible trouvée près de {target}: {accessible_pos}")
    assert kitchen.is_walkable(accessible_pos), "❌ Position trouvée n'est pas marchable"
    print(f"  ✅ Position trouvée est bien marchable")

    pygame.quit()
    return True


def test_dish_assembly():
    """Test l'assemblage de plats"""
    print("\n" + "="*60)
    print("🧪 TEST 13: ASSEMBLAGE DE PLATS")
    print("="*60)

    from objects import Dish, Ingredient
    from recipes import recipes

    # Créer les ingrédients pour un sandwich
    ingredients = [
        Ingredient("pain", "cru"),
        Ingredient("fromage", "cru"),
        Ingredient("tomate", "coupe")
    ]

    dish = Dish("sandwich", ingredients)
    print(f"  ✅ Plat créé: {dish}")

    # Vérifier si le plat est complet
    required = recipes["sandwich"]["ingredients"]
    is_complete = dish.is_complete(required)
    print(f"  ✅ Vérification complétude: {is_complete}")
    print(f"  ✅ Ingrédients requis: {required}")
    print(f"  ✅ Ingrédients présents: {[ing.get_full_name() for ing in ingredients]}")

    return True


def test_station_items():
    """Test l'ajout/retrait d'items dans les stations"""
    print("\n" + "="*60)
    print("🧪 TEST 14: GESTION DES STATIONS")
    print("="*60)

    from objects import Station, Ingredient

    station = Station("assembly", (8, 8), (3, 3))
    print(f"  ✅ Station créée: {station}")

    # Ajouter un item
    tomato = Ingredient("tomate", "coupe")
    station.add_item(tomato)
    print(f"  ✅ Item ajouté: {tomato}")
    assert len(station.items) == 1, "❌ Item non ajouté"

    # Vérifier la position
    assert tomato.position == station.position, "❌ Position de l'item incorrecte"
    print(f"  ✅ Position de l'item correcte: {tomato.position}")

    # Retirer l'item
    removed = station.remove_item(tomato)
    assert removed, "❌ Item non retiré"
    assert len(station.items) == 0, "❌ Station devrait être vide"
    print(f"  ✅ Item retiré avec succès")

    return True


def test_full_workflow():
    """Test du workflow complet (simplifié)"""
    print("\n" + "="*60)
    print("🧪 TEST 15: WORKFLOW COMPLET (SIMULATION)")
    print("="*60)

    from kitchen import Kitchen
    from agent import Agent
    from recipes import recipes
    import pygame

    kitchen = Kitchen(width=16, height=16, cell_size=50)
    agent = Agent(position=[0, 15], kitchen=kitchen)

    # Configurer une recette simple (sandwich)
    agent.set_recipe("sandwich", recipes["sandwich"])
    print(f"  ✅ Recette configurée: sandwich")
    print(f"  ✅ Nombre de tâches: {len(agent.task_queue)}")

    # Simuler quelques updates
    print("\n  Simulation de 20 updates:")
    for i in range(20):
        agent.update()
        if agent.current_action != "En attente":
            print(f"    Update {i+1}: {agent.current_action}")

    print(f"\n  ✅ Simulation terminée")
    print(f"  ✅ Tâches restantes: {len(agent.task_queue)}")
    print(f"  ✅ Action actuelle: {agent.current_action}")
    print(f"  ✅ Objet porté: {agent.holding}")
    print(f"  ✅ Position actuelle: {agent.position}")

    pygame.quit()
    return True


def run_all_tests():
    """Execute tous les tests"""
    print("\n" + "="*60)
    print("🧪 TESTS COMPLETS DU JEU OVERCOOKED")
    print("="*60)

    tests = [
        ("Imports", test_imports),
        ("États des ingrédients", test_ingredient_states),
        ("Outils", test_tools),
        ("Recettes", test_recipes),
        ("Création de la cuisine", test_kitchen_creation),
        ("Grille de la cuisine", test_kitchen_grid),
        ("Zones marchables", test_walkability),
        ("Chargement des images", test_images),
        ("Création de l'agent", test_agent_creation),
        ("Configuration recette agent", test_agent_recipe),
        ("Recherche de chemin (A*)", test_pathfinding),
        ("Positions adjacentes", test_adjacent_positions),
        ("Assemblage de plats", test_dish_assembly),
        ("Gestion des stations", test_station_items),
        ("Workflow complet", test_full_workflow)
    ]

    passed = 0
    failed = 0
    errors = []

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ Test '{name}' RÉUSSI\n")
            else:
                failed += 1
                errors.append(name)
                print(f"❌ Test '{name}' ÉCHOUÉ\n")
        except Exception as e:
            failed += 1
            errors.append(name)
            print(f"❌ Test '{name}' A PLANTÉ: {e}\n")
            import traceback
            traceback.print_exc()

    print("\n" + "="*60)
    print(f"📊 RÉSULTATS FINAUX")
    print("="*60)
    print(f"✅ Tests réussis: {passed}/{len(tests)}")
    print(f"❌ Tests échoués: {failed}/{len(tests)}")

    if failed == 0:
        print("\n🎉 TOUS LES TESTS SONT PASSÉS!")
        print("💡 Vous pouvez lancer le jeu avec: python main.py")
    else:
        print(f"\n⚠️  {failed} test(s) ont échoué:")
        for error in errors:
            print(f"  - {error}")
        print("\n💡 Corrigez les erreurs avant de lancer le jeu")

    print("="*60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)