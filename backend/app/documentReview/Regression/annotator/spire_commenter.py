"""使用Spire.Doc库为Word文档添加批注的工具模块"""
import os
import uuid
from typing import List, Dict, Optional
import logging

try:
    from spire.doc import Document, FileFormat, Comment, CommentMark, CommentMarkType
    from spire.doc.common import *
    SPIRE_AVAILABLE = True
except ImportError:
    SPIRE_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Spire.Doc库未安装，批注功能不可用")

logger = logging.getLogger(__name__)


def add_comments_to_document_spire(document_path: str, issues: List[Dict[str, str]], output_dir: str, session_id: Optional[int] = None, doc_type: str = "document") -> str:
    """使用Spire.Doc为文档添加批注
    
    Args:
        document_path: 原始文档文件路径
        issues: AI分析出的问题列表
        output_dir: 输出目录
        session_id: 会话ID
        doc_type: 文档类型 (taskBook 或 requirementSpec)
        
    Returns:
        批注版文档的路径
    """
    if not SPIRE_AVAILABLE:
        raise ImportError("Spire.Doc库未安装，无法使用批注功能")
    
    try:
        # 加载文档
        doc = Document()
        doc.LoadFromFile(document_path)
        logger.info(f"成功加载文档: {document_path}")
        logger.info(f"开始为文档添加批注，共 {len(issues)} 个问题")
        
        # 统计批注添加情况
        success_count = 0
        total_count = len(issues)
        
        for idx, item in enumerate(issues, start=1):
            # 优先使用 issue_location，然后是 requirement_content
            target_text = (item.get("issue_location") or item.get("requirement_content") or "").strip()
            
            if not target_text:
                logger.warning(f"问题 #{idx} 缺少定位文本，跳过")
                continue
            
            # 构建批注内容
            comment_parts = []
            if item.get('violation_rules'):
                comment_parts.append(f"违反规则：{item['violation_rules']}")
            if item.get('issue_level'):
                comment_parts.append(f"问题等级：{item['issue_level']}")
            if item.get('issue_name'):
                comment_parts.append(f"问题名称：{item['issue_name']}")
            if item.get('description_issue'):
                comment_parts.append(f"问题描述：{item['description_issue']}")
            
            comment_text = "\n".join(comment_parts) if comment_parts else f"问题 #{idx}"
            
            # 查找目标文本并添加批注
            if _add_comment_to_text_correct(doc, target_text, comment_text, f"AI审查_{idx}"):
                success_count += 1
                logger.info(f"成功为问题 #{idx} 添加批注: {target_text[:30]}...")
            else:
                logger.warning(f"无法为问题 #{idx} 添加批注: {target_text[:30]}...")
        
        # 保存批注版文档
        os.makedirs(output_dir, exist_ok=True)
        base_name = os.path.splitext(os.path.basename(document_path))[0]
        
        # 根据文档类型确定文件名
        doc_name_map = {
            'taskBook': '研制任务书',
            'requirementSpec': '需求规格说明',
            'impactReport': '影响域分析报告'
        }
        doc_display_name = doc_name_map.get(doc_type, '文档')
        
        # 包含session_id的文件名
        if session_id:
            annotated_path = os.path.join(output_dir, f"{doc_display_name}_批注版_session_{session_id}.docx")
        else:
            annotated_path = os.path.join(output_dir, f"{doc_display_name}_批注版_{uuid.uuid4().hex[:6]}.docx")
        
        # 保存为Word格式
        doc.SaveToFile(annotated_path, FileFormat.Docx)
        logger.info(f"批注版文档已保存: {annotated_path}")
        logger.info(f"批注添加统计: {success_count}/{total_count} 成功")
        
        # 释放资源
        doc.Close()
        
        return annotated_path
        
    except Exception as e:
        logger.error(f"使用Spire.Doc生成批注版文档失败: {e}", exc_info=True)
        raise


def _add_comment_to_text_correct(doc: Document, target_text: str, comment_text: str, author: str = "AI") -> bool:
    """使用正确的Spire.Doc API添加批注并高亮文本"""
    if not SPIRE_AVAILABLE:
        return False
        
    try:
        # 查找要批注的文本
        text_selection = doc.FindString(target_text, True, True)
        
        if text_selection is None:
            # 尝试部分匹配
            target_words = target_text.split()
            for word in target_words:
                if len(word) > 2:  # 只搜索长度大于2的词
                    text_selection = doc.FindString(word, True, True)
                    if text_selection is not None:
                        logger.info(f"使用部分匹配找到文本: {word}")
                        break
        
        if text_selection is None:
            logger.warning(f"未找到目标文本: {target_text}")
            return False
        
        # 将找到的文本作为文本范围，并获取其所属的段落
        text_range = text_selection.GetAsOneRange()
        paragraph = text_range.OwnerParagraph
        
        # 首先给文本添加黄色高亮
        try:
            # 设置文本背景色为黄色
            from spire.doc.common import Color
            text_range.CharacterFormat.HighlightColor = Color.get_Yellow()
            logger.info(f"成功为文本添加黄色高亮: {target_text[:30]}...")
        except Exception as highlight_err:
            logger.warning(f"添加高亮失败: {highlight_err}")
        
        # 创建批注并设置批注内容和作者
        comment = Comment(doc)
        comment.Body.AddParagraph().Text = comment_text
        comment.Format.Author = author
        
        # 将批注添加到段落中
        paragraph.ChildObjects.Insert(paragraph.ChildObjects.IndexOf(text_range) + 1, comment)
        
        # 创建批注开始标记和结束标记
        comment_start = CommentMark(doc, CommentMarkType.CommentStart)
        comment_end = CommentMark(doc, CommentMarkType.CommentEnd)
        comment_start.CommentId = comment.Format.CommentId
        comment_end.CommentId = comment.Format.CommentId
        
        # 在找到的文本之前和之后插入批注开始和结束标记
        paragraph.ChildObjects.Insert(paragraph.ChildObjects.IndexOf(text_range), comment_start)
        paragraph.ChildObjects.Insert(paragraph.ChildObjects.IndexOf(text_range) + 1, comment_end)
        
        logger.info(f"成功添加批注和高亮到文本: {target_text[:30]}...")
        return True
        
    except Exception as e:
        logger.warning(f"添加批注失败: {e}")
        return False 