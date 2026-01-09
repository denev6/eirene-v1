"""NOTE
To avoid influencing subsequent development, detailed prompt designs are not disclosed.
후속 개발에 영향을 미치지 않기 위해 프롬프트 설계는 공개하지 않습니다.
"""

from langchain.prompts import ChatPromptTemplate


counselor_agent_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """[undisclosed]""",
        ),
        (
            "user",
            """[undisclosed]""",
        ),
    ]
)

DEFAULT_INSTRUCTION_PROMPT = """[undisclosed]"""
SETTING_INSTRUCTION_PROMPT = """[undisclosed]"""
PERCEPTION_INSTRUCTION_PROMPT = """[undisclosed]"""
EMOTION_INSTRUCTION_PROMPT = """[undisclosed]"""
ACCEPTANCE_INSTRUCTION_PROMPT = """[undisclosed]"""
REMINISCENCE_INSTRUCTION_PROMPT = """[undisclosed]"""


SESSION_INSTRUCTION_PROMPTS = {
    "SETTING": SETTING_INSTRUCTION_PROMPT,
    "PERCEPTION": PERCEPTION_INSTRUCTION_PROMPT,
    "EMOTION": EMOTION_INSTRUCTION_PROMPT,
    "ACCEPTANCE": ACCEPTANCE_INSTRUCTION_PROMPT,
    "REMINISCENCE": REMINISCENCE_INSTRUCTION_PROMPT,
}

monitor_agent_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """[undisclosed]""",
        ),
        (
            "user",
            """[undisclosed]""",
        ),
    ]
)

medical_agent_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """[undisclosed]""",
        ),
        (
            "user",
            """[undisclosed]""",
        ),
    ]
)


acp_agent_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """[undisclosed]""",
        ),
        (
            "user",
            """[undisclosed]""",
        ),
    ]
)


legacy_agent_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """[undisclosed]""",
        ),
        (
            "user",
            """[undisclosed]""",
        ),
    ]
)


cultural_agent_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """[undisclosed]""",
        ),
        (
            "user",
            """[undisclosed]""",
        ),
    ]
)


escalation_agent_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """[undisclosed]""",
        ),
        (
            "user",
            """[undisclosed]""",
        ),
    ]
)


aaq_scoring_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """[undisclosed]""",
        ),
        (
            "user",
            """[undisclosed]""",
        ),
    ]
)


# Memory
short_term_summarize_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """[undisclosed]""",
        ),
        (
            "user",
            """[undisclosed]""",
        ),
    ]
)

# Router
ROUTING_PROMPTS = {
    "MEDICAL": """[undisclosed]""",
    "LEGACY": """[undisclosed]""",
    "ACP": """[undisclosed]""",
    "CULTURAL": """[undisclosed]""",
}

routing_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """[undisclosed]""",
        ),
        (
            "user",
            """[undisclosed]""",
        ),
    ]
)
