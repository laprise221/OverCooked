# 🤖 Mode Single-Agent

Mode de jeu avec un seul agent autonome qui prépare toutes les commandes séquentiellement.

## 🎯 Architecture

### Agent autonome (agent.py)
- **Pathfinding** : A* pour navigation optimale
- **Planification** : File de tâches (FIFO)
- **Actions** : pickup, cut, cook, bring_to_assembly, deliver

### Kitchen (kitchen.py)
- Environnement 16x16
- Zones : ingrédients, découpe, cuisson, assemblage, livraison
- Pas de synchronisation nécessaire (agent unique)

## 🚀 Lancement

```bash
cd /home/samir/Bureau/OverCooked
python -m single_agent.main
```

## 🎮 Utilisation

1. Cliquez sur les boutons de recettes pour composer une commande
2. Cliquez sur "Envoyer" pour démarrer la préparation
3. L'agent prépare automatiquement les plats un par un
4. Appuyez sur Q pour quitter

## 📊 Caractéristiques

- **Simplicité** : Code facile à comprendre
- **Déterministe** : Même ordre d'exécution à chaque fois
- **Performance** : 40-50s pour un burger complet

## 🧪 Tests

```bash
python -m single_agent.test_game
```

## 📝 Algorithme

1. **Décomposition de recette** : Chaque recette → liste de tâches
2. **Exécution séquentielle** : Une tâche après l'autre
3. **Pathfinding A*** : Navigation optimale vers les ressources
4. **Livraison** : Assemblage final + dépôt au comptoir

## 💡 Améliorations possibles

- Optimisation de l'ordre des tâches
- Anticipation des prochaines commandes
- Réduction des trajets à vide
