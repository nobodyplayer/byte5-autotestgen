from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import StreamingResponse, FileResponse
from typing import List, Optional, Dict, Any, Union
import os
import json
import uuid
from datetime import datetime
import asyncio
import csv
import io
from pydantic import BaseModel

from models.test_case import TestCase, TestCaseRequest, TestCaseResponse, MindMapRequest
from services.excel_service import excel_service

class EvaluationRequest(BaseModel):
    ai_generated_cases: str
    human_reference_cases: str

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

@router.post("/evaluate")
async def evaluate_test_cases(
    request: Request,
    ai_generated_cases: str = Form(None),
    human_reference_cases: Optional[str] = Form(None),
    csv_file: Optional[UploadFile] = File(None),
    ai_csv_file: Optional[UploadFile] = File(None)
):
    """
    自动化评测AI生成的测试用例与人工参考用例
    支持三种输入模式：
    1. 直接文本输入：ai_generated_cases + human_reference_cases
    2. 人工用例CSV上传：ai_generated_cases + csv_file
    3. AI用例CSV上传：ai_csv_file + human_reference_cases/csv_file
    """
    try:
        ai_service = request.app.state.ai_service
        # 处理人工参考用例输入
        if csv_file and csv_file.filename:
            content = await csv_file.read()
            csv_content = content.decode('utf-8')
            csv_reader = csv.reader(io.StringIO(csv_content))
            human_cases = []
            headers = next(csv_reader, None)
            for row in csv_reader:
                if row:
                    case_text = ' '.join(row).strip()
                    if case_text:
                        human_cases.append(case_text)
            human_reference_text = '\n'.join(human_cases)
        elif human_reference_cases:
            human_reference_text = human_reference_cases
        else:
            raise HTTPException(status_code=400, detail="请提供人工参考用例（文本或CSV文件）")
        # 处理AI生成用例输入
        if ai_csv_file and ai_csv_file.filename:
            content = await ai_csv_file.read()
            csv_content = content.decode('utf-8')
            csv_reader = csv.reader(io.StringIO(csv_content))
            ai_cases = []
            headers = next(csv_reader, None)
            for row in csv_reader:
                if row:
                    case_text = ' '.join(row).strip()
                    if case_text:
                        ai_cases.append(case_text)
            ai_generated_cases_text = '\n'.join(ai_cases)
        elif ai_generated_cases:
            ai_generated_cases_text = ai_generated_cases
        else:
            raise HTTPException(status_code=400, detail="请提供AI生成的测试用例（文本或CSV文件）")
        if not ai_generated_cases_text.strip():
            raise HTTPException(status_code=400, detail="请提供AI生成的测试用例")
        return StreamingResponse(
            ai_service.evaluate_test_cases_stream(
                ai_generated_cases=ai_generated_cases_text,
                human_reference_cases=human_reference_text
            ),
            media_type="text/plain; charset=utf-8"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"评测过程中发生错误: {str(e)}")

@router.post("/evaluate-json")
async def evaluate_test_cases_json(
    request: Request,
    evaluation_request: EvaluationRequest
):
    """
    自动化评测AI生成的测试用例与人工参考用例（JSON格式）
    
    参数:
        evaluation_request: 包含AI生成用例和人工参考用例的请求体
    """
    try:
        ai_service = request.app.state.ai_service
        
        if not evaluation_request.ai_generated_cases.strip():
            raise HTTPException(status_code=400, detail="请提供AI生成的测试用例")
        
        if not evaluation_request.human_reference_cases.strip():
            raise HTTPException(status_code=400, detail="请提供人工参考用例")
        
        # 调用AI服务进行评测
        return StreamingResponse(
            ai_service.evaluate_test_cases_stream(
                ai_generated_cases=evaluation_request.ai_generated_cases,
                human_reference_cases=evaluation_request.human_reference_cases
            ),
            media_type="text/plain; charset=utf-8"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"评测过程中发生错误: {str(e)}")
