"""
后端应用入口文件 (FastAPI版本)

负责：
1. 初始化应用实例
2. 配置中间件
3. 挂载子应用
4. 启动ASGI服务器
"""
import os
import sys
import logging
import json
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional, Union

# === 屏蔽 uvicorn/asyncio socket 报错日志 ===
class IgnoreSocketErrorFilter(logging.Filter):
    def filter(self, record):
        msg = str(record.getMessage())
        # 过滤掉 socket 相关的 int() 报错
        return "invalid literal for int() with base 10" not in msg

logging.getLogger("uvicorn.error").addFilter(IgnoreSocketErrorFilter())
logging.getLogger("asyncio").addFilter(IgnoreSocketErrorFilter())
# ======================================

# 确保导入路径包含当前目录
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入日志工具模块
from app.utils.log_utils import setup_logger, disable_log_pattern

# === 自动创建所有运行所需目录，避免 FileNotFoundError ===
BASE_DIR = Path(__file__).parent
required_dirs = [
    BASE_DIR / 'logs',
    BASE_DIR / 'logs' / 'prompts',
    BASE_DIR / 'uploads',
    BASE_DIR / 'uploads' / 'regression',
    BASE_DIR / 'uploads' / 'configuration_item',
    BASE_DIR / 'uploads' / 'configuration_item' / 'requirement_specs',
    BASE_DIR / 'uploads' / 'configuration_item' / 'task_books',
]
for d in required_dirs:
    os.makedirs(d, exist_ok=True)

# 加载环境变量
from dotenv import load_dotenv
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

# 添加项目根目录到 Python 路径
sys.path.append(str(Path(__file__).parent))

# FastAPI 相关导入
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute, APIRouter
import uvicorn
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware
import time
import json
from typing import Optional, Dict, Any, List, Union, Callable
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.datastructures import Headers, FormData
from starlette.middleware.wsgi import WSGIMiddleware

# 应用配置
APP_VERSION = "1.0.0"

# 检查模块可用性
FLASK_APPS_AVAILABLE = False
PROJECTS_API_AVAILABLE = True
CONFIG_ITEM_MODULE_AVAILABLE = True
CODE_REVIEW_MODULE_AVAILABLE = True
CODE_REVIEW_REGRESSION_MODULE_AVAILABLE = True

# 尝试导入各个模块（已移除对 Flask 的依赖）

# 数据库初始化函数（Code Review已迁移到PostgreSQL，无需init_db）
init_code_review_db = lambda: logger.info("Code Review已使用PostgreSQL，请运行 init_postgresql.py 初始化数据库")

try:
    from app.staticAnalysis.normalModeC.database import init_db as init_static_analysis_db
except ImportError:
    init_static_analysis_db = lambda: None

# 配置日志：同时输出到文件和终端
def configure_root_logger():
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    log_path = BASE_DIR / 'logs' / 'app.log'
    log_path.parent.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    for handler in list(root_logger.handlers):
        handler.close()
        root_logger.removeHandler(handler)

    # 文件日志处理器
    file_handler = logging.FileHandler(str(log_path), encoding='utf-8')
    file_handler.setFormatter(logging.Formatter(log_format))
    root_logger.addHandler(file_handler)
    
    # 控制台日志处理器（输出到终端）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(log_format))
    root_logger.addHandler(console_handler)
    
    root_logger.setLevel(log_level)

    # 确保uvicorn和httpx日志也走根日志器
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "httpx"):
        logger_ref = logging.getLogger(name)
        logger_ref.handlers.clear()
        logger_ref.propagate = True


configure_root_logger()
logger = logging.getLogger(__name__)

# 导入tree-sitter语言库构建工具
from tree_sitter import Language

