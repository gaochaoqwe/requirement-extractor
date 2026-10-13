"""
数据准备模块
负责获取和准备回归测试审查所需的数据
"""
import os
from typing import Dict, Any, Optional

from app.codeReview.Regression.db.repository.file_repo import FileRepository
from app.codeReview.Regression.db.repository.task_repo import TaskRepository


def log_debug(msg):
    """记录调试日志"""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.abspath(os.path.join(base_dir, '..', '..', '..', '..', '..', '..'))
        log_dir = os.path.join(backend_dir, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, 'bg_debug.txt')
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        # Suppress logging errors if path resolution or writing fails
        pass


def prepare_review_data(db, file_id: int, task_id: int) -> Dict[str, Any]:
    """
    准备回归测试审查所需的数据
    
    Args:
        db: 数据库会话
        file_id: 文件ID
        task_id: 任务ID
        
    Returns:
        Dict[str, Any]: 包含准备结果的字典
    """
    result = {
        "success": False,
        "message": "",
        "extract_path": None,
        "impact_report_content": None
    }
    
    # 获取文件信息
    file_repo = FileRepository(db)
    task_repo = TaskRepository(db)
    
    db_file = file_repo.get_file(file_id)
    log_debug(f"[prepare_review_data] file_id={file_id}, db_file={db_file.to_dict() if db_file else 'None'}")
    if not db_file or not db_file.extract_path or not os.path.exists(db_file.extract_path):
        result["message"] = f"文件或解压路径无效. file_id: {file_id}"
        return result
    
    extract_path = db_file.extract_path
    result["extract_path"] = extract_path
    log_debug(f"[prepare_review_data] extract_path={extract_path}")
    
    # 优先使用任务记录中的 report_file_id
    impact_report_path = None
    try:
        task = task_repo.get_task(task_id)
        if task and getattr(task, "report_file_id", None):
            report_record = file_repo.get_file(task.report_file_id)
            if report_record:
                # 如果上传的是 docx（通常 extract_path 为空），直接用 file_path
                if report_record.extract_path and os.path.exists(report_record.extract_path):
                    impact_report_path = report_record.extract_path
                elif report_record.file_path and os.path.exists(report_record.file_path):
                    impact_report_path = report_record.file_path
    except Exception as e:
        log_debug(f"[prepare_review_data] 获取任务中 report_file 失败: {e}")

    # 回退：在合并后的 workspace 中搜索报告
    if not impact_report_path:
        impact_report_path = find_impact_report(extract_path)

    log_debug(f"[prepare_review_data] impact_report_path={impact_report_path}")

    if not impact_report_path:
        result["message"] = "找不到影响域分析报告"
        return result
    
    # 读取报告内容
    try:
        impact_report_content = read_file_content(impact_report_path)
        if not impact_report_content:
            result["message"] = "影响域分析报告内容为空"
            return result
        
        result["impact_report_content"] = impact_report_content
        result["success"] = True
        return result
        
    except Exception as e:
        result["message"] = f"读取影响域分析报告时出错: {str(e)}"
        return result


def find_impact_report(extract_path: str) -> Optional[str]:
    """
    在解压目录中查找影响域分析报告文件
    
    Args:
        extract_path: 解压目录路径
        
    Returns:
        Optional[str]: 报告文件路径，如果找不到则返回None
    """
    # 常见的影响域分析报告文件名
    report_filenames = [
        "impact_analysis_report.txt",
        "impact_analysis_report.md",
        "impact_analysis.txt",
        "impact_analysis.md",
        "impact_analysis_report.docx",
        "impact_analysis.docx",
        "影响域分析报告.txt",
        "影响域分析报告.md",
        "影响域分析报告.docx",
        "影响域.docx"
    ]
    
    # 在解压目录下搜索
    for filename in report_filenames:
        report_path = os.path.join(extract_path, filename)
        if os.path.exists(report_path):
            return report_path
    
    # 如果在根目录没找到，搜索子目录
    for root, _, files in os.walk(extract_path):
        for file in files:
            lower_file = file.lower()
            if lower_file.endswith('.docx'):
                if ("impact" in lower_file and "analysis" in lower_file) or ("影响域" in file):
                    return os.path.join(root, file)

    # 最后兜底：返回工作目录下第一个 .docx
    for root, _, files in os.walk(extract_path):
        for file in files:
            if file.lower().endswith('.docx'):
                return os.path.join(root, file)
    
    return None


def read_file_content(file_path: str) -> str:
    """
    读取文件内容
    
    Args:
        file_path: 文件路径
        
    Returns:
        str: 文件内容
    """
    # 对于Word文档(.docx)的处理
    if file_path.lower().endswith('.docx'):
        try:
            from docx import Document
            doc = Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])
        except ImportError:
            log_debug("未安装python-docx库，无法读取Word文档")
            raise Exception("需要安装python-docx库来读取Word文档")
        except Exception as e:
            log_debug(f"读取Word文档时出错: {e}")
            raise
    
    # 对于文本文件的处理
    encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'big5', 'latin1']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
                return content
        except UnicodeDecodeError:
            continue
        except Exception as e:
            log_debug(f"读取文件时出错: {e}")
            raise
    
    # 如果所有编码都失败，尝试使用chardet检测编码
    try:
        import chardet
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding']
            return raw_data.decode(encoding)
    except ImportError:
        log_debug("未安装chardet库，无法自动检测文件编码")
    except Exception as e:
        log_debug(f"使用chardet检测编码时出错: {e}")
    
    raise Exception(f"无法读取文件: {file_path}，请检查文件编码") 