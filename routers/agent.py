from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from routers.auth import get_current_active_user
from schemas.chat import (
    ChatRequest,
    ChatResponse,
)

router = APIRouter(prefix="/agent", tags=["智能体"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    智能体对话接口
    
    接收用户消息，返回 AI 回复
    """
    # TODO: 实现  LangGraph +的对话逻辑
    
    # 预留接口，暂时返回模拟数据
    return ChatResponse(
        message="这是一个预留接口，等待对接 LangChain 和 Google AI。",
        conversation_id=request.conversation_id or "new_conversation_id"
    )


