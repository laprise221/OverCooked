"""
recipes.py
Définit toutes les recettes disponibles dans le jeu
"""

# Dictionnaire des recettes avec leurs ingrédients requis
recipes = {
    "burger": {
        "ingredients": [
            "salade_coupe",
            "tomate_coupe",
            "oignon_coupe",
            "viande_cuit",
            "pain"
        ],
        "image": "images/burger.png",
        "description": "Un délicieux burger avec salade, tomate, oignon, viande cuite et pain"
    },

    "sandwich": {
        "ingredients": [
            "pain",
            "fromage",
            "tomate_coupe"
        ],
        "image": "images/sandwich.png",
        "description": "Un sandwich simple au fromage et tomate"
    }
}

# Configuration des ingrédients et leurs traitements requis
ingredient_config = {
    "salade": {
        "needs_cutting": True,
        "needs_cooking": False,
        "cutting_time": 2.0
    },
    "tomate": {
        "needs_cutting": True,
        "needs_cooking": False,
        "cutting_time": 2.0
    },
    "oignon": {
        "needs_cutting": True,
        "needs_cooking": False,
        "cutting_time": 2.0
    },
    "viande": {
        "needs_cutting": False,
        "needs_cooking": True,
        "cooking_time": 3.0
    },
    "pain": {
        "needs_cutting": False,
        "needs_cooking": False
    },
    "fromage": {
        "needs_cutting": False,
        "needs_cooking": False
    }
}


def get_recipe_by_name(recipe_name):
    """
    Retourne une recette par son nom
    """
    return recipes.get(recipe_name)


def get_all_recipe_names():
    """
    Retourne la liste de tous les noms de recettes
    """
    return list(recipes.keys())


def get_ingredient_config(ingredient_name):
    """
    Retourne la configuration d'un ingrédient
    """
    return ingredient_config.get(ingredient_name, {
        "needs_cutting": False,
        "needs_cooking": False
    })


def parse_ingredient_requirement(requirement):
    """
    Parse une exigence d'ingrédient (ex: "tomate_coupe")
    Retourne (nom_base, état_requis)
    """
    if "_coupe" in requirement:
        return requirement.replace("_coupe", ""), "coupe"
    elif "_cuit" in requirement:
        return requirement.replace("_cuit", ""), "cuit"
    else:
        return requirement, "cru"