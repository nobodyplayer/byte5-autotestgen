#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建测试文档脚本
帮助用户创建包含PRD内容的飞书文档进行测试
我的链接：https://ccnau24t1m2v.feishu.cn/docx/QpjcdhQWmo09YzxNJKhcJtvEnsg?from=from_copylink
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def get_sample_prd_content():
    """获取示例PRD内容"""
    return """
# 用户登录功能产品需求文档 (PRD)

## 1. 功能概述
用户登录功能是系统的核心功能之一，允许用户通过用户名和密码安全地访问系统。

## 2. 功能需求

### 2.1 基本登录流程
- 用户在登录页面输入用户名和密码
- 系统验证用户凭证的有效性
- 验证成功后跳转到用户主页面
- 验证失败显示相应的错误提示信息

### 2.2 输入验证
- 用户名：必填，长度3-20个字符，支持字母、数字、下划线
- 密码：必填，长度6-20个字符，至少包含字母和数字
- 输入框失去焦点时进行实时验证

### 2.3 安全要求
- 密码输入框显示为掩码形式
- 连续登录失败3次后账户锁定30分钟
- 支持图形验证码防止暴力破解
- 登录成功后生成安全的会话令牌

### 2.4 用户体验
- 支持"记住我"功能，下次访问自动填充用户名
- 提供"忘记密码"链接，支持密码重置
- 登录按钮在输入完成前保持禁用状态
- 登录过程中显示加载状态

## 3. 异常处理

### 3.1 输入异常
- 用户名为空：提示"请输入用户名"
- 密码为空：提示"请输入密码"
- 用户名格式错误：提示"用户名格式不正确"
- 密码格式错误：提示"密码格式不正确"

### 3.2 业务异常
- 用户名不存在：提示"用户名或密码错误"
- 密码错误：提示"用户名或密码错误"
- 账户被锁定：提示"账户已被锁定，请30分钟后重试"
- 验证码错误：提示"验证码错误，请重新输入"

### 3.3 系统异常
- 网络连接失败：提示"网络连接失败，请检查网络设置"
- 服务器错误：提示"系统繁忙，请稍后重试"
- 会话超时：提示"登录已过期，请重新登录"

## 4. 界面设计要求

### 4.1 布局要求
- 登录表单居中显示
- 响应式设计，支持移动端和桌面端
- 品牌Logo显示在表单上方
- 简洁清晰的视觉设计

### 4.2 交互要求
- 支持Tab键切换输入框
- 支持Enter键提交表单
- 错误提示以红色文字显示在对应输入框下方
- 成功状态以绿色提示显示

## 5. 性能要求
- 登录请求响应时间不超过2秒
- 页面加载时间不超过3秒
- 支持并发用户数不少于1000

## 6. 兼容性要求
- 支持主流浏览器：Chrome、Firefox、Safari、Edge
- 支持移动端浏览器
- 兼容iOS和Android系统

## 7. 测试要点
- 正常登录流程测试
- 各种异常情况的错误处理测试
- 安全性测试（SQL注入、XSS等）
- 性能压力测试
- 兼容性测试
- 用户体验测试
"""

def get_ecommerce_prd_content():
    """获取电商购物车PRD内容"""
    return """
# 电商购物车功能产品需求文档 (PRD)

## 1. 功能概述
购物车是电商平台的核心功能，允许用户临时存储商品，进行数量调整，并最终完成购买。

## 2. 功能需求

### 2.1 添加商品到购物车
- 用户在商品详情页点击"加入购物车"按钮
- 支持选择商品规格（颜色、尺寸等）
- 支持设置购买数量
- 添加成功后显示确认提示
- 购物车图标显示商品数量徽章

### 2.2 购物车页面展示
- 显示所有已添加的商品列表
- 每个商品显示：图片、名称、规格、单价、数量、小计
- 显示商品总数量和总金额
- 支持全选/取消全选功能
- 支持批量删除选中商品

### 2.3 数量调整
- 支持通过+/-按钮调整数量
- 支持直接输入数量
- 数量不能小于1
- 数量不能超过库存限制
- 数量变更后实时更新小计和总计

### 2.4 商品管理
- 支持单个商品删除
- 支持批量删除
- 支持移入收藏夹
- 显示商品库存状态
- 缺货商品置灰显示

## 3. 业务规则

### 3.1 库存检查
- 添加商品时检查库存是否充足
- 数量调整时验证库存限制
- 库存不足时显示相应提示
- 缺货商品不能加入购物车

### 3.2 价格计算
- 实时计算商品小计（单价 × 数量）
- 实时计算购物车总金额
- 支持优惠券折扣计算
- 支持会员价格显示

### 3.3 数据持久化
- 登录用户的购物车数据保存到服务器
- 未登录用户的购物车数据保存到本地存储
- 登录后合并本地和服务器购物车数据

## 4. 异常处理

### 4.1 商品异常
- 商品已下架：提示"商品已下架"并自动移除
- 库存不足：提示"库存不足，已调整为最大可购买数量"
- 价格变动：提示"商品价格已更新"

### 4.2 操作异常
- 网络异常：提示"网络连接失败，请重试"
- 服务器异常：提示"系统繁忙，请稍后重试"
- 数据同步失败：提示"数据同步失败，请刷新页面"

## 5. 界面设计要求

### 5.1 布局设计
- 清晰的商品列表布局
- 明显的操作按钮
- 突出显示总金额
- 响应式设计适配移动端

### 5.2 交互设计
- 数量调整有动画效果
- 删除操作需要确认
- 加载状态有进度提示
- 操作反馈及时明确

## 6. 性能要求
- 购物车页面加载时间不超过2秒
- 数量调整响应时间不超过500ms
- 支持购物车商品数量不少于100个
- 数据同步延迟不超过1秒

## 7. 测试要点
- 添加商品到购物车的各种场景
- 数量调整的边界值测试
- 库存不足的处理测试
- 商品删除和批量操作测试
- 价格计算准确性测试
- 数据持久化和同步测试
- 异常情况的错误处理测试
- 性能和并发测试
"""

