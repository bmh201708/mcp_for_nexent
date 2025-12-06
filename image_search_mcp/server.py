"""
图谱以图搜图 MCP Server
使用FastMCP提供图像搜索服务
"""
import base64
import io
import json
import os
from typing import List, Dict
from PIL import Image
import numpy as np
from fastmcp import FastMCP
import chromadb
from chromadb.config import Settings
from plip_model import get_extractor, PLIPEmbeddingFunction

# 配置代理（用于模型下载和图片下载）
os.environ['HTTP_PROXY'] = 'http://10.196.180.160:7897'
os.environ['HTTPS_PROXY'] = 'http://10.196.180.160:7897'

# 检查requests库是否可用
HAS_REQUESTS = False
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    pass

# 数据库配置
DB_PATH = "./pathology_atlas_db"
COLLECTION_NAME = "pathology_cases"

# 初始化MCP服务器
mcp = FastMCP(name="Pathology Atlas Image Search MCP")

# 全局变量
_chroma_client = None
_collection = None
_extractor = None


def get_collection():
    """获取ChromaDB collection（懒加载）"""
    global _chroma_client, _collection
    
    if _collection is None:
        if not os.path.exists(DB_PATH):
            raise FileNotFoundError(
                f"数据库不存在: {DB_PATH}\n"
                f"请先运行 indexer.py 构建索引"
            )
        
        print(f"正在连接ChromaDB数据库: {DB_PATH}")
        _chroma_client = chromadb.PersistentClient(
            path=DB_PATH,
            settings=Settings(anonymized_telemetry=False)
        )
        
        embedding_func = PLIPEmbeddingFunction()
        _collection = _chroma_client.get_collection(
            name=COLLECTION_NAME,
            embedding_function=embedding_func
        )
        
        count = _collection.count()
        print(f"数据库连接成功，包含 {count} 条记录")
    
    return _collection


def decode_image(image_data: str) -> Image.Image:
    """
    将Base64编码的图片、文件路径或URL解码为PIL Image
    支持多种输入格式，兼容Nexent平台的文件处理方式
    
    Args:
        image_data: 可以是以下格式之一：
                   - Base64编码字符串（支持data:image/...格式）
                   - 本地文件路径
                   - HTTP/HTTPS URL（会下载图片）
        
    Returns:
        PIL Image对象
    """
    # 检查是否是HTTP/HTTPS URL
    if image_data.startswith(('http://', 'https://')):
        if not HAS_REQUESTS:
            raise ValueError("requests库未安装，无法从URL下载图片。请安装: pip install requests")
        try:
            print(f"正在从URL下载图片: {image_data}")
            response = requests.get(image_data, timeout=30)
            response.raise_for_status()
            image = Image.open(io.BytesIO(response.content))
        except Exception as e:
            raise ValueError(f"无法从URL下载图片: {e}")
    
    # 检查是否是本地文件路径
    elif os.path.exists(image_data):
        print(f"从文件路径读取图片: {image_data}")
        image = Image.open(image_data)
    
    # 否则认为是Base64编码
    else:
        print("检测到Base64编码格式")
        # 移除data URL前缀（如果有）
        if "," in image_data:
            image_data = image_data.split(",")[1]
        
        try:
            # Base64解码
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            raise ValueError(f"Base64解码失败: {e}。请确保输入是正确的Base64编码或文件路径")
    
    # 转换为RGB（确保兼容性）
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    return image


