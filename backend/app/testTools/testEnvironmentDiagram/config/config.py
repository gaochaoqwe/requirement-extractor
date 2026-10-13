from pathlib import Path

# 数据库配置
DATABASE_URL = f"sqlite:///{Path(__file__).parent.parent / 'test_environment.db'}"

# 上传目录配置
UPLOAD_DIR = Path("uploads/testTools/test_environment")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 输出目录配置
OUTPUT_DIR = Path("outputs/testTools/test_environment")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 日志配置
LOG_CONFIG = {
    "base_dir": Path(__file__).parent.parent / "logs",
    "max_file_size": 10 * 1024 * 1024,  # 10MB
    "backup_count": 5,
    "format": "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
}

# 测试环境图配置
ENVIRONMENT_CONFIG = {
    "default_devices": {
        "软件名称": "测试软件",
        "检测仪名称": "检测仪",
        "软件运行设备": "探测设备",
        "接口1": "RS422接口",
        "接口2": "以太网",
        "目标模拟器": "目标模拟器"
    },
    "device_functions": {
        "检测仪": "发送测试指令，同时监控软件状态。",
        "探测设备": "提供被测软件运行环境，运行被测软件。",
        "调试计算机": "调试代码，同时完成软件的编译、烧录及状态监控。",
        "目标模拟器": "模拟探测目标"
    }
} 