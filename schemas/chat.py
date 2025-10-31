from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ChatMessage(BaseModel):
    """聊天消息模型"""
    role: str = Field(..., description="角色：user 或 assistant")
    content: str = Field(..., description="消息内容")
    

class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str = Field(..., min_length=1, description="用户消息")
    conversation_id: Optional[str] = Field(None, description="对话ID，用于保持上下文")
    

class ChatResponse(BaseModel):
    """聊天响应模型"""
    message: str = Field(..., description="AI 回复内容")
    conversation_id: str = Field(..., description="对话ID")
    

class FileUploadResponse(BaseModel):
    """文件上传响应模型"""
    file_id: str = Field(..., description="文件ID")
    filename: str = Field(..., description="文件名")
    file_size: int = Field(..., description="文件大小（字节）")
    file_type: str = Field(..., description="文件类型")
    uploaded_at: datetime = Field(..., description="上传时间")


class ConversationHistory(BaseModel):
    """对话历史模型"""
    conversation_id: str = Field(..., description="对话ID")
    title: str = Field(..., description="对话标题")
    messages: List[ChatMessage] = Field(..., description="消息列表")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

