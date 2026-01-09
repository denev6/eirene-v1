import asyncio
from typing import AsyncGenerator
from abc import ABC, abstractmethod

from langchain_naver import ChatClovaX

from .scoring import AAQScoring
from .database import VectorDB
from .router import Router
from .memory import ShortTermMemory, LongTermMemory
from .prompt import (
    SESSION_INSTRUCTION_PROMPTS,
    DEFAULT_INSTRUCTION_PROMPT,
    counselor_agent_template,
    monitor_agent_template,
    legacy_agent_template,
    medical_agent_template,
    cultural_agent_template,
    escalation_agent_template,
    acp_agent_template,
)
from .utils import logger, extract_int, trim_str


class CounselorAgent:
    def __init__(self, medical_db_path: str, legacy_db_path: str):
        self.counselor_agent = ChatClovaX(
            model="HCX-005", temperature=0.2, max_tokens=512
        )
        self._agents: dict[str, SpecialistAgent] = {
            "MEDICAL": MedicalAgent(medical_db_path),
            "LEGACY": LegacyAgent(legacy_db_path),
            "CULTURAL": CulturalAgent(),
            "ACP": ACPAgent(),
        }
        self._router = Router()

    async def stream(
        self, query: str, history: str, user_info: str, counseling_session: str
    ) -> AsyncGenerator:
        try:
            agents_to_call = await self._router.ainvoke(query=query, history=history)
            specialist_responses = ""

            if agents_to_call:
                tasks = [
                    self._agents[agent.upper()].ainvoke(query, history, user_info)
                    for agent in agents_to_call
                ]
                specialist_responses = await asyncio.gather(*tasks)
                specialist_responses = "\n".join(
                    [
                        f"- {agent_name} 전문가: {response}"
                        for agent_name, response in zip(
                            agents_to_call, specialist_responses
                        )
                        if response
                    ]
                )

            session_instruction = SESSION_INSTRUCTION_PROMPTS.get(
                counseling_session, DEFAULT_INSTRUCTION_PROMPT
            )
            prompt = counselor_agent_template.format_messages(
                session_instruction=session_instruction,
                specialist_info=specialist_responses,
                user_info=user_info,
                history=history,
                user_input=query,
            )
            for chunk in self.counselor_agent.stream(prompt):
                content = chunk.content
                yield content

        except Exception as exp:
            logger.error(f"[{self.__class__.__name__}] {exp}")
            yield "\n[ERROR] 연결이 원활하지 못합니다."


class SpecialistAgent(ABC):
    @abstractmethod
    async def ainvoke(self, query: str, **kwargs) -> str:
        pass


class MedicalAgent(SpecialistAgent):
    def __init__(self, medical_db_path: str):
        self.llm = ChatClovaX(model="HCX-005", temperature=0, max_tokens=256)
        self.retriever = VectorDB(medical_db_path)
        self._default_return = ""

    async def ainvoke(self, query: str, history: str, user_info: str) -> str:
        docs = self.retriever.search(query=query, k=4, use_keyword=False)

        try:
            prompt = medical_agent_template.format_messages(
                user_input=query,
                history=history,
                user_info=user_info,
                medical_info="\n".join([doc.page_content for doc in docs]),
            )
            response = await self.llm.ainvoke(prompt)
            logger.debug(f"MEDICAL Agent: {trim_str(response.content)}")
            return response.content

        except Exception as e:
            logger.error(f"[{self.__class__.__name__}] {e}")
            return self._default_return


class LegacyAgent(SpecialistAgent):
    def __init__(self, legacy_db_path: str):
        self.llm = ChatClovaX(model="HCX-005", temperature=0, max_tokens=256)
        self.retriever = VectorDB(legacy_db_path)
        self._default_return = ""

    async def ainvoke(self, query: str, history: str, user_info: str) -> str:
        docs = self.retriever.search(query=query, k=1, use_keyword=False)

        try:
            prompt = legacy_agent_template.format_messages(
                user_input=query,
                history=history,
                user_info=user_info,
                legacy_info="\n".join([doc.page_content for doc in docs]),
            )
            response = await self.llm.ainvoke(prompt)
            logger.debug(f"LEGACY Agent: {trim_str(response.content)}")
            return response.content

        except Exception as e:
            logger.error(f"[{self.__class__.__name__}] {e}")
            return self._default_return


