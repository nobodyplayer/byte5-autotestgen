#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书集成功能验证脚本
用于验证飞书应用配置是否正确，以及基本功能是否正常
"""

import os
import asyncio
from dotenv import load_dotenv
from services.feishu_service import FeishuService
from services.ai_service import AIService

# 加载环境变量
load_dotenv()

async def test_feishu_config():
    """测试飞书配置"""
    print("=" * 50)
    print("飞书集成功能验证")
    print("=" * 50)
    
    # 检查环境变量
    feishu_app_id = os.getenv('FEISHU_APP_ID')
    feishu_app_secret = os.getenv('FEISHU_APP_SECRET')
    
    print("\n1. 检查环境变量配置...")
    if not feishu_app_id:
        print("❌ FEISHU_APP_ID 未配置")
        return False
    if not feishu_app_secret:
        print("❌ FEISHU_APP_SECRET 未配置")
        return False
    
    print(f"✅ FEISHU_APP_ID: {feishu_app_id[:8]}...")
    print(f"✅ FEISHU_APP_SECRET: {feishu_app_secret[:8]}...")
    
    # 初始化飞书服务
    print("\n2. 初始化飞书服务...")
    try:
        feishu_service = FeishuService(feishu_app_id, feishu_app_secret)
        print("✅ 飞书服务初始化成功")
    except Exception as e:
        print(f"❌ 飞书服务初始化失败: {e}")
        return False
    
    # 测试获取访问令牌
    print("\n3. 测试获取访问令牌...")
    try:
        token = await feishu_service.get_access_token()
        if token:
            print(f"✅ 访问令牌获取成功: {token[:20]}...")
        else:
            print("❌ 访问令牌获取失败")
            return False
    except Exception as e:
        print(f"❌ 访问令牌获取异常: {e}")
        return False
    
    # 测试URL解析
    print("\n4. 测试URL解析功能...")
    test_urls = [
        "https://example.feishu.cn/docx/abc123",
        "https://example.feishu.cn/docs/def456",
        "https://example.feishu.cn/sheets/ghi789"
    ]
    
    for url in test_urls:
        try:
            doc_type, doc_token = feishu_service.parse_feishu_url(url)
            print(f"✅ URL解析成功: {url} -> 类型: {doc_type}, Token: {doc_token}")
        except Exception as e:
            print(f"❌ URL解析失败: {url} -> {e}")
    
    print("\n5. 测试完整的AI服务集成...")
    try:
        ai_service = AIService(
            feishu_app_id=feishu_app_id,
            feishu_app_secret=feishu_app_secret
        )
        print("✅ AI服务初始化成功")
    except Exception as e:
        print(f"❌ AI服务初始化失败: {e}")
        return False
    
    print("\n=" * 50)
    print("✅ 所有基础功能验证通过！")
    print("=" * 50)
    
    return True

async def test_document_access():
    """测试文档访问功能（需要真实的飞书文档URL）"""
    print("\n" + "=" * 50)
    print("文档访问测试（可选）")
    print("=" * 50)
    
    # 提示用户输入真实的飞书文档URL进行测试
    print("\n如果您有可访问的飞书文档，可以输入URL进行测试：")
    print("（直接按回车跳过此测试）")
    
    doc_url = input("请输入飞书文档URL: ").strip()
    
    if not doc_url:
        print("跳过文档访问测试")
        return
    
    try:
        # 初始化AI服务
        feishu_app_id = os.getenv('FEISHU_APP_ID')
        feishu_app_secret = os.getenv('FEISHU_APP_SECRET')
        ai_service = AIService(
            feishu_app_id=feishu_app_id,
            feishu_app_secret=feishu_app_secret
        )
        
        print(f"\n正在获取文档内容: {doc_url}")
        
        # 获取文档内容
        content = await ai_service.feishu_service.get_document_content(doc_url)
        
        if content:
            print(f"✅ 文档内容获取成功，长度: {len(content)} 字符")
            print(f"内容预览: {content[:200]}...")
        else:
            print("❌ 文档内容为空")
            
    except Exception as e:
        print(f"❌ 文档访问失败: {e}")
        print("\n可能的原因:")
        print("1. 文档URL格式不正确")
        print("2. 应用没有访问该文档的权限")
        print("3. 文档不存在或已被删除")
        print("4. 网络连接问题")

def print_usage_guide():
    """打印使用指南"""
    print("\n" + "=" * 50)
    print("使用指南")
    print("=" * 50)
    
    print("\n1. 确保已正确配置 .env 文件:")
    print("   FEISHU_APP_ID=your_app_id")
    print("   FEISHU_APP_SECRET=your_app_secret")
    
    print("\n2. 确保飞书应用已开通以下权限:")
    print("   - 获取与更新文档内容 (docx:read)")
    print("   - 查看文档 (docs:read)")
    print("   - 查看电子表格 (sheets:read)")
    
    print("\n3. API调用示例:")
    print("   POST /api/test-cases/generate")
    print("   {")
    print('     "input_type": "feishu",')
    print('     "feishu_url": "https://your-domain.feishu.cn/docx/your-doc-token"')
    print("   }")
    
    print("\n4. 支持的文档类型:")
    print("   - 新版文档 (docx)")
    print("   - 旧版文档 (docs)")
    print("   - 电子表格 (sheets)")
    
    print("\n5. 如遇问题，请检查:")
    print("   - 网络连接")
    print("   - 应用权限配置")
    print("   - 文档访问权限")
    print("   - 环境变量配置")

async def main():
    """主函数"""
    try:
        # 基础配置验证
        success = await test_feishu_config()
        
        if success:
            # 可选的文档访问测试
            await test_document_access()
        
        # 打印使用指南
        print_usage_guide()
        
    except KeyboardInterrupt:
        print("\n用户中断测试")
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())