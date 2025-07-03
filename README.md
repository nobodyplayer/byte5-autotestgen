# 测试用例生成器
一个使用多模态AI模型从流程图、思维导图和UI截图生成测试用例的智能系统。

## 功能

- 上传流程图、思维导图或UI截图
- 提供测试用例生成的上下文和需求
- AI驱动的视觉输入分析
- 自动生成全面的测试用例
- 实时流式生成测试用例
- 将测试用例导出到Excel
- 现代化的Gemini风格界面

## 项目结构

```
├── backend/                # FastAPI后端
│   ├── models/             # 数据模型
│   ├── routers/            # API路由
│   ├── services/           # 业务逻辑
│   ├── utils/              # 工具函数
│   └── main.py             # 应用入口点
│
├── frontend/               # React前端
│   ├── public/             # 静态资源
│   └── src/                # 源代码
│       ├── components/     # UI组件
│       ├── services/       # API服务
│       ├── styles/         # CSS样式
│       ├── App.jsx         # 主应用组件
│       └── index.jsx       # 应用入口点
│
└── README.md               # 项目文档
```

## 开始使用

### 前置条件

- Python 3.8+
- Node.js 14+
- npm 或 yarn

### 后端设置

1. 进入后端目录:
   ```
   cd backend
   ```

2. 创建虚拟环境:
   ```
   python -m venv venv
   ```

3. 激活虚拟环境:
   - Windows系统:
     ```
     venv\Scripts\activate
     ```
   - macOS/Linux系统:
     ```
     source venv/bin/activate
     ```

4. 安装依赖:
   ```
   pip install -r requirements.txt
   ```

5. 运行FastAPI服务器:
   ```
   uvicorn main:app --reload
   ```

### 前端设置

1. 进入前端目录:
   ```
   cd frontend
   ```

2. 安装依赖:
   ```
   npm install
   ```

3. 启动开发服务器:
   ```
   npm start
   ```

4. 打开浏览器并访问 `http://localhost:3000`



