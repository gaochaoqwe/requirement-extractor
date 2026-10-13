"""
用户认证API路由 (FastAPI版本)
"""
from fastapi import APIRouter, Request, Response, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from .db.database import UserModel
import os
from datetime import datetime, timedelta
import jwt

router = APIRouter(prefix="/auth", tags=["认证"])

# JWT配置
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", 24))


# 请求模型
class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    display_name: str


def generate_token(user_id, username):
    """生成JWT token"""
    payload = {
        'user_id': user_id,
        'username': username,
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm='HS256')


def verify_token(token):
    """验证JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_session_user_id(request: Request) -> Optional[int]:
    """从session中获取用户ID"""
    return request.session.get('user_id')


@router.post('/login')
async def login(login_data: LoginRequest, request: Request):
    """用户登录"""
    try:
        username = login_data.username
        password = login_data.password
        
        if not username or not password:
            return JSONResponse(
                status_code=400,
                content={
                    'success': False,
                    'message': '用户名和密码不能为空'
                }
            )
        
        # 验证用户
        user = UserModel.authenticate(username, password)
        if not user:
            return JSONResponse(
                status_code=401,
                content={
                    'success': False,
                    'message': '用户名或密码错误'
                }
            )
        
        # 生成token
        token = generate_token(user['id'], user['username'])
        
        # 设置session
        request.session['user_id'] = user['id']
        request.session['username'] = user['username']
        request.session['display_name'] = user['display_name']
        
        return {
            'success': True,
            'message': '登录成功',
            'data': {
                'token': token,
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'display_name': user['display_name']
                }
            }
        }
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                'success': False,
                'message': f'登录失败: {str(e)}'
            }
        )


@router.post('/logout')
async def logout(request: Request):
    """用户登出"""
    try:
        request.session.clear()
        return {
            'success': True,
            'message': '登出成功'
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                'success': False,
                'message': f'登出失败: {str(e)}'
            }
        )


@router.get('/check')
async def check_auth(request: Request):
    """检查登录状态"""
    try:
        # 检查session
        user_id = request.session.get('user_id')
        if user_id:
            user = UserModel.get_user_by_id(user_id)
            if user:
                return {
                    'success': True,
                    'authenticated': True,
                    'user': {
                        'id': user['id'],
                        'username': user['username'],
                        'display_name': user['display_name']
                    }
                }
        
        # 检查token
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            payload = verify_token(token)
            if payload:
                user = UserModel.get_user_by_id(payload['user_id'])
                if user:
                    return {
                        'success': True,
                        'authenticated': True,
                        'user': {
                            'id': user['id'],
                            'username': user['username'],
                            'display_name': user['display_name']
                        }
                    }
        
        return {
            'success': True,
            'authenticated': False
        }
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                'success': False,
                'message': f'检查登录状态失败: {str(e)}'
            }
        )


@router.get('/users')
async def get_users(request: Request):
    """获取所有用户（需要登录）"""
    try:
        user_id = request.session.get('user_id')
        if not user_id:
            return JSONResponse(
                status_code=401,
                content={
                    'success': False,
                    'message': '未登录'
                }
            )
        
        users = UserModel.get_all_users()
        return {
            'success': True,
            'data': users
        }
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                'success': False,
                'message': f'获取用户列表失败: {str(e)}'
            }
        )


@router.post('/register')
async def register(register_data: RegisterRequest, request: Request):
    """用户注册（需登录，用于管理员在人员管理页新建账号）"""
    try:
        # 校验登录状态，避免未登录用户随意创建账号
        if not request.session.get('user_id'):
            return JSONResponse(
                status_code=401,
                content={
                    'success': False,
                    'message': '未登录，无法创建账号'
                }
            )

        username = register_data.username
        password = register_data.password
        display_name = register_data.display_name
        
        if not username or not password or not display_name:
            return JSONResponse(
                status_code=400,
                content={
                    'success': False,
                    'message': '用户名、密码和显示名不能为空'
                }
            )
        
        # 检查用户名是否已存在
        existing_user = UserModel.get_user_by_username(username)
        if existing_user:
            return JSONResponse(
                status_code=400,
                content={
                    'success': False,
                    'message': '用户名已存在'
                }
            )
        
        # 创建用户
        user = UserModel.create_user(username, password, display_name)
        if user:
            return {
                'success': True,
                'message': '注册成功',
                'data': {
                    'user': {
                        'id': user['id'],
                        'username': user['username'],
                        'display_name': user['display_name']
                    }
                }
            }
        else:
            return JSONResponse(
                status_code=500,
                content={
                    'success': False,
                    'message': '注册失败'
                }
            )
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                'success': False,
                'message': f'注册失败: {str(e)}'
            }
        )
