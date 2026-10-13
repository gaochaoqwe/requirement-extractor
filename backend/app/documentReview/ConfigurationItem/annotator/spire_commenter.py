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
            # 调整匹配策略：优先使用 requirement_content，然后是 issue_location
            primary_text = (item.get("requirement_content") or "").strip()
            fallback_text = (item.get("issue_location") or "").strip()
            
            if not primary_text and not fallback_text:
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
            
            # 查找目标文本并添加批注，优先使用原始需求内容
            success = False
            if primary_text:
                success = _add_comment_to_text_correct(doc, primary_text, comment_text, f"AI审查_{idx}", use_partial_match=True)
                if success:
                    logger.info(f"成功为问题 #{idx} 添加批注（使用需求内容）: {primary_text[:30]}...")
                else:
                    logger.info(f"使用需求内容匹配失败，问题 #{idx}: {primary_text[:30]}...")
            
            # 如果使用需求内容匹配失败，再尝试使用位置信息
            if not success and fallback_text:
                success = _add_comment_to_text_correct(doc, fallback_text, comment_text, f"AI审查_{idx}", use_partial_match=True)
                if success:
                    logger.info(f"成功为问题 #{idx} 添加批注（使用位置信息）: {fallback_text[:30]}...")
                else:
                    logger.warning(f"无法为问题 #{idx} 添加批注: 需求内容和位置信息都匹配失败")
            
            if success:
                success_count += 1
        
        # 保存批注版文档
        os.makedirs(output_dir, exist_ok=True)
        base_name = os.path.splitext(os.path.basename(document_path))[0]
        
        # 根据文档类型确定文件名
        doc_name_map = {
            'taskBook': '研制任务书',
            'requirementSpec': '需求规格说明'
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


def _add_comment_to_text_correct(doc: Document, target_text: str, comment_text: str, author: str = "AI", use_partial_match: bool = False) -> bool:
    """使用正确的Spire.Doc API添加批注并高亮文本
    
    Args:
        doc: Spire.Doc文档对象
        target_text: 要匹配的目标文本
        comment_text: 批注内容
        author: 批注作者
        use_partial_match: 是否使用部分匹配策略
    """
    if not SPIRE_AVAILABLE:
        return False
        
    try:
        text_selection = None
        
        if use_partial_match:
            # 使用改进的部分匹配策略
            text_selection = _find_text_with_partial_match(doc, target_text)
        else:
            # 尝试精确匹配
            text_selection = doc.FindString(target_text, True, True)
        
        if text_selection is None:
            logger.warning(f"未找到目标文本: {target_text[:50]}...")
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


def _find_text_with_partial_match(doc: Document, target_text: str):
    """使用改进的部分匹配策略查找文本
    
    Args:
        doc: Spire.Doc文档对象
        target_text: 要匹配的目标文本
        
    Returns:
        找到的文本选择对象，如果未找到则返回None
    """
    if not target_text or len(target_text.strip()) < 3:
        return None
    
    # 清理目标文本
    target_text = target_text.strip()
    
    # 策略1: 尝试完整匹配（去除多余空白字符）
    normalized_target = ' '.join(target_text.split())
    text_selection = doc.FindString(normalized_target, True, True)
    if text_selection is not None:
        logger.info(f"完整匹配成功: {normalized_target[:30]}...")
        return text_selection
    
    # 策略2: 提取关键短语进行匹配
    # 去除常见的标点符号和连接词，提取有意义的短语
    import re
    
    # 移除标点符号，保留中文、英文、数字
    cleaned_text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s]', ' ', target_text)
    words = cleaned_text.split()
    
    # 过滤掉过短的词和常见停用词
    stop_words = {'的', '了', '和', '与', '或', '及', '等', '对', '在', '是', '有', '为', '与', '等等', '以及'}
    meaningful_words = [word for word in words if len(word) >= 2 and word not in stop_words]
    
    # 策略3: 尝试匹配较长的有意义短语（连续的3-5个词）
    for phrase_len in range(min(5, len(meaningful_words)), 2, -1):  # 从长到短
        for i in range(len(meaningful_words) - phrase_len + 1):
            phrase = ' '.join(meaningful_words[i:i + phrase_len])
            if len(phrase) >= 6:  # 确保短语足够长
                text_selection = doc.FindString(phrase, True, True)
                if text_selection is not None:
                    logger.info(f"短语匹配成功: {phrase}")
                    return text_selection
    
    # 策略4: 尝试匹配单个较长的关键词
    for word in meaningful_words:
        if len(word) >= 4:  # 只搜索长度大于等于4的词
            text_selection = doc.FindString(word, True, True)
            if text_selection is not None:
                logger.info(f"关键词匹配成功: {word}")
                return text_selection
    
    # 策略5: 如果是数字编号开头的内容，尝试匹配编号后的主要内容
    number_match = re.match(r'^(\d+\.?\d*\.?\s*)', target_text)
    if number_match:
        content_after_number = target_text[number_match.end():].strip()
        if len(content_after_number) >= 6:
            text_selection = doc.FindString(content_after_number, True, True)
            if text_selection is not None:
                logger.info(f"编号后内容匹配成功: {content_after_number[:30]}...")
                return text_selection
    
    logger.warning(f"所有匹配策略都失败: {target_text[:50]}...")
    return None


