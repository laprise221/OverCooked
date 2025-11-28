import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

"""
Système de communication inter-agents pour coopération

Implémente un modèle de Blackboard (tableau noir) pour la coordination:
- Les agents lisent et écrivent des messages sur un tableau partagé
- Permet la communication asynchrone
- Types de messages: TASK_CLAIMED, TASK_COMPLETED, RESOURCE_REQUEST, etc.

Référence cours: Communication et coordination dans les systèmes multi-agents
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import time
from collections import deque


class MessageType(Enum):
    """Types de messages inter-agents"""
    # Task-related messages
    TASK_CLAIMED = "task_claimed"           # Un agent revendique une tâche
    TASK_STARTED = "task_started"           # Un agent commence une tâche
    TASK_COMPLETED = "task_completed"       # Une tâche est terminée
    TASK_FAILED = "task_failed"             # Une tâche a échoué
    TASK_HELP_REQUEST = "task_help_request" # Un agent demande de l'aide

    # Resource-related messages
    RESOURCE_LOCKED = "resource_locked"     # Une ressource est verrouillée
    RESOURCE_FREE = "resource_free"         # Une ressource est libérée
    RESOURCE_REQUEST = "resource_request"   # Demande d'accès à une ressource

    # Coordination messages
    AGENT_IDLE = "agent_idle"               # Un agent est inactif
    AGENT_BUSY = "agent_busy"               # Un agent est occupé
    POSITION_UPDATE = "position_update"     # Mise à jour de position
    COLLISION_WARNING = "collision_warning" # Alerte de collision potentielle

    # System messages
    ORDER_RECEIVED = "order_received"       # Nouvelle commande reçue
    ORDER_COMPLETED = "order_completed"     # Commande terminée
    EMERGENCY_STOP = "emergency_stop"       # Arrêt d'urgence


@dataclass
class Message:
    """
    Message échangé entre agents ou avec le système central
    """
    msg_id: int
    msg_type: MessageType
    sender_id: Optional[int]  # None si message système
    receiver_id: Optional[int]  # None si broadcast
    timestamp: float
    content: Dict[str, Any]
    priority: int = 0  # Plus élevé = plus prioritaire

    def __lt__(self, other):
        """Pour tri par priorité (plus élevée d'abord)"""
        return self.priority > other.priority

    def __repr__(self) -> str:
        return f"Msg({self.msg_type.value}, from={self.sender_id}, to={self.receiver_id})"


class Blackboard:
    """
    Tableau noir (Blackboard) pour communication inter-agents

    Pattern architectural classique pour systèmes multi-agents:
    - Espace de mémoire partagée
    - Les agents lisent et écrivent de manière asynchrone
    - Facilite la coordination sans communication directe point-à-point
    """

    def __init__(self, max_messages: int = 1000):
        self.messages: deque = deque(maxlen=max_messages)
        self.message_counter = 0
        self.agent_states: Dict[int, Dict[str, Any]] = {}
        self.global_state: Dict[str, Any] = {
            'total_orders': 0,
            'completed_orders': 0,
            'active_agents': set()
        }

    def post_message(self, msg_type: MessageType, sender_id: Optional[int],
                    receiver_id: Optional[int], content: Dict[str, Any],
                    priority: int = 0) -> Message:
        """
        Publie un message sur le tableau noir
        """
        msg = Message(
            msg_id=self.message_counter,
            msg_type=msg_type,
            sender_id=sender_id,
            receiver_id=receiver_id,
            timestamp=time.time(),
            content=content,
            priority=priority
        )
        self.messages.append(msg)
        self.message_counter += 1
        return msg

    def get_messages(self, receiver_id: Optional[int] = None,
                    msg_type: Optional[MessageType] = None,
                    since_timestamp: Optional[float] = None,
                    limit: int = 100) -> List[Message]:
        """
        Récupère les messages du tableau noir avec filtres optionnels

        Args:
            receiver_id: Filtrer par destinataire (None = broadcast)
            msg_type: Filtrer par type de message
            since_timestamp: Récupérer uniquement les messages après ce timestamp
            limit: Nombre maximum de messages à retourner
        """
        filtered_messages = []

        for msg in reversed(self.messages):  # Plus récents d'abord
            # Filtrage par timestamp
            if since_timestamp and msg.timestamp < since_timestamp:
                continue

            # Filtrage par destinataire
            if receiver_id is not None:
                if msg.receiver_id not in [receiver_id, None]:  # None = broadcast
                    continue

            # Filtrage par type
            if msg_type and msg.msg_type != msg_type:
                continue

            filtered_messages.append(msg)

            if len(filtered_messages) >= limit:
                break

        return filtered_messages

    def get_latest_message(self, receiver_id: Optional[int] = None,
                          msg_type: Optional[MessageType] = None) -> Optional[Message]:
        """Récupère le message le plus récent selon les filtres"""
        messages = self.get_messages(receiver_id, msg_type, limit=1)
        return messages[0] if messages else None

    def update_agent_state(self, agent_id: int, state: Dict[str, Any]):
        """Met à jour l'état d'un agent sur le tableau"""
        if agent_id not in self.agent_states:
            self.agent_states[agent_id] = {}
        self.agent_states[agent_id].update(state)
        self.agent_states[agent_id]['last_update'] = time.time()

    def get_agent_state(self, agent_id: int) -> Optional[Dict[str, Any]]:
        """Récupère l'état d'un agent"""
        return self.agent_states.get(agent_id)

    def get_all_agent_states(self) -> Dict[int, Dict[str, Any]]:
        """Récupère les états de tous les agents"""
        return self.agent_states.copy()

    def update_global_state(self, updates: Dict[str, Any]):
        """Met à jour l'état global du système"""
        self.global_state.update(updates)

    def get_global_state(self) -> Dict[str, Any]:
        """Récupère l'état global du système"""
        return self.global_state.copy()

    def clear_old_messages(self, older_than_seconds: float = 60.0):
        """Nettoie les messages plus anciens qu'une durée donnée"""
        current_time = time.time()
        cutoff_time = current_time - older_than_seconds

        # Filtrer les messages récents
        recent_messages = [msg for msg in self.messages if msg.timestamp >= cutoff_time]
        self.messages = deque(recent_messages, maxlen=self.messages.maxlen)

    def get_message_stats(self) -> Dict[str, int]:
        """Retourne des statistiques sur les messages"""
        stats = {msg_type.value: 0 for msg_type in MessageType}
        for msg in self.messages:
            stats[msg.msg_type.value] += 1
        stats['total'] = len(self.messages)
        return stats

    def __repr__(self) -> str:
        return f"Blackboard(messages={len(self.messages)}, agents={len(self.agent_states)})"


class AgentCommunicator:
    """
    Interface de communication pour un agent individuel
    Facilite l'interaction avec le Blackboard
    """

    def __init__(self, agent_id: int, blackboard: Blackboard):
        self.agent_id = agent_id
        self.blackboard = blackboard
        self.last_check_timestamp = time.time()

    def send_message(self, msg_type: MessageType, receiver_id: Optional[int],
                    content: Dict[str, Any], priority: int = 0) -> Message:
        """Envoie un message via le blackboard"""
        return self.blackboard.post_message(
            msg_type=msg_type,
            sender_id=self.agent_id,
            receiver_id=receiver_id,
            content=content,
            priority=priority
        )

    def broadcast(self, msg_type: MessageType, content: Dict[str, Any],
                 priority: int = 0) -> Message:
        """Envoie un message broadcast (tous les agents)"""
        return self.send_message(msg_type, receiver_id=None, content=content, priority=priority)

    def receive_messages(self, msg_type: Optional[MessageType] = None) -> List[Message]:
        """Récupère les nouveaux messages pour cet agent"""
        messages = self.blackboard.get_messages(
            receiver_id=self.agent_id,
            msg_type=msg_type,
            since_timestamp=self.last_check_timestamp
        )
        self.last_check_timestamp = time.time()
        return messages

    def update_status(self, status: str, position: Optional[tuple] = None,
                     current_task: Optional[int] = None):
        """Met à jour le statut de l'agent sur le blackboard"""
        state = {
            'status': status,
            'position': position,
            'current_task': current_task
        }
        self.blackboard.update_agent_state(self.agent_id, state)

    def notify_task_claimed(self, task_id: int):
        """Notifie que l'agent a revendiqué une tâche"""
        self.broadcast(
            MessageType.TASK_CLAIMED,
            content={'task_id': task_id, 'agent_id': self.agent_id}
        )

    def notify_task_started(self, task_id: int):
        """Notifie que l'agent a commencé une tâche"""
        self.broadcast(
            MessageType.TASK_STARTED,
            content={'task_id': task_id, 'agent_id': self.agent_id}
        )

    def notify_task_completed(self, task_id: int):
        """Notifie que l'agent a terminé une tâche"""
        self.broadcast(
            MessageType.TASK_COMPLETED,
            content={'task_id': task_id, 'agent_id': self.agent_id},
            priority=5  # Haute priorité pour débloquer les tâches dépendantes
        )

    def request_resource(self, resource_name: str):
        """Demande l'accès à une ressource"""
        self.broadcast(
            MessageType.RESOURCE_REQUEST,
            content={'resource': resource_name, 'agent_id': self.agent_id}
        )

    def notify_resource_locked(self, resource_name: str):
        """Notifie que l'agent a verrouillé une ressource"""
        self.broadcast(
            MessageType.RESOURCE_LOCKED,
            content={'resource': resource_name, 'agent_id': self.agent_id}
        )

    def notify_resource_free(self, resource_name: str):
        """Notifie que l'agent a libéré une ressource"""
        self.broadcast(
            MessageType.RESOURCE_FREE,
            content={'resource': resource_name, 'agent_id': self.agent_id}
        )

    def update_position(self, x: int, y: int):
        """Met à jour la position de l'agent"""
        self.update_status('moving', position=(x, y))
        self.broadcast(
            MessageType.POSITION_UPDATE,
            content={'x': x, 'y': y, 'agent_id': self.agent_id},
            priority=1
        )

    def notify_idle(self):
        """Notifie que l'agent est inactif"""
        self.update_status('idle')
        self.broadcast(
            MessageType.AGENT_IDLE,
            content={'agent_id': self.agent_id}
        )

    def notify_busy(self, task_id: int):
        """Notifie que l'agent est occupé"""
        self.update_status('busy', current_task=task_id)
        self.broadcast(
            MessageType.AGENT_BUSY,
            content={'agent_id': self.agent_id, 'task_id': task_id}
        )

    def get_other_agents_positions(self) -> Dict[int, tuple]:
        """Récupère les positions des autres agents pour éviter les collisions"""
        positions = {}
        all_states = self.blackboard.get_all_agent_states()
        for agent_id, state in all_states.items():
            if agent_id != self.agent_id and 'position' in state:
                positions[agent_id] = state['position']
        return positions

    def check_collision_risk(self, target_position: tuple) -> bool:
        """Vérifie si un autre agent se dirige vers la même position"""
        other_positions = self.get_other_agents_positions()
        return target_position in other_positions.values()

    def __repr__(self) -> str:
        return f"AgentCommunicator(agent_id={self.agent_id})"
