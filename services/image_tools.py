"""图片搜索和生成工具"""
import json
from typing import Optional, Dict, Any

import httpx

from core.config import settings
from services.minio_client import minio_client


class ImageSearchTool:
    """图片搜索工具 - 使用 Serper API"""
    
    def __init__(self):
        self.api_key = settings.SERPER_API_KEY
        self.base_url = "https://google.serper.dev/images"
        
        if not self.api_key:
            print("⚠️  Warning: SERPER_API_KEY not configured, image search will fail")
    
    async def search_image(self, query: str) -> Optional[Dict[str, Any]]:
        """
        搜索图片
        
        Args:
            query: 搜索关键词
            
        Returns:
            包含图片信息的字典，失败返回 None
        """
        try:
            headers = {
                "X-API-KEY": self.api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "q": query,
                "num": 1  # 只获取第一个结果
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                response.raise_for_status()
                
                data = response.json()
                
                if data.get("images") and len(data["images"]) > 0:
                    first_image = data["images"][0]
                    image_url = first_image.get("imageUrl")
                    
                    if image_url:
                        # 下载并上传到 MinIO
                        minio_path = await minio_client.upload_image_from_url(
                            image_url, 
                            prefix="search-results"
                        )
                        
                        if minio_path:
                            # 获取预签名 URL
                            presigned_url = minio_client.get_image_url(minio_path)
                            
                            return {
                                "success": True,
                                "original_url": image_url,
                                "minio_path": minio_path,
                                "presigned_url": presigned_url,
                                "title": first_image.get("title", ""),
                                "source": first_image.get("source", "")
                            }
                
                return None
                
        except Exception as e:
            print(f"Error searching image: {e}")
            return None


class ImageGenerationTool:
    """图片生成工具 - 使用图片生成 API"""
    
    def __init__(self):
        self.api_key = settings.NANOBANBAN_API_KEY
        # 这里需要根据实际的 API 端点调整
        self.base_url = "https://api.nanobanban.com/v1/generate"  # 示例端点
    
    async def generate_image(
        self, 
        prompt: str, 
        reference_image_url: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        生成图片
        
        Args:
            prompt: 生成提示词
            reference_image_url: 参考图片 URL（可选）
            
        Returns:
            包含生成图片信息的字典，失败返回 None
        """
        try:
            # 根据实际 API 调整请求格式
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "prompt": prompt,
                "model": "stable-diffusion",  # 示例模型
            }
            
            if reference_image_url:
                payload["reference_image"] = reference_image_url
            
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    self.base_url,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                
                data = response.json()
                
                # 根据实际 API 响应格式调整
                generated_image_url = data.get("image_url") or data.get("url")
                
                if generated_image_url:
                    # 下载并上传到 MinIO
                    minio_path = await minio_client.upload_image_from_url(
                        generated_image_url,
                        prefix="generated-images"
                    )
                    
                    if minio_path:
                        # 获取预签名 URL
                        presigned_url = minio_client.get_image_url(minio_path)
                        
                        return {
                            "success": True,
                            "minio_path": minio_path,
                            "presigned_url": presigned_url,
                            "prompt": prompt
                        }
                
                return None
                
        except Exception as e:
            print(f"Error generating image: {e}")
            return None
    
    async def generate_image_simple(
        self,
        prompt: str,
        reference_image_url: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        简化的图片生成方法 - 如果没有实际 API，可以返回模拟数据
        
        实际项目中应该替换为真实的图片生成 API 调用
        """
        # 这里可以使用其他图片生成服务，比如：
        # - DALL-E (OpenAI)
        # - Stable Diffusion API
        # - Midjourney API
        # 或者其他类似服务
        
        print(f"Generating image with prompt: {prompt}")
        print(f"Reference image: {reference_image_url}")
        
        # 返回模拟数据（实际使用时应该调用真实 API）
        return {
            "success": True,
            "minio_path": "generated-images/placeholder.jpg",
            "presigned_url": "https://placeholder.com/generated-image.jpg",
            "prompt": prompt,
            "message": "Image generation placeholder - replace with actual API call"
        }


# 全局实例
image_search_tool = ImageSearchTool()
image_generation_tool = ImageGenerationTool()