def test_spire_comment_correct():
    """测试正确的Spire.Doc批注功能"""
    if not SPIRE_AVAILABLE:
        import sys
        sys.stderr.write("Spire.Doc库不可用，跳过测试\n")
        return
        
    try:
        # 创建测试文档
        doc = Document()
        
        # 添加一个节
        section = doc.AddSection()
        
        # 添加标题段落
        title = section.AddParagraph()
        title.AppendText("测试研制任务书")
        
        # 添加目录段落（模拟目录结构）
        toc = section.AddParagraph()
        toc.AppendText("目录\n1. 项目概述\n2. 技术要求\n3. 系统架构")
        
        # 添加章节标题
        chapter1 = section.AddParagraph()
        chapter1.AppendText("1. 项目概述")
        
        # 添加正文内容
        para1 = section.AddParagraph()
        para1.AppendText("本项目旨在开发一个高性能的软件系统，该系统应具备良好的可扩展性和稳定性。系统需要支持多用户并发访问，并确保数据的安全性和完整性。")
        
        # 添加另一个章节
        chapter2 = section.AddParagraph()
        chapter2.AppendText("2. 技术要求")
        
        para2 = section.AddParagraph()
        para2.AppendText("系统应采用模块化设计，支持分布式部署。数据库应具备高可用性，支持实时备份和恢复功能。")
        
        # 保存测试文档
        test_path = "test_document_improved_matching.docx"
        doc.SaveToFile(test_path, FileFormat.Docx)
        doc.Close()
        
        logger.info(f"创建测试文档: {test_path}")
        
        # 测试批注功能 - 使用新的匹配策略
        test_issues = [
            {
                # 测试1：使用requirement_content进行匹配（应该匹配到正文而不是目录）
                'requirement_content': '本项目旨在开发一个高性能的软件系统，该系统应具备良好的可扩展性和稳定性',
                'issue_location': '1. 项目概述',  # 这个可能会匹配到目录
                'issue_name': '系统性能要求不够明确',
                'violation_rules': '系统性能指标缺乏具体数值',
                'issue_level': '重要问题',
                'description_issue': '系统性能要求描述过于笼统，缺乏具体的性能指标'
            },
            {
                # 测试2：测试部分匹配功能
                'requirement_content': '系统应采用模块化设计，支持分布式部署。数据库应具备高可用性',
                'issue_location': '2. 技术要求',
                'issue_name': '技术架构描述不完整',
                'violation_rules': '缺少具体的技术实现方案',
                'issue_level': '一般问题',
                'description_issue': '技术要求描述缺少具体的实现细节'
            },
            {
                # 测试3：测试只有issue_location的情况（应该避免匹配到目录）
                'requirement_content': '',  # 空的requirement_content
                'issue_location': '项目概述',  # 这个应该匹配到章节标题而不是目录
                'issue_name': '章节标题格式问题',
                'violation_rules': '章节标题格式不规范',
                'issue_level': '建议改进',
                'description_issue': '建议统一章节标题的格式'
            }
        ]
        
        # 生成批注版文档
        output_dir = "test_output_improved_matching"
        annotated_path = add_comments_to_document_spire(
            test_path, 
            test_issues, 
            output_dir, 
            session_id=999,
            doc_type='taskBook'
        )
        
        logger.info(f"批注版文档已生成: {annotated_path}")
        
        # 验证文档
        if os.path.exists(annotated_path):
            logger.info("✅ 批注版文档生成成功")
            
            # 尝试加载文档验证批注
            doc_check = Document()
            doc_check.LoadFromFile(annotated_path)
            
            # 获取批注数量
            comment_count = doc_check.Comments.Count
            logger.info(f"文档中的批注数量: {comment_count}")
            
            # 列出所有批注
            for i in range(comment_count):
                comment = doc_check.Comments.get_Item(i)
                try:
                    # 尝试获取批注文本内容
                    comment_text = ""
                    if comment.Body.Paragraphs.Count > 0:
                        comment_text = comment.Body.Paragraphs.get_Item(0).Text
                    logger.info(f"批注 {i+1}: {comment_text[:100]}...")
                    logger.info(f"  作者: {comment.Format.Author}")
                except Exception as e:
                    logger.warning(f"批注 {i+1}: 无法读取内容 ({e})")
                    logger.info(f"  作者: {comment.Format.Author}")
            
            doc_check.Close()
            
            if comment_count > 0:
                logger.info("✅ 批注功能正常工作")
                logger.info("✅ 新的匹配策略测试完成")
                logger.info("说明：")
                logger.info("- 优先使用requirement_content进行匹配，避免匹配到目录")
                logger.info("- 支持多层次的部分匹配策略")
                logger.info("- 只有在requirement_content匹配失败时才使用issue_location")
            else:
                logger.warning("❌ 未找到批注")
        else:
            logger.warning("❌ 批注版文档生成失败")
            
        # 清理测试文件
        try:
            if os.path.exists(test_path):
                os.remove(test_path)
            if os.path.exists(output_dir):
                import shutil
                shutil.rmtree(output_dir)
            logger.info("测试文件已清理")
        except Exception as e:
            logger.warning(f"清理文件失败: {e}")
            
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_spire_comment_correct() 