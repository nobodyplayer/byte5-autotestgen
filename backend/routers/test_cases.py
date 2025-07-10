import os
import uuid
from typing import List, Dict, Any, Union

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import StreamingResponse, FileResponse
from models.test_case import TestCase
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
    生成测试用例的核心API端点。

    功能描述:
        该端点接收用户通过表单（form-data）提交的需求信息，支持两种灵活的输入模式：
        1. 基于飞书文档URL的输入。
        2. 基于PRD（产品需求文档）文本和图片（如UI截图、流程图）的混合输入。
        处理后，它会调用后端的AI服务，并以流式响应（StreamingResponse）的方式
        实时返回生成的Markdown格式的测试用例。

    Args:
        request (Request): FastAPI的请求对象，用于访问应用级的共享状态（如ai_service）。
        prd_text (str, optional): 来自表单的PRD纯文本内容。默认为None。
        images (List[UploadFile], optional): 来自表单的图片文件列表。默认为空列表。
        feishu_url (str, optional): 来自表单的飞书文档URL。默认为None。
        context (str): 来自表单的必需字段，提供生成测试用例的上下文。
        requirements (str): 来自表单的必需字段，提供具体的生成要求。

    Returns:
        StreamingResponse: 一个流式响应对象，它会以'text/markdown'的媒体类型
                           持续地将AI生成的文本块发送给客户端。

    Raises:
        HTTPException: 如果输入不合法（例如，选择了PRD模式但未提供任何文本或图片），
                       会抛出状态码为400的HTTP异常。
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
    """
    POST API端点。接收一个包含测试用例数据的列表，
    调用Excel服务将这些数据生成为一个.xlsx格式的Excel文件，
    然后通过文件响应(FileResponse)的方式返回给客户端，以触发浏览器下载。

    Args:
        test_cases (List[Union[TestCase, Dict[str, Any]]]):
            一个列表，其中每个元素都是一个测试用例对象（可以是Pydantic模型或字典）。
            是需要被写入到Excel文件中的核心数据。

    Returns:
        FileResponse: 一个文件响应对象，包含了生成的Excel电子表格，
                      其MIME类型为 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'。

    Raises:
        HTTPException: 如果在生成Excel文件或创建文件响应的过程中发生任何错误，
                       将抛出状态码为500的HTTP异常。
    """
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
    """
        这是一个GET API端点。它根据URL路径中提供的文件名，
        在服务器的预设目录（例如 "results/"）中查找对应的文件。
        如果文件存在，则返回该文件供用户下载。

        Args:
            filename (str): 需要下载的文件的名称，通过URL路径参数传入。

        Returns:
            FileResponse: 如果文件被成功找到，则返回包含该文件的文件响应对象，
                          触发客户端下载。

        Raises:
            HTTPException: 如果根据提供的文件名在服务器上找不到对应的文件，
                           将抛出状态码为404 (Not found) 的HTTP异常。
        """
    file_path = f"results/{filename}"

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@router.post("/fullPipeline")
async def full_pipeline(
        request: Request,
        prd_text: str = Form(None)
):
    ai_service = request.app.state.ai_service
    return StreamingResponse(
        ai_service.generate_test_cases_full_pipeline(
            prd_text=prd_text or ""
        ),
        media_type="text/markdown"
    )
