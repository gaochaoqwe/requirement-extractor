from enum import Enum

class DocumentType(str, Enum):
    REQUIREMENT_SPEC = "requirementSpec"
    TASK_BOOK = "taskBook"

def get_document_config(doc_type: str) -> dict:
    """获取文档类型配置"""
    if doc_type == DocumentType.REQUIREMENT_SPEC:
        return {"name": "需求规格说明", "dir_suffix": "requirement_specs"}
    elif doc_type == DocumentType.TASK_BOOK:
        return {"name": "任务书", "dir_suffix": "task_books"}
    else:
        raise ValueError(f"未知的文档类型: {doc_type}")
