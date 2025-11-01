"""MinIO 客户端服务"""
import io
import uuid
from datetime import timedelta
from typing import Optional

import httpx
from minio import Minio
from minio.error import S3Error

from core.config import settings


class MinIOClient:
    """MinIO 客户端类"""
    
    def __init__(self):
        self.client = None
        self.bucket_name = settings.MINIO_BUCKET
        self._initialized = False
    
    def _initialize(self):
        """延迟初始化 MinIO 客户端"""
        if self._initialized:
            return
        
        try:
            self.client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE
            )
            self._ensure_bucket_exists()
            self._initialized = True
            print(f"✅ MinIO client initialized: {settings.MINIO_ENDPOINT}")
        except Exception as e:
            print(f"⚠️  Warning: MinIO initialization failed: {e}")
            print(f"   MinIO endpoint: {settings.MINIO_ENDPOINT}")
            print(f"   Image storage features will not work until MinIO is available")
    
    def _ensure_bucket_exists(self):
        """确保存储桶存在"""
        if not self.client:
            return
        
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                print(f"✅ Created MinIO bucket: {self.bucket_name}")
        except S3Error as e:
            print(f"⚠️  Error ensuring bucket exists: {e}")
    
    async def upload_image_from_url(self, image_url: str, prefix: str = "images") -> Optional[str]:
        """
        从 URL 下载图片并上传到 MinIO
        
        Args:
            image_url: 图片 URL
            prefix: 存储路径前缀
            
        Returns:
            上传后的文件路径，失败返回 None
        """
        self._initialize()
        
        if not self.client:
            print("⚠️  MinIO client not available, skipping upload")
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(image_url, timeout=30)
                response.raise_for_status()
                
                # 生成唯一文件名
                file_extension = self._get_extension_from_url(image_url)
                filename = f"{prefix}/{uuid.uuid4()}{file_extension}"
                
                # 上传到 MinIO
                image_data = io.BytesIO(response.content)
                self.client.put_object(
                    self.bucket_name,
                    filename,
                    image_data,
                    length=len(response.content),
                    content_type=response.headers.get('content-type', 'image/jpeg')
                )
                
                return filename
        except Exception as e:
            print(f"Error uploading image from URL: {e}")
            return None
    
    async def upload_image_from_bytes(
        self, 
        image_data: bytes, 
        prefix: str = "images",
        extension: str = ".jpg"
    ) -> Optional[str]:
        """
        从字节数据上传图片到 MinIO
        
        Args:
            image_data: 图片字节数据
            prefix: 存储路径前缀
            extension: 文件扩展名
            
        Returns:
            上传后的文件路径，失败返回 None
        """
        self._initialize()
        
        if not self.client:
            print("⚠️  MinIO client not available, skipping upload")
            return None
        
        try:
            filename = f"{prefix}/{uuid.uuid4()}{extension}"
            data_stream = io.BytesIO(image_data)
            
            self.client.put_object(
                self.bucket_name,
                filename,
                data_stream,
                length=len(image_data),
                content_type=self._get_content_type(extension)
            )
            
            return filename
        except Exception as e:
            print(f"Error uploading image from bytes: {e}")
            return None
    
    def get_image_url(self, object_name: str, expires: timedelta = timedelta(hours=1)) -> Optional[str]:
        """
        获取图片的预签名 URL
        
        Args:
            object_name: 对象名称（文件路径）
            expires: URL 过期时间
            
        Returns:
            预签名 URL，失败返回 None
        """
        self._initialize()
        
        if not self.client:
            print("⚠️  MinIO client not available, cannot generate URL")
            return None
        
        try:
            url = self.client.presigned_get_object(
                self.bucket_name,
                object_name,
                expires=expires
            )
            return url
        except Exception as e:
            print(f"Error getting presigned URL: {e}")
            return None
    
    def _get_extension_from_url(self, url: str) -> str:
        """从 URL 获取文件扩展名"""
        if '.jpg' in url or '.jpeg' in url:
            return '.jpg'
        elif '.png' in url:
            return '.png'
        elif '.gif' in url:
            return '.gif'
        elif '.webp' in url:
            return '.webp'
        else:
            return '.jpg'
    
    def _get_content_type(self, extension: str) -> str:
        """根据扩展名获取 content type"""
        content_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        return content_types.get(extension.lower(), 'image/jpeg')


# 全局单例
minio_client = MinIOClient()