class RequestLoggingMiddleware:
    """详细的请求日志中间件 (FastAPI版本)"""
    
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
            
        start_time = time.time()
        request = Request(scope, receive)
        
        # 检查是否是进度查询请求，如果是，则完全不记录日志
        url_path = request.url.path
        is_progress_query = ('/progress' in url_path or '/task_progress' in url_path or '/task-status' in url_path) and request.method == 'GET'
        
        # 只对非进度查询请求记录详细日志
        if not is_progress_query:
            # 记录请求信息
            logger.info(f"\n{'='*50}")
            logger.info(f"[REQUEST] {request.method} {request.url}")
            logger.info(f"[HEADERS] {dict(request.headers)}")
        
        # 记录查询参数
        if request.query_params and not is_progress_query:
            logger.info(f"[QUERY PARAMS] {dict(request.query_params)}")
        
        # 记录请求体
        body = b''
        receive_ = request.receive
        
        async def receive_wrapper():
            nonlocal body
            message = await receive_()
            if message.get('type') == 'http.request':
                body += message.get('body', b'')
                if not message.get('more_body', False) and not is_progress_query:
                    try:
                        body_str = body.decode('utf-8')
                        if body_str:
                            logger.info(f"[REQUEST BODY] {body_str}")
                            
                            # 尝试解析为JSON
                            try:
                                json_body = json.loads(body_str)
                                logger.info("[PARSED JSON BODY]")
                                logger.info(json.dumps(json_body, indent=2, ensure_ascii=False))
                            except json.JSONDecodeError:
                                logger.info("[BODY IS NOT JSON]")
                                
                    except Exception as e:
                        logger.warning(f"Failed to decode request body: {e}")
            return message
        
        # 处理响应
        response_started = False
        response_headers = {}
        
        async def send_wrapper(message):
            nonlocal response_started, response_headers
            
            if message['type'] == 'http.response.start':
                response_started = True
                response_headers = dict(message.get('headers', []))
                if not is_progress_query:
                    logger.info(f"\n[RESPONSE] Status: {message.get('status', 'N/A')}")
                    logger.info(f"[RESPONSE HEADERS] {response_headers}")
            
            elif message['type'] == 'http.response.body':
                if not response_started:
                    return
                    
                body = message.get('body', b'')
                if body and not is_progress_query:
                    try:
                        body_str = body.decode('utf-8')
                        logger.info("[RESPONSE BODY]")
                        logger.info(body_str)
                        
                        # 尝试解析为JSON
                        try:
                            json_body = json.loads(body_str)
                            logger.info("[PARSED JSON RESPONSE]")
                            logger.info(json.dumps(json_body, indent=2, ensure_ascii=False))
                        except json.JSONDecodeError:
                            logger.info("[RESPONSE BODY IS NOT JSON]")
                            
                    except Exception as e:
                        logger.warning(f"Failed to decode response body: {e}")
            
            await send(message)
        
        # 处理请求
        try:
            await self.app(scope, receive_wrapper, send_wrapper)
            process_time = (time.time() - start_time) * 1000
            
            # 只为非进度查询记录响应时间
            if not is_progress_query:
                logger.info(f"[RESPONSE TIME] {process_time:.2f}ms")
                logger.info(f"{'='*50}\n")
            
        except Exception as e:
            logger.error(f"Request processing failed: {str(e)}", exc_info=True)
            raise


def setup_global_logging():
    """在应用启动时设置全局日志配置"""
    logs_dir = os.path.join(BASE_DIR, 'logs')
    
    # 配置主要的日志器
    main_logger = setup_logger("__main__", os.path.join(logs_dir, 'main.log'))
    wordllm_logger = setup_logger("wordllm", os.path.join(logs_dir, 'wordllm.log'))
    regression_logger = setup_logger("app.documentReview.Regression", os.path.join(logs_dir, 'regression.log'))
    config_item_logger = setup_logger("app.documentReview.ConfigurationItem", os.path.join(logs_dir, 'config_item.log'))
    
    # 禁用某些重复频繁的日志
    disable_log_pattern("[进度查询]")
    disable_log_pattern("创建OpenAI客户端")
    disable_log_pattern("最终API基础URL")
    
    main_logger.info("全局日志系统初始化完成")
    return main_logger


