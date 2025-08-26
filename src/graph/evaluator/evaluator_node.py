from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from src.prompts.evaluator import EVALUATOR_SYSTEM_PROMPT
from langchain_core.messages import BaseMessage
from typing import TypedDict, Sequence, Literal, Annotated
import operator
from src.schemas import AgentState

class Evaluator:
    def __init__(self, llm=None):
        self.llm = llm or ChatOpenAI(temperature=0)
        self.prompt = ChatPromptTemplate.from_template(
            EVALUATOR_SYSTEM_PROMPT + "\n\nÚltima mensagem: {input}"
        )
        self.chain = self.prompt | self.llm | StrOutputParser()

    def evaluate(self, state: AgentState):
        """
        Avalia o estado atual e decide o próximo passo.

        Args:
            state (AgentState): O estado atual do agente.

        Returns:
            dict: O próximo estado com a decisão.
        """
        decision = self.chain.invoke({"input": state["messages"][-1].content})
        return {"next": decision}
