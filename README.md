# MCP Services for Nexent Platform

本仓库包含为 Nexent 平台设计的 MCP (Model Context Protocol) 服务集合，专门用于病理诊断工作流程。这些服务可以独立运行，也可以集成到 Nexent 平台中，为病理诊断 AI Agent 提供强大的工具支持。

## 📋 目录

- [服务概览](#服务概览)
- [快速开始](#快速开始)
- [服务详情](#服务详情)
- [项目结构](#项目结构)
- [系统要求](#系统要求)
- [Nexent 平台集成](#nexent-平台集成)
- [许可证](#许可证)
- [贡献](#贡献)

---

## 🚀 服务概览

本仓库包含三个核心 MCP 服务：

### 1. 🖼️ 图像搜索服务 (`image_search_mcp/`)

**功能**: 基于内容的图像检索（CBIR）服务，使用 PLIP 模型提取病理切片图像特征，通过向量相似度搜索找到最相似的历史确诊病例。**该服务可以为病理图片诊断提供重要参考依据**，帮助医生快速找到相似的历史病例，辅助诊断决策。

**核心工具**:
- `search_similar_cases`: 通过图像搜索相似病例（支持 URL、Base64、文件路径）
- `search_similar_cases_from_file`: 从文件路径搜索相似病例

**端口**: `18930`

**适用场景**:
- **病理图片诊断参考**: 为病理医生提供相似病例的视觉参考，辅助诊断决策
- 病理切片图像相似病例检索
- 诊断参考案例查找
- 组织形态学特征匹配
- 病例库检索

**数据集**: 使用 NCT-CRC-HE-100K 数据集（约 10 万张病理切片图像）

**诊断价值**:
- 🎯 **快速参考**: 通过图像相似度快速找到历史相似病例，为诊断提供参考
- 🎯 **提高准确性**: 基于大量历史病例的视觉特征匹配，提高诊断准确性
- 🎯 **学习辅助**: 帮助年轻医生学习不同病理类型的视觉特征
- 🎯 **质量控制**: 通过对比相似病例，辅助病理诊断的质量控制

📖 **详细文档**: 请查看 [`image_search_mcp/README.md`](image_search_mcp/README.md)

---

### 2. 📄 病理报告解析服务 (`pathology_mcp/`)

**功能**: 从原始病理报告文本中提取结构化信息，并提供 IHC 标记和基因突变的临床意义解释。

**核心工具**:
- `extract_pathology_fields`: 提取病理报告的结构化字段（部位、分级、分期、IHC、突变等）
- `interpret_ihc`: 解释 IHC 标记的临床意义
- `map_mutations`: 映射基因突变到临床意义和靶向治疗

**端口**: `18910`

**适用场景**: 
- 病理报告结构化解析
- 临床信息提取
- IHC 和突变结果解释

📖 **详细文档**: 请查看 [`pathology_mcp/README.md`](pathology_mcp/README.md)

---

### 3. 🔍 PubMed 文献搜索服务 (`pubmed_mcp/`)

**功能**: 通过 NCBI E-utilities API 搜索 PubMed 医学文献，特别适用于病理学相关的病例报告和临床研究检索。

**核心工具**:
- `search_pubmed`: 搜索 PubMed 数据库，支持关键词、布尔查询、发表类型过滤、时间范围限制等

**端口**: `18920`

**适用场景**:
- 病例报告检索
- 临床研究查找
- 文献综述搜索
- 最新研究追踪

📖 **详细文档**: 请查看 [`pubmed_mcp/README.md`](pubmed_mcp/README.md)

---

## 🚀 快速开始

### 前置要求

- Python 3.9+（推荐 3.11+）
- FastMCP >= 2.13.0
- 网络连接（用于下载模型和访问 API）
- CUDA-capable GPU（推荐，用于图像搜索服务加速）

### 安装步骤

每个服务都有独立的依赖和配置，请分别安装：

#### 1. 图像搜索服务（推荐优先安装）

**重要**: 图像搜索服务可以为病理图片诊断提供重要参考依据，建议优先安装和配置。

```bash
cd image_search_mcp
conda create -n mcp-image-search-env python=3.11 -y
conda activate mcp-image-search-env
pip install -r requirements.txt

# 构建图谱索引（开发测试：每个类别200张）
python build_atlas.py \
    --source_dir /path/to/NCT-CRC-HE-100K/versions/1/NCT-CRC-HE-100K \
    --target_dir ./atlas_data_200 \
    --images_per_category 200

# 构建索引
python indexer.py --atlas_dir ./atlas_data_200

# 启动服务器
python server.py
# 服务器启动在 http://0.0.0.0:18930/sse
```

**注意**: 图像搜索服务需要先构建图谱索引才能使用。详细步骤请参考 [`image_search_mcp/README.md`](image_search_mcp/README.md)。

#### 2. 病理报告解析服务

```bash
cd pathology_mcp
pip install -r requirements.txt
python server.py
# 服务器启动在 http://0.0.0.0:18910/sse
```

#### 3. PubMed 文献搜索服务

```bash
cd pubmed_mcp
pip install -r requirements.txt
# 可选：配置 NCBI API Key 以提升速率限制
# export NCBI_API_KEY=your_api_key_here
python server.py
# 服务器启动在 http://0.0.0.0:18920/sse
```

```bash
cd image_search_mcp
conda create -n mcp-image-search-env python=3.11 -y
conda activate mcp-image-search-env
pip install -r requirements.txt

# 构建图谱索引（开发测试：每个类别200张）
python build_atlas.py \
    --source_dir /path/to/NCT-CRC-HE-100K/versions/1/NCT-CRC-HE-100K \
    --target_dir ./atlas_data_200 \
    --images_per_category 200

# 构建索引
python indexer.py --atlas_dir ./atlas_data_200

# 启动服务器
python server.py
# 服务器启动在 http://0.0.0.0:18930/sse
```

**注意**: 图像搜索服务需要先构建图谱索引才能使用。详细步骤请参考 [`image_search_mcp/README.md`](image_search_mcp/README.md)。

---

## 📚 服务详情

### 服务对比

| 服务 | 主要功能 | 技术栈 | 端口 | 依赖 | 诊断价值 |
|------|---------|--------|------|------|---------|
| **图像搜索** | 相似病例检索 | FastMCP + PLIP + ChromaDB | 18930 | FastMCP + PyTorch + ChromaDB | ⭐⭐⭐⭐⭐ 为病理图片诊断提供重要参考依据 |
| **病理报告解析** | 文本结构化提取 | FastMCP + 规则引擎 | 18910 | FastMCP | ⭐⭐⭐⭐ 结构化提取诊断信息 |
| **PubMed 搜索** | 文献检索 | FastMCP + NCBI API | 18920 | FastMCP + requests | ⭐⭐⭐ 提供文献参考 |

### 工作流程示例

**典型病理诊断工作流程**：

```
1. 用户上传病理切片图像
   ↓
2. 图像搜索服务 → 找到相似病例（为诊断提供重要参考依据）
   ↓
3. 用户输入病理报告文本
   ↓
4. 病理报告解析服务 → 提取结构化信息
   ↓
5. PubMed 搜索服务 → 查找相关文献
   ↓
6. 综合结果 → 辅助诊断决策
```

**核心价值**: 图像搜索服务通过视觉特征匹配，为病理医生提供相似历史病例的参考，这是病理诊断的重要依据之一。

---

## 📁 项目结构

```
mcp/
├── pathology_mcp/              # 病理报告解析服务
│   ├── server.py               # FastMCP 服务器
│   ├── requirements.txt        # Python 依赖
│   └── README.md               # 详细文档
│
├── pubmed_mcp/                 # PubMed 文献搜索服务
│   ├── server.py               # FastMCP 服务器
│   ├── requirements.txt        # Python 依赖
│   └── README.md               # 详细文档
│
├── image_search_mcp/           # 图像搜索服务
│   ├── server.py               # FastMCP 服务器
│   ├── indexer.py              # 索引构建脚本
│   ├── plip_model.py           # PLIP 模型封装
│   ├── build_atlas.py          # 图谱构建工具
│   ├── requirements.txt        # Python 依赖
│   └── README.md               # 详细文档
│
├── mcp_server.py              # 示例 MCP 服务器
├── 图谱MCP.md                  # 开发文档
└── README.md                   # 本文档
```

---

## 💻 系统要求

### 基础要求

- **Python**: 3.9+（推荐 3.11+）
- **操作系统**: Linux, macOS, Windows
- **内存**: 至少 4GB RAM（图像搜索服务推荐 8GB+）
- **网络**: 稳定的网络连接

### 图像搜索服务额外要求

- **GPU**: CUDA-capable GPU（推荐，用于加速）
- **磁盘空间**: 
  - 开发测试：~300 MB
  - 生产环境：~15 GB（完整数据集）
- **Conda**: 用于环境管理（推荐）

### 依赖管理

每个服务都有独立的 `requirements.txt`，建议为每个服务创建独立的虚拟环境：

```bash
# 方式1: 使用 conda（推荐）
conda create -n mcp-pathology-env python=3.11
conda create -n mcp-pubmed-env python=3.11
conda create -n mcp-image-search-env python=3.11

# 方式2: 使用 venv
python -m venv venv_pathology
python -m venv venv_pubmed
python -m venv venv_image_search
```

---

## 🔗 Nexent 平台集成

### 配置步骤

在 Nexent 平台中配置这些 MCP 服务：

1. **添加 MCP 服务器**

   在 Nexent 的 MCP 配置中添加以下服务器：

   | 服务名称 | MCP URL | 端口 | 优先级 |
   |---------|---------|------|--------|
   | Image Search MCP | `http://172.17.0.1:18930/sse` | 18930 | ⭐⭐⭐⭐⭐ 推荐优先配置 |
   | Pathology MCP | `http://172.17.0.1:18910/sse` | 18910 | ⭐⭐⭐⭐ |
   | PubMed MCP | `http://172.17.0.1:18920/sse` | 18920 | ⭐⭐⭐ |

   **注意**: 
   - 如果 Nexent 在 Docker 中运行，使用 `172.17.0.1`（Docker 默认网关）
   - 如果同机运行，可以使用 `localhost` 或 `127.0.0.1`

2. **验证连接**

   启动各个服务后，在 Nexent 平台中测试工具调用，确保连接正常。

3. **使用工具**

   在 Nexent 的 AI Agent 中，这些工具会自动可用，可以通过自然语言或直接调用工具名称来使用。

### 集成示例

**在 Nexent 中使用图像搜索**（为病理图片诊断提供重要参考依据）：

```
用户: 上传一张病理切片图片，帮我找相似的病例作为诊断参考

Agent: 
1. 调用 search_similar_cases 工具
2. 返回 Top-5 相似病例
3. 展示诊断类别和相似度得分
4. 提供历史病例的视觉参考，辅助诊断决策
```

**在 Nexent 中使用病理报告解析**：

```
用户: 解析这份病理报告：[粘贴报告文本]

Agent:
1. 调用 extract_pathology_fields 工具
2. 提取结构化信息
3. 调用 interpret_ihc 和 map_mutations 解释结果
4. 返回结构化数据和临床意义
```

**在 Nexent 中使用 PubMed 搜索**：

```
用户: 查找关于 EGFR 突变的病例报告

Agent:
1. 调用 search_pubmed 工具
2. 搜索 "EGFR mutation" + Case Reports
3. 返回相关文献列表和摘要
```

---

## 📊 服务端口分配

| 服务 | 端口 | 协议 | 说明 |
|------|------|------|------|
| Pathology MCP | 18910 | SSE | 病理报告解析 |
| PubMed MCP | 18920 | SSE | 文献搜索 |
| Image Search MCP | 18930 | SSE | 图像搜索 |

**注意**: 确保这些端口未被其他服务占用。如需修改端口，请编辑各服务的 `server.py` 文件。

---

## 🔧 开发说明

### 扩展服务

每个服务都使用 FastMCP 框架，可以轻松扩展：

1. **添加新工具**: 使用 `@mcp.tool` 装饰器
2. **修改现有工具**: 编辑 `server.py` 中的工具函数
3. **集成外部服务**: 在工具函数中调用外部 API 或数据库

### 测试

每个服务都可以独立测试：

```bash
# 测试病理报告解析服务
cd pathology_mcp
python server.py
# 使用 MCP 客户端测试工具调用

# 测试 PubMed 搜索服务
cd pubmed_mcp
python server.py
# 使用 MCP 客户端测试工具调用

# 测试图像搜索服务
cd image_search_mcp
python server.py
# 使用 MCP 客户端测试工具调用
```

---

## 📖 详细文档

每个服务都有详细的 README 文档，包含：

- ✅ **原理概述**: 服务的工作原理和技术细节
- ✅ **快速开始**: 详细的安装和配置步骤
- ✅ **API 文档**: 完整的工具参数和返回格式说明
- ✅ **使用示例**: 实际使用场景和代码示例
- ✅ **配置说明**: 各种配置选项和优化建议
- ✅ **故障排除**: 常见问题和解决方案

**请查看各服务目录下的 README.md 获取详细信息**：

- 📄 [`pathology_mcp/README.md`](pathology_mcp/README.md) - 病理报告解析服务详细文档
- 📄 [`pubmed_mcp/README.md`](pubmed_mcp/README.md) - PubMed 搜索服务详细文档
- 📄 [`image_search_mcp/README.md`](image_search_mcp/README.md) - 图像搜索服务详细文档

---

## 📄 许可证

请参考项目根目录的 LICENSE 文件。

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 代码规范

- 遵循 PEP 8 Python 代码规范
- 添加适当的注释和文档字符串
- 更新相关的 README 文档

---

## 📧 联系方式

如有问题或建议，请通过 GitHub Issues 联系。

---

## 🙏 致谢

- **FastMCP**: MCP 协议服务器框架
- **PLIP**: 病理图像预训练模型（vinid/plip）
- **ChromaDB**: 向量数据库
- **NCBI**: PubMed API 服务
- **NCT-CRC-HE-100K**: 病理图像数据集

---

**最后更新**: 2025-12-07
