import os
import time
import logging
import functools
import warnings
from pathlib import Path

from dotenv import load_dotenv
from langchain.schema import BaseMessage

dotenv_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path)


USER_SESSION_SQLITE = os.getenv("USER_SESSION_SQLITE")
MEDICAL_DB_FAISS = os.getenv("MEDICAL_DB_FAISS")
LEGACY_DB_FAISS = os.getenv("LEGACY_DB_FAISS")
LTM_DB_FAISS = os.getenv("LTM_DB_FAISS")
USE_DUMMY_RESPONSE = (
    True if os.getenv("USE_DUMMY_RESPONSE", "true").strip().lower() == "true" else False
)
LOGGER_NAME = "Eirene"  # `mem0-naver`에서도 'Eirene'을 사용


def set_clovax_api_key():
    api_key = os.getenv("CLOVASTUDIO_API_KEY", "").strip()
    if not api_key.startswith("nv-"):
        raise ValueError(f"Invalid Clova API KEY!")
    os.environ["CLOVASTUDIO_API_KEY"] = api_key


def set_logger(log_name, ignore_warning=False):
    mapping = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    level = str(os.getenv("LOG_LEVEL")).strip().upper()
    if ignore_warning:
        warnings.filterwarnings("ignore")

    level = mapping.get(level, logging.INFO)

    logger = logging.getLogger(log_name)
    logger.setLevel(level)

    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt="[%(asctime)s] %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
    return logger


logger = set_logger(LOGGER_NAME, ignore_warning=True)


def trim_str(msg: str, limit: int = 50) -> str:
    if len(msg) > limit:
        return f"{msg[:limit].replace('\n', ' ')}..."
    return msg


def extract_int(raw_answer: str, min_option: int, max_option: int, default=None):
    assert max_option < 10, f"`max_option` must be ones digit, got {max_option}"

    first_digit = next((char for char in raw_answer if char.isdigit()), None)
    if first_digit is None:
        raw_answer = trim_str(raw_answer, 10)
        logger.warning(
            f"No option is found in '{raw_answer}' (expected {min_option}-{max_option})"
        )
        return default

    if first_digit.isdigit():
        last_choice_idx = int(first_digit)
        if min_option <= last_choice_idx <= max_option:
            return last_choice_idx

    logger.warning(
        f"No option is found (got {first_digit}, expected {min_option}-{max_option})"
    )
    return default


def safe_str(input_string: str) -> str:
    return input_string.encode("utf-8", errors="replace").decode("utf-8")


def format_chat_history(chat_history: list[BaseMessage]) -> str:
    return "\n".join([f"- {msg.type}: {msg.content}" for msg in chat_history])


def async_timer(func):
    @functools.wraps(func)
    async def wrapper_timer(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        run_time = end_time - start_time
        logger.debug(f"Execution time: '{func.__name__}' {run_time:.4f}s")
        return result

    return wrapper_timer
