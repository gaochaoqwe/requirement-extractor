#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR模块配置文件
"""

# OCR数据提取配置
OCR_CONFIG = {
    # 是否使用传统算法进行数据提取
    # True: 使用传统算法（推荐，速度快，准确性高）
    # False: 使用AI算法（较慢，需要OLLAMA服务）
    "USE_TRADITIONAL_ALGORITHM": True,
    
    # 传统算法配置
    "TRADITIONAL_ALGORITHM": {
        # 是否启用调试日志
        "DEBUG_LOGGING": False,
        
        # 字段提取置信度阈值（未来扩展用）
        "CONFIDENCE_THRESHOLD": 0.8,
    },
    
    # AI算法配置（当USE_TRADITIONAL_ALGORITHM=False时使用）
    "AI_ALGORITHM": {
        # 最大重试次数
        "MAX_RETRY": 3,
        
        # 请求超时时间（秒）
        "TIMEOUT": 30,
        
        # 是否启用详细日志
        "VERBOSE_LOGGING": True,
    }
}

def get_ocr_config():
    """获取OCR配置"""
    return OCR_CONFIG

def use_traditional_algorithm():
    """是否使用传统算法"""
    return OCR_CONFIG.get("USE_TRADITIONAL_ALGORITHM", True)

def get_traditional_config():
    """获取传统算法配置"""
    return OCR_CONFIG.get("TRADITIONAL_ALGORITHM", {})

def get_ai_config():
    """获取AI算法配置"""
    return OCR_CONFIG.get("AI_ALGORITHM", {}) 