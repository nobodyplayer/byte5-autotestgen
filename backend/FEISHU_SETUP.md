# 飞书文档集成配置指南

本指南将帮助您配置飞书文档集成功能，实现从飞书文档URL直接获取内容并生成测试用例。

## 🚀 快速开始

### 1. 获取飞书应用凭证

#### 步骤 1: 创建飞书应用
1. 访问 [飞书开放平台](https://open.feishu.cn/)
2. 登录您的飞书账号
3. 点击「创建应用」→「企业自建应用」
4. 填写应用基本信息（应用名称、描述等）

#### 步骤 2: 获取应用凭证
1. 在应用详情页面，找到「凭证与基础信息」
2. 复制 `App ID` 和 `App Secret`

#### 步骤 3: 配置应用权限
1. 在应用管理页面，点击「权限管理」
2. 添加以下权限：
   - `docs:doc:readonly` - 查看新版文档
   - `wiki:wiki:readonly` - 查看知识库
   - `drive:drive:readonly` - 查看云空间中所有文件

#### 步骤 4: 发布应用
1. 完成权限配置后，点击「创建版本」
2. 提交审核并发布应用

### 2. 配置环境变量

在 `backend/.env` 文件中添加飞书配置：

```env
# 飞书开放平台配置
FEISHU_APP_ID=cli_your_app_id_here
FEISHU_APP_SECRET=your_app_secret_here
```

### 3. 测试配置

运行测试脚本验证配置：

```bash
cd backend
python demo_feishu_integration.py
```

## 📖 使用方法

### API 调用

```bash
curl -X POST "http://localhost:8000/api/test-cases/generate" \
  -H "Content-Type: multipart/form-data" \
  -F "context=移动应用用户注册功能" \
  -F "requirements=需要测试用户注册的各种场景" \
  -F "input_type=feishu" \
  -F "feishu_url=https://bytedance.feishu.cn/docx/your_document_token"
```

### 前端界面

1. 启动后端服务：`python main.py`
2. 启动前端服务：`npm start`
3. 在界面中选择「飞书文档」输入类型
4. 粘贴飞书文档URL
5. 填写上下文和需求信息
6. 点击生成测试用例

## 🔧 支持的文档类型

- **新版文档 (Docs)**: `https://bytedance.feishu.cn/docx/xxx`
- **旧版文档**: `https://feishu.cn/docs/xxx`
- **知识库 (Wiki)**: `https://bytedance.feishu.cn/wiki/xxx`

## ⚠️ 注意事项

1. **文档权限**: 确保飞书应用有权限访问目标文档
2. **文档类型**: 目前支持纯文本内容，不支持图片、表格等复杂元素
3. **访问限制**: 只能访问应用安装范围内的文档
4. **API限制**: 遵守飞书API的调用频率限制

## 🐛 常见问题

### Q: 获取文档内容失败
A: 检查以下几点：
- 飞书应用是否有正确的权限
- 文档URL是否正确
- 应用是否已发布并安装
- 网络连接是否正常

### Q: 访问令牌获取失败
A: 检查：
- App ID 和 App Secret 是否正确
- 网络是否能访问飞书API
- 应用状态是否正常

### Q: 文档解析为空
A: 可能原因：
- 文档内容为空
- 文档包含不支持的内容类型
- 权限不足

## 📚 相关文档

- [飞书开放平台文档](https://open.feishu.cn/document/)
- [文档API参考](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN)
- [权限配置指南](https://open.feishu.cn/document/ukTMukTMukTM/uQjN3QjL0YzN04CN2cDN)

## 🎯 下一步

配置完成后，您可以：
1. 测试基本的文档获取功能
2. 集成到您的工作流程中
3. 根据需要调整prompt模板
4. 扩展支持更多文档类型