#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
用户认证服务
提供 JWT 令牌生成、验证和用户认证功能
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from ..config import config

# OAuth2 密码认证方案
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{config.API_PREFIX}/auth/login")


# ============== 数据模型 ==============

class Token(BaseModel):
    """访问令牌响应"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # 过期时间（秒）


class TokenData(BaseModel):
    """令牌数据"""
    username: Optional[str] = None


class User(BaseModel):
    """用户信息"""
    username: str


class UserInDB(User):
    """数据库中的用户（包含密码哈希）"""
    hashed_password: str


# ============== 用户数据存储（简单实现，生产环境应使用数据库）==============

def get_user(username: str) -> Optional[UserInDB]:
    """获取用户信息"""
    if username == config.DEFAULT_USERNAME:
        return UserInDB(
            username=config.DEFAULT_USERNAME,
            hashed_password=config.DEFAULT_PASSWORD_HASH
        )
    return None


# ============== 密码验证 ==============

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


# ============== 用户认证 ==============

def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """验证用户名和密码"""
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


# ============== JWT 令牌 ==============

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建 JWT 访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[TokenData]:
    """解码 JWT 访问令牌"""
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return TokenData(username=username)
    except JWTError:
        return None


# ============== 依赖注入 ==============

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """获取当前登录用户（用于需要认证的路由）"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_data = decode_access_token(token)
    if token_data is None:
        raise credentials_exception
    user = get_user(token_data.username)
    if user is None:
        raise credentials_exception
    return User(username=user.username)


# ============== 可选认证依赖（用于可选认证的路由）==============

async def get_current_user_optional(token: str = Depends(oauth2_scheme)) -> Optional[User]:
    """获取当前用户（可选，不强制要求登录）"""
    try:
        return await get_current_user(token)
    except HTTPException:
        return None
