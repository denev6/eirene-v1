import asyncio

from langchain_naver import ChatClovaX, ClovaXEmbeddings
from langchain.schema import AIMessage, BaseMessage
from langchain.memory import ConversationBufferMemory

from mem0_naver import AsyncMemory
from .utils import logger, format_chat_history
from .prompt import short_term_summarize_template


class LongTermMemory:
    def __init__(self, vector_store_path: str) -> None:
        self.memory: AsyncMemory = None
        self.vector_store_path = vector_store_path

    @classmethod
    async def create(
        cls, vector_store_path: str = "./db/faiss_ltm"
    ) -> "LongTermMemory":
        instance = cls(vector_store_path)
        config = {
            "llm": {
                "provider": "langchain",
                "config": {"model": ChatClovaX(model="HCX-005", temperature=0)},
            },
            "embedder": {
                "provider": "langchain",
                "config": {"model": ClovaXEmbeddings(model="clir-emb-dolphin")},
                "embedding_dims": 1024,
            },
            "vector_store": {
                "provider": "faiss",
                "config": {
                    "collection_name": "ltm",
                    "distance_strategy": "inner_product",
                    "path": instance.vector_store_path,
                    "embedding_model_dims": 1024,
                },
            },
            "version": "v1.1",
        }
        instance.memory = await AsyncMemory.from_config(config)
        logger.debug(f"Initialized LTM at {vector_store_path}.")
        return instance

    async def add(self, content: str | list[dict[str, str]], user_id: str):
        if not self.memory:
            logger.error(
                "Memory not initialized. Call `LongTermMemory.create()` first."
            )
            return
        try:
            await self.memory.add(messages=content, user_id=user_id)
        except Exception as e:
            logger.error(
                f"[{self.__class__.__name__}] Not able to `add` in LTM: {e} ({user_id})"
            )

    async def search(self, query: str, user_id: str, limit: int = 3) -> list[str]:
        if not self.memory:
            logger.error(
                "Memory not initialized. Call `LongTermMemory.create()` first."
            )
            return []

        try:
            retrieved = await self.memory.search(
                query=query, limit=limit, user_id=user_id
            )
        except Exception as e:
            logger.error(f"[{self.__class__.__name__}] {e}")
            return []

        retrieved = retrieved.get("results", [])
        logger.debug(f"Retrieved from LTM: {retrieved}")
        if retrieved:
            retrieved = [data["memory"] for data in retrieved]
        return retrieved

    async def get(self, user_id: str) -> list[str]:
        if not self.memory:
            logger.error(
                "Memory not initialized. Call `LongTermMemory.create()` first."
            )
            return []

        try:
            parsed = await self.memory.get_all(user_id=user_id)
        except Exception as e:
            logger.error(f"[{self.__class__.__name__}] {e}")
            return []

        parsed = parsed.get("results", [])
        logger.debug(f"Parsed from LTM: {parsed}")

        if parsed:
            parsed = [data["memory"] for data in parsed]
        return parsed


class ShortTermMemory:
    def __init__(self):
        self.llm = ChatClovaX(model="HCX-DASH-002", temperature=0, max_tokens=256)
        self.memory = ConversationBufferMemory()
        self.summary = None
        self.memory_buffer_limit = 20
        self.num_chat_to_reserve = 4
        self.len_history = 0

        # Async `_summary()`
        self._summary_queue = asyncio.Queue()
        self._summary_task = asyncio.create_task(self._summary_worker())
        self._is_summarizing = False
        self._lock = asyncio.Lock()

    def get_history(self) -> list[BaseMessage]:
        if self.summary:
            return [self.summary] + self.memory.chat_memory.messages
        return self.memory.chat_memory.messages

    async def add_user_message(self, message: str):
        async with self._lock:
            self.memory.chat_memory.add_user_message(message)
            self.len_history += 1

    async def add_ai_message(self, message: str):
        async with self._lock:
            self.memory.chat_memory.add_ai_message(message)
            self.len_history += 1

            if (
                self.len_history >= self.memory_buffer_limit
                and not self._is_summarizing
            ):
                snapshot = self.get_history().copy()
                asyncio.create_task(self._summary_queue.put(snapshot))
                self._is_summarizing = True

    async def _summary_worker(self):
        while True:
            chat_snapshot = await self._summary_queue.get()

            if chat_snapshot is None:
                self._summary_queue.task_done()
                break

            try:
                await self._summarize(chat_snapshot)
            finally:
                self._is_summarizing = False
                self._summary_queue.task_done()

    async def _summarize(self, snapshot: list):
        chat_history_to_summarize = snapshot[: -self.num_chat_to_reserve]

        if not chat_history_to_summarize:
            return

        chat_history_str = format_chat_history(chat_history_to_summarize)
        summarize_prompt = short_term_summarize_template.format_messages(
            history=chat_history_str
        )
        summary_result = await asyncio.to_thread(self.llm.invoke, summarize_prompt)
        new_summary = AIMessage(content=summary_result.content)

        async with self._lock:
            num_to_prune = len(snapshot) - self.num_chat_to_reserve
            if num_to_prune > 0:
                self.memory.chat_memory.messages = self.memory.chat_memory.messages[
                    num_to_prune:
                ]

            self.summary = new_summary
            self.len_history = len(self.memory.chat_memory.messages)

    async def shutdown(self):
        await self._summary_queue.put(None)
        await self._summary_queue.join()
        await self._summary_task
