#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FastAPI 应用入口
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from .config import config
from .routes import analytics_router, auth_router


# 创建 FastAPI 应用
app = FastAPI(
    title=config.API_TITLE,
    version=config.API_VERSION,
    description="AwesomeTrader 账户收益分析 API - 提供收益率、风控指标、基准对比等分析功能",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 注册路由
app.include_router(auth_router, prefix=config.API_PREFIX)
app.include_router(analytics_router, prefix=config.API_PREFIX)


@app.get("/", tags=["Health"])
async def root():
    """健康检查接口"""
    return {
        "status": "ok",
        "service": config.API_TITLE,
        "version": config.API_VERSION,
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info(f"启动 {config.API_TITLE} v{config.API_VERSION}")
    logger.info(f"API 文档: http://localhost:8000/docs")
    
    # 预加载账户数据
    try:
        from .services.data_loader import data_loader
        data_loader.load_account_data()
        logger.success("账户数据预加载成功")
        
        # 启动文件监控，自动检测 account.csv 变更
        data_loader.start_file_watcher()
    except Exception as e:
        logger.warning(f"账户数据预加载失败: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("关闭服务...")
    
    # 停止文件监控
    try:
        from .services.data_loader import data_loader
        data_loader.stop_file_watcher()
    except Exception as e:
        logger.warning(f"停止文件监控失败: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "webapp.backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )

