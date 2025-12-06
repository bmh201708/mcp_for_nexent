"""
PLIP模型封装模块
提供图像特征提取功能，使用代理下载模型
"""
import os
import torch
from PIL import Image
import numpy as np
from typing import Union, List
from transformers import AutoProcessor, AutoModel

# 配置代理（用于模型下载）
os.environ['HTTP_PROXY'] = 'http://10.196.180.160:7897'
os.environ['HTTPS_PROXY'] = 'http://10.196.180.160:7897'

# PLIP模型名称
PLIP_MODEL_NAME = "vinid/plip"


class PLIPFeatureExtractor:
    """PLIP特征提取器"""
    
    def __init__(self, device=None):
        """
        初始化PLIP模型
        
        Args:
            device: 计算设备，None时自动选择（优先GPU）
        """
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)
        
        print(f"正在加载PLIP模型 ({PLIP_MODEL_NAME})，设备: {self.device}")
        print("首次运行会从HuggingFace下载模型，可能需要一些时间...")
        
        try:
            self.processor = AutoProcessor.from_pretrained(PLIP_MODEL_NAME)
            self.model = AutoModel.from_pretrained(PLIP_MODEL_NAME).to(self.device)
            self.model.eval()
            print("PLIP模型加载完成")
        except Exception as e:
            print(f"模型加载失败: {e}")
            raise
    
    def preprocess_image(self, image: Union[str, Image.Image, np.ndarray]) -> torch.Tensor:
        """
        预处理图像
        
        Args:
            image: 图像路径、PIL Image或numpy数组
            
        Returns:
            预处理后的tensor
        """
        if isinstance(image, str):
            image = Image.open(image).convert('RGB')
        elif isinstance(image, np.ndarray):
            image = Image.fromarray(image).convert('RGB')
        elif not isinstance(image, Image.Image):
            raise ValueError(f"不支持的图像类型: {type(image)}")
        
        # 使用PLIP的processor处理图像
        inputs = self.processor(images=image, return_tensors="pt")
        return inputs['pixel_values'].to(self.device)
    
    def extract_features(self, image: Union[str, Image.Image, np.ndarray]) -> np.ndarray:
        """
        提取图像特征向量
        
        Args:
            image: 图像路径、PIL Image或numpy数组
            
        Returns:
            特征向量（numpy数组）
        """
        with torch.no_grad():
            pixel_values = self.preprocess_image(image)
            outputs = self.model.get_image_features(pixel_values=pixel_values)
            # 归一化特征向量
            features = outputs / outputs.norm(dim=-1, keepdim=True)
            return features.cpu().numpy().flatten()
    
    def extract_features_batch(self, images: List[Union[str, Image.Image, np.ndarray]]) -> np.ndarray:
        """
        批量提取特征向量
        
        Args:
            images: 图像列表
            
        Returns:
            特征向量矩阵（n_samples, feature_dim）
        """
        features_list = []
        for img in images:
            features = self.extract_features(img)
            features_list.append(features)
        return np.array(features_list)


# 全局模型实例（懒加载）
_global_extractor = None


def get_extractor() -> PLIPFeatureExtractor:
    """获取全局特征提取器实例（单例模式）"""
    global _global_extractor
    if _global_extractor is None:
        _global_extractor = PLIPFeatureExtractor()
    return _global_extractor


class PLIPEmbeddingFunction:
    """ChromaDB的自定义embedding function，使用PLIP模型"""
    
    def __init__(self):
        self.extractor = None  # 懒加载
    
    def _get_extractor(self):
        """获取extractor实例（懒加载）"""
        if self.extractor is None:
            self.extractor = get_extractor()
        return self.extractor
    
    def name(self):
        """返回embedding function的名称（ChromaDB要求）"""
        return "plip"
    
    def __call__(self, input):
        """
        处理输入并返回特征向量
        
        Args:
            input: 图像路径列表或单个图像路径
            
        Returns:
            特征向量列表
        """
        extractor = self._get_extractor()
        
        if isinstance(input, list):
            # 批量处理
            features = extractor.extract_features_batch(input)
            return features.tolist()
        else:
            # 单个图像
            features = extractor.extract_features(input)
            return features.tolist()

