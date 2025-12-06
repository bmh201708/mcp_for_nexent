# 图谱以图搜图 MCP Server

基于 FastMCP 的病理图谱以图搜图服务，使用 PLIP 模型提取图像特征，ChromaDB 存储向量索引，实现基于内容的图像检索（CBIR - Content-Based Image Retrieval）。

## 📋 目录

- [原理概述](#原理概述)
- [技术架构](#技术架构)
- [核心组件](#核心组件)
- [快速开始](#快速开始)
- [Nexent 平台集成](#nexent-平台集成)
- [API 文档](#api-文档)
- [配置说明](#配置说明)
- [故障排除](#故障排除)

---

## 🔬 原理概述

### CBIR (Content-Based Image Retrieval) 工作流程

本 MCP 服务实现了基于内容的图像检索系统，核心流程如下：

```
查询图片 → 特征提取 → 向量化 → 相似度搜索 → 返回结果
    ↓           ↓          ↓          ↓           ↓
 输入图像   PLIP模型   512维向量   ChromaDB     Top-K病例
```

### 1. **特征提取阶段**

使用 **PLIP (Pathology Language-Image Pretraining)** 模型将病理切片图像转换为高维特征向量：

- **输入**: 原始病理图像（RGB格式，自动resize到模型输入尺寸）
- **处理**: PLIP 视觉编码器提取深层视觉特征
- **输出**: 512维特征向量（embedding）

PLIP 模型是专门为病理图像设计的预训练模型，能够捕获：
- 组织架构特征（tissue architecture）
- 细胞形态学特征（cellular morphology）
- 病理学相关的视觉模式

### 2. **向量存储阶段**

使用 **ChromaDB** 向量数据库存储所有历史病例的特征向量：

- 每个病例存储为一条记录
- 包含：特征向量（512维）、元数据（诊断类别、文件路径等）
- 支持高效的相似度搜索

### 3. **相似度搜索阶段**

当查询图片输入时：

1. 提取查询图片的特征向量
2. 在 ChromaDB 中使用余弦相似度（cosine similarity）计算与所有病例的距离
3. 返回 Top-K 个最相似的病例

**相似度计算**：
```
similarity = 1 - cosine_distance(query_vector, case_vector)
similarity_score = similarity × 100%
```

### 4. **结果返回**

返回 JSON 格式的结果，包含：
- 相似度得分（百分比）
- 诊断类别
- 原始图像路径
- 距离值（用于进一步分析）

---

## 🏗️ 技术架构

### 技术栈

| 组件 | 技术选型 | 版本要求 | 用途 |
|------|---------|---------|------|
| **框架** | FastMCP | >= 2.13.0 | MCP 协议服务器框架 |
| **特征提取** | PLIP (vinid/plip) | Latest | 病理图像特征提取 |
| **深度学习** | PyTorch | Latest | 模型推理 |
| **向量数据库** | ChromaDB | Latest | 向量存储和相似度搜索 |
| **图像处理** | PIL/Pillow | Latest | 图像预处理 |
| **HTTP客户端** | requests | Latest | URL 图片下载 |

### 系统架构图

```
┌─────────────────────────────────────────────────────────┐
│                    Nexent Platform                      │
│  ┌──────────────┐         ┌──────────────────────────┐ │
│  │  Frontend    │ ──────> │  MCP Client (SSE)       │ │
│  │  (上传图片URL) │         │  http://host:18930/sse   │ │
│  └──────────────┘         └──────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│              Image Search MCP Server                     │
│  ┌──────────────────────────────────────────────────┐   │
│  │  FastMCP Server (server.py)                     │   │
│  │  - search_similar_cases(query_image, top_k)     │   │
│  └──────────────────────────────────────────────────┘   │
│                            │                            │
│  ┌────────────────────────┴────────────────────────┐   │
│  │                                                 │   │
│  ▼                                                 ▼   │
│  ┌──────────────────┐              ┌────────────────┐ │
│  │ PLIP Model       │              │ ChromaDB       │ │
│  │ (plip_model.py) │              │ (向量数据库)     │ │
│  │                  │              │                │ │
│  │ - 特征提取       │              │ - 存储1800+病例 │ │
│  │ - GPU加速        │              │ - 相似度搜索     │ │
│  └──────────────────┘              └────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 核心组件

### 1. `plip_model.py` - PLIP 模型封装

**功能**：
- 加载 PLIP 预训练模型（从 HuggingFace）
- 图像预处理（resize, normalize）
- 特征向量提取（单个/批量）
- GPU 加速支持

**关键类**：
- `PLIPFeatureExtractor`: 特征提取器主类
- `PLIPEmbeddingFunction`: ChromaDB 自定义 embedding function

### 2. `indexer.py` - 索引构建脚本

**功能**：
- 遍历图谱目录（按诊断分类）
- 批量提取特征向量
- 存储到 ChromaDB
- 支持增量索引

**工作流程**：
```
扫描目录 → 收集图片 → 批量提取特征 → 写入数据库
```

### 3. `server.py` - MCP 服务器

**功能**：
- 提供 `search_similar_cases` 工具
- 支持多种输入格式（Base64、文件路径、URL）
- 图像解码和预处理
- 相似度搜索和结果格式化

**关键函数**：
- `decode_image()`: 智能图像解码（自动识别格式）
- `get_collection()`: ChromaDB 连接管理
- `search_similar_cases()`: 主搜索函数

### 4. `build_atlas.py` - 图谱构建辅助工具

**功能**：
- 从大型数据集（NCT-CRC-HE-100K）抽取样本
- 构建测试用的迷你图谱
- 支持自定义类别和数量

---

## 🚀 快速开始

### 前置要求

- Python 3.11+
- CUDA-capable GPU（推荐，用于加速）
- 至少 8GB RAM
- 网络连接（用于下载模型）

### 步骤 1: 环境准备

```bash
# 创建 conda 环境
conda create -n mcp-image-search-env python=3.11 -y
conda activate mcp-image-search-env

# 安装依赖
cd ~/mcp/image_search_mcp
pip install -r requirements.txt
```

### 步骤 2: 准备图谱数据

#### 选项 A: 使用 NCT-CRC-HE-100K 数据集（推荐）

```bash
# 1. 构建图谱（每个类别200张图片）
python build_atlas.py \
    --source_dir /path/to/NCT-CRC-HE-100K/versions/1/NCT-CRC-HE-100K \
    --target_dir ./atlas_data_200 \
    --images_per_category 200

# 2. 构建索引
python indexer.py --atlas_dir ./atlas_data_200
# 当询问是否清空现有数据时，选择 y（首次构建）或 n（增量添加）
```

#### 选项 B: 使用自定义图谱数据

准备按诊断分类的文件夹结构：

```
atlas_data/
├── ADI/          # 脂肪组织
│   ├── img1.tif
│   └── img2.tif
├── TUM/          # 肿瘤
│   ├── img1.tif
│   └── img2.tif
├── STR/          # 基质
└── ...
```

然后运行：

```bash
python indexer.py --atlas_dir ./atlas_data
```

### 步骤 3: 启动服务器

```bash
python server.py
```

服务器将启动在 `http://0.0.0.0:18930/sse`

**验证服务器运行**：
```bash
# 检查日志
tail -f server.log

# 应该看到：
# - 数据库连接成功，包含 X 条记录
# - PLIP模型预加载完成（如果配置了预加载）
# - Uvicorn running on http://0.0.0.0:18930
```

### 步骤 4: 测试搜索功能

#### 使用 Python 测试

```python
import requests
import json

# MCP 服务器地址
server_url = "http://localhost:18930/sse"

# 测试数据（使用图片URL）
test_data = {
    "query_image": "https://example.com/pathology_image.jpg",
    "top_k": 5
}

# 调用 MCP 工具（实际调用方式取决于您的 MCP 客户端）
# 这里仅作示例
```

---

## 🔗 Nexent 平台集成

### Nexent 配置

在 Nexent 平台中配置 MCP 服务器：

1. **MCP 服务器 URL**: `http://172.17.0.1:18930/sse`（如果 Nexent 在 Docker 中）
   - 或 `http://localhost:18930/sse`（如果同机运行）

2. **工具名称**: `search_similar_cases`

3. **参数**:
   - `query_image`: 图片 URL（字符串）
   - `top_k`: 返回结果数量（整数，默认 5）

### ⚠️ 为什么 Nexent 上暂时只支持 URL 传图片？

**当前限制**：在 Nexent 平台上，`search_similar_cases` 工具**暂时只支持通过 HTTP/HTTPS URL 传递图片**。

#### 技术原因

1. **Nexent 文件预处理机制**

   Nexent 平台在上传文件时有一个预处理流程：
   - 用户上传文件 → Nexent 后端处理 → 生成可访问的 URL
   - 文件被存储在 Nexent 的存储系统中
   - 前端通过 URL 访问文件

   当前 Nexent 的文件预处理端点（`/api/file/preprocess`）存在以下问题：
   - 端点返回 404（未实现或已禁用）
   - 前端预处理功能被注释掉
   - 文件上传后无法直接获取 Base64 编码或文件路径

2. **MCP 工具调用限制**

   - MCP 协议通过 JSON-RPC 传递参数
   - Base64 编码的图片会产生非常大的 JSON（几MB到几十MB）
   - 大文件传输可能导致：
     - 网络超时
     - JSON 解析性能问题
     - 内存占用过高

3. **文件路径访问限制**

   - Nexent 运行在 Docker 容器中
   - MCP 服务器可能运行在宿主机或其他容器
   - 容器间文件系统隔离，无法直接访问文件路径
   - 需要配置共享卷（volume）才能访问文件路径

#### 当前解决方案

**使用 URL 方式**：
- ✅ Nexent 上传文件后自动生成 URL
- ✅ URL 可以通过网络访问（跨容器/跨主机）
- ✅ MCP 服务器使用 `requests` 库下载图片
- ✅ 避免了文件系统权限和路径问题

**工作流程**：
```
用户上传图片 
  → Nexent 存储并生成 URL 
    → MCP 工具接收 URL 
      → 服务器下载图片 
        → 提取特征并搜索
```

#### 未来改进方向

1. **实现文件预处理端点**
   - 在 Nexent 后端实现 `/api/file/preprocess`
   - 返回文件的 Base64 编码或可访问路径

2. **支持 Base64 编码**
   - 优化 JSON 传输性能
   - 添加流式传输支持

3. **配置共享存储**
   - 使用 Docker volume 共享文件系统
   - 支持直接文件路径访问

4. **优化文件处理流程**
   - 实现文件缓存机制
   - 支持大文件分块传输

### 在 Nexent 中使用示例

**场景**：用户在 Nexent 聊天界面上传病理切片图片

1. **用户操作**：
   - 在聊天界面点击上传按钮
   - 选择病理切片图片（JPG/PNG/TIF）
   - 上传到 Nexent 平台

2. **Nexent 处理**：
   - 文件存储到 Nexent 存储系统
   - 生成可访问的 URL（如 `https://nexent.example.com/files/image_123.jpg`）

3. **MCP 工具调用**：
   ```json
   {
     "tool": "search_similar_cases",
     "parameters": {
       "query_image": "https://nexent.example.com/files/image_123.jpg",
       "top_k": 5
     }
   }
   ```

4. **MCP 服务器处理**：
   - 从 URL 下载图片
   - 提取特征向量
   - 搜索相似病例
   - 返回结果

5. **结果显示**：
   - Nexent 前端展示 Top-5 相似病例
   - 包含诊断类别、相似度得分等信息

---

## 📚 API 文档

### 工具: `search_similar_cases`

**描述**: 在图谱库中搜索与查询图片视觉特征最相似的历史确诊病例。

**参数**:

| 参数名 | 类型 | 必需 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `query_image` | string | 是 | - | 查询图片，支持以下格式：<br>- HTTP/HTTPS URL（如 `https://example.com/image.jpg`）<br>- Base64 编码（如 `data:image/jpeg;base64,...`）<br>- 本地文件路径（如 `/path/to/image.jpg`） |
| `top_k` | integer | 否 | 5 | 返回最相似的病例数量，范围 1-20 |

**返回格式**:

```json
{
  "query_status": "success",
  "total_results": 5,
  "cases": [
    {
      "rank": 1,
      "diagnosis": "TUM",
      "similarity_score": "92.34%",
      "distance": "0.0766",
      "image_path": "/path/to/atlas_data/TUM/TUM_001.tif",
      "filename": "TUM_001.tif",
      "source": "Internal Atlas",
      "note": "Visual match based on tissue architecture and morphological features."
    },
    {
      "rank": 2,
      "diagnosis": "TUM",
      "similarity_score": "89.12%",
      "distance": "0.1088",
      "image_path": "/path/to/atlas_data/TUM/TUM_002.tif",
      "filename": "TUM_002.tif",
      "source": "Internal Atlas",
      "note": "Visual match based on tissue architecture and morphological features."
    }
    // ... 更多结果
  ]
}
```

**错误响应**:

```json
{
  "query_status": "error",
  "error": "图片解码失败: 无法从URL下载图片: Connection timeout",
  "error_type": "ValueError",
  "suggestion": "请确保输入是有效的Base64编码、文件路径或URL。如果是Nexent平台上传的文件，可能需要等待文件处理完成。",
  "input_preview": "https://example.com/image.jpg"
}
```

### 工具: `search_similar_cases_from_file`

**描述**: `search_similar_cases` 的便捷版本，专门接收服务器上的图片文件路径。

**参数**:

| 参数名 | 类型 | 必需 | 说明 |
|--------|------|------|------|
| `image_path` | string | 是 | 服务器可访问的图片文件路径 |
| `top_k` | integer | 否 | 返回最相似的病例数量，默认 5 |

---

## ⚙️ 配置说明

### 数据库配置

- **路径**: `./pathology_atlas_db`（相对于运行目录）
- **Collection 名称**: `pathology_cases`
- **向量维度**: 512（PLIP 模型输出）

### 服务器配置

- **端口**: 18930
- **协议**: SSE (Server-Sent Events)
- **监听地址**: `0.0.0.0:18930/sse`

### 模型配置

- **模型名称**: `vinid/plip`
- **特征维度**: 512
- **设备**: 自动检测（优先 GPU）
- **缓存位置**: `~/.cache/huggingface/hub/`

### 代理配置

如果需要通过代理下载模型，在 `plip_model.py` 中配置：

```python
os.environ['HTTP_PROXY'] = 'http://proxy.example.com:7897'
os.environ['HTTPS_PROXY'] = 'http://proxy.example.com:7897'
```

### 性能优化

1. **批量大小调整**（`indexer.py`）:
   ```python
   batch_size = 50  # 默认 10，可根据内存调整
   ```

2. **GPU 加速**:
   - 自动检测并使用 GPU（如果可用）
   - 确保安装了 CUDA 版本的 PyTorch

3. **预加载模型**（`server.py`）:
   - 服务器启动时预加载 PLIP 模型
   - 避免首次查询时的延迟

---

## 🔍 故障排除

### 1. 数据库不存在错误

**错误**: `FileNotFoundError: 数据库不存在: ./pathology_atlas_db`

**解决**:
```bash
# 先构建索引
python indexer.py --atlas_dir /path/to/atlas_data
```

### 2. 模型下载失败

**错误**: `ConnectionError` 或 `MaxRetriesExceeded`

**解决**:
- 检查网络连接
- 配置代理（如果需要）
- 手动设置环境变量：
  ```bash
  export HTTP_PROXY=http://proxy.example.com:7897
  export HTTPS_PROXY=http://proxy.example.com:7897
  ```

### 3. URL 图片下载失败

**错误**: `无法从URL下载图片: Connection timeout`

**可能原因**:
- URL 不可访问
- 网络连接问题
- 服务器防火墙阻止

**解决**:
- 验证 URL 是否可访问（浏览器打开测试）
- 检查网络连接
- 如果 Nexent 在 Docker 中，确保网络配置正确

### 4. 内存不足

**错误**: `OutOfMemoryError` 或系统卡死

**解决**:
- 减少 `indexer.py` 中的 `batch_size`
- 使用 GPU（减少 CPU 内存占用）
- 分批处理图片

### 5. ChromaDB 连接错误

**错误**: `'PLIPEmbeddingFunction' object has no attribute 'name'`

**解决**:
- 确保 `plip_model.py` 中的 `PLIPEmbeddingFunction` 类有 `name()` 方法
- 重新构建索引

### 6. 端口被占用

**错误**: `Address already in use`

**解决**:
```bash
# 查找占用端口的进程
lsof -i :18930

# 杀死进程
kill -9 <PID>

# 或修改 server.py 中的端口号
```

---

## 📊 性能指标

### 典型性能（使用 GPU）

- **特征提取速度**: ~50-100 张/秒（GPU）
- **搜索速度**: < 100ms（1800 条记录）
- **内存占用**: ~2-4GB（包含模型和数据库）
- **模型加载时间**: ~10-30 秒（首次）

### 当前图谱规模

- **总病例数**: 1800+ 条
- **类别数**: 9 个（ADI, BACK, DEB, LYM, MUC, MUS, NORM, STR, TUM）
- **每个类别**: 200 张图片
- **数据库大小**: ~7 MB

---

## 📝 开发说明

### 项目结构

```
image_search_mcp/
├── server.py              # FastMCP 服务器主文件
├── indexer.py             # 索引构建脚本
├── plip_model.py          # PLIP 模型封装
├── build_atlas.py         # 图谱构建辅助工具
├── requirements.txt       # Python 依赖
├── setup.sh              # 环境设置脚本
└── README.md             # 本文档
```

### 扩展开发

1. **添加新的特征提取模型**:
   - 修改 `plip_model.py`
   - 实现新的 `FeatureExtractor` 类
   - 更新 `PLIPEmbeddingFunction`

2. **优化搜索算法**:
   - 修改 `server.py` 中的搜索逻辑
   - 添加过滤条件（按诊断类别等）
   - 实现混合搜索（特征 + 元数据）

3. **添加新工具**:
   - 在 `server.py` 中使用 `@mcp.tool` 装饰器
   - 实现工具函数
   - 更新文档

---

## 📄 许可证

请参考项目根目录的 LICENSE 文件。

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📧 联系方式

如有问题或建议，请通过 GitHub Issues 联系。

---

**最后更新**: 2025-12-07
