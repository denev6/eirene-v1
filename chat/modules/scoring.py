from langchain_naver import ChatClovaX

from .prompt import aaq_scoring_template
from .utils import logger, extract_int


class AAQScoring:
    def __init__(self):
        self.model = ChatClovaX(temperature=0, max_tokens=8)
        self._score_threshold = 18
        self._questions = [
            "고통스러운 경험과 기억으로 인해 나는 내가 가치 있게 여기는 삶을 살기가 어렵다.",
            "나는 내 감정을 느끼는 것이 두렵다.",
            "나는 내 걱정과 느낌을 통제하지 못하는 것에 대해 염려한다.",
            "내 고통스러운 기억들은 내가 만족스러운 삶을 살지 못하게 한다.",
            "감정은 내 일상생활에서 문제를 일으킨다.",
            "대부분의 사람들은 나보다 자신의 삶을 잘 꾸려나가고 있는 것 같다.",
            "걱정은 내가 성공하는 데 걸림돌이 된다.",
        ]

    def _get_score(self, question: str, user_info: str) -> int:
        try:
            aaq_prompt = aaq_scoring_template.format_messages(
                user_info=user_info, user_input=question
            )
            raw_response = self.model.invoke(aaq_prompt)
            score = extract_int(
                raw_response.content, min_option=1, max_option=7, default=0
            )
        except Exception as e:
            logger.error(f"[{self.__class__.__name__}] {e}")
            score = 0

        logger.debug(f"{question}: {score}")
        return score

    def _get_overall_score(self, scores: list[int]) -> int:
        non_zero_count = 7 - scores.count(0)
        if non_zero_count == 0:
            return -1
        return int(sum(scores) * 7 / non_zero_count)

    def is_ready_to_accept(self, user_info: str) -> tuple[bool, int]:
        scores = [self._get_score(question, user_info) for question in self._questions]
        overall_score = self._get_overall_score(scores)
        logger.debug(f"AAQ-II Score: {overall_score}/49")

        if 7 <= overall_score < self._score_threshold:
            return True, overall_score
        return False, overall_score
