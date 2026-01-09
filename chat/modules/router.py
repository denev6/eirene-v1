import json
import uuid
import asyncio
import http.client
from http import HTTPStatus
from typing import List, Dict, Any, Tuple, Optional

from langchain_naver import ChatClovaX
from langchain.schema.messages import BaseMessage

from .utils import logger, extract_int
from .prompt import ROUTING_PROMPTS, routing_template


class Router:
    def __init__(self):
        self.routing_llm = ChatClovaX(model="HCX-DASH-002", temperature=0, max_tokens=4)
        self._states = [
            "MEDICAL",
            "LEGACY",
            "ACP",
            "CULTURAL",
        ]

    async def ainvoke(self, query: str, history: str = "") -> list[str]:
        try:
            prompts = [
                routing_template.format_messages(
                    history=history,
                    agent_prompt=ROUTING_PROMPTS[state],
                    user_input=query,
                )
                for state in self._states
            ]
            tasks = [self.routing_llm.ainvoke(prompt) for prompt in prompts]
            results = await asyncio.gather(*tasks)
            list_is_required = [
                extract_int(res.content, min_option=0, max_option=1, default=0)
                for res in results
            ]
            logger.debug(f"{self._states}: {list_is_required}")
            required_states = [
                state
                for state, is_required in zip(self._states, list_is_required)
                if bool(is_required)
            ]
            return required_states
        except Exception as e:
            logger.error(f"[{self.__class__.__name__}] {e}")
            return []


class ClovaRouter:
    def __init__(self, api_key: str):
        logger.warning(
            f"(Deprecated) `{self.__class__.__name__}` returns only one domain as the result."
        )
        self._host = "clovastudio.stream.ntruss.com"
        self.headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {api_key}",
            "X-NCP-CLOVASTUDIO-REQUEST-ID": str(uuid.uuid4()),
        }

    def _send_request(
        self, request: Dict[str, Any], url: str
    ) -> Tuple[Optional[Dict[str, Any]], int]:
        conn = None
        try:
            conn = http.client.HTTPSConnection(self._host)
            conn.request(
                "POST",
                url,
                json.dumps(request),
                self.headers,
            )
            response = conn.getresponse()
            status = response.status
            if status != HTTPStatus.OK:
                logger.error(
                    f"Request failed with status {status}: {response.read().decode()}"
                )
                return None, status
            result = json.loads(response.read().decode(encoding="utf-8"))
            return result, status
        except Exception as e:
            logger.error(f"An error occurred during request: {e}")
            return None, HTTPStatus.INTERNAL_SERVER_ERROR
        finally:
            if conn:
                conn.close()

    def _convert_history_to_clova_format(
        self, history: List[BaseMessage]
    ) -> List[Dict[str, str]]:
        role_map = {
            "human": "user",
            "ai": "assistant",
            "system": "system",
        }
        return [
            {"role": role_map.get(msg.type, "user"), "content": msg.content}
            for msg in history
        ]

    def invoke(self, query: str, url: str, history: List[BaseMessage] = []) -> str:
        clova_history = (
            self._convert_history_to_clova_format(history) if history else []
        )
        request = {
            "query": query,
            "chatHistory": clova_history,
        }
        res, status = self._send_request(request, url)
        if status == HTTPStatus.OK and res:
            return res.get("result", "Error: No result key")
        else:
            logger.error(
                f"Failed to get a valid response. Status: {status}, Response: {res}"
            )
            return "Error"
