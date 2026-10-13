"""maintenance 模块鉴权依赖

复用 app.auth.routes.py 的逻辑：
- 优先使用 session
- fallback Bearer token

提供给 maintenance 模块路由使用。
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, Request

from app.auth.db.database import UserModel
from app.auth.routes import verify_token


def get_current_user(request: Request) -> dict:
    """获取当前登录用户；未登录则抛 401。"""

    # 1) session
    user_id = request.session.get("user_id")
    if user_id:
        user = UserModel.get_user_by_id(user_id)
        if user:
            return user

    # 2) token
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
        payload = verify_token(token)
        if payload:
            user = UserModel.get_user_by_id(payload.get("user_id"))
            if user:
                return user

    raise HTTPException(status_code=401, detail="未登录")


def require_user(user: dict = Depends(get_current_user)) -> dict:
    return user


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    username = str(user.get("username") or "")
    if username != "gaochao":
        raise HTTPException(status_code=403, detail="无权限")
    return user
