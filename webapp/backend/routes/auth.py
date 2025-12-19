#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
认证相关 API 路由
"""

from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from ..config import config
from ..services.auth_service import (
    Token,
    User,
    authenticate_user,
    create_access_token,
    get_current_user,
)


router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    """登录请求体"""
    username: str
    password: str


class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: User


# ============== API 端点 ==============

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    用户登录
    
    - **username**: 用户名
    - **password**: 密码
    
    成功返回访问令牌，失败返回 401 错误
    """
    user = authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=config.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=User(username=user.username)
    )


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """
    OAuth2 兼容的登录端点（用于 Swagger UI 测试）
    
    使用表单格式提交用户名和密码
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        expires_in=config.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get("/me", response_model=User)
async def get_current_user_info(current_user: Annotated[User, Depends(get_current_user)]):
    """
    获取当前登录用户信息
    
    需要在请求头中携带有效的 Bearer Token
    """
    return current_user


@router.post("/logout")
async def logout(current_user: Annotated[User, Depends(get_current_user)]):
    """
    用户登出
    
    注意：JWT 是无状态的，服务端不维护会话。
    登出操作由客户端删除本地存储的 token 完成。
    此端点主要用于确认用户仍然处于有效登录状态。
    """
    return {"message": "登出成功", "username": current_user.username}


@router.get("/verify")
async def verify_token(current_user: Annotated[User, Depends(get_current_user)]):
    """
    验证 Token 是否有效
    
    用于前端检查登录状态
    """
    return {"valid": True, "user": current_user}
