from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from dotenv import load_dotenv

from routers import test_cases
from services.ai_service import AIService

# 加载环境变量
load_dotenv()

# 如果上传目录不存在，则创建
os.makedirs("uploads", exist_ok=True)
os.makedirs("results", exist_ok=True)

# 创建AI服务实例
feishu_app_id = os.getenv("FEISHU_APP_ID")
feishu_app_secret = os.getenv("FEISHU_APP_SECRET")
ai_service = AIService(feishu_app_id=feishu_app_id, feishu_app_secret=feishu_app_secret)

app = FastAPI(
    title="Test Case Generator",
    description="Generate test cases from flowcharts, mind maps, and UI screenshots",
    version="1.0.0"
)

# 配置跨域资源共享(CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中，应替换为特定的来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含路由
app.include_router(test_cases.router)

# 将ai_service实例设置为应用状态，供路由使用
app.state.ai_service = ai_service

@app.get("/")
async def root():
    return {"message": "Welcome to Test Case Generator API"}

@app.get("/api/ping")
async def ping():
    return {"status": "success", "message": "pong"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
