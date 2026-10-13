"""
清理旧的日志文件夹结构

此脚本用于清理使用旧格式（task_{task_id}_{timestamp}）的日志文件夹
新格式统一使用 task_{task_id}，包含 logs/ 和 memory/ 子文件夹
"""
from pathlib import Path
import re
import shutil

def cleanup_old_log_folders():
    """清理旧格式的日志文件夹"""
    
    # 获取logs目录
    logs_dir = Path(__file__).parent.parent / "logs"
    if not logs_dir.exists():
        print("Logs目录不存在")
        return
    
    # 正则表达式匹配旧格式：task_{task_id}_{timestamp}
    old_format_pattern = re.compile(r'^task_(\d+)_\d{8}_\d{6}$')
    
    cleaned_count = 0
    for folder in logs_dir.iterdir():
        if not folder.is_dir():
            continue
        
        # 检查是否是旧格式
        match = old_format_pattern.match(folder.name)
        if match:
            task_id = match.group(1)
            new_folder_name = f"task_{task_id}"
            new_folder_path = logs_dir / new_folder_name
            
            # 如果新格式文件夹不存在，重命名旧文件夹
            if not new_folder_path.exists():
                print(f"迁移: {folder.name} -> {new_folder_name}")
                
                # 创建新格式文件夹结构
                new_folder_path.mkdir(exist_ok=True)
                logs_subfolder = new_folder_path / "logs"
                logs_subfolder.mkdir(exist_ok=True)
                
                # 移动所有.log文件到logs子文件夹
                for log_file in folder.glob("*.log"):
                    shutil.move(str(log_file), str(logs_subfolder / log_file.name))
                
                # 如果有memory文件夹，也移动过去
                old_memory = folder / "memory"
                if old_memory.exists():
                    shutil.move(str(old_memory), str(new_folder_path / "memory"))
                
                # 移动其他文件（如view_logs.py）
                for other_file in folder.iterdir():
                    if other_file.is_file():
                        shutil.move(str(other_file), str(new_folder_path / other_file.name))
                
                # 删除旧文件夹
                shutil.rmtree(folder)
                cleaned_count += 1
            else:
                # 新格式文件夹已存在，删除旧文件夹
                print(f"删除重复: {folder.name} (新格式 {new_folder_name} 已存在)")
                shutil.rmtree(folder)
                cleaned_count += 1
    
    print(f"\n清理完成！共处理 {cleaned_count} 个旧格式文件夹")
    
    # 显示当前logs目录结构
    print("\n当前日志目录结构:")
    for folder in sorted(logs_dir.iterdir()):
        if folder.is_dir() and folder.name.startswith('task_'):
            print(f"  {folder.name}/")
            logs_subfolder = folder / "logs"
            if logs_subfolder.exists():
                log_count = len(list(logs_subfolder.glob("*.log")))
                print(f"    ├── logs/ ({log_count} 个日志文件)")
            memory_subfolder = folder / "memory"
            if memory_subfolder.exists():
                mem_count = len(list(memory_subfolder.glob("*.json")))
                print(f"    └── memory/ ({mem_count} 个记忆文件)")

if __name__ == "__main__":
    cleanup_old_log_folders()

