# 🍳 Overcooked - Projet Multi-Agents

Simulation d'un jeu Overcooked avec deux modes de jeu distincts : **Single-Agent** et **Multi-Agent**.

## 📋 Vue d'ensemble

Ce projet implémente une cuisine virtuelle où des agents autonomes préparent des recettes en coordonnant leurs actions. Le projet explore deux approches différentes :

- **Mode Single-Agent** : Un agent unique prépare séquentiellement toutes les commandes
- **Mode Multi-Agent** : Deux agents coopératifs travaillent ensemble avec coordination intelligente

## 🏗️ Structure du projet

```
OverCooked/
├── common/              # Code partagé entre les deux modes
│   ├── objects.py       # Classes de base (Ingredient, Tool, Dish, Station)
│   ├── recipes.py       # Définition des recettes
│   └── kitchen_base.py  # Environnement de base de la cuisine
│
├── single_agent/        # Mode single-agent
│   ├── main.py          # Point d'entrée
│   ├── agent.py         # Agent autonome
│   ├── kitchen.py       # Kitchen simple
│   └── test_game.py     # Tests
│
├── multi_agent/         # Mode multi-agent
│   ├── main.py          # Point d'entrée
│   ├── agent.py         # Agent coopératif
│   ├── kitchen.py       # Kitchen avec locks
│   ├── planning/        # Planification STRIPS
│   ├── coordination/    # Task Market + Blackboard
│   ├── analytics/       # Métriques de performance
│   └── tests/           # Tests multi-agent
│
├── images/              # Assets graphiques
│   ├── agents/          # Sprites des agents
│   ├── ingredients/     # Images des ingrédients
│   ├── tools/           # Outils (planche, poêle)
│   ├── stations/        # Stations (table, comptoir)
│   └── dishes/          # Plats finaux
│
└── docs/                # Documentation détaillée
```

## 🚀 Installation

```bash
# Installer les dépendances
pip install -r requirements.txt
```

## 🎮 Utilisation

### Mode Single-Agent

```bash
cd /home/samir/Bureau/OverCooked
python -m single_agent.main
```

**Caractéristiques** :
- Un seul agent autonome
- Planification séquentielle
- Pathfinding A*
- Temps moyen : 40-50s pour un burger

### Mode Multi-Agent

```bash
cd /home/samir/Bureau/OverCooked
python -m multi_agent.main
```

**Caractéristiques** :
- 2 agents coopératifs
- Planification STRIPS
- Allocation dynamique (Task Market)
- Communication (Blackboard)
- Synchronisation par resource locks
- Temps moyen : 25-35s pour un burger
- Métriques de performance détaillées

## 🧪 Tests

### Tests Single-Agent
```bash
python -m single_agent.test_game
```

### Tests Multi-Agent
```bash
python -m multi_agent.tests.test_cooperation
```

## 📊 Recettes disponibles

1. **Burger** : salade_coupe, tomate_coupe, oignon_coupe, viande_cuit, pain
2. **Sandwich** : pain, fromage, tomate_coupe
3. **Pizza** : pate, fromage, tomate_coupe, oignon_coupe

## 🎯 Concepts implémentés (Multi-Agent)

- **STRIPS** : Planification formelle avec préconditions et effets
- **Task Market** : Allocation par enchères (bidding system)
- **Blackboard** : Communication asynchrone inter-agents
- **Resource Locks** : Synchronisation des ressources partagées
- **Métriques** : Throughput, équilibrage de charge, utilisation ressources

## 📈 Performance

Mode Multi-Agent vs Single-Agent :
- **Gain de temps** : ~40% plus rapide
- **Équilibrage** : 85-95% de distribution de charge
- **Throughput** : ~2.0 commandes/min

## 📚 Documentation

- [Architecture détaillée](docs/ARCHITECTURE.md)
- [Guide Single-Agent](single_agent/README.md)
- [Guide Multi-Agent](multi_agent/README.md)


