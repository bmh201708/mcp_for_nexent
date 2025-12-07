# Pathology MCP 输入输出格式说明

## 📡 MCP 协议层面

### 服务器配置

- **协议**: SSE (Server-Sent Events)
- **服务器地址**: `http://0.0.0.0:18910/sse`
- **Docker 环境**: `http://172.17.0.1:18910/sse`

### MCP 请求格式

MCP 客户端通过 SSE 协议发送请求，请求格式遵循 MCP 标准协议：

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "extract_pathology_fields",
    "arguments": {
      "report_text": "病理报告文本内容..."
    }
  }
}
```

### MCP 响应格式

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"site\":\"lung\",\"grade\":\"G3\",...}"
      }
    ]
  }
}
```

---

## 🔧 工具函数层面

### 工具 1: `extract_pathology_fields`

**输入格式**:
- **参数名**: `report_text`
- **类型**: `string`
- **格式**: 原始病理报告文本（支持中英文混合）

**输出格式**:
- **类型**: `string` (JSON 格式)
- **内容**: 结构化 JSON 对象

**示例**:

**输入**:
```
患者，男性，65岁。右肺上叶切除标本。
病理诊断：右肺上叶浸润性腺癌，分化差（G3），大小约 2.5 x 1.8 cm。
TNM 分期：pT2N1M0。
免疫组化：TTF-1(+), Napsin(+), P40(-), CK5/6(-)。
基因检测：EGFR L858R 突变阳性，ALK 阴性。
```

**输出** (JSON 字符串):
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

---

### 工具 2: `extract_blood_test_fields`

**输入格式**:
- **参数名**: `report_text`
- **类型**: `string`
- **格式**: 血检报告文本（支持多种格式）

**支持的文本格式**:
- `项目名: 数值 单位 (参考范围)`
- `项目名 数值 单位`
- `项目名(数值) 单位`

**输出格式**:
- **类型**: `string` (JSON 格式)
- **内容**: 结构化 JSON 对象

**示例**:

**输入**:
```
血常规检查：
WBC: 6.5 ×10^9/L (参考范围: 3.5-10.0)
RBC: 4.2 ×10^12/L (参考范围: 4.0-5.5)
HGB: 125 g/L (参考范围: 120-160)
PLT: 220 ×10^9/L (参考范围: 100-300)

肝功能：
ALT: 45 U/L (参考范围: 0-40)
AST: 38 U/L (参考范围: 0-40)
```

**输出** (JSON 字符串):
```json
{
  "wbc": {
    "item": "WBC",
    "value": "6.5",
    "unit": "×10^9/L",
    "reference_range": "3.5-10.0",
    "abnormal": false
  },
  "rbc": {
    "item": "RBC",
    "value": "4.2",
    "unit": "×10^12/L",
    "reference_range": "4.0-5.5",
    "abnormal": false
  },
  "hgb": {
    "item": "HGB",
    "value": "125",
    "unit": "g/L",
    "reference_range": "120-160",
    "abnormal": false
  },
  "plt": {
    "item": "PLT",
    "value": "220",
    "unit": "×10^9/L",
    "reference_range": "100-300",
    "abnormal": false
  },
  "liver_function": [
    {
      "item": "ALT",
      "value": "45",
      "unit": "U/L",
      "reference_range": "0-40",
      "abnormal": true
    },
    {
      "item": "AST",
      "value": "38",
      "unit": "U/L",
      "reference_range": "0-40",
      "abnormal": false
    }
  ],
  "kidney_function": null,
  "glucose": null,
  "lipid": null,
  "coagulation": null,
  "all_values": [
    {
      "item": "WBC",
      "value": "6.5",
      "unit": "×10^9/L",
      "reference_range": "3.5-10.0",
      "abnormal": false
    },
    ...
  ]
}
```

**字段说明**:
- `item`: 检测项目名称
- `value`: 检测数值（字符串格式）
- `unit`: 单位
- `reference_range`: 参考范围（格式：`低值-高值`）
- `abnormal`: 是否异常（`true`/`false`/`null`）

---

### 工具 3: `extract_hormone_fields`

**输入格式**:
- **参数名**: `report_text`
- **类型**: `string`
- **格式**: 激素检测报告文本

**输出格式**:
- **类型**: `string` (JSON 格式)

**示例**:

**输入**:
```
甲状腺功能检查：
TSH: 2.5 mIU/L (参考范围: 0.4-4.0)
FT3: 4.2 pmol/L (参考范围: 3.1-6.8)
FT4: 15.5 pmol/L (参考范围: 12.0-22.0)

性激素检查：
E2: 180 pg/mL (参考范围: 50-300)
P: 15 ng/mL (参考范围: 5-20)
```

**输出** (JSON 字符串):
```json
{
  "thyroid": [
    {
      "item": "TSH",
      "value": "2.5",
      "unit": "mIU/L",
      "reference_range": "0.4-4.0",
      "abnormal": false
    },
    {
      "item": "FT3",
      "value": "4.2",
      "unit": "pmol/L",
      "reference_range": "3.1-6.8",
      "abnormal": false
    },
    {
      "item": "FT4",
      "value": "15.5",
      "unit": "pmol/L",
      "reference_range": "12.0-22.0",
      "abnormal": false
    }
  ],
  "sex_hormones": [
    {
      "item": "E2",
      "value": "180",
      "unit": "pg/mL",
      "reference_range": "50-300",
      "abnormal": false
    },
    {
      "item": "P",
      "value": "15",
      "unit": "ng/mL",
      "reference_range": "5-20",
      "abnormal": false
    }
  ],
  "cortisol": null,
  "insulin": null,
  "growth_hormone": null,
  "all_values": [...]
}
```

