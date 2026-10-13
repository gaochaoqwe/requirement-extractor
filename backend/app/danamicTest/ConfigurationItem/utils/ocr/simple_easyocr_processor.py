#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import base64
import io
from PIL import Image
from pathlib import Path
import tempfile
import numpy as np

class SimpleEasyOCRProcessor:
    """简化的EasyOCR处理器，避免复杂的依赖导入"""
    
    def __init__(self):
        """初始化EasyOCR处理器"""
        self.ocr = None
        self._init_ocr()
    
    def _init_ocr(self):
        """初始化EasyOCR"""
        try:
            # 尝试导入EasyOCR
            try:
                import easyocr
            except ImportError as e:
                self.ocr = "unavailable"
                return

            try:
                # 初始化EasyOCR Reader，支持中文和英文
                self.ocr = easyocr.Reader(
                    ['ch_sim', 'en'],  # 简体中文和英文
                    gpu=False,  # 使用CPU，更稳定
                    verbose=False  # 减少输出
                )

            except Exception as init_error:
                self.ocr = "unavailable"

        except Exception as e:
            self.ocr = "unavailable"
    
    def process_image_from_base64(self, base64_data: str) -> str:
        """
        处理base64编码的图片，进行OCR识别
        
        Args:
            base64_data (str): base64编码的图片数据
            
        Returns:
            str: OCR识别的文本结果
        """
        try:
            # 解码base64数据
            if ',' in base64_data:
                # 移除data:image/xxx;base64,前缀
                base64_data = base64_data.split(',')[1]
            
            image_data = base64.b64decode(base64_data)
            
            # 转换为PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            return self._process_pil_image(image)
            
        except Exception as e:
            print(f"处理base64图片失败: {str(e)}")
            return ""
    
    def process_image_file(self, image_path: str) -> str:
        """
        处理图片文件，进行OCR识别
        
        Args:
            image_path (str): 图片文件路径
            
        Returns:
            str: OCR识别的文本结果
        """
        try:
            if not os.path.exists(image_path):
                print(f"图片文件不存在: {image_path}")
                return ""
            
            # 使用PIL打开图片
            image = Image.open(image_path)
            
            return self._process_pil_image(image)
            
        except Exception as e:
            print(f"处理图片文件失败: {str(e)}")
            return ""
    
    def _process_pil_image(self, image: Image.Image) -> str:
        """
        处理PIL图片对象
        
        Args:
            image (Image.Image): PIL图片对象
            
        Returns:
            str: OCR识别的文本结果
        """
        try:
            print("开始处理PIL图片对象")
            print(f"当前OCR状态: {type(self.ocr)} - {self.ocr}")
            
            if self.ocr is None:
                print("OCR未初始化")
                return ""
            elif isinstance(self.ocr, str):
                if self.ocr == "unavailable":
                    print("OCR功能不可用")
                    return ""
                else:
                    print(f"未知的OCR状态: {self.ocr}")
                    return ""
            
            # 转换为RGB模式（EasyOCR需要）
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            return self._use_easyocr(image)
                
        except Exception as e:
            print(f"OCR处理失败: {str(e)}")
            return ""
    
    def _use_easyocr(self, image: Image.Image) -> str:
        """使用EasyOCR进行识别"""
        try:
            # 将PIL图像转换为numpy数组
            img_array = np.array(image)
            
            # 进行OCR识别
            result = self.ocr.readtext(img_array, detail=1, paragraph=False)
            print(f"EasyOCR原始结果类型: {type(result)}, 检测到文本块数量: {len(result) if result else 0}")
            
            # 提取文本
            texts = []
            if result:
                print(f"EasyOCR原始结果类型: {type(result)}, 检测到文本块数量: {len(result)}")
                
                for detection in result:
                    # EasyOCR返回格式: [bbox, text, confidence]
                    # bbox: 四个角点坐标
                    # text: 识别的文本
                    # confidence: 置信度
                    if len(detection) >= 2:
                        bbox, text = detection[0], detection[1]
                        confidence = detection[2] if len(detection) > 2 else 1.0
                        
                        # 🔍 显示所有检测到的文本（调试用）
                        print(f"检测到文本: '{text}' (置信度: {confidence:.3f})")
                        
                        # 🎯 智能置信度过滤策略
                        should_include = False
                        
                        # 前端必需字段：绝对不能被过滤（包含OCR常见误识别变体）
                        essential_fields = [
                            '申请部门', '申请音门', '申请剖门',  # "部"常被误识别为"音"或"剖"
                            '申请人', '申请^', '申请A',  # "人"常被误识别为"^"或"A"
                            '项目主管', 
                            '主任设计师', '主任设汁师', '主任设让师',  # "计"常被误识别
                            '项目主管总师', '项目主管总帅', '项目主管怨师',  # "师"常被误识别
                            '组件', '产品类型'  # 组件字段
                        ]
                        is_essential_field = any(keyword in text for keyword in essential_fields)
                        
                        # 其他重要字段：使用较低置信度阈值
                        important_fields = ['机型', '产品', '填写时间', '电话', '课题代号', '产品型号']
                        is_important_field = any(keyword in text for keyword in important_fields)
                        
                        if is_essential_field:
                            # 前端必需字段：只要有文本内容就保留，不考虑置信度
                            if text.strip():
                                should_include = True
                                print(f"  → ✅ 前端必需字段保留 (忽略置信度: {confidence:.3f})")
                        elif is_important_field:
                            # 重要字段：置信度 > 0.2
                            if confidence > 0.2 and text.strip():
                                should_include = True
                                print(f"  → ✅ 重要字段保留 (置信度阈值: 0.2)")
                        else:
                            # 普通字段：置信度 > 0.5  
                            if confidence > 0.5 and text.strip():
                                should_include = True
                                print(f"  → ✅ 普通字段保留 (置信度阈值: 0.5)")
                        
                        if should_include:
                            texts.append(text.strip())
                        else:
                            print(f"  → ❌ 被过滤 (置信度过低或非关键字段)")

            extracted_text = '\n'.join(texts)
            print(f"EasyOCR识别成功，提取{len(texts)}行文本，总长度: {len(extracted_text)}")
            
            # 🔍 调试信息：显示最终提取的文本
            print("=" * 50)
            print("最终提取的文本内容:")
            for i, line in enumerate(texts, 1):
                print(f"{i:2d}. {line}")
            print("=" * 50)
            
            return extracted_text
            
        except Exception as e:
            print(f"EasyOCR识别失败: {str(e)}")
            import traceback
            print(f"详细错误信息: {traceback.format_exc()}")
            return ""

# 全局实例
simple_ocr_processor = None

def get_ocr_processor():
    """获取OCR处理器实例（单例模式）"""
    global simple_ocr_processor
    if simple_ocr_processor is None:
        simple_ocr_processor = SimpleEasyOCRProcessor()
    return simple_ocr_processor

# OCR处理器现在使用延迟加载，只有在调用get_ocr_processor()时才创建实例

# 测试代码
if __name__ == "__main__":
    print("=== 测试简化EasyOCR处理器 ===")
    
    processor = SimpleEasyOCRProcessor()
    
    # 测试图片识别
    test_image = "test.png"
    if os.path.exists(test_image):
        print(f"\n测试识别图片: {test_image}")
        result = processor.process_image_file(test_image)
        print("\n=== 最终识别结果 ===")
        print(result)
    else:
        print(f"测试图片不存在: {test_image}")
    
    print("\n=== 测试完成 ===") 