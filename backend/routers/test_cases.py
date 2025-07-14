import os
import uuid
from typing import List, Dict, Any, Union

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import StreamingResponse, FileResponse
from models.test_case import TestCase
from services.excel_service import excel_service
import logging

logger = logging.getLogger(__name__)

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


@router.post("/detect_test_point")
async def detect_test_point(
        request: Request,
        prd_text: str = Form(None)
):
    # 获取服务与session
    print("开始检测服务")
    ai_service = request.app.state.ai_service
    session = request.session
    # set-cookie设置
    if not session.get("user_id"):
        session["user_id"] = os.urandom(32).hex()
    # 流式执行
    headers = {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",  # 要求客户端或代理不缓存此响应
        "X-Accel-Buffering": "no"  # 一个常用于Nginx的指令，很多代理也会识别它，明确禁止缓冲
    }
    return StreamingResponse(
        ai_service.detected_test_point(
            prd_text=prd_text or "",
            session=session
        ),
        headers=headers
    )


@router.post("/test_point_review")
async def test_point_review(
        request: Request,
        user_review: str = Form(None)
):
    # 获取服务与session
    ai_service = request.app.state.ai_service
    session = request.session
    # 流式执行
    return StreamingResponse(
        ai_service.test_point_review(
            user_review=user_review or "",
            session=session
        ),
        media_type="text/markdown"
    )


@router.post("/generate_test_case")
async def generate_test_case(
        request: Request
):
    # 获取服务与session
    ai_service = request.app.state.ai_service
    session = request.session
    # 流式执行
    return StreamingResponse(
        ai_service.generate_test_case(
            session=session
        ),
        media_type="text/markdown"
    )


@router.post("/test_case_review")
async def test_case_review(
        request: Request,
        review_list: List[str] = Form(None),
        review_function: str = Form(None),
):
    # 获取服务与session
    ai_service = request.app.state.ai_service
    session = request.session
    # 流式执行
    return StreamingResponse(
        ai_service.test_case_review(
            review_list=review_list or "",
            review_function=review_function or "",
            session=session
        ),
        media_type="text/markdown"
    )


@router.get("/get_test_points", response_model=Dict[str, Any])
async def get_test_points(request: Request):
    """
    从当前用户的会话中，获取已经提取好的功能测试点数据。

    这个接口是作为流式分析接口（如/detect_test_point）的补充，
    用于在流式日志输出完毕后，由前端主动调用以获取结构化的最终结果。

    Args:
        request (Request): FastAPI的请求对象，用于访问会话(session)。

    Returns:
        Dict[str, Any]: 一个字典，其中键是功能模块名称，值是该模块下的测试点列表。
                        如果session中没有找到数据，则返回404错误。

    Raises:
        HTTPException: 如果在会话中找不到有效的测试点数据，则抛出404 Not Found异常。
    """
    # 1. 通过注入的request对象，安全地获取session
    session = request.session
    if not session.get("user_id"):
        raise HTTPException(status_code=404, detail="Session中未找到状态信息，请先执行分析步骤。")
    ai_service = request.app.state.ai_service
    test_points_dict = await ai_service.get_test_points(session["user_id"])
    if not test_points_dict:
        raise HTTPException(status_code=404, detail="状态中未找到已提取的测试点，请确认分析步骤是否成功完成。")
    # 4. 如果成功找到，直接返回该字典
    # FastAPI会自动将其序列化为JSON响应
    print(f"成功从Session中为用户检索到测试点数据: {test_points_dict}")
    return test_points_dict


@router.get("/get_test_cases", response_model=List[TestCase])  # 假设TestCase是您的Pydantic模型
async def get_all_test_cases(request: Request):
    """
    获取当前会话中存储的、最新的完整测试用例列表。
    """
    session = request.session
    if not session.get("user_id"):
        raise HTTPException(status_code=404, detail="Session中未找到状态信息，请先执行分析步骤。")
    ai_service = request.app.state.ai_service

    # 从我们之前迭代流程中最后保存的地方获取数据
    all_cases = await ai_service.get_all_test_cases(session["user_id"])
    if not all_cases:
        raise HTTPException(status_code=404, detail="状态中未找到已生成的测试用例，请确认分析步骤是否成功完成。")
    print(f"成功从Session中为用户检索到测试点数据: {all_cases}")
    return all_cases