class CulturalAgent(SpecialistAgent):
    def __init__(self):
        self.llm = ChatClovaX(model="HCX-005", temperature=0, max_tokens=256)
        self._default_return = ""

    async def ainvoke(self, query: str, history: str, user_info: str) -> str:
        try:
            prompt = cultural_agent_template.format_messages(
                user_input=query, history=history, user_info=user_info
            )
            response = await self.llm.ainvoke(prompt)
            logger.debug(f"CULTURAL Agent: {trim_str(response.content)}")
            return response.content

        except Exception as e:
            logger.error(f"[{self.__class__.__name__}] {e}")
            return self._default_return


class EscalationAgent(SpecialistAgent):
    def __init__(self):
        self.llm = ChatClovaX(model="HCX-005", temperature=0, max_tokens=4)
        self.message = "지금 매우 힘든 상황이시군요. 즉시 전문가와 상담해 주세요."
        self._default_return = 0

    async def ainvoke(self, query: str, history: str) -> int:
        try:
            prompt = escalation_agent_template.format_messages(
                user_input=query, history=history
            )
            response = await self.llm.ainvoke(prompt)
            need_intervention = extract_int(
                response.content,
                min_option=0,
                max_option=1,
                default=self._default_return,
            )
            return need_intervention

        except Exception as e:
            logger.error(f"[{self.__class__.__name__}] {e}")
            return self._default_return


class ACPAgent(SpecialistAgent):
    def __init__(self):
        self.llm = ChatClovaX(model="HCX-005", temperature=0, max_tokens=256)
        self._default_return = ""

    async def ainvoke(self, query: str, history: str, user_info: str) -> str:
        try:
            prompt = acp_agent_template.format_messages(
                user_input=query, history=history, user_info=user_info
            )
            response = await self.llm.ainvoke(prompt)
            logger.debug(f"ACP Agent: {trim_str(response.content)}")
            return response.content

        except Exception as e:
            logger.error(f"[{self.__class__.__name__}] {e}")
            return self._default_return


class MonitorAgent(SpecialistAgent):
    def __init__(self):
        self.llm = ChatClovaX(model="HCX-005", temperature=0, max_tokens=4)
        self.session_transition = {
            "SETTING": "PERCEPTION",
            "PERCEPTION": "EMOTION",
            "EMOTION": "ACCEPTANCE",
            "ACCEPTANCE": "REMINISCENCE",
        }
        self._aaq = AAQScoring()
        self._default_return = False

    async def ainvoke(self, query: str, history: str, current_session: str) -> bool:
        if current_session.upper() in {"ACCEPTANCE", "REMINISCENCE"}:
            return False

        try:
            prompt = monitor_agent_template.format_messages(
                current_session_phase=current_session,
                history=history,
                user_input=query,
            )
            response = await self.llm.ainvoke(prompt)
            is_ready_to_move = extract_int(
                response.content, min_option=0, max_option=1, default=0
            )
            return bool(is_ready_to_move)

        except Exception as e:
            logger.error(f"[{self.__class__.__name__}] {e}")
            return self._default_return

    def to_next_session(self, current_session: str) -> str:
        return self.session_transition.get(current_session.upper(), current_session)

    def is_ready_to_accept(self, user_info: str) -> tuple[bool, int]:
        is_ready, aaq_score = self._aaq.is_ready_to_accept(user_info)
        return is_ready, aaq_score


class ContextAgent:
    def __init__(self, ltm_cls: LongTermMemory):
        self.stm: dict[str, ShortTermMemory] = {}
        self.ltm: LongTermMemory = ltm_cls

    @classmethod
    async def create(cls, ltm_db_path: str):
        ltm_cls = await LongTermMemory.create(vector_store_path=ltm_db_path)
        return cls(ltm_cls)

    def add_session(self, session_id: str, force_init: bool = False):
        if session_id in self.stm and not force_init:
            return
        self.stm[session_id] = ShortTermMemory()

    async def remove_session(self, session_id: str):
        await self.stm[session_id].shutdown()
        self.stm.pop(session_id, None)

    async def add_message(
        self, session_id: str, user_id: str, user_msg: str, ai_msg: str
    ):
        if session_id not in self.stm:
            logger.debug(
                f"[{self.__class__.__name__}] Initializing a new session ({session_id})."
            )
            self.add_session(session_id)

        await self.stm[session_id].add_user_message(user_msg)
        await self.stm[session_id].add_ai_message(ai_msg)
        await self.ltm.add(content=user_msg, user_id=user_id)

    def get_stm(self, session_id: str) -> list:
        session_stm = self.stm.get(session_id, None)
        if session_stm is None:
            return []
        return session_stm.get_history()

    async def get_ltm(self, user_id: str, query: str = None, k: int = 3) -> list[str]:
        if query is None:
            all_ltm = await self.ltm.get(user_id)
            return all_ltm
        related_ltm = await self.ltm.search(query, user_id, limit=k)
        return related_ltm
