import re
import httpx
from typing import Optional, Dict, Any, List, Tuple
from urllib.parse import urlparse


class FeishuService:
    """飞书文档服务类，用于获取飞书文档内容"""
    
    def __init__(self, app_id: str, app_secret: str):
        """初始化飞书服务
        
        Args:
            app_id: 飞书应用ID
            app_secret: 飞书应用密钥
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self.access_token = None
        self.base_url = "https://open.feishu.cn/open-apis"

        """获取访问令牌"""
    async def get_access_token(self) -> str:
        if self.access_token:
            return self.access_token
            
        url = f"{self.base_url}/auth/v3/tenant_access_token/internal"
        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            if data.get("code") == 0:
                self.access_token = data["tenant_access_token"]
                return self.access_token
            else:
                raise Exception(f"获取访问令牌失败: {data.get('msg')}")
    
    def parse_feishu_url(self, url: str) -> Dict[str, Any]:
        """解析飞书文档URL，提取文档ID和类型
        """
        # 新版文档URL模式: https://sample.feishu.cn/docx/UXEAd6cRUoj5pexJZr0cdwaFnpd
        # 旧版文档URL模式: https://sample.feishu.cn/doc/doccnxxxxxx
        
        # 提取document_id或doc_token
        if "/docx/" in url:
            # 新版文档
            match = re.search(r'/docx/([^/?]+)', url)
            if match:
                document_id = match.group(1)
                # 去除可能的等号
                document_id = document_id.strip('=')
                return {
                    "type": "docx",
                    "id": document_id
                }
        elif "/doc/" in url:
            # 旧版文档
            match = re.search(r'/doc/([^/?]+)', url)
            if match:
                doc_token = match.group(1)
                return {
                    "type": "doc",
                    "id": doc_token
                }
        
        raise ValueError("无法解析飞书文档URL，请确保URL格式正确")
    
    async def get_document_content(self, url: str) -> str:
        """获取飞书文档纯文本内容"""
        # 解析URL获取文档信息
        doc_info = self.parse_feishu_url(url)
        doc_type = doc_info["type"]
        doc_id = doc_info["id"]
        
        # 获取访问令牌
        access_token = await self.get_access_token()
        
        # 根据文档类型选择对应的API
        if doc_type == "docx":
            # 新版文档API
            api_url = f"{self.base_url}/docx/v1/documents/{doc_id}/raw_content"
        else:
            # 旧版文档API
            api_url = f"{self.base_url}/doc/v2/{doc_id}/raw_content"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(api_url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            if data.get("code") == 0:
                return data.get("data", {}).get("content", "")
            else:
                raise Exception(f"获取文档内容失败: {data.get('msg')}")
    
    async def get_document_multimodal_content(self, url: str) -> Tuple[str, List[str]]:
        """获取飞书文档的多模态内容（文本+图片）
        
        Returns:
            Tuple[str, List[str]]: (文本内容, 图片文件路径列表)
        """
        # 解析URL获取文档信息
        doc_info = self.parse_feishu_url(url)
        doc_type = doc_info["type"]
        doc_id = doc_info["id"]
        
        # 获取访问令牌
        access_token = await self.get_access_token()
        
        # 先获取文本内容
        text_content = await self.get_document_content(url)
        
        # 获取文档结构化内容以提取图片
        images = []
        try:
            if doc_type == "docx":
                # 新版文档API - 获取文档块内容
                blocks_url = f"{self.base_url}/docx/v1/documents/{doc_id}/blocks"
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                }
                
                async with httpx.AsyncClient() as client:
                    response = await client.get(blocks_url, headers=headers)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("code") == 0:
                            blocks = data.get("data", {}).get("items", [])
                            
                            # 遍历文档块，查找图片
                            for block in blocks:
                                if block.get("block_type") == 23:  # 图片块类型
                                    image_info = block.get("image", {})
                                    image_token = image_info.get("token")
                                    
                                    if image_token:
                                        # 下载图片并保存到文件系统
                                        image_path = await self._download_and_save_image(access_token, doc_id, image_token)
                                        if image_path:
                                            images.append(image_path)
                                
                                # 递归处理子块（如果存在）
                                children = block.get("children", [])
                                if children:
                                    await self._extract_images_from_blocks(children, access_token, doc_id, images)
            # 注意：旧版文档(doc)的图片获取较为复杂，这里暂时只处理新版文档
            
        except Exception as e:
            # 如果获取图片失败，只返回文本内容
            print(f"获取文档图片失败: {e}")
        
        return text_content, images
    
    async def _extract_images_from_blocks(self, blocks: List[Dict], access_token: str, doc_id: str, images: List[str]) -> None:
        """递归提取文档块中的图片
        
        Args:
            blocks: 文档块列表
            access_token: 访问令牌
            doc_id: 文档ID
            images: 图片文件路径列表（用于收集结果）
        """
        for block in blocks:
            if block.get("block_type") == 23:  # 图片块类型
                image_info = block.get("image", {})
                image_token = image_info.get("token")
                
                if image_token:
                    # 下载图片并保存到文件系统
                    image_path = await self._download_and_save_image(access_token, doc_id, image_token)
                    if image_path:
                        images.append(image_path)
            
            # 递归处理子块
            children = block.get("children", [])
            if children:
                await self._extract_images_from_blocks(children, access_token, doc_id, images)
    
    async def _download_and_save_image(self, access_token: str, doc_id: str, image_token: str) -> Optional[str]:
        """下载文档中的图片并保存到文件系统
        
        Args:
            access_token: 访问令牌
            doc_id: 文档ID
            image_token: 图片token
            
        Returns:
            Optional[str]: 图片文件路径
        """
        try:
            # 下载图片字节数据
            image_data = await self._download_image(access_token, doc_id, image_token)
            if not image_data:
                return None
            
            # 生成唯一的文件名
            import uuid
            import os
            image_id = str(uuid.uuid4())
            image_path = f"uploads/feishu_{image_id}.png"  # 默认使用png格式
            
            # 确保uploads目录存在
            os.makedirs("uploads", exist_ok=True)
            
            # 保存图片到文件系统
            with open(image_path, "wb") as f:
                f.write(image_data)
            
            print(f"成功保存飞书图片到: {image_path}")
            return image_path
            
        except Exception as e:
            print(f"保存图片失败: {e}")
            return None
    
    async def _download_image(self, access_token: str, doc_id: str, image_token: str) -> Optional[bytes]:
        """下载文档中的图片
        
        Args:
            access_token: 访问令牌
            doc_id: 文档ID
            image_token: 图片token
            
        Returns:
            Optional[bytes]: 图片字节数据
        """
        try:
            # 飞书API获取图片下载链接
            image_url = f"{self.base_url}/drive/v1/medias/{image_token}/download"
            headers = {
                "Authorization": f"Bearer {access_token}"
            }
            
            async with httpx.AsyncClient() as client:
                # 下载图片
                response = await client.get(image_url, headers=headers)
                if response.status_code == 200:
                    return response.content
            
            return None
        except Exception as e:
            print(f"下载图片失败: {e}")
            return None
    
    async def validate_document_access(self, url: str) -> bool:
        """验证是否有文档访问权限
        """
        try:
            content = await self.get_document_content(url)
            return len(content.strip()) > 0
        except Exception:
            return False