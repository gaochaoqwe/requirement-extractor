"""
文档审查-配置项模块配置文件

包含并发处理设置、审查规则和其他配置项
"""

# AI文档审查并发设置
AI_CONCURRENT_REQUESTS = 3  # AI模型并发请求数量，可以根据服务器能力调整

# 文档分块设置
DEFAULT_CHUNK_SIZE = 2000  # 默认文档分块大小（字符数）
MAX_CHUNK_SIZE = 3000     # 最大分块大小
MIN_CHUNK_SIZE = 500      # 最小分块大小

# 审查超时设置
AI_REQUEST_TIMEOUT = 60   # AI请求超时时间（秒）
CHUNK_PROCESS_TIMEOUT = 120  # 单个分块处理超时时间（秒）

# 重试设置
MAX_RETRY_ATTEMPTS = 3    # AI请求失败时的最大重试次数
RETRY_DELAY = 1          # 重试间隔（秒）

# 日志设置
LOG_LEVEL = "INFO"       # 日志级别
ENABLE_DEBUG_LOGS = True # 是否启用详细调试日志
ENABLE_AI_RESPONSE_LOG = True  # 是否记录AI响应内容

# 文档类型标识
DOC_TYPE_TASKBOOK = "taskBook"
DOC_TYPE_REQUIREMENTSPEC = "requirementSpec"

# 支持的文档类型
SUPPORTED_DOC_TYPES = [DOC_TYPE_TASKBOOK, DOC_TYPE_REQUIREMENTSPEC]

# 问题严重程度级别
ISSUE_LEVELS = [
    "严重问题",
    "重要问题", 
    "一般问题",
    "轻微问题"
]

# 默认问题级别
DEFAULT_ISSUE_LEVEL = "一般问题"

# 批注生成设置
ENABLE_ANNOTATION = True  # 是否生成批注版文档
ANNOTATION_TIMEOUT = 300  # 批注生成超时时间（秒）

# 数据库连接池设置
DB_CONNECTION_POOL_SIZE = 5  # 数据库连接池大小
DB_CONNECTION_TIMEOUT = 30   # 数据库连接超时时间（秒）

# 性能监控设置
ENABLE_PERFORMANCE_MONITORING = True  # 是否启用性能监控
PERFORMANCE_LOG_INTERVAL = 10         # 性能日志记录间隔（秒） 