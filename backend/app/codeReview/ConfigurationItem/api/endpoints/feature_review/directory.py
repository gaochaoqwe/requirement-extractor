"""
功能审查 - 目录树API
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import os
from pathlib import Path

from ....db.deps import get_db
from ....db.repository import FileRepository

router = APIRouter()


def build_directory_tree(path: str, base_path: str = None) -> list:
    """
    递归构建目录树结构
    
    Args:
        path: 当前目录路径
        base_path: 基础路径，用于计算相对路径
        
    Returns:
        目录树列表
    """
    if base_path is None:
        base_path = path
    
    tree = []
    
    try:
        # 获取目录下的所有项
        items = sorted(os.listdir(path))
        
        for item in items:
            item_path = os.path.join(path, item)
            relative_path = os.path.relpath(item_path, base_path)
            
            # 跳过隐藏文件和特殊目录
            if item.startswith('.') or item == '__pycache__':
                continue
            
            if os.path.isdir(item_path):
                # 目录节点
                children = build_directory_tree(item_path, base_path)
                tree.append({
                    "name": item,
                    "path": relative_path.replace('\\', '/'),
                    "type": "directory",
                    "children": children
                })
            else:
                # 文件节点 - 只包含代码文件
                ext = os.path.splitext(item)[-1].lower()
                if ext in ['.c', '.cpp', '.h', '.hpp', '.cc', '.cxx', '.v', '.vhd', '.vhdl']:
                    tree.append({
                        "name": item,
                        "path": relative_path.replace('\\', '/'),
                        "type": "file"
                    })
    
    except Exception as e:
        print(f"读取目录失败: {path}, 错误: {e}")
    
    return tree


@router.get("/directory/{file_id}")
async def get_directory_tree(file_id: int, db: Session = Depends(get_db)):
    """
    获取代码库的目录树结构
    
    Args:
        file_id: 代码库文件ID
        
    Returns:
        {
            "file_id": 123,
            "file_name": "xxx.zip",
            "tree": [
                {
                    "name": "src",
                    "path": "src",
                    "type": "directory",
                    "children": [...]
                },
                {
                    "name": "main.c",
                    "path": "main.c",
                    "type": "file"
                }
            ]
        }
    """
    try:
        # 获取文件记录
        file_repo = FileRepository(db)
        file_record = file_repo.get_file(file_id)
        
        if not file_record:
            raise HTTPException(status_code=404, detail="代码库文件不存在")
        
        # 获取解压路径
        extract_path = file_record.extract_path
        
        if not os.path.exists(extract_path):
            raise HTTPException(status_code=404, detail="代码库解压路径不存在")
        
        # 构建目录树
        tree = build_directory_tree(extract_path)
        
        return {
            "file_id": file_id,
            "file_name": file_record.file_name,
            "tree": tree
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取目录树失败: {str(e)}")


@router.get("/file/{file_id}/content")
async def get_file_content(file_id: int, file_path: str, db: Session = Depends(get_db)):
    """
    获取指定文件的内容
    
    Args:
        file_id: 代码库文件ID
        file_path: 文件相对路径
        
    Returns:
        {
            "file_path": "src/main.c",
            "content": "文件内容..."
        }
    """
    try:
        # 获取文件记录
        file_repo = FileRepository(db)
        file_record = file_repo.get_file(file_id)
        
        if not file_record:
            raise HTTPException(status_code=404, detail="代码库文件不存在")
        
        # 构建完整文件路径
        full_path = os.path.join(file_record.extract_path, file_path)
        
        # 安全检查：确保文件在允许的目录内
        extract_path_abs = os.path.abspath(file_record.extract_path)
        full_path_abs = os.path.abspath(full_path)
        
        if not full_path_abs.startswith(extract_path_abs):
            raise HTTPException(status_code=403, detail="非法的文件路径")
        
        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 读取文件内容
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # 尝试其他编码
            with open(full_path, 'r', encoding='gbk') as f:
                content = f.read()
        
        return {
            "file_path": file_path,
            "content": content
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取文件内容失败: {str(e)}")

