from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import StreamingResponse, FileResponse
from typing import List, Optional, Dict, Any, Union
import os
import json
import uuid
from datetime import datetime
import asyncio

from models.test_case import TestCase, TestCaseRequest, TestCaseResponse, MindMapRequest
from services.excel_service import excel_service

router = APIRouter(
    prefix="/api/test-cases",
    tags=["test-cases"],
    responses={404: {"description": "Not found"}},
)

# 如果上传目录不存在，则创建
os.makedirs("uploads", exist_ok=True)

@router.post("/generate")
async def generate_test_cases(
    request: Request,
    prd_text: str = Form(None),
    images: List[UploadFile] = File(default=[]),
    feishu_url: str = Form(None),
    context: str = Form(...),
    requirements: str = Form(...)
):
    ai_service = request.app.state.ai_service
    image_paths = []
    if feishu_url:
        # 飞书文档模式
        return StreamingResponse(
            ai_service.generate_test_points_stream(
                feishu_url=feishu_url,
                context=context,
                requirements=requirements
            ),
            media_type="text/plain; charset=utf-8"
        )
    else:
        try:
            for image in images:
                if image.filename:
                    file_extension = os.path.splitext(image.filename)[1]
                    unique_filename = f"{uuid.uuid4()}{file_extension}"
                    file_path = os.path.join("uploads", unique_filename)
                    with open(file_path, "wb") as buffer:
                        content = await image.read()
                        buffer.write(content)
                    image_paths.append(file_path)
            return StreamingResponse(
                ai_service.generate_test_points_stream(
                    prd_text=prd_text,
                    prd_images=image_paths,
                    context=context,
                    requirements=requirements
                ),
                media_type="text/plain; charset=utf-8"
            )
        except Exception as e:
            for path in image_paths:
                if os.path.exists(path):
                    os.remove(path)
            raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@router.post("/export")
async def export_test_cases(test_cases: List[Union[TestCase, Dict[str, Any]]]):
    try:
        # 生成Excel文件
        excel_path = excel_service.generate_excel(test_cases)

        # 返回文件供下载
        return FileResponse(
            path=excel_path,
            filename=os.path.basename(excel_path),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting test cases: {str(e)}")

@router.post("/generate-mindmap")
async def generate_mindmap_from_test_cases(
    request: Request,
    mindmap_request: MindMapRequest
):
    """
    从测试用例生成思维导图数据
    
    参数:
        mindmap_request: 包含测试用例列表的请求体
    
    返回:
        思维导图的JSON数据
    """
    try:
        ai_service = request.app.state.ai_service
        mindmap_data = ai_service.generate_mindmap_from_test_cases(mindmap_request.test_cases)
        return {"mindmap": mindmap_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成思维导图失败: {str(e)}")

@router.get("/download/{filename}")
async def download_excel(filename: str):
    file_path = f"results/{filename}"

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
