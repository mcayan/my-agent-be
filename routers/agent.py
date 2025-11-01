from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from routers.auth import get_current_active_user
from schemas.chat import (
    ChatRequest,
    ChatResponse,
)
from services.agent import agent

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
    支持图片搜索和生成功能
    """
    try:
        # 调用 LangGraph 智能体
        result = await agent.run(
            user_input=request.message,
            conversation_history=[]  # 可以从数据库加载历史记录
        )
        
        # 构建响应
        response_message = result["response"]
        
        # 如果有图片信息，可以添加到响应中
        if result.get("reference_image"):
            reference_image = result["reference_image"]
            if reference_image.get("presigned_url"):
                # 图片信息已经包含在 response 中了
                pass
        
        return ChatResponse(
            message=response_message,
            conversation_id=request.conversation_id or "new_conversation"
        )
        
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"处理消息时出错: {str(e)}"
        )


