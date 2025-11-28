# 🤖🤖 Mode Multi-Agent

Mode de jeu avec 2 agents coopératifs utilisant des techniques avancées de coordination.

## 🎯 Architecture

### Composants principaux

#### 1. Agent Coopératif (agent.py)
- Évaluation de coûts (distance + durée)
- Soumission d'enchères au Task Market
- Communication via Blackboard
- Évitement de collisions

#### 2. Planification STRIPS (planning/strips.py)
- Représentation formelle des actions
- Préconditions, Delete List, Add List
- Décomposition de recettes en tâches atomiques

#### 3. Task Market (coordination/task_market.py)
- Pool de tâches partagé
- Système d'enchères (bidding)
- Allocation optimale selon les coûts
- Gestion des dépendances

#### 4. Blackboard (coordination/communication.py)
- Communication asynchrone
- Types de messages : TASK_CLAIMED, RESOURCE_LOCKED, etc.
- État global partagé

#### 5. Métriques (analytics/metrics.py)
- Temps de complétion
- Throughput (commandes/min)
- Utilisation des ressources
- Équilibrage de charge

### Kitchen Multi-Agent (kitchen.py)
- **Resource Locks** : Synchronisation cutting_board, stove, assembly
- **Shared Assembly Table** : Table d'assemblage commune
- **Collision Avoidance** : Les agents s'évitent mutuellement

## 🚀 Lancement

```bash
cd /home/samir/Bureau/OverCooked
python -m multi_agent.main
```

## 🎮 Utilisation

1. Sélectionnez les recettes à préparer
2. Cliquez sur "Envoyer"
3. Les 2 agents se coordonnent automatiquement
4. Observez la coopération en temps réel
5. Consultez les métriques en fin de session

## 📊 Performance

- **Temps burger** : 25-35s (vs 40-50s mono-agent)
- **Équilibrage** : 85-95%
- **Throughput** : ~2.0 commandes/min

## 🧪 Tests

```bash
# Test de coopération de base
python -m multi_agent.tests.test_cooperation

# Test de simulation
python -m multi_agent.tests.test_simulation
```

## 🔬 Algorithme détaillé

### Phase 1 : Planification (STRIPS)
1. Recevoir commande (ex: burger)
2. Décomposer en tâches atomiques :
   - PICKUP(salade) → CUT(salade) → BRING_TO_ASSEMBLY(salade_coupe)
   - PICKUP(tomate) → CUT(tomate) → BRING_TO_ASSEMBLY(tomate_coupe)
   - PICKUP(viande) → COOK(viande) → BRING_TO_ASSEMBLY(viande_cuit)
   - etc.
3. Identifier les dépendances entre tâches

### Phase 2 : Allocation (Task Market)
1. Obtenir tâches disponibles (dépendances satisfaites)
2. Chaque agent évalue le coût de chaque tâche
3. Les agents soumettent leurs enchères
4. Market alloue chaque tâche à l'agent avec le coût minimal

### Phase 3 : Exécution
1. Agent reçoit tâche assignée
2. Vérifie préconditions (ex: a-t-il l'ingrédient?)
3. Tente de verrouiller la ressource nécessaire
4. Exécute l'action
5. Notifie la complétion via Blackboard
6. Libère la ressource

### Phase 4 : Synchronisation
- Les agents communiquent leurs positions
- Évitent les collisions lors du pathfinding
- Attendent si une ressource est occupée
- Débloquent les tâches dépendantes

## 💡 Concepts avancés

### STRIPS (Stanford Research Institute Problem Solver)
```python
Action(PICKUP(salade)):
  Preconditions: agent_hands_free
  Delete List:
  Add List: agent_has(salade)
```

### Task Market Bidding
```python
Agent 0: PICKUP(salade) → coût = 5.2 (distance=3, durée=2.0)
Agent 1: PICKUP(salade) → coût = 8.1 (distance=6, durée=2.0)
→ Agent 0 obtient la tâche
```

### Blackboard Messages
```python
Agent 0: RESOURCE_LOCKED(cutting_board)
Agent 1: [lit le message] → attend que la planche se libère
Agent 0: RESOURCE_FREE(cutting_board)
Agent 1: [lit le message] → peut maintenant utiliser la planche
```

## 🎯 Avantages vs Single-Agent

✅ **Performance** : ~40% plus rapide
✅ **Parallélisation** : Tâches indépendantes en parallèle
✅ **Scalabilité** : Facile d'ajouter plus d'agents
✅ **Robustesse** : Redistribution si un agent échoue

## ⚠️ Défis

⚠️ **Complexité** : Code plus difficile à maintenir
⚠️ **Overhead** : Communication et synchronisation
⚠️ **Deadlocks** : Risque si mauvaise gestion des locks
⚠️ **Débogage** : Comportements non-déterministes

## 📚 Références

- Cours : DeductiveAgents.pdf, IntroPlanning.pdf
- Pattern Blackboard : Architecture multi-agents
- Contract Net Protocol : Inspiration pour Task Market
