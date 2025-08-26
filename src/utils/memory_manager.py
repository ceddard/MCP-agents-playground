from typing import Dict, List
from datetime import datetime
from src.schemas import AgentState
from cachetools import LRUCache

class MemoryManager:
    def __init__(self, cache_size=1000):
        self.memory: Dict[str, Dict[str, List[Dict]]] = {}
        self.cache = LRUCache(maxsize=cache_size)

    def save_state(self, user_id: str, agent_id: str, input_text: str, output_text: str):
        """
        Salva o input e output no histórico para um usuário e agente específicos.

        Args:
            user_id (str): Identificador do usuário.
            agent_id (str): Identificador do agente.
            input_text (str): Texto de entrada do usuário.
            output_text (str): Texto de saída do agente.
        """
        if user_id not in self.memory:
            self.memory[user_id] = {}
        if agent_id not in self.memory[user_id]:
            self.memory[user_id][agent_id] = []

        interaction = {
            "input": input_text,
            "output": output_text,
            "timestamp": datetime.utcnow().isoformat()
        }

        self.memory[user_id][agent_id].append(interaction)
        self.cache[(user_id, agent_id)] = self.memory[user_id][agent_id]

    def get_memory(self, user_id: str, agent_id: str) -> List[Dict[str, str]]:
        """
        Recupera o histórico de inputs e outputs para um usuário e agente específicos.

        Args:
            user_id (str): Identificador do usuário.
            agent_id (str): Identificador do agente.

        Returns:
            List[Dict[str, str]]: Lista de interações contendo inputs e outputs.
        """
        if (user_id, agent_id) in self.cache:
            return self.cache[(user_id, agent_id)]
        return self.memory.get(user_id, {}).get(agent_id, [])
