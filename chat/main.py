import uuid
import asyncio
from datetime import datetime
from typing import Dict
from contextlib import asynccontextmanager

from pydantic import BaseModel
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from modules.utils import (
    set_clovax_api_key,
    logger,
    format_chat_history,
    safe_str,
    trim_str,
    USER_SESSION_SQLITE,
    MEDICAL_DB_FAISS,
    LEGACY_DB_FAISS,
    LTM_DB_FAISS,
    USE_DUMMY_RESPONSE,
)
from modules.agents import CounselorAgent, MonitorAgent, EscalationAgent, ContextAgent
from modules.database import UserSessionDB

set_clovax_api_key()

# Agent initialization
counselor_agent: CounselorAgent = None
monitor_agent: MonitorAgent = None
escalation_agent: EscalationAgent = None
context_agent: ContextAgent = None
user_session_db: UserSessionDB = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global counselor_agent
    global monitor_agent
    global escalation_agent
    global context_agent
    global user_session_db

    # On server startup
    logger.info("Starting server...")
    counselor_agent = CounselorAgent(
        medical_db_path=MEDICAL_DB_FAISS, legacy_db_path=LEGACY_DB_FAISS
    )
    monitor_agent = MonitorAgent()
    escalation_agent = EscalationAgent()
    context_agent = await ContextAgent.create(ltm_db_path=LTM_DB_FAISS)
    user_session_db = UserSessionDB(db_path=USER_SESSION_SQLITE)

    yield

    # On server shutdown
    logger.info("Killing server...")
    user_session_db.close()


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

session_store: Dict[str, "SessionContext"] = {}


class SessionContext(BaseModel):
    """Manages the context of a user session.

    Each session has a unique ID and includes user information,
    conversation history, initialization status, and creation time.

    Attributes:
        user_id (str): Unique identifier for the user.
        counseling_session (str): The ongoing counseling session.
        created_at (datetime): The time the session was created.
    """

    user_id: str
    counseling_session: str
    created_at: datetime = datetime.now()


class StartSessionRequest(BaseModel):
    """Request model for the '/chat/start' endpoint.

    Attributes:
        user_id (str): The ID of the user starting the session.
    """

    user_id: str


class CheckSessionRequest(BaseModel):
    """Request model for the '/chat/check' endpoint.

    Attributes:
        session_id (str): The ID of the session to check.
    """

    session_id: str


class ChatRequest(BaseModel):
    """Request model for the '/chat' endpoint.

    Attributes:
        session_id (str): The ID of the session for the conversation.
        message (str): The message sent by the user.
    """

    session_id: str
    message: str


class EndSessionRequest(BaseModel):
    """Request model for the '/chat/end' endpoint.

    Attributes:
        session_id (str): The ID of the session to end.
    """

    session_id: str


@app.post("/chat/start")
async def start_session(req: StartSessionRequest):
    """Starts a new chat session and returns a unique session ID.

    Creates a new session context based on the user ID and adds it to the in-memory store.
    If the user has no existing counseling session history, it initializes to the 'SETTING' stage.

    Args:
        req (StartSessionRequest): The session start request data.

    Raises:
        HTTPException: Raises a 400 error if the same session ID already exists and is active.

    Returns:
        dict: The created unique session ID (`session_id`).
    """
    user_id = req.user_id
    logger.debug(f"Access from {user_id}.")
    session_id = str(uuid.uuid4())

    if session_id in session_store:
        if session_store[session_id].user_id == user_id:
            raise HTTPException(status_code=400, detail="Session already exists.")
        session_id = str(uuid.uuid4())

    user_session = user_session_db.get(user_id)
    if user_session is None:
        user_session = "SETTING"
        user_session_db.insert(user_id, user_session)

    session_store[session_id] = SessionContext(
        user_id=user_id,
        counseling_session=user_session,
    )
    context_agent.add_session(session_id)
    logger.debug(f"USER {user_id} started {user_session} session ({session_id})")

    return {"session_id": session_id}


@app.post("/chat/check")
async def check_session(req: CheckSessionRequest):
    """Checks the status of the specified session.

    Checks if the session exists to inform the client whether chatting is possible.

    Args:
        req (CheckSessionRequest): The session check request data.

    Raises:
        HTTPException: Raises a 404 error if the session does not exist.

    Returns:
        dict: A status message indicating that the session is ready.
    """
    ctx = session_store.get(req.session_id)

    if ctx is None:
        raise HTTPException(status_code=404, detail="Session not found")

    logger.debug(
        f"USER {ctx.user_id} is in {ctx.counseling_session} session ({req.session_id}) / created_at: {ctx.created_at}"
    )

    return {"status": "ready"}


