from src.utils.memory_manager import MemoryManager
from src.schemas import AgentState
from langchain_core.messages import BaseMessage
from typing import List, Dict

class HistoryAgent:
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager

    def get_conversation_history(self, user_id: str, agent_id: str) -> List[Dict[str, str]]:
        """
        Recupera o histórico de inputs e outputs para um usuário e agente específicos.

        Args:
            user_id (str): Identificador do usuário.
            agent_id (str): Identificador do agente.

        Returns:
            List[Dict[str, str]]: Lista de interações contendo inputs e outputs.
        """
        return self.memory_manager.get_memory(user_id, agent_id)