---

### 工具 4: `extract_tumor_marker_fields`

**输入格式**:
- **参数名**: `report_text`
- **类型**: `string`
- **格式**: 肿瘤标志物检测报告文本

**输出格式**:
- **类型**: `string` (JSON 格式)

**示例**:

**输入**:
```
肿瘤标志物检查：
CEA: 5.2 ng/mL (参考范围: 0-5.0)
CA19-9: 25.0 U/mL (参考范围: 0-37)
CA125: 18.5 U/mL (参考范围: 0-35)
```

**输出** (JSON 字符串):
```json
{
  "markers": [
    {
      "item": "CEA",
      "value": "5.2",
      "unit": "ng/mL",
      "reference_range": "0-5.0",
      "abnormal": true
    },
    {
      "item": "CA19-9",
      "value": "25.0",
      "unit": "U/mL",
      "reference_range": "0-37",
      "abnormal": false
    },
    {
      "item": "CA125",
      "value": "18.5",
      "unit": "U/mL",
      "reference_range": "0-35",
      "abnormal": false
    }
  ],
  "all_values": [...]
}
```

---

### 工具 5: `interpret_ihc`

**输入格式**:
- **参数名**: `ihc_text`
- **类型**: `string`
- **格式**: 支持以下三种格式：
  1. **JSON 格式**: `[{"marker": "TTF-1", "result": "positive"}]`
  2. **逗号分隔**: `TTF-1: positive, P40: negative`
  3. **自由文本**: 自动提取标记和结果

**输出格式**:
- **类型**: `string` (纯文本，多行)
- **格式**: 每行一个标记的解释

**示例**:

**输入**:
```
TTF-1: positive, P40: negative, ER: positive
```

**输出** (纯文本):
```
TTF-1(positive): 肺腺常阳性，提示肺来源/腺系
P40(negative): 鳞系标志，鳞癌常阳性
ER(positive): 乳腺/妇科相关，ER阳性提示激素相关
```

---

### 工具 6: `map_mutations`

**输入格式**:
- **参数名**: `mutations_text`
- **类型**: `string`
- **格式**: 支持以下三种格式：
  1. **JSON 格式**: `[{"gene": "EGFR", "value": "L858R"}]`
  2. **逗号分隔**: `EGFR: L858R, ALK: negative`
  3. **自由文本**: 自动提取基因和变异

**输出格式**:
- **类型**: `string` (纯文本，多行)
- **格式**: 每行一个基因突变的解释

**示例**:

**输入**:
```
EGFR: L858R, ALK: negative, KRAS: G12C
```

**输出** (纯文本):
```
EGFR: L858R -> NSCLC 常见驱动，部分突变可用 EGFR-TKI
ALK: negative -> NSCLC 融合，ALK 抑制剂可选
KRAS: G12C -> KRAS 驱动，特定亚型有靶向（如 G12C）
```

---

## 📝 通用说明

### 输入要求

1. **文本编码**: UTF-8
2. **支持语言**: 中文、英文、中英文混合
3. **格式灵活性**: 
   - 支持多种文本格式（冒号分隔、空格分隔、括号格式等）
   - 自动识别和解析

### 输出说明

1. **JSON 工具** (`extract_*_fields`):
   - 返回 JSON 字符串（需要客户端解析）
   - 使用 `json.dumps()` 序列化，`ensure_ascii=False` 保留中文
   - `null` 值表示该字段未找到或为空

2. **文本工具** (`interpret_ihc`, `map_mutations`):
   - 返回纯文本字符串
   - 多行格式，每行一个结果

### 错误处理

- 如果输入为空或无法解析，返回空结果或默认值
- JSON 工具返回空对象 `{}` 或包含 `null` 字段的对象
- 文本工具返回提示信息（如 "未能解析 IHC 输入"）

### 数据类型

- **数值**: 以字符串形式返回（如 `"6.5"`），便于处理各种单位
- **布尔值**: `true`/`false` 表示异常值标记
- **数组**: 使用列表 `[]` 表示多个项目
- **对象**: 使用字典 `{}` 表示结构化数据

---

## 🔗 与 Nexent 平台集成

### Nexent 调用示例

Nexent 平台通过 MCP 客户端调用工具：

```python
# Nexent 后端调用示例（伪代码）
response = mcp_client.call_tool(
    tool_name="extract_blood_test_fields",
    arguments={
        "report_text": user_uploaded_text
    }
)

# response 是 JSON 字符串，需要解析
result = json.loads(response)
```

### 注意事项

1. **文本长度**: 建议单次输入不超过 10,000 字符
2. **格式要求**: 虽然支持多种格式，但规范格式（`项目名: 数值 单位`）解析准确度更高
3. **参考范围**: 如果报告中包含参考范围，会自动标记异常值

---

**最后更新**: 2025-12-07