@app.post("/chat")
async def chat(req: ChatRequest, background_tasks: BackgroundTasks):
    """Processes a user message and returns a streaming response.

    Retrieves and processes the user's conversation history based on the session ID,
    and streams the response generated by the LLM in real-time.

    Args:
        req (ChatRequest): The user chat request data.

    Raises:
        HTTPException: Raises a 404 error if the session does not exist.

    Returns:
        StreamingResponse: A stream of response text generated by the LLM.
    """
    if req.session_id not in session_store:
        raise HTTPException(status_code=404, detail="Session not found.")

    user_msg = safe_str(req.message).strip()
    ctx = session_store[req.session_id]
    logger.debug(f"Received({ctx.user_id, ctx.counseling_session}): {user_msg} ")

    user_info = await context_agent.get_ltm(ctx.user_id, user_msg, k=3)
    user_info_str = "\n".join(f"- {info}" for info in user_info)
    history_list = context_agent.get_stm(req.session_id)
    history_str = format_chat_history(history_list)

    # Check for risk situations
    should_stop = await escalation_agent.ainvoke(user_msg, history_str)

    async def event_generator():
        if USE_DUMMY_RESPONSE:
            # Dummy Response
            # Since the prompts are undisclosed,
            # a dummy response is returned for testing purposes.
            # 프롬프트가 공개되어 있지 않기 때문에,
            # 테스트를 위해 임의의 값을 반환합니다.
            yield f"INPUT: '{trim_str(user_msg, 30)}'"
            return

        # Actual Response
        global session_store
        full_response = ""
        counseling_session = ctx.counseling_session

        if bool(should_stop):
            # When judged to be a risk situation
            logger.info(
                f"Escalation Agent triggered. {ctx.user_id}: {user_msg} ({req.session_id})."
            )
            full_response = escalation_agent.message
            yield escalation_agent.message

        else:
            # When not a risk situation
            should_transition_session = await monitor_agent.ainvoke(
                user_msg, history_str, counseling_session
            )
            if bool(should_transition_session):
                previous_session = counseling_session
                counseling_session = monitor_agent.to_next_session(previous_session)
                logger.info(
                    f"User({ctx.user_id}) session: {previous_session} -> {counseling_session} ({req.session_id})"
                )
                session_store[req.session_id].counseling_session = counseling_session

            async for chunk in counselor_agent.stream(
                user_msg, history_str, user_info_str, counseling_session
            ):
                if chunk:
                    full_response += chunk
                    yield chunk
                    await asyncio.sleep(0.01)

        logger.debug(f"Return: {trim_str(full_response)}")

        # Add conversation history in the background (& summarize)
        background_tasks.add_task(
            context_agent.add_message,
            req.session_id,
            ctx.user_id,
            user_msg,
            full_response,
        )

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/chat/end")
async def end_session(req: EndSessionRequest, background_tasks: BackgroundTasks):
    """Ends the active chat session.

    Removes the context of the session ID from the session store,
    and updates the user's counseling session stage in the background.

    Args:
        req (EndSessionRequest): The session end request data.

    Raises:
        HTTPException: Raises a 404 error if the session does not exist.

    Returns:
        dict: A success message for ending the session.
    """
    if req.session_id not in session_store:
        raise HTTPException(status_code=404, detail="Session not found.")

    user_id = session_store[req.session_id].user_id
    counseling_session = session_store[req.session_id].counseling_session

    # Update user therapy session
    background_tasks.add_task(
        update_user_counseling_session, user_id, counseling_session
    )

    # Clean up session and STM
    session_store.pop(req.session_id, None)
    await context_agent.remove_session(req.session_id)
    logger.info(f"End session {req.session_id}.")

    return {"message": f"Session {req.session_id} ended."}


async def update_user_counseling_session(user_id: str, counseling_session: str):
    """Evaluates the user's counseling session stage and updates the database if necessary.

    In the 'ACCEPTANCE' session, it attempts to transition to 'REMINISCENCE' based on the AAQ-II score.
    If the session stage changes during counseling, the final stage is recorded in the database.

    Args:
        user_id (str): The user's unique ID.
        counseling_session (str): The current counseling session stage.
    """
    previous_user_session = user_session_db.get(user_id)

    if counseling_session == "ACCEPTANCE":
        # AAQ-II acceptance survey
        acceptance_clues = await context_agent.get_ltm(
            user_id=user_id,
            query="User's inner expressions to check readiness for therapy",
            k=10,
        )
        should_update, aaq_score = monitor_agent.is_ready_to_accept(
            user_info="\n".join(acceptance_clues)
        )
        if should_update:
            user_session_db.update(user_id, session_name="REMINISCENCE")
            logger.info(
                f"UPDATE USER {user_id} from 'ACCEPTANCE' to 'REMINISCENCE' session (score: {aaq_score}/49)"
            )

    if previous_user_session != counseling_session:
        # When the session is switched during counseling
        user_session_db.update(user_id, session_name=counseling_session)
