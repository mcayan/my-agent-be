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
    """图片生成工具 - 使用豆包图片生成 API"""
    
    def __init__(self):
        self.api_key = settings.DOUBAO_API_KEY
        self.base_url = "https://ark.cn-beijing.volces.com/api/v3/images/generations"
        
        if not self.api_key:
            print("⚠️  Warning: DOUBAO_API_KEY not configured, image generation will use mock mode")
    
    async def generate_image(
        self, 
        prompt: str, 
        reference_image_url: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        使用豆包 API 生成图片
        
        Args:
            prompt: 生成提示词（建议使用中文或英文）
            reference_image_url: 参考图片 URL（豆包 API 暂不支持）
            
        Returns:
            包含生成图片信息的字典，失败返回 None
        """
        if not self.api_key:
            print("⚠️  DOUBAO_API_KEY not configured, using mock mode")
            return await self.generate_image_simple(prompt, reference_image_url)
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "doubao-seedream-4-0-250828",
                "prompt": prompt,
                "sequential_image_generation": "disabled",
                "response_format": "url",
                "size": "2K",
                "stream": False,
                "watermark": True
            }
            
            print(f"🎨 正在调用豆包 API 生成图片...")
            
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    self.base_url,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                
                data = response.json()
                print(f"✅ 豆包 API 响应成功")
                
                # 豆包 API 响应格式：{"data": [{"url": "..."}]}
                if data.get("data") and len(data["data"]) > 0:
                    generated_image_url = data["data"][0].get("url")
                    
                    if generated_image_url:
                        print(f"📥 正在下载生成的图片...")
                        # 下载并上传到 MinIO
                        minio_path = await minio_client.upload_image_from_url(
                            generated_image_url,
                            prefix="generated-images"
                        )
                        
                        if minio_path:
                            # 获取预签名 URL
                            presigned_url = minio_client.get_image_url(minio_path)
                            
                            print(f"✅ 图片已保存到 MinIO: {minio_path}")
                            
                            return {
                                "success": True,
                                "minio_path": minio_path,
                                "presigned_url": presigned_url,
                                "prompt": prompt,
                                "original_url": generated_image_url
                            }
                        else:
                            # MinIO 上传失败，但至少返回原始 URL
                            return {
                                "success": True,
                                "minio_path": None,
                                "presigned_url": generated_image_url,  # 使用原始 URL
                                "prompt": prompt,
                                "original_url": generated_image_url
                            }
                
                print(f"⚠️  豆包 API 响应格式异常: {data}")
                return None
                
        except httpx.HTTPStatusError as e:
            print(f"❌ 豆包 API HTTP 错误: {e.response.status_code}")
            print(f"   响应内容: {e.response.text}")
            return None
        except httpx.TimeoutException:
            print(f"❌ 豆包 API 请求超时（120秒）")
            return None
        except Exception as e:
            print(f"❌ 调用豆包 API 失败: {type(e).__name__}: {str(e)}")
            return None
    
    async def generate_image_simple(
        self,
        prompt: str,
        reference_image_url: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        模拟模式 - 当没有配置 API Key 时使用
        
        返回模拟数据和提示词，提示用户配置豆包 API
        """
        print(f"⚠️  模拟模式：生成提示词 - {prompt[:100]}...")
        
        # 返回模拟响应
        return {
            "success": False,  # 标记为未成功
            "minio_path": None,
            "presigned_url": None,
            "prompt": prompt,
            "message": "请配置 DOUBAO_API_KEY 以启用真实的图片生成功能"
        }


# 全局实例
image_search_tool = ImageSearchTool()
image_generation_tool = ImageGenerationTool()