def print_document_creation_guide():
    """打印文档创建指南"""
    print("📋 飞书文档创建指南")
    print("=" * 50)
    
    print("\n🎯 目标：创建包含PRD内容的飞书文档用于测试")
    
    print("\n📝 步骤1：创建飞书文档")
    print("1. 打开飞书客户端或网页版")
    print("2. 点击'新建' -> '文档'")
    print("3. 选择'新版文档'（推荐）或'旧版文档'")
    print("4. 为文档命名，如：'测试PRD文档'")
    
    print("\n📄 步骤2：添加PRD内容")
    print("选择以下示例内容之一复制到文档中：")
    print("\n选项A：用户登录功能PRD")
    print("-" * 30)
    print(get_sample_prd_content()[:200] + "...")
    
    print("\n选项B：电商购物车功能PRD")
    print("-" * 30)
    print(get_ecommerce_prd_content()[:200] + "...")
    
    print("\n🔗 步骤3：获取文档链接")
    print("1. 点击文档右上角的'分享'按钮")
    print("2. 设置权限为'组织内可查看'或'任何人可查看'")
    print("3. 复制分享链接")
    print("4. 链接格式示例：")
    print("   - 新版：https://your-domain.feishu.cn/docx/ABC123DEF456")
    print("   - 旧版：https://your-domain.feishu.cn/doc/doccnXXXXXX")
    
    print("\n🧪 步骤4：测试验证")
    print("使用获取的链接运行以下测试：")
    print("1. 快速验证：python quick_test.py")
    print("2. 完整验证：python verify_feishu.py")
    print("3. API测试：python test_api_demo.py")
    
    print("\n⚠️ 注意事项")
    print("1. 确保文档权限设置正确，应用能够访问")
    print("2. 确保飞书应用已开通文档读取权限")
    print("3. 文档内容建议包含完整的PRD结构")
    print("4. 测试时使用真实的文档链接")
    
    print("\n🔧 权限检查")
    print("如果遇到权限问题，请检查：")
    print("1. 飞书应用权限配置")
    print("2. 文档分享权限设置")
    print("3. 应用是否在正确的组织下")
    print("4. App ID和App Secret是否正确")

def save_sample_content_to_files():
    """保存示例内容到文件"""
    # 保存用户登录PRD
    with open("sample_login_prd.md", "w", encoding="utf-8") as f:
        f.write(get_sample_prd_content())
    
    # 保存电商购物车PRD
    with open("sample_ecommerce_prd.md", "w", encoding="utf-8") as f:
        f.write(get_ecommerce_prd_content())
    
    print("\n📁 示例内容已保存到文件：")
    print("- sample_login_prd.md (用户登录功能PRD)")
    print("- sample_ecommerce_prd.md (电商购物车功能PRD)")
    print("\n您可以直接复制这些文件的内容到飞书文档中")

def main():
    """主函数"""
    print("🚀 飞书文档测试准备工具")
    print("=" * 50)
    
    # 检查环境配置
    feishu_app_id = os.getenv('FEISHU_APP_ID')
    feishu_app_secret = os.getenv('FEISHU_APP_SECRET')
    
    if not feishu_app_id or not feishu_app_secret:
        print("⚠️ 警告：飞书应用配置未找到")
        print("请确保 .env 文件中配置了 FEISHU_APP_ID 和 FEISHU_APP_SECRET")
        print("\n继续显示文档创建指南...\n")
    else:
        print("✅ 飞书应用配置已找到")
        print(f"App ID: {feishu_app_id[:8]}...")
        print("")
    
    # 显示创建指南
    print_document_creation_guide()
    
    # 询问是否保存示例内容
    print("\n" + "=" * 50)
    save_choice = input("是否保存示例PRD内容到本地文件？(y/n): ").strip().lower()
    
    if save_choice in ['y', 'yes', '是']:
        save_sample_content_to_files()
    
    print("\n🎉 准备完成！")
    print("现在您可以：")
    print("1. 按照指南创建飞书文档")
    print("2. 复制示例PRD内容到文档")
    print("3. 获取文档分享链接")
    print("4. 运行验证脚本测试功能")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断操作")
    except Exception as e:
        print(f"\n发生错误: {e}")
        import traceback
        traceback.print_exc()