@mcp.tool(
    name="search_similar_cases",
    description="以图搜图工具。接收一张病理切片图片，在图谱库中搜索视觉特征最相似的历史确诊病例，返回Top-K个最相似的病例及其诊断信息。支持多种输入格式：Base64编码（data:image/...格式）、文件路径、或HTTP/HTTPS URL。支持jpg、png、tif等格式。适用于Nexent平台的文件上传功能。"
)
def search_similar_cases(
    query_image: str,
    top_k: int = 5
) -> str:
    """
    搜索相似病例
    
    Args:
        query_image: 查询图片，支持多种格式（自动识别）：
                    - Base64编码字符串（推荐data:image/jpeg;base64,...格式）
                    - 本地文件路径（如 /path/to/image.jpg）
                    - HTTP/HTTPS URL（如 https://example.com/image.jpg）
                    Nexent平台上传文件后，通常会提供Base64编码或文件路径
        top_k: 返回最相似的病例数量，默认5个，范围1-20
        
    Returns:
        JSON字符串，包含相似病例列表
    """
    try:
        # 验证top_k参数
        top_k = max(1, min(top_k, 20))  # 限制在1-20之间
        
        print(f"收到搜索请求，top_k={top_k}")
        
        # 获取collection
        collection = get_collection()
        
        # 解码查询图片（自动识别格式：Base64、文件路径或URL）
        try:
            print(f"输入长度: {len(query_image)} 字符")
            print(f"输入前100字符: {query_image[:100]}...")
            query_image_obj = decode_image(query_image)
            print(f"图片解码成功，尺寸: {query_image_obj.size}, 模式: {query_image_obj.mode}")
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"图片解码失败: {e}")
            print(f"错误详情: {error_trace}")
            return json.dumps({
                "query_status": "error",
                "error": f"图片解码失败: {str(e)}",
                "error_type": type(e).__name__,
                "suggestion": "请确保输入是有效的Base64编码、文件路径或URL。如果是Nexent平台上传的文件，可能需要等待文件处理完成。",
                "input_preview": query_image[:200] if len(query_image) > 200 else query_image
            }, indent=2, ensure_ascii=False)
        
        # 提取特征向量
        print("正在提取查询图片的特征向量...")
        global _extractor
        if _extractor is None:
            print("初始化PLIP特征提取器...")
            _extractor = get_extractor()
        
        try:
            query_features = _extractor.extract_features(query_image_obj)
            print(f"特征提取成功，特征向量维度: {len(query_features)}")
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"特征提取失败: {e}")
            print(f"错误详情: {error_trace}")
            return json.dumps({
                "query_status": "error",
                "error": f"特征提取失败: {str(e)}",
                "error_type": type(e).__name__,
                "suggestion": "可能是图片格式不支持或模型加载失败，请检查图片格式和模型状态"
            }, indent=2, ensure_ascii=False)
        
        # 在数据库中搜索
        # 注意：ChromaDB的query方法在使用自定义embedding function时，
        # 可以直接传入query_embeddings（已提取的特征向量）
        print(f"正在搜索最相似的 {top_k} 个病例...")
        max_results = min(top_k, collection.count())
        if max_results == 0:
            return json.dumps({
                "query_status": "error",
                "error": "数据库为空，请先运行 indexer.py 构建索引"
            }, indent=2, ensure_ascii=False)
        
        results = collection.query(
            query_embeddings=[query_features.tolist()],
            n_results=max_results,
            include=["metadatas", "distances"]
        )
        
        # 格式化结果
        found_cases = []
        
        if results['ids'] and len(results['ids'][0]) > 0:
            metadatas = results['metadatas'][0]
            distances = results['distances'][0]
            
            for i, (meta, dist) in enumerate(zip(metadatas, distances)):
                # 计算相似度得分（距离越小越相似，转换为0-100分）
                # ChromaDB使用余弦距离，范围通常是0-2，这里转换为相似度百分比
                similarity_score = max(0, (1 - dist) * 100)
                
                case_info = {
                    "rank": i + 1,
                    "diagnosis": meta.get('diagnosis', 'Unknown'),
                    "similarity_score": f"{similarity_score:.2f}%",
                    "distance": f"{dist:.4f}",
                    "image_path": meta.get('image_path', ''),
                    "filename": meta.get('filename', ''),
                    "source": meta.get('source', 'Internal Atlas'),
                    "note": "Visual match based on tissue architecture and morphological features."
                }
                
                found_cases.append(case_info)
            
            print(f"找到 {len(found_cases)} 个相似病例")
        else:
            print("未找到相似病例")
        
        # 返回JSON格式结果
        result = {
            "query_status": "success",
            "total_results": len(found_cases),
            "cases": found_cases
        }
        
        return json.dumps(result, indent=2, ensure_ascii=False)
        
    except FileNotFoundError as e:
        error_msg = {
            "query_status": "error",
            "error": str(e),
            "suggestion": "请先运行 indexer.py 构建图谱索引"
        }
        return json.dumps(error_msg, indent=2, ensure_ascii=False)
    
    except Exception as e:
        import traceback
        error_msg = {
            "query_status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }
        print(f"搜索失败: {e}")
        traceback.print_exc()
        return json.dumps(error_msg, indent=2, ensure_ascii=False)


@mcp.tool(
    name="search_similar_cases_from_file",
    description="以图搜图工具（文件路径版本）。接收图片文件路径，在图谱库中搜索视觉特征最相似的历史确诊病例。这是search_similar_cases的便捷版本，专门用于处理服务器上的图片文件。"
)
def search_similar_cases_from_file(
    image_path: str,
    top_k: int = 5
) -> str:
    """
    从文件路径搜索相似病例（便捷函数）
    
    Args:
        image_path: 图片文件路径（服务器可访问的路径）
        top_k: 返回最相似的病例数量，默认5个
        
    Returns:
        JSON字符串，包含相似病例列表
    """
    return search_similar_cases(query_image=image_path, top_k=top_k)


if __name__ == "__main__":
    print("=" * 60)
    print("图谱以图搜图 MCP Server")
    print("=" * 60)
    print(f"数据库路径: {DB_PATH}")
    print(f"Collection: {COLLECTION_NAME}")
    print(f"服务器监听: http://0.0.0.0:18930/sse")
    print("=" * 60)
    print()
    print("可用工具:")
    print("  1. search_similar_cases: 接收Base64编码或文件路径")
    print("  2. search_similar_cases_from_file: 接收文件路径（便捷版本）")
    print()
    
    # 检查数据库是否存在
    if not os.path.exists(DB_PATH):
        print("⚠️  警告: 数据库不存在，请先运行 indexer.py 构建索引")
        print()
    
    # 预加载模型（避免首次查询时的延迟）
    print("正在预加载PLIP模型...")
    try:
        # 在模块级别直接访问全局变量，不需要global声明
        if globals()['_extractor'] is None:
            globals()['_extractor'] = get_extractor()
            print("✅ PLIP模型预加载完成")
        else:
            print("✅ PLIP模型已加载")
    except Exception as e:
        print(f"⚠️  PLIP模型预加载失败: {e}")
        print("   模型将在首次查询时尝试加载")
    print()
    
    # 启动服务器
    mcp.run(transport="sse", host="0.0.0.0", port=18930)

