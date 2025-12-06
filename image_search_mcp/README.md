# 图谱以图搜图 MCP Server

基于 FastMCP 的病理图谱以图搜图服务，使用 PLIP 模型提取图像特征，ChromaDB 存储向量索引。

## 功能

- `search_similar_cases`: 接收 Base64 编码的查询图片，在图谱库中搜索视觉特征最相似的历史确诊病例，返回 Top-K 个最相似的病例及其诊断信息。

## 项目结构

```
image_search_mcp/
├── server.py          # FastMCP服务器主文件
├── indexer.py         # 图谱索引构建脚本
├── plip_model.py      # PLIP模型封装模块
├── build_atlas.py     # 从NCT-CRC-HE-100K构建迷你图谱的辅助脚本
├── requirements.txt   # Python依赖
└── README.md          # 项目文档
```

## 安装

### 1. 创建 conda 环境

```bash
conda create -n mcp-image-search-env python=3.11 -y
conda activate mcp-image-search-env
```

### 2. 安装依赖

```bash
cd ~/mcp/image_search_mcp
pip install -r requirements.txt
```

**注意**: PLIP 模型首次运行时会从 HuggingFace 下载，需要网络连接。代码已配置代理（http://10.196.180.160:7897）。

### 3. 准备图谱数据

#### 方式一：使用 NCT-CRC-HE-100K 数据集（推荐）

如果已下载 NCT-CRC-HE-100K 数据集：

```bash
# 构建迷你图谱（每个类别20张图片）
python build_atlas.py --source_dir ~/nct-crc-he-100k --target_dir ./atlas_data

# 构建索引
python indexer.py --atlas_dir ./atlas_data
```

#### 方式二：使用自定义图谱数据

准备按诊断分类的文件夹结构：

```
atlas_data/
├── ADI/          # 脂肪组织
│   ├── img1.tif
│   └── img2.tif
├── TUM/          # 肿瘤
│   ├── img1.tif
│   └── img2.tif
└── ...
```

然后运行：

```bash
python indexer.py --atlas_dir ./atlas_data
```

### 4. 启动服务器

```bash
python server.py
```

服务器监听 `http://0.0.0.0:18930/sse`

如果 Nexent 在 Docker 中运行，配置 MCP URL 为 `http://172.17.0.1:18930/sse`

## 使用

### 构建索引

索引脚本会遍历指定目录，按文件夹名称作为诊断类别，使用 PLIP 模型提取每张图片的特征向量并存储到 ChromaDB。

```bash
python indexer.py --atlas_dir /path/to/atlas_data
```

**选项**:
- `--atlas_dir`: 图谱目录路径（必需）
- `--db_path`: ChromaDB 数据库路径（默认: `./pathology_atlas_db`）

如果数据库已存在，脚本会询问是否清空重建。

### 搜索相似病例

通过 MCP 工具调用 `search_similar_cases`：

**参数**:
- `query_image_base64`: Base64 编码的查询图片（支持 `data:image/...` 格式）
- `top_k`: 返回最相似的病例数量（默认: 5）

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
      "image_path": "/path/to/image.tif",
      "filename": "TUM_001.tif",
      "source": "Internal Atlas",
      "note": "Visual match based on tissue architecture and morphological features."
    },
    ...
  ]
}
```

## 配置

### 代理设置

模型下载时会自动使用代理（已在代码中配置）：
- HTTP_PROXY: http://10.196.180.160:7897
- HTTPS_PROXY: http://10.196.180.160:7897

### 数据库位置

ChromaDB 数据存储在 `./pathology_atlas_db` 目录（相对于运行脚本的目录）。

### 端口配置

服务器默认监听端口 `18930`。如需修改，编辑 `server.py` 文件末尾的端口号。

## 技术栈

- **框架**: FastMCP
- **特征提取模型**: PLIP (Pathology Language-Image Pretraining) - `vinid/plip`
- **向量数据库**: ChromaDB
- **图像处理**: PIL/Pillow
- **深度学习**: PyTorch, Transformers

## 注意事项

1. **首次运行**: PLIP 模型首次运行时会从 HuggingFace 下载（约几百MB），需要网络连接和代理配置。
2. **GPU 支持**: 如果系统有 GPU，代码会自动使用 GPU 加速特征提取。
3. **图谱数据格式**: 图谱数据应按照诊断类别组织在子文件夹中，文件夹名作为诊断类别名称。
4. **支持的图片格式**: jpg, jpeg, png, tif, tiff
5. **内存使用**: 索引大量图片时可能需要较多内存，建议分批处理或使用 GPU。

## 故障排除

### 数据库不存在错误

如果启动服务器时提示数据库不存在，请先运行 `indexer.py` 构建索引。

### 模型下载失败

确保网络连接正常，代理配置正确。可以手动设置环境变量：

```bash
export HTTP_PROXY=http://10.196.180.160:7897
export HTTPS_PROXY=http://10.196.180.160:7897
```

### 内存不足

如果处理大量图片时内存不足，可以：
1. 减少 `indexer.py` 中的批量大小
2. 使用 GPU（如果有）
3. 分批处理图片

## 开发说明

- `plip_model.py`: PLIP 模型封装，提供特征提取功能
- `indexer.py`: 索引构建脚本，批量处理图片并存储到 ChromaDB
- `server.py`: MCP 服务器，提供搜索接口
- `build_atlas.py`: 辅助脚本，从大型数据集构建测试用的迷你图谱