def create_fastapi_app() -> FastAPI:
    """
    创建和配置主 FastAPI 应用
    """
    # 初始化全局日志系统
    logger = setup_global_logging()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """启动时执行幂等数据库检查与补字段"""
        try:
            from app.codeReview.ConfigurationItem.db.database import check_database as check_config_review_database
            check_config_review_database()
            logger.info("配置项代码审查数据库检查完成")
        except Exception as e:
            logger.error(f"配置项代码审查数据库检查失败: {e}", exc_info=True)
        yield
    
    # 创建 FastAPI 应用实例
    app = FastAPI(
        title="需求信息提取服务",
        description="提供需求信息提取和项目管理功能",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    
    # 配置跨域资源共享 (CORS)
    # 注意：当使用 allow_credentials=True 时，不能使用通配符 "*"
    cors_allow_origins_env = os.getenv("CORS_ALLOW_ORIGINS", "").strip()
    cors_allow_origins_from_env = [o.strip() for o in cors_allow_origins_env.split(",") if o.strip()] if cors_allow_origins_env else []
    allow_origins = (cors_allow_origins_from_env or [
        "http://localhost:5173",  # Vite开发服务器
        "http://localhost:5174",
        "http://localhost:3000",
        "http://localhost:8085",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8085",
    ])
    print(f"CORS allow_origins 生效列表: {allow_origins}")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,  # 允许携带凭证（cookies, session）
        allow_methods=["*"],  # 允许所有方法
        allow_headers=["*"],  # 允许所有头
    )
    
    # 添加Session中间件（用于用户认证）
    app.add_middleware(
        SessionMiddleware,
        secret_key=os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production"),
        session_cookie="session_id",
        max_age=86400,  # 24小时
        same_site="lax",
        https_only=False  # 开发环境设为False，生产环境应设为True
    )
    
    # 添加请求日志中间件
    app.add_middleware(RequestLoggingMiddleware)
    
    # 根路径路由
    @app.get("/")
    async def welcome() -> Dict[str, Any]:
        """根路径处理器，返回欢迎信息和API文档链接"""
        return {
            "message": "欢迎使用需求提取系统API",
            "version": "1.0.0",
            "documentation": f"http://{os.getenv('HOST', '0.0.0.0')}:{os.getenv('PORT', '5002')}/docs",
            "endpoints": {
                "document_review": "/api",
                "regression": "/regression",
                "project_management": "/api/projects"
            }
        }
    
    # 健康检查端点
    @app.get("/health")
    async def health_check() -> Dict[str, str]:
        """健康检查"""
        return {
            "status": "healthy",
            "version": "1.0.0"
        }
    
    return app


