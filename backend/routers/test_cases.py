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
    支持两种输入模式：
    1. PRD输入（文本+多图片）：prd_text + images
    2. 飞书文档输入：feishu_url
    """
    ai_service = request.app.state.ai_service
    image_paths = []
    if feishu_url:
        # 飞书文档模式
        return StreamingResponse(
            ai_service.generate_test_cases_stream_from_feishu(
                feishu_url=feishu_url,
                context=context,
                requirements=requirements
            ),
            media_type="text/markdown"
        )
    elif prd_text or images:
        # PRD模式，允许文本、图片任意组合
        if not prd_text and not images:
            raise HTTPException(status_code=400, detail="请提供PRD文本或图片")
        for image in images:
            if image.filename:
                image_id = str(uuid.uuid4())
                image_extension = os.path.splitext(image.filename)[1]
                image_path = f"uploads/{image_id}{image_extension}"
                with open(image_path, "wb") as image_file:
                    image_file.write(await image.read())
                image_paths.append(image_path)
        return StreamingResponse(
            ai_service.generate_test_cases_from_multimodal_prd_stream(
                prd_text=prd_text or "",
                prd_images=image_paths,
                context=context,
                requirements=requirements
            ),
            media_type="text/markdown"
        )
    else:
        raise HTTPException(status_code=400, detail="请提供有效的输入")

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
