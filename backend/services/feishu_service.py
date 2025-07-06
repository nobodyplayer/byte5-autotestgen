import re
import httpx
from typing import Optional, Dict, Any, List, Tuple
from urllib.parse import urlparse


class FeishuService:
    """飞书文档服务类，用于获取飞书文档内容"""
    def __init__(self, app_id: str, app_secret: str):

        self.app_id = app_id
        self.app_secret = app_secret
        self.access_token = None
        self.base_url = "https://open.feishu.cn/open-apis"

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
                # 新版文档API - 获取文档所有块
                blocks_url = f"{self.base_url}/docx/v1/documents/{doc_id}/blocks"
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                }
                
                # 分页获取所有块
                page_token = None
                while True:
                    params = {"page_size": 500}
                    if page_token:
                        params["page_token"] = page_token
                    
                    async with httpx.AsyncClient() as client:
                        response = await client.get(blocks_url, headers=headers, params=params)
                        if response.status_code == 200:
                            data = response.json()
                            if data.get("code") == 0:
                                blocks = data.get("data", {}).get("items", [])
                                
                                # 遍历文档块，查找图片和文件
                                for block in blocks:
                                    block_type = block.get("block_type")
                                    
                                    # 处理图片块 (block_type = 27)
                                    if block_type == 27:
                                        image_info = block.get("image", {})
                                        image_token = image_info.get("token")
                                        
                                        if image_token:
                                            # 下载图片并保存到文件系统
                                            image_path = await self._download_and_save_image(access_token, image_token)
                                            if image_path:
                                                images.append(image_path)
                                    
                                    # 处理文件块 (block_type = 23) - 可能包含图片文件
                                    elif block_type == 23:
                                        file_info = block.get("file", {})
                                        file_token = file_info.get("token")
                                        file_name = file_info.get("name", "")
                                        
                                        # 检查是否为图片文件
                                        if file_token and self._is_image_file(file_name):
                                            # 下载图片文件并保存到文件系统
                                            image_path = await self._download_and_save_file_as_image(access_token, file_token, file_name)
                                            if image_path:
                                                images.append(image_path)
                                
                                # 检查是否还有更多页
                                if not data.get("data", {}).get("has_more", False):
                                    break
                                page_token = data.get("data", {}).get("page_token")
                            else:
                                print(f"获取文档块失败: {data.get('msg')}")
                                break
                        else:
                            print(f"请求文档块失败: {response.status_code}")
                            break
            
            # 注意：旧版文档(doc)的图片获取较为复杂，这里暂时只处理新版文档
            
        except Exception as e:
            # 如果获取图片失败，只返回文本内容
            print(f"获取文档图片失败: {e}")
        
        return text_content, images
    
    def _is_image_file(self, filename: str) -> bool:
        """检查文件是否为图片文件
        """
        if not filename:
            return False
        
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'}
        file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
        return f'.{file_ext}' in image_extensions
    
    async def _download_and_save_image(self, access_token: str, image_token: str) -> Optional[str]:
        """下载文档中的图片并保存到文件系统
        
        Args:
            access_token: 访问令牌
            image_token: 图片token
            
        Returns:
            Optional[str]: 图片文件路径
        """
        try:
            # 下载图片字节数据
            image_data = await self._download_media(access_token, image_token)
            if not image_data:
                return None
            
            # 生成唯一的文件名
            import uuid
            import os
            image_id = str(uuid.uuid4())
            image_path = f"uploads/feishu_image_{image_id}.png"  # 默认使用png格式
            
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
    
    async def _download_and_save_file_as_image(self, access_token: str, file_token: str, filename: str) -> Optional[str]:
        """下载文档中的文件（图片）并保存到文件系统
        
        Args:
            access_token: 访问令牌
            file_token: 文件token
            filename: 原始文件名
            
        Returns:
            Optional[str]: 图片文件路径
        """
        try:
            # 下载文件字节数据
            file_data = await self._download_media(access_token, file_token)
            if not file_data:
                return None
            
            # 生成唯一的文件名，保留原始扩展名
            import uuid
            import os
            image_id = str(uuid.uuid4())
            file_ext = filename.split('.')[-1] if '.' in filename else 'png'
            image_path = f"uploads/feishu_file_{image_id}.{file_ext}"
            
            # 确保uploads目录存在
            os.makedirs("uploads", exist_ok=True)
            
            # 保存文件到文件系统
            with open(image_path, "wb") as f:
                f.write(file_data)
            
            print(f"成功保存飞书文件图片到: {image_path}")
            return image_path
            
        except Exception as e:
            print(f"保存文件图片失败: {e}")
            return None
    
    async def _download_media(self, access_token: str, media_token: str) -> Optional[bytes]:
        """下载文档中的媒体文件（图片或文件）
        
        Args:
            access_token: 访问令牌
            media_token: 媒体token（图片token或文件token）
            
        Returns:
            Optional[bytes]: 媒体文件字节数据
        """
        try:
            # 飞书API下载素材接口
            media_url = f"{self.base_url}/drive/v1/medias/{media_token}/download"
            headers = {
                "Authorization": f"Bearer {access_token}"
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                # 下载媒体文件
                response = await client.get(media_url, headers=headers)
                if response.status_code == 200:
                    return response.content
                else:
                    print(f"下载媒体文件失败，状态码: {response.status_code}")
            
            return None
        except Exception as e:
            print(f"下载媒体文件失败: {e}")
            return None
    
    async def validate_document_access(self, url: str) -> bool:
        """验证是否有文档访问权限
        """
        try:
            content = await self.get_document_content(url)
            return len(content.strip()) > 0
        except Exception:
            return False