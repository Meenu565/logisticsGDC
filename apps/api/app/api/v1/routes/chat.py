from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.conversation import ConversationOrchestrator
from app.db.session import get_db
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat")


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    """Handle a dispatcher chat message."""
    orchestrator = ConversationOrchestrator(db)
    result = orchestrator.handle_message(
        session_id=UUID(request.session_id),
        user_message=request.message,
        tool_args=request.tool_args,
    )
    return ChatResponse(**result)