def setup_routers(app: FastAPI) -> None:
    """
    设置和挂载各个子应用/路由器
    """
    # 创建API子路由器
    api_router = APIRouter(prefix="/api")

    # 挂载项目管理API路由到 /api
    if PROJECTS_API_AVAILABLE:
        try:
            # 项目管理模块
            from app.projectManagement.api import router as project_api_router
            api_router.include_router(project_api_router, prefix="")
            logger.info("已挂载项目管理API路由到/api")
        except Exception as e:
            logger.error(f"挂载项目管理API路由失败: {e}", exc_info=True)

    # 挂载配置项相关模块
    if CONFIG_ITEM_MODULE_AVAILABLE:
        try:
            # 配置项审查相关模块
            from app.documentReview.ConfigurationItem.upload.router import router as upload_router
            from app.documentReview.ConfigurationItem.reviewer.router import router as review_router
            from app.documentReview.ConfigurationItem.downloadDocument.router import router as download_router
            
            # 文件上传
            api_router.include_router(upload_router, prefix="/documentReview/ConfigurationItem/upload")
            logger.info("已挂载文件上传模块到/api/documentReview/ConfigurationItem/upload")
        except Exception as e:
            logger.error(f"挂载配置项上传模块失败: {e}", exc_info=True)
        
        try:
            # AI审查
            api_router.include_router(review_router, prefix="/documentReview/ConfigurationItem/reviewer")
            logger.info("已挂载AI审查模块到/api/documentReview/ConfigurationItem/reviewer")
        except Exception as e:
            logger.error(f"挂载配置项审查模块失败: {e}", exc_info=True)
        
        try:
            # 下载结果
            api_router.include_router(download_router, prefix="/documentReview/ConfigurationItem/download")
            logger.info("已挂载下载模块到/api/documentReview/ConfigurationItem/download")
        except Exception as e:
            logger.error(f"挂载配置项下载模块失败: {e}", exc_info=True)

    # 挂载AI代码审查模块（配置项测试）
    if CODE_REVIEW_MODULE_AVAILABLE:
        try:
            # 代码审查相关模块
            from app.codeReview.ConfigurationItem.api.router import code_review_router as code_review_router_actual
            api_router.include_router(code_review_router_actual, prefix="/codeReview")
            logger.info("已挂载AI代码审查模块（配置项测试）到/api/codeReview")
        except Exception as e:
            logger.error(f"挂载AI代码审查模块（配置项测试）失败: {e}", exc_info=True)
    
    # 挂载AI代码审查模块（新回归测试）
    try:
        from app.codeReview.RegressionTest.api.router import code_review_router as regression_test_router
        api_router.include_router(regression_test_router, prefix="/codeReview/regressionTest")
        logger.info("已挂载AI代码审查模块（新回归测试）到/api/codeReview/regressionTest")
    except Exception as e:
        logger.error(f"挂载AI代码审查模块（新回归测试）失败: {e}", exc_info=True)

    # 挂载AI回归代码审查模块
    # 在函数内部导入，避免全局导入可能的循环依赖
    try:
        # 尝试直接导入各个端点
        from app.codeReview.Regression.api.endpoints.upload_file import router as regression_upload_router
        from app.codeReview.Regression.api.endpoints.start_analysis import router as regression_start_router
        from app.codeReview.Regression.api.endpoints.task_progress import router as regression_progress_router
        from app.codeReview.Regression.api.endpoints.download_result import router as regression_download_router
        from app.codeReview.Regression.api.endpoints.codemap import router as regression_codemap_router
        
        # 直接挂载各个端点
        api_router.include_router(regression_upload_router, prefix="/codeReview/regression")
        api_router.include_router(regression_start_router, prefix="/codeReview/regression")
        api_router.include_router(regression_progress_router, prefix="/codeReview/regression")
        api_router.include_router(regression_download_router, prefix="/codeReview/regression")
        api_router.include_router(regression_codemap_router, prefix="/codeReview/regression")
        
        # 同时挂载到直接的 /regression 前缀下，供前端访问
        app.include_router(regression_codemap_router, prefix="/regression")
        
        logger.info("已直接挂载AI回归代码审查各个端点到/api/codeReview/regression")
        logger.info("已挂载代码地图端点到/regression")
    except Exception as e:
        logger.error(f"挂载AI回归代码审查端点失败: {e}", exc_info=True)

    # ------------------- Regression 回归测试模块挂载 -------------------
    try:
        from app.documentReview.Regression.upload.router import router as regression_upload_router
        from app.documentReview.Regression.reviewer.router import router as regression_reviewer_router
        from app.documentReview.Regression.downloadDocument.router import router as regression_download_router
        
        # 挂载上传模块
        api_router.include_router(regression_upload_router, prefix="/documentReview/Regression/upload")
        logger.info("已挂载回归测试文件上传模块到/api/documentReview/Regression/upload")
            
        # 挂载审查模块
        api_router.include_router(regression_reviewer_router, prefix="/documentReview/Regression/reviewer")
        logger.info("已挂载回归测试AI审查模块到/api/documentReview/Regression/reviewer")
            
        # 挂载下载模块
        api_router.include_router(regression_download_router, prefix="/documentReview/Regression/download")
        logger.info("已挂载回归测试下载模块到/api/documentReview/Regression/download")
    except Exception as e:
        logger.error(f"挂载回归测试Regression模块失败: {e}")
    # ------------------------------------------------------------------

    # ------------------- 文档审查测试工具模块挂载 -------------------
    try:
        from app.documentReview.testTools.documentAnnotations2problemsSheet.api.api import router as doc_annotations_router
        api_router.include_router(doc_annotations_router, prefix="/documentReview/testTools/document-annotations-to-problems")
        logger.info("已挂载文档审查测试工具模块到/api/documentReview/testTools/document-annotations-to-problems")
    except Exception as e:
        logger.error(f"挂载文档审查测试工具模块失败: {e}", exc_info=True)
    # ------------------------------------------------------------------

    # ------------------- 静态分析模块挂载 -------------------
    try:
        print("[DEBUG] 开始挂载静态分析模块...")
        from app.staticAnalysis import static_analysis_router
        api_router.include_router(static_analysis_router, prefix="/staticAnalysis")
        logger.info("已挂载静态分析模块到/api/staticAnalysis")
        print("[DEBUG] 静态分析模块挂载成功")
    except Exception as e:
        error_msg = f"挂载静态分析模块失败: {e}"
        print(f"[DEBUG ERROR] {error_msg}")
        import traceback
        print(f"[DEBUG ERROR] 详情: {traceback.format_exc()}")
        logger.error(error_msg, exc_info=True)
    # ------------------------------------------------------------------

    # ------------------- 动态测试模块挂载 -------------------
    try:
        from app.danamicTest.ConfigurationItem.api.configuration_item import router as config_item_router
        api_router.include_router(config_item_router, prefix="/dynamic-test/configuration-item")
        logger.info("已挂载配置项测试模块到/api/dynamic-test/configuration-item")
    except Exception as e:
        logger.error(f"挂载配置项测试模块失败: {e}", exc_info=True)

    try:
        from app.danamicTest.Regression.api.regression import router as regression_test_router
        api_router.include_router(regression_test_router, prefix="/dynamic-test/regression")
        logger.info("已挂载回归测试模块到/api/dynamic-test/regression")
    except Exception as e:
        logger.error(f"挂载回归测试模块失败: {e}", exc_info=True)
    # ------------------------------------------------------------------

    # ------------------- 数据库管理模块挂载 -------------------
    try:
        from app.databaseManage import router as database_manage_router
        api_router.include_router(database_manage_router, prefix="/database")
        logger.info("已挂载数据库管理模块到/api/database")
    except Exception as e:
        logger.error(f"挂载数据库管理模块失败: {e}", exc_info=True)
    # ------------------------------------------------------------------

    # ------------------- 测试工具模块挂载 -------------------
    try:
        from app.testTools.router import router as test_tools_router
        app.include_router(test_tools_router, prefix="/api/test-tools")
        logger.info("已挂载测试工具模块到/api/test-tools")
    except Exception as e:
        logger.error(f"挂载测试工具模块失败: {e}", exc_info=True)
    # ------------------------------------------------------------------

    # ------------------- 账户认证模块挂载 -------------------
    try:
        from app.auth.routes import router as auth_router
        api_router.include_router(auth_router, prefix="")
        logger.info("已挂载账户认证模块到/api/auth")
    except Exception as e:
        logger.error(f"挂载账户认证模块失败: {e}", exc_info=True)
    # ------------------------------------------------------------------

    # ------------------- 维护模块挂载 -------------------
    try:
        from app.maintenance.db.database import init_database as init_maintenance_db
        from app.maintenance.api.router import router as maintenance_router

        # 幂等建表，避免首次运行没有表导致报错
        init_maintenance_db()

        api_router.include_router(maintenance_router, prefix="")
        logger.info("已挂载维护模块到/api/maintenance")
    except Exception as e:
        logger.error(f"挂载维护模块失败: {e}", exc_info=True)
    # ------------------------------------------------------------------

    # 将API路由器挂载到主应用
    app.include_router(api_router)

    # 不再挂载 Flask 回归测试应用


