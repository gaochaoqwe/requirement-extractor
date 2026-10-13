"""
AI分析服务
"""
import os


def log_debug(msg):
    """记录调试日志"""
    try:
        # 获取后端目录路径
        base_dir = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.abspath(os.path.join(base_dir, '..', '..', '..', '..', '..'))
        log_dir = os.path.join(backend_dir, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, 'bg_debug.txt')
        
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        # 抑制日志错误
        pass
