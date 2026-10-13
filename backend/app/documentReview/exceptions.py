"""
自定义异常模块

定义应用程序中使用的自定义异常类
"""

class AppBaseError(Exception):
    """应用程序基础异常类"""
    default_message = "应用程序发生错误"
    status_code = 500
    
    def __init__(self, message=None, payload=None):
        super().__init__()
        self.message = message or self.default_message
        self.payload = payload or {}
    
    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        rv['status'] = 'error'
        rv['code'] = self.status_code
        return rv


class FileProcessingError(AppBaseError):
    """文件处理异常"""
    default_message = "文件处理失败"
    status_code = 400


class FileValidationError(AppBaseError):
    """文件验证异常"""
    default_message = "文件验证失败"
    status_code = 400


class DatabaseOperationError(AppBaseError):
    """数据库操作异常"""
    default_message = "数据库操作失败"
    status_code = 500


class AuthenticationError(AppBaseError):
    """认证异常"""
    default_message = "认证失败"
    status_code = 401


class AuthorizationError(AppBaseError):
    """授权异常"""
    default_message = "没有权限执行此操作"
    status_code = 403


class ResourceNotFoundError(AppBaseError):
    """资源未找到异常"""
    default_message = "请求的资源不存在"
    status_code = 404


class BadRequestError(AppBaseError):
    """错误请求异常"""
    default_message = "请求参数错误"
    status_code = 400


class ConflictError(AppBaseError):
    """资源冲突异常"""
    default_message = "资源已存在"
    status_code = 409


class RateLimitExceededError(AppBaseError):
    """请求频率限制异常"""
    default_message = "请求过于频繁，请稍后再试"
    status_code = 429


class ServiceUnavailableError(AppBaseError):
    """服务不可用异常"""
    default_message = "服务暂时不可用，请稍后再试"
    status_code = 503


def register_error_handlers(app):
    """
    注册错误处理器
    
    参数:
        app: Flask应用实例
    """
    @app.errorhandler(AppBaseError)
    def handle_app_error(error):
        """处理自定义应用异常"""
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response
    
    @app.errorhandler(404)
    def not_found_error(error):
        """处理404错误"""
        return jsonify({
            'status': 'error',
            'code': 404,
            'message': '请求的资源不存在'
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """处理500错误"""
        app.logger.error(f'服务器内部错误: {str(error)}', exc_info=True)
        return jsonify({
            'status': 'error',
            'code': 500,
            'message': '服务器内部错误，请稍后再试'
        }), 500
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """处理未捕获的异常"""
        app.logger.error(f'未处理的异常: {str(error)}', exc_info=True)
        return jsonify({
            'status': 'error',
            'code': 500,
            'message': '服务器发生意外错误'
        }), 500
