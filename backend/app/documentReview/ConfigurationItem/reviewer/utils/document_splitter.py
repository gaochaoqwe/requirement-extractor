import logging
import re
from typing import List, Tuple, Optional


def is_likely_heading(paragraph: str) -> bool:
    """
    判断一个段落是否可能是标题（简化规则）

    规则：
    1. 段落去除首尾空白后字符数 < 30
    2. 不包含标点符号（除了英文句点）
    3. 不包含关键字 "图" 或 "表"
    4. 不能是列表项格式（以字母/数字编号开头）
    5. 可以包含数字编号格式（如 3.2.2）
    6. 不能是方括号中的描述性文本
    """
    text = paragraph.strip()

    # 1. 必须非空且少于 30 个字符
    if not text or len(text) >= 30:
        return False

    # 2. 排除列表项格式
    if re.match(r'^[a-z]\)', text) or re.match(r'^\d+\)', text):
        return False

    # 3. 不能含有标点（除了英文句点）
    punctuation_pattern = r'[。！？；;：:,，、\?\!\(\)（）\-]'
    if re.search(punctuation_pattern, text):
        return False

    # 4. 不能包含图/表
    if ('图' in text) or ('表' in text):
        return False

    # 5. 不能是方括号中的描述性文本
    if text.startswith('[') and text.endswith(']'):
        return False

    # 6. 检查是否包含数字编号格式（如 3.2.2）
    if re.match(r'^\d+(\.\d+)*\s+', text):
        return True

    return True


def split_at_headings(text: str) -> List[str]:
    """
    按标题分割文本，使得返回的每个元素都以一个标题段落开头，包含直到下一个标题之前的所有段落。

    :param text: 原始全文
    :return: 按标题切分后的块列表（标题+内容）
    """
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

    blocks: List[str] = []
    current_block: List[str] = []

    for para in paragraphs:
        if is_likely_heading(para):
            # 遇到新标题，先保存之前的块
            if current_block:
                blocks.append('\n\n'.join(current_block))
                current_block = []
        current_block.append(para)

    # 保存最后一个块
    if current_block:
        blocks.append('\n\n'.join(current_block))

    return blocks


def split_document(content: str, chunk_size: int = 2000, overlap: int = 200) -> List[str]:
    """
    根据标题优先切分文档，并确保每块大小不超过 chunk_size。
    若单个标题块本身超过 chunk_size，则将该块单独作为一块，不进行切分。
    """
    logger = logging.getLogger(__name__)

    # 1. 先按标题分块
    heading_blocks = split_at_headings(content)
    if not heading_blocks:
        heading_blocks = [content]

    final_chunks: List[str] = []
    current_chunk_parts: List[str] = []
    current_len = 0

    for block in heading_blocks:
        block_len = len(block)

        # 如果当前块本身超过chunk_size，直接作为单独的一块
        if block_len > chunk_size:
            # 如果当前有未完成的块，先保存
            if current_chunk_parts:
                final_chunks.append('\n\n'.join(current_chunk_parts))
                current_chunk_parts = []
                current_len = 0
            # 将超长块作为单独的一块
            final_chunks.append(block)
            continue

        # 如果当前块为空，直接放入
        if not current_chunk_parts:
            current_chunk_parts.append(block)
            current_len = block_len
            continue

        # 如果加上后仍不超限，则合并（这样相邻小标题可以共享一块）
        if current_len + block_len <= chunk_size:
            current_chunk_parts.append(block)
            current_len += block_len
        else:
            # 结束当前块
            final_chunks.append('\n\n'.join(current_chunk_parts))
            # 开启新块
            current_chunk_parts = [block]
            current_len = block_len

    # 收尾
    if current_chunk_parts:
        final_chunks.append('\n\n'.join(current_chunk_parts))

    logger.info(
        "文档已分割为 %s 个块, 块大小范围: %s-%s 字符",
        len(final_chunks),
        min(map(len, final_chunks)) if final_chunks else 0,
        max(map(len, final_chunks)) if final_chunks else 0,
    )

    return final_chunks


def merge_issues(issues):
    """
    合并问题列表并去重
    :param issues: 问题列表
    :return: 去重后的问题列表
    """
    seen = set()
    unique_issues = []
    for issue in issues:
        key = (issue.get('issue_name'), issue.get('issue_location'))
        if key not in seen:
            seen.add(key)
            unique_issues.append(issue)
    return unique_issues