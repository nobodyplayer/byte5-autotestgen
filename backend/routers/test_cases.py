from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import StreamingResponse, FileResponse
from typing import List, Optional, Dict, Any, Union
import os
import json
import uuid
from datetime import datetime
import asyncio

from models.test_case import TestCase, TestCaseRequest, TestCaseResponse
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
    """
    结构化功能测试点生成：
    1. 数据预处理（文本切块、图片分类）
    2. 功能模块分解
    3. 按模块生成测试点
    
    支持两种输入模式：
    1. PRD输入（文本+多图片）：prd_text + images
    2. 飞书文档输入：feishu_url
    """
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
        # PRD输入模式
        try:
            # 保存上传的图片
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
            # 清理已上传的文件
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