def print_routes(app: FastAPI) -> None:
    """
    打印所有已注册的路由
    """
    logger.info("\n=== 可用路由 ===")
    
    def print_fastapi_routes(app, prefix=""):
        """递归打印FastAPI路由"""
        from fastapi import FastAPI, APIRouter
        from starlette.applications import Starlette
        for route in app.routes:
            path = prefix + getattr(route, "path", "")
            # 处理APIRoute
            if isinstance(route, APIRoute):
                methods = ",".join(route.methods)
                name = route.name
                logger.info(f"{methods:20} {path:40} -> {name}")
            # 处理挂载的子应用
            elif hasattr(route, "app"):
                sub_app = route.app
                if isinstance(sub_app, (FastAPI, Starlette, APIRouter)):
                    print_fastapi_routes(sub_app, prefix=prefix + getattr(route, "path", ""))
    
    print_fastapi_routes(app)
    logger.info("")


def main() -> None:
    """
    主函数，创建应用并启动服务器
    """
    # 创建FastAPI应用
    app = create_fastapi_app()
    
    # 挂载路由器和子应用
    setup_routers(app)
    
    # 打印所有路由
    print_routes(app)
    
    # 启动配置
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', '5002'))
    debug = os.getenv('FLASK_DEBUG', '0').lower() in ('1', 'true', 'yes')
    
    logger.info(f"\n启动服务: http://{host}:{port}")
    logger.info(f"调试模式: {'开启' if debug else '关闭'}")
    logger.info(f"API文档: http://{host}:{port}/docs")
    logger.info("按 Ctrl+C 退出\n")
    
    # 启动Uvicorn服务器
    uvicorn.run(
        app,  # 直接传 app 对象，兼容 PyInstaller 打包
        host=host,
        port=port,
        reload=debug,
        log_level="info" if debug else "error"
    )


