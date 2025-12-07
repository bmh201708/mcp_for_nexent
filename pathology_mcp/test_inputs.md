# Pathology MCP 测试输入示例

## 测试用例 1: 病理报告 (`extract_pathology_fields`)

### 输入文本

```
患者，男性，65岁。右肺上叶切除标本。
病理诊断：右肺上叶浸润性腺癌，分化差（G3），大小约 2.5 x 1.8 cm。
TNM 分期：pT2N1M0。
免疫组化：TTF-1(+), Napsin(+), P40(-), CK5/6(-), Ki67(30%)。
基因检测：EGFR L858R 突变阳性，ALK 阴性，KRAS 阴性。
```

### 预期输出字段

- `site`: "lung"
- `grade`: "G3"
- `stage`: "pT2N1M0"
- `lesion_size`: "2.5 x 1.8 cm"
- `ihc`: 包含 TTF-1, Napsin, P40, CK5/6, Ki67
- `mutations`: 包含 EGFR L858R

---

## 测试用例 2: 血检报告 (`extract_blood_test_fields`)

### 输入文本

```
血常规检查报告

患者信息：张三，男，45岁
检查日期：2024-12-07

血常规：
WBC: 6.5 ×10^9/L (参考范围: 3.5-10.0)
RBC: 4.2 ×10^12/L (参考范围: 4.0-5.5)
HGB: 125 g/L (参考范围: 120-160)
HCT: 0.38 (参考范围: 0.35-0.50)
PLT: 220 ×10^9/L (参考范围: 100-300)
MCV: 85 fL (参考范围: 80-100)
MCH: 28 pg (参考范围: 27-32)
MCHC: 330 g/L (参考范围: 320-360)

肝功能：
ALT: 45 U/L (参考范围: 0-40)
AST: 38 U/L (参考范围: 0-40)
ALP: 95 U/L (参考范围: 40-150)
GGT: 32 U/L (参考范围: 0-50)
TBIL: 15.2 μmol/L (参考范围: 5.0-21.0)
DBIL: 4.5 μmol/L (参考范围: 0-6.8)
ALB: 42 g/L (参考范围: 35-55)
TP: 68 g/L (参考范围: 60-80)

肾功能：
CREA: 85 μmol/L (参考范围: 60-110)
BUN: 5.2 mmol/L (参考范围: 2.9-7.1)
UA: 350 μmol/L (参考范围: 150-420)
eGFR: 95 mL/min/1.73m² (参考范围: >90)

血糖：
GLU: 5.5 mmol/L (参考范围: 3.9-6.1)
HbA1c: 5.8% (参考范围: 4.0-6.0)

血脂：
CHOL: 5.2 mmol/L (参考范围: 3.1-5.7)
TG: 1.5 mmol/L (参考范围: 0.45-1.70)
HDL: 1.2 mmol/L (参考范围: 1.0-1.6)
LDL: 3.2 mmol/L (参考范围: 0-3.4)

凝血功能：
PT: 12.5 秒 (参考范围: 11-13)
APTT: 35 秒 (参考范围: 28-40)
INR: 1.05 (参考范围: 0.8-1.2)
FIB: 3.2 g/L (参考范围: 2.0-4.0)
D-Dimer: 0.5 mg/L (参考范围: 0-0.5)
```

### 预期输出字段

- `wbc`: 包含 WBC 信息，`abnormal: false`
- `hgb`: 包含 HGB 信息
- `liver_function`: 包含 ALT（`abnormal: true`，因为 45 > 40）、AST 等
- `kidney_function`: 包含 CREA、BUN、UA、eGFR
- `glucose`: 包含 GLU
- `lipid`: 包含 CHOL、TG、HDL、LDL
- `coagulation`: 包含 PT、APTT、INR、FIB、D-Dimer

---

## 测试用例 3: 激素报告 (`extract_hormone_fields`)

### 输入文本

```
激素检测报告

患者信息：李四，女，35岁
检查日期：2024-12-07

甲状腺功能：
TSH: 2.5 mIU/L (参考范围: 0.4-4.0)
FT3: 4.2 pmol/L (参考范围: 3.1-6.8)
FT4: 15.5 pmol/L (参考范围: 12.0-22.0)
T3: 1.8 nmol/L (参考范围: 1.3-3.1)
T4: 120 nmol/L (参考范围: 66-181)
rT3: 0.4 nmol/L (参考范围: 0.2-0.8)
TgAb: 15 IU/mL (参考范围: 0-115)
TPOAb: 20 IU/mL (参考范围: 0-34)
TRAb: 0.8 IU/L (参考范围: 0-1.75)

性激素：
E2: 180 pg/mL (参考范围: 50-300)
P: 15 ng/mL (参考范围: 5-20)
T: 0.5 ng/mL (参考范围: 0.1-0.75)
LH: 8.5 mIU/mL (参考范围: 2.0-12.0)
FSH: 6.2 mIU/mL (参考范围: 3.0-8.1)
PRL: 25 ng/mL (参考范围: 5-25)
SHBG: 60 nmol/L (参考范围: 18-114)

皮质醇：
Cortisol: 180 ng/mL (参考范围: 50-250)
ACTH: 25 pg/mL (参考范围: 7.2-63.3)

胰岛素相关：
Insulin: 8.5 μIU/mL (参考范围: 2.6-24.9)
C-Peptide: 2.5 ng/mL (参考范围: 1.1-4.4)

生长激素：
GH: 2.5 ng/mL (参考范围: 0-5.0)
IGF-1: 180 ng/mL (参考范围: 100-300)
```

### 预期输出字段

