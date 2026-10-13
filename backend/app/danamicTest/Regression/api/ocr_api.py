"""
回归测试OCR功能API端点
处理图片文字识别和数据提取
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

try:
    from ..utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
except ImportError:
    try:
        from ...utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    except ImportError:
        from app.danamicTest.Regression.utils.logging_utils.logger import log_info, log_error, log_warning, log_debug

from ..utils.logging_utils.log_utils import setup_logger

router = APIRouter(tags=["OCR功能"])
logger = setup_logger(__name__)


# OCR相关的数据模型
class OCRImageRequest(BaseModel):
    image_data: str  # base64编码的图片数据


@router.post("/ocr/extract-from-image")
async def extract_data_from_image(request: OCRImageRequest):
    """
    从图片中提取回归测试表单数据
    """
    try:
        log_info("接收到OCR图片提取请求", "ocr_api")

        # 导入OCR处理器和数据提取器
        from ..utils.ocr.simple_easyocr_processor import get_ocr_processor
        ocr_processor = get_ocr_processor()
        from ..utils.ocr.data_extractor import data_extractor

        # 1. OCR识别图片文本
        log_info("开始OCR识别...", "ocr_api")
        ocr_text = ocr_processor.process_image_from_base64(request.image_data)

        if not ocr_text:
            # 检查OCR状态，提供更详细的错误信息
            if isinstance(ocr_processor.ocr, str):
                if ocr_processor.ocr == "model_download_failed":
                    raise HTTPException(
                        status_code=503,
                        detail="OCR模型下载失败，可能是网络问题。请检查网络连接或稍后重试。您也可以手动输入表单信息。"
                    )
                elif ocr_processor.ocr == "unavailable":
                    raise HTTPException(
                        status_code=503,
                        detail="OCR服务不可用。请手动输入表单信息或联系管理员。"
                    )

            raise HTTPException(status_code=400, detail="OCR识别失败，未能从图片中提取到文本。请确保图片清晰且包含文字内容。")

        log_info(f"OCR识别成功，提取文本长度: {len(ocr_text)}", "ocr_api")

        # 2. AI提取结构化数据
        log_info("开始AI数据提取...", "ocr_api")
        structured_data = data_extractor.extract_form_data(ocr_text)

        if not structured_data:
            raise HTTPException(status_code=400, detail="数据提取失败，未能从文本中提取到有效信息")

        log_info(f"数据提取成功: {structured_data}", "ocr_api")

        # 3. 返回结构化数据
        return {
            "status": "success",
            "message": "图片数据提取成功",
            "data": {
                "ocr_text": ocr_text,
                "extracted_data": structured_data
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        log_error(f"OCR数据提取失败: {str(e)}", "ocr_api")
        raise HTTPException(status_code=500, detail=f"OCR数据提取失败: {str(e)}")


@router.post("/ocr/test-connection")
async def test_ocr_connection():
    """
    测试OCR服务连接状态
    """
    try:
        from ..utils.ocr.simple_easyocr_processor import get_ocr_processor
        ocr_processor = get_ocr_processor()

        if ocr_processor.ocr is None:
            return {
                "status": "error",
                "message": "OCR服务未初始化",
                "ocr_available": False
            }
        elif isinstance(ocr_processor.ocr, str):
            if ocr_processor.ocr == "unavailable":
                return {
                    "status": "error",
                    "message": "OCR服务不可用",
                    "ocr_available": False
                }
            elif ocr_processor.ocr == "model_download_failed":
                return {
                    "status": "warning",
                    "message": "CnOCR模型下载失败，可能是网络问题。OCR功能暂时不可用",
                    "ocr_available": False,
                    "suggestion": "请检查网络连接或稍后重试"
                }
            elif ocr_processor.ocr == "tesseract":
                return {
                    "status": "success",
                    "message": "OCR服务连接正常",
                    "ocr_available": True,
                    "ocr_type": "Tesseract"
                }

        return {
            "status": "success",
            "message": "OCR服务连接正常",
            "ocr_available": True,
            "ocr_type": "CnOCR"
        }

    except Exception as e:
        log_error(f"OCR连接测试失败: {str(e)}", "ocr_api")
        return {
            "status": "error",
            "message": f"OCR连接测试失败: {str(e)}",
            "ocr_available": False
        }


@router.get("/ocr/status")
async def get_ocr_status():
    """
    获取OCR服务状态信息
    """
    try:
        from ..utils.ocr.simple_easyocr_processor import get_ocr_processor
        ocr_processor = get_ocr_processor()
        
        status_info = {
            "service_available": False,
            "ocr_type": None,
            "status": "unknown",
            "message": "OCR服务状态未知"
        }
        
        if ocr_processor.ocr is None:
            status_info.update({
                "status": "not_initialized",
                "message": "OCR服务未初始化"
            })
        elif isinstance(ocr_processor.ocr, str):
            if ocr_processor.ocr == "unavailable":
                status_info.update({
                    "status": "unavailable",
                    "message": "OCR服务不可用"
                })
            elif ocr_processor.ocr == "model_download_failed":
                status_info.update({
                    "status": "model_download_failed",
                    "message": "OCR模型下载失败"
                })
            elif ocr_processor.ocr == "tesseract":
                status_info.update({
                    "service_available": True,
                    "ocr_type": "Tesseract",
                    "status": "available",
                    "message": "Tesseract OCR服务可用"
                })
        else:
            # CnOCR对象
            status_info.update({
                "service_available": True,
                "ocr_type": "CnOCR",
                "status": "available",
                "message": "CnOCR服务可用"
            })
        
        return {
            "status": "success",
            "data": status_info
        }
        
    except Exception as e:
        log_error(f"获取OCR状态失败: {str(e)}", "ocr_api")
        return {
            "status": "error",
            "message": f"获取OCR状态失败: {str(e)}",
            "data": {
                "service_available": False,
                "ocr_type": None,
                "status": "error",
                "message": f"状态检查失败: {str(e)}"
            }
        }


@router.post("/ocr/extract-text-only")
async def extract_text_only(request: OCRImageRequest):
    """
    仅进行OCR文字识别，不进行AI数据提取
    """
    try:
        log_info("接收到纯OCR文字识别请求", "ocr_api")
        
        # 导入OCR处理器
        from ..utils.ocr.simple_easyocr_processor import get_ocr_processor
        ocr_processor = get_ocr_processor()
        
        # OCR识别图片文本
        log_info("开始OCR识别...", "ocr_api")
        ocr_text = ocr_processor.process_image_from_base64(request.image_data)
        
        if not ocr_text:
            raise HTTPException(status_code=400, detail="OCR识别失败，未能从图片中提取到文本")
        
        log_info(f"OCR识别成功，提取文本长度: {len(ocr_text)}", "ocr_api")
        
        return {
            "status": "success",
            "message": "OCR文字识别成功",
            "data": {
                "ocr_text": ocr_text,
                "text_length": len(ocr_text)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"OCR文字识别失败: {str(e)}", "ocr_api")
        raise HTTPException(status_code=500, detail=f"OCR文字识别失败: {str(e)}")


# 响应模型
class OCRResponse(BaseModel):
    """OCR响应模型"""
    status: str
    message: str
    data: dict


class OCRStatusResponse(BaseModel):
    """OCR状态响应模型"""
    status: str
    data: dict