# 全局应用实例，供Uvicorn引用
app = create_fastapi_app()

setup_routers(app)

if __name__ == '__main__':
    # Code Review模块已迁移到PostgreSQL，请先运行 init_postgresql.py 初始化数据库
    logger.info("="*70)
    logger.info("  Code Review模块使用PostgreSQL数据库".center(70))
    logger.info("="*70)
    logger.info("如需初始化数据库，请运行:")
    logger.info("  cd backend/app/codeReview/ConfigurationItem/db")
    logger.info("  python init_postgresql.py")
    logger.info("="*70)
    
    # 初始化回归测试代码审查模块的数据库表
    try:
        from app.codeReview.Regression.db.database import init_db as init_regression_db
        init_regression_db()
        logger.info("回归测试代码审查数据库初始化成功")
    except Exception as e:
        logger.error(f"回归测试代码审查数据库初始化失败: {e}")

    # 初始化Static Analysis模块的数据库表
    init_static_analysis_db()
    
    # 初始化数据库管理模块的数据库表
    try:
        from app.databaseManage import init_db as init_database_manage_db
        init_database_manage_db()
        logger.info("数据库管理模块数据库初始化成功")
    except Exception as e:
        logger.error(f"数据库管理模块数据库初始化失败: {e}")
    
    # 初始化项目管理模块的数据库表
    try:
        from app.projectManagement.db_init import init_project_db
        init_project_db()
        logger.info("项目管理模块数据库初始化成功")
    except Exception as e:
        logger.error(f"项目管理模块数据库初始化失败: {e}")
    
    main()
