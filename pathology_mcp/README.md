# 病理报告解析 MCP Server

基于 FastMCP 的病理报告结构化解析和基础解释服务，使用规则引擎从原始病理文本中提取结构化信息，并提供 IHC 标记和基因突变的临床意义解释。

## 📋 目录

- [原理概述](#原理概述)
- [功能特性](#功能特性)
- [技术架构](#技术架构)
- [快速开始](#快速开始)
- [API 文档](#api-文档)
- [使用示例](#使用示例)
- [配置说明](#配置说明)
- [故障排除](#故障排除)

---

## 🔬 原理概述

### 病理报告结构化解析

病理报告是临床诊断的重要依据，但通常以非结构化的文本形式存在。本 MCP 服务通过规则引擎和正则表达式，从原始病理文本中自动提取关键信息：

```
原始病理文本 → 规则匹配 → 结构化JSON → 临床解释
     ↓              ↓           ↓            ↓
  自由文本    正则表达式    字段提取    IHC/突变解释
```

### 核心处理流程

1. **文本标准化**
   - 统一中英文标点符号
   - 转换为小写（部分字段）
   - 规范化空格和特殊字符

2. **字段提取**
   - **解剖部位**：匹配器官和组织类型（支持中英文）
   - **分化程度**：提取肿瘤分级（G1-G4 或文字描述）
   - **TNM 分期**：提取 pT/pN/pM 分期信息
   - **病变大小**：提取尺寸信息（cm/mm）
   - **IHC 标记**：提取免疫组化标记及其结果
   - **基因突变**：提取常见驱动基因突变
   - **关键术语**：识别重要病理学术语

3. **临床解释**
   - IHC 标记的临床意义提示
   - 基因突变的靶向治疗关联

---

## ✨ 功能特性

### 1. `extract_pathology_fields` - 病理报告字段提取

从原始病理文本中提取结构化字段，返回 JSON 格式数据。

**提取的字段**：
- `site`: 解剖部位（如 lung, breast, colon 等）
- `grade`: 分化程度（如 well differentiated, G1-G4）
- `stage`: TNM 分期（如 pT1N0M0）
- `lesion_size`: 病变大小（如 2.5 x 1.8 cm）
- `ihc`: IHC 标记列表（标记名称和结果）
- `mutations`: 基因突变列表（基因名称和变异）
- `key_terms`: 关键术语列表（如 invasive, carcinoma 等）

### 2. `interpret_ihc` - IHC 标记解释

对常见免疫组化（IHC）标记提供临床意义解释。

**支持的标记**：
- TTF-1, Napsin（肺腺癌相关）
- P40, CK5/6（鳞癌相关）
- ER, PR（激素受体）
- HER2（HER2 扩增）
- Ki67（增殖指数）

### 3. `map_mutations` - 基因突变映射

将常见驱动基因突变映射到临床意义和靶向治疗关联。

**支持的基因**：
- EGFR（EGFR-TKI 靶向）
- ALK（ALK 抑制剂）
- KRAS（特定亚型有靶向）
- BRAF（BRAF/MEK 抑制）
- HER2（抗 HER2 治疗）
- PIK3CA（PI3K 抑制剂）

---

## 🏗️ 技术架构

### 技术栈

| 组件 | 技术选型 | 版本要求 | 用途 |
|------|---------|---------|------|
| **框架** | FastMCP | >= 2.13.0 | MCP 协议服务器框架 |
| **文本处理** | Python re | 标准库 | 正则表达式匹配 |
| **数据格式** | JSON | 标准库 | 结构化数据输出 |

### 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    Nexent Platform                      │
│  ┌──────────────┐         ┌──────────────────────────┐ │
│  │  Frontend    │ ──────> │  MCP Client (SSE)       │ │
│  │  (输入病理文本) │         │  http://host:18910/sse   │ │
│  └──────────────┘         └──────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│              Pathology MCP Server                      │
│  ┌──────────────────────────────────────────────────┐   │
│  │  FastMCP Server (server.py)                     │   │
│  │  - extract_pathology_fields                    │   │
│  │  - interpret_ihc                              │   │
│  │  - map_mutations                              │   │
│  └──────────────────────────────────────────────────┘   │
│                            │                            │
│  ┌────────────────────────┴────────────────────────┐   │
│  │                                                 │   │
│  ▼                                                 ▼   │
│  ┌──────────────────┐              ┌────────────────┐ │
│  │ 规则引擎         │              │ 知识库         │ │
│  │ (正则表达式)     │              │ (IHC/突变提示)  │ │
│  │                  │              │                │ │
│  │ - 部位匹配       │              │ - IHC_HINTS    │ │
│  │ - 分级提取       │              │ - MUTATION_    │ │
│  │ - 分期提取       │              │   HINTS        │ │
│  └──────────────────┘              └────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 快速开始

### 前置要求

- Python 3.9+
- FastMCP 框架

### 步骤 1: 环境准备

```bash
# 创建 conda 环境（可选）
conda create -n mcp-env python=3.11 -y
conda activate mcp-env

# 安装依赖
cd ~/mcp/pathology_mcp
pip install -r requirements.txt
```

### 步骤 2: 启动服务器

```bash
python server.py
```

服务器将启动在 `http://0.0.0.0:18910/sse`

**验证服务器运行**：
```bash
# 检查日志输出
# 应该看到：
# - FastMCP server started
# - Uvicorn running on http://0.0.0.0:18910
```

### 步骤 3: Nexent 平台配置

在 Nexent 平台中配置 MCP 服务器：

1. **MCP 服务器 URL**: 
   - 如果 Nexent 在 Docker 中：`http://172.17.0.1:18910/sse`
   - 如果同机运行：`http://localhost:18910/sse`

2. **可用工具**:
   - `extract_pathology_fields`
   - `interpret_ihc`
   - `map_mutations`

---

## 📚 API 文档

### 工具 1: `extract_pathology_fields`

**描述**: 从原始病理报告文本中提取结构化字段。

**参数**:

| 参数名 | 类型 | 必需 | 说明 |
|--------|------|------|------|
| `report_text` | string | 是 | 原始病理报告文本（支持中英文） |

**返回格式**:

```json
{
  "site": "lung",
  "grade": "poorly differentiated",
  "stage": "pT2N1M0",
  "lesion_size": "2.5 x 1.8 cm",
  "ihc": [
    {"marker": "TTF-1", "result": "positive"},
    {"marker": "P40", "result": "negative"}
  ],
  "mutations": [
    {"gene": "EGFR", "value": "L858R"},
    {"gene": "ALK", "value": "negative"}
  ],
  "key_terms": ["invasive", "carcinoma", "adenocarcinoma"]
}
```

**字段说明**:
- `site`: 解剖部位（如 lung, breast, colon 等，unknown 表示未识别）
- `grade`: 分化程度（如 well/moderately/poorly differentiated 或 G1-G4）
- `stage`: TNM 分期（如 pT1N0M0）
- `lesion_size`: 病变大小（如 "2.5 x 1.8 cm"）
- `ihc`: IHC 标记数组，每个元素包含 `marker` 和 `result`
- `mutations`: 基因突变数组，每个元素包含 `gene` 和 `value`
- `key_terms`: 关键术语数组（如 invasive, carcinoma 等）

### 工具 2: `interpret_ihc`

**描述**: 对 IHC 标记提供临床意义解释。

**参数**:

| 参数名 | 类型 | 必需 | 说明 |
|--------|------|------|------|
| `ihc_text` | string | 是 | IHC 标记文本，支持以下格式：<br>- JSON 格式：`[{"marker": "TTF-1", "result": "positive"}]`<br>- 逗号分隔：`TTF-1: positive, P40: negative`<br>- 自由文本：自动提取标记和结果 |

**返回格式**:

```
TTF-1(positive): 肺腺常阳性，提示肺来源/腺系
P40(negative): 鳞系标志，鳞癌常阳性
Ki67(30%): 增殖指数，数值越高增殖越强
```

### 工具 3: `map_mutations`

**描述**: 将基因突变映射到临床意义和靶向治疗关联。

**参数**:

| 参数名 | 类型 | 必需 | 说明 |
|--------|------|------|------|
| `mutations_text` | string | 是 | 突变文本，支持以下格式：<br>- JSON 格式：`[{"gene": "EGFR", "value": "L858R"}]`<br>- 逗号分隔：`EGFR: L858R, ALK: negative`<br>- 自由文本：自动提取基因和变异 |

**返回格式**:

```
EGFR: L858R -> NSCLC 常见驱动，部分突变可用 EGFR-TKI
ALK: negative -> NSCLC 融合，ALK 抑制剂可选
KRAS: G12C -> KRAS 驱动，特定亚型有靶向（如 G12C）
```

---

## 💡 使用示例

### 示例 1: 提取病理报告字段

**输入文本**：
```
患者，男性，65岁。右肺上叶切除标本。
病理诊断：右肺上叶浸润性腺癌，分化差（G3），大小约 2.5 x 1.8 cm。
TNM 分期：pT2N1M0。
免疫组化：TTF-1(+), Napsin(+), P40(-), CK5/6(-)。
基因检测：EGFR L858R 突变阳性，ALK 阴性。
```

**调用**：
```json
{
  "tool": "extract_pathology_fields",
  "parameters": {
    "report_text": "患者，男性，65岁。右肺上叶切除标本。病理诊断：右肺上叶浸润性腺癌，分化差（G3），大小约 2.5 x 1.8 cm。TNM 分期：pT2N1M0。免疫组化：TTF-1(+), Napsin(+), P40(-), CK5/6(-)。基因检测：EGFR L858R 突变阳性，ALK 阴性。"
  }
}
```

**输出**：
```json
{
  "site": "lung",
  "grade": "G3",
  "stage": "pT2N1M0",
  "lesion_size": "2.5 x 1.8 cm",
  "ihc": [
    {"marker": "TTF-1", "result": "+"},
    {"marker": "Napsin", "result": "+"},
    {"marker": "P40", "result": "-"},
    {"marker": "CK5/6", "result": "-"}
  ],
  "mutations": [
    {"gene": "EGFR", "value": "L858R"},
    {"gene": "ALK", "value": "negative"}
  ],
  "key_terms": ["invasive", "carcinoma", "adenocarcinoma"]
}
```

### 示例 2: 解释 IHC 标记

**输入**：
```
TTF-1: positive, P40: negative, ER: positive
```

**输出**：
```
TTF-1(positive): 肺腺常阳性，提示肺来源/腺系
P40(negative): 鳞系标志，鳞癌常阳性
ER(positive): 乳腺/妇科相关，ER阳性提示激素相关
```

### 示例 3: 映射基因突变

**输入**：
```
EGFR: L858R, ALK: negative, KRAS: G12C
```

**输出**：
```
EGFR: L858R -> NSCLC 常见驱动，部分突变可用 EGFR-TKI
ALK: negative -> NSCLC 融合，ALK 抑制剂可选
KRAS: G12C -> KRAS 驱动，特定亚型有靶向（如 G12C）
```

---

## ⚙️ 配置说明

### 服务器配置

- **端口**: 18910
- **协议**: SSE (Server-Sent Events)
- **监听地址**: `0.0.0.0:18910/sse`

### 支持的解剖部位

系统支持以下解剖部位的中英文识别：

| 英文 | 中文 | 别名 |
|------|------|------|
| lung | 肺 | pulm, pulmonary, pneumo |
| breast | 乳腺 | mammary |
| colon | 结肠 | colonic |
| stomach | 胃 | gastric |
| liver | 肝 | hepatic |
| ... | ... | ... |

完整列表请参考 `server.py` 中的 `SITE_SYNONYMS` 字典。

### 支持的 IHC 标记

系统内置了常见 IHC 标记的临床意义提示：

- **肺相关**: TTF-1, Napsin, P40, CK5/6
- **乳腺/妇科**: ER, PR, HER2
- **增殖**: Ki67

### 支持的基因突变

系统内置了常见驱动基因的临床意义：

- **NSCLC**: EGFR, ALK, KRAS, BRAF, ROS1, MET, RET
- **其他**: HER2, PIK3CA

---

## 🔍 故障排除

### 1. 字段提取不准确

**问题**: 某些字段未能正确提取

**可能原因**:
- 文本格式不规范
- 使用了不常见的术语
- 中英文混用导致匹配失败

**解决**:
- 检查文本格式是否规范
- 查看 `server.py` 中的匹配规则
- 可以扩展 `SITE_SYNONYMS`、`IHC_HINTS` 等字典

### 2. IHC 标记未识别

**问题**: IHC 标记无法识别或解释

**可能原因**:
- 标记名称拼写不同
- 结果格式不规范

**解决**:
- 检查标记名称是否正确（支持常见别名）
- 确保结果格式为 `positive/negative/+/-` 等
- 可以扩展 `IHC_ALIASES` 字典添加别名

### 3. 端口被占用

**错误**: `Address already in use`

**解决**:
```bash
# 查找占用端口的进程
lsof -i :18910

# 杀死进程
kill -9 <PID>

# 或修改 server.py 中的端口号
```

### 4. Nexent 连接失败

**问题**: Nexent 平台无法连接到 MCP 服务器

**解决**:
- 检查服务器是否正常运行
- 确认网络配置（Docker 环境需要配置 `172.17.0.1`）
- 检查防火墙设置

---

## 📝 开发说明

### 扩展功能

本服务使用规则引擎，适合作为起点。可以扩展：

1. **添加更多解剖部位**
   - 修改 `SITE_SYNONYMS` 字典

2. **添加更多 IHC 标记**
   - 修改 `IHC_HINTS` 字典
   - 添加 `IHC_ALIASES` 别名

3. **添加更多基因突变**
   - 修改 `MUTATION_HINTS` 字典
   - 添加 `MUT_ALIASES` 别名

4. **集成 NLP 模型**
   - 替换规则引擎为 NLP 模型
   - 使用 BERT/BioBERT 等医学领域模型

5. **连接数据库**
   - 存储历史报告
   - 建立知识库

### 项目结构

```
pathology_mcp/
├── server.py          # FastMCP 服务器主文件
├── requirements.txt   # Python 依赖
└── README.md         # 本文档
```

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