- `thyroid`: 包含 TSH、FT3、FT4、T3、T4、rT3、TgAb、TPOAb、TRAb
- `sex_hormones`: 包含 E2、P、T、LH、FSH、PRL、SHBG
- `cortisol`: 包含 Cortisol、ACTH
- `insulin`: 包含 Insulin、C-Peptide
- `growth_hormone`: 包含 GH、IGF-1

---

## 测试用例 4: 肿瘤标志物报告 (`extract_tumor_marker_fields`)

### 输入文本

```
肿瘤标志物检测报告

患者信息：王五，男，58岁
检查日期：2024-12-07

肿瘤标志物：
CEA: 5.2 ng/mL (参考范围: 0-5.0)
CA19-9: 25.0 U/mL (参考范围: 0-37)
CA125: 18.5 U/mL (参考范围: 0-35)
CA15-3: 22.0 U/mL (参考范围: 0-30)
CA72-4: 4.5 U/mL (参考范围: 0-6.9)
CA242: 12.0 U/mL (参考范围: 0-20)
PSA: 2.8 ng/mL (参考范围: 0-4.0)
fPSA: 0.8 ng/mL (参考范围: 0-1.0)
AFP: 8.5 ng/mL (参考范围: 0-20)
CYFRA21-1: 2.5 ng/mL (参考范围: 0-3.3)
NSE: 12.0 ng/mL (参考范围: 0-16.3)
SCC: 1.2 ng/mL (参考范围: 0-1.5)
HE4: 45 pmol/L (参考范围: 0-70)
ProGRP: 35 pg/mL (参考范围: 0-81)
```

### 预期输出字段

- `markers`: 包含所有肿瘤标志物，其中 CEA 的 `abnormal: true`（因为 5.2 > 5.0）
- `all_values`: 包含所有检测项目的完整列表

---

## 测试用例 5: IHC 标记解释 (`interpret_ihc`)

### 输入文本（格式 1: 逗号分隔）

```
TTF-1: positive, P40: negative, ER: positive, PR: positive, HER2: negative, Ki67: 30%
```

### 输入文本（格式 2: JSON）

```json
[
  {"marker": "TTF-1", "result": "positive"},
  {"marker": "P40", "result": "negative"},
  {"marker": "ER", "result": "positive"},
  {"marker": "PR", "result": "positive"},
  {"marker": "HER2", "result": "negative"},
  {"marker": "Ki67", "result": "30%"}
]
```

### 预期输出

```
TTF-1(positive): 肺腺常阳性，提示肺来源/腺系
P40(negative): 鳞系标志，鳞癌常阳性
ER(positive): 乳腺/妇科相关，ER阳性提示激素相关
PR(positive): 乳腺/妇科相关，PR阳性提示激素相关
HER2(negative): 乳腺/胃腺相关，注意分级和FISH
Ki67(30%): 增殖指数，数值越高增殖越强
```

---

## 测试用例 6: 基因突变映射 (`map_mutations`)

### 输入文本（格式 1: 逗号分隔）

```
EGFR: L858R, ALK: negative, KRAS: G12C, BRAF: V600E, HER2: negative, PIK3CA: E545K
```

### 输入文本（格式 2: JSON）

```json
[
  {"gene": "EGFR", "value": "L858R"},
  {"gene": "ALK", "value": "negative"},
  {"gene": "KRAS", "value": "G12C"},
  {"gene": "BRAF", "value": "V600E"},
  {"gene": "HER2", "value": "negative"},
  {"gene": "PIK3CA", "value": "E545K"}
]
```

### 预期输出

```
EGFR: L858R -> NSCLC 常见驱动，部分突变可用 EGFR-TKI
ALK: negative -> NSCLC 融合，ALK 抑制剂可选
KRAS: G12C -> KRAS 驱动，特定亚型有靶向（如 G12C）
BRAF: V600E -> BRAF V600 系列可考虑 BRAF/MEK 抑制
HER2: negative -> HER2 扩增/突变可能考虑抗 HER2 治疗
PIK3CA: E545K -> 无预置提示，需结合变异类型和指南
```

---

## 快速测试命令

### 使用 curl 测试（需要 MCP 客户端）

```bash
# 测试病理报告提取
curl -X POST http://localhost:18910/sse \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "extract_pathology_fields",
      "arguments": {
        "report_text": "患者，男性，65岁。右肺上叶切除标本。病理诊断：右肺上叶浸润性腺癌，分化差（G3），大小约 2.5 x 1.8 cm。TNM 分期：pT2N1M0。免疫组化：TTF-1(+), Napsin(+), P40(-), CK5/6(-)。基因检测：EGFR L858R 突变阳性，ALK 阴性。"
      }
    }
  }'
```

### 使用 Python 测试

```python
import json
import requests

# 测试血检报告提取
url = "http://localhost:18910/sse"
payload = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "extract_blood_test_fields",
        "arguments": {
            "report_text": """血常规检查：
WBC: 6.5 ×10^9/L (参考范围: 3.5-10.0)
RBC: 4.2 ×10^12/L (参考范围: 4.0-5.5)
HGB: 125 g/L (参考范围: 120-160)
PLT: 220 ×10^9/L (参考范围: 100-300)

肝功能：
ALT: 45 U/L (参考范围: 0-40)
AST: 38 U/L (参考范围: 0-40)"""
        }
    }
}

response = requests.post(url, json=payload)
result = response.json()
print(json.dumps(result, indent=2, ensure_ascii=False))
```

---

## 注意事项

1. **文本格式**: 虽然支持多种格式，但使用冒号分隔格式（`项目名: 数值 单位`）解析准确度最高
2. **参考范围**: 如果报告中包含参考范围，会自动标记异常值
3. **中英文混合**: 支持中英文混合输入
4. **空值处理**: 如果某个字段未找到，返回 `null`

---

**最后更新**: 2025-12-07

