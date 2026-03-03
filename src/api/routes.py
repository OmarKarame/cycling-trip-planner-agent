from fastapi import APIRouter, Depends

from src.agent.orchestrator import AgentOrchestrator
from src.agent.session import SessionStore
from src.api.dependencies import get_orchestrator, get_session_store
from src.models import ChatRequest, ChatResponse

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    session_store: SessionStore = Depends(get_session_store),
    orchestrator: AgentOrchestrator = Depends(get_orchestrator),
) -> ChatResponse:
    session = session_store.get_or_create(request.session_id)

    response_text = await orchestrator.chat(request.message, session)

    return ChatResponse(
        session_id=session.session_id,
        response=response_text,
        tools_used=session.tools_used_this_turn,
    )
