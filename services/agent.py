"""LangGraph 智能体实现"""
import json
from typing import TypedDict, Annotated, Sequence, Literal
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.constants import START
from langgraph.graph import StateGraph, END

from core.config import settings
from services.image_tools import image_search_tool, image_generation_tool


# 定义状态
class AgentState(TypedDict):
    """智能体状态"""
    messages: Sequence[BaseMessage]
    user_input: str
    need_image_generation: bool
    search_query: str
    reference_image: dict
    generated_image: dict
    response: str


class ImageAgent:
    """图片生成智能体"""
    
    def __init__(self):
        # 初始化 LLM
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required in .env file")
        
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=settings.OPENAI_API_KEY,
            base_url="https://api.openai-proxy.org/v1"
        )
        
        # 构建图
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """构建 LangGraph 工作流"""
        workflow = StateGraph(AgentState)
        
        # 添加节点
        workflow.add_node("analyze_intent", self.analyze_intent)
        workflow.add_node("search_image", self.search_image)
        workflow.add_node("generate_image", self.generate_image)
        workflow.add_node("normal_chat", self.normal_chat)
        workflow.add_node("format_response", self.format_response)
        
        # 设置入口
        workflow.add_edge(START,"analyze_intent")
        
        # 添加条件边
        workflow.add_conditional_edges(
            "analyze_intent",
            self.route_after_intent,
            {
                "search": "search_image",
                "chat": "normal_chat"
            }
        )
        
        workflow.add_edge("search_image", "generate_image")
        workflow.add_edge("generate_image", "format_response")
        workflow.add_edge("normal_chat", "format_response")
        workflow.add_edge("format_response", END)
        
        return workflow.compile()
    
    async def analyze_intent(self, state: AgentState) -> AgentState:
        """节点1: 分析用户意图"""
        user_input = state["user_input"]
        
        # 使用 LLM 分析意图
        prompt = f"""分析以下用户输入，判断用户是否需要生成图片。

用户输入: {user_input}

如果用户明确要求生成、搜索或要某个图片（比如"我要一张xxx的图片"、"给我生成xxx图片"、"帮我找xxx图片"等），
请回复 JSON 格式: {{"need_image": true, "search_query": "提取的搜索关键词"}}

如果是普通对话，请回复: {{"need_image": false}}

只返回 JSON，不要其他内容。
"""
        
        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            response_text = response.content.strip()
            
            # 解析 JSON 响应
            # 提取 JSON 部分（防止有其他文字）
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            result = json.loads(response_text)
            
            state["need_image_generation"] = result.get("need_image", False)
            if state["need_image_generation"]:
                state["search_query"] = result.get("search_query", user_input)
            
        except Exception as e:
            print(f"Error analyzing intent: {e}")
            # 默认作为普通对话处理
            state["need_image_generation"] = False
        
        return state
    
    def route_after_intent(self, state: AgentState) -> Literal["search", "chat"]:
        """条件路由: 根据意图决定下一步"""
        if state["need_image_generation"]:
            return "search"
        return "chat"
    
    async def search_image(self, state: AgentState) -> AgentState:
        """节点2: 搜索参考图片"""
        search_query = state["search_query"]
        
        print(f"Searching for: {search_query}")
        
        result = await image_search_tool.search_image(search_query)
        
        if result:
            state["reference_image"] = result
            print(f"Found reference image: {result['presigned_url']}")
        else:
            state["reference_image"] = {}
            print("No reference image found")
        
        return state
    
    async def generate_image(self, state: AgentState) -> AgentState:
        """节点3: 生成新图片"""
        user_input = state["user_input"]
        reference_image = state.get("reference_image", {})
        
        # 使用 LLM 生成更好的图片提示词
        prompt_generation = f"""基于用户请求，生成一个详细的图片生成提示词（英文）。

用户请求: {user_input}

请生成一个详细的英文提示词，描述图片应该包含的内容、风格、颜色等。
只返回提示词本身，不要其他解释。
"""
        
        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt_generation)])
            generation_prompt = response.content.strip()
        except Exception as e:
            print(f"Error generating prompt: {e}")
            generation_prompt = state["search_query"]
        
        print(f"Generation prompt: {generation_prompt}")
        
        # 调用图片生成 API
        reference_url = reference_image.get("presigned_url") if reference_image else None
        
        result = await image_generation_tool.generate_image_simple(
            prompt=generation_prompt,
            reference_image_url=reference_url
        )
        
        if result:
            state["generated_image"] = result
            print(f"Generated image: {result.get('presigned_url', 'N/A')}")
        else:
            state["generated_image"] = {}
            print("Failed to generate image")
        
        return state
    
    async def normal_chat(self, state: AgentState) -> AgentState:
        """节点4: 普通对话"""
        user_input = state["user_input"]
        messages = state.get("messages", [])
        
        # 构建对话历史
        chat_messages = [
            SystemMessage(content="你是一个友好的 AI 助手。请用简洁、自然的方式回答用户的问题。")
        ]
        chat_messages.extend(messages[-5:])  # 保留最近5条消息
        chat_messages.append(HumanMessage(content=user_input))
        
        try:
            response = await self.llm.ainvoke(chat_messages)
            state["response"] = response.content
        except Exception as e:
            print(f"Error in normal chat: {e}")
            state["response"] = "抱歉，我遇到了一些问题，请稍后再试。"
        
        return state
    
    async def format_response(self, state: AgentState) -> AgentState:
        """节点5: 格式化最终响应"""
        if state["need_image_generation"]:
            reference_image = state.get("reference_image", {})
            generated_image = state.get("generated_image", {})
            
            response_parts = []
            
            if reference_image.get("success"):
                response_parts.append(
                    f"✅ 已找到参考图片：{reference_image.get('title', '样例图片')}"
                )
                response_parts.append(f"📷 参考图片链接：{reference_image['presigned_url']}")
            else:
                response_parts.append("⚠️ 未找到合适的参考图片")
            
            if generated_image.get("success"):
                response_parts.append(
                    f"\n✨ 已根据您的需求生成新图片！"
                )
                response_parts.append(f"🎨 生成的图片链接：{generated_image['presigned_url']}")
                response_parts.append(f"💡 生成提示词：{generated_image.get('prompt', '')}")
            else:
                response_parts.append("\n❌ 图片生成失败，请稍后重试")
            
            state["response"] = "\n".join(response_parts)
        
        return state
    
    async def run(self, user_input: str, conversation_history: list = None) -> dict:
        """
        运行智能体
        
        Args:
            user_input: 用户输入
            conversation_history: 对话历史
            
        Returns:
            包含响应和图片信息的字典
        """
        # 初始化状态
        initial_state = {
            "messages": conversation_history or [],
            "user_input": user_input,
            "need_image_generation": False,
            "search_query": "",
            "reference_image": {},
            "generated_image": {},
            "response": ""
        }
        
        # 运行图
        final_state = await self.graph.ainvoke(initial_state)
        
        return {
            "response": final_state["response"],
            "reference_image": final_state.get("reference_image"),
            "generated_image": final_state.get("generated_image"),
            "need_image_generation": final_state["need_image_generation"]
        }


# 全局智能体实例
agent = ImageAgent()


