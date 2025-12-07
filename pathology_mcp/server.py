"""
Pathology MCP Server (rule-based starter).
支持多种医学报告类型的结构化解析：
- extract_pathology_fields: 肿瘤病理报告字段提取
- extract_blood_test_fields: 血检报告字段提取
- extract_hormone_fields: 激素报告字段提取
- extract_tumor_marker_fields: 肿瘤标志物报告字段提取
- interpret_ihc: IHC 标记解释
- map_mutations: 基因突变映射

Run:
  conda activate mcp-env  # env with fastmcp installed
  python server.py

Server URL: http://0.0.0.0:18910/sse
If Nexent runs in Docker, use http://172.17.0.1:18910/sse or add extra_hosts for host.docker.internal.
"""
import json
import re
from typing import Dict, List, Optional

from fastmcp import FastMCP

mcp = FastMCP(name="Pathology MCP Server")

SITE_SYNONYMS = {
    "lung": ["lung", "pulm", "pulmonary", "pneumo", "肺"],
    "breast": ["breast", "mammary", "乳腺"],
    "colon": ["colon", "colonic", "结肠"],
    "rectum": ["rectum", "rectal", "直肠"],
    "stomach": ["stomach", "gastric", "胃"],
    "liver": ["liver", "hepatic", "肝"],
    "pancreas": ["pancreas", "pancreatic", "胰"],
    "prostate": ["prostate", "prostatic", "前列腺"],
    "kidney": ["kidney", "renal", "肾"],
    "bladder": ["bladder", "vesical", "膀胱"],
    "cervix": ["cervix", "cervical", "宫颈"],
    "ovary": ["ovary", "ovarian", "卵巢"],
    "endometrium": ["endometrium", "endometrial", "子宫内膜"],
    "thyroid": ["thyroid", "thyroidal", "甲状腺"],
    "skin": ["skin", "cutaneous", "皮肤"],
    "brain": ["brain", "cerebral", "脑"],
    "esophagus": ["esophagus", "esophageal", "食管", "食道"],
    "nasopharynx": ["nasopharynx", "nasopharyngeal", "鼻咽"],
    "oropharynx": ["oropharynx", "oropharyngeal", "口咽"],
}
GRADE_PATTERNS = [
    (r"well[- ]differentiated|highly differentiated", "well differentiated"),
    (r"moderately[- ]differentiated", "moderately differentiated"),
    (r"poorly[- ]differentiated|poorly diff", "poorly differentiated"),
    (r"g([1-4])", None),  # 改为小写，因为文本会被normalize为小写
]
STAGE_REGEX = re.compile(r"pT\d+[a-z]?(?:N\d+[a-z]?)?(?:M[0-1])?|pT\d+[a-z]?(?:\s*/\s*pN\d+[a-z]?)?(?:\s*/\s*pM[0-1])?", re.IGNORECASE)
SIZE_REGEX = re.compile(r"(\d+(?:\.\d+)?\s*(?:x|×)\s*\d+(?:\.\d+)?\s*(?:cm|mm))", re.IGNORECASE)
# 改进 IHC 正则：要求标记名称至少包含一个字母，且结果部分必须明确
IHC_ITEM_REGEX = re.compile(r"([A-Za-z][A-Za-z0-9\-/\.]*)\s*[:：]?\s*\(?([0-3]\+|\+{1,3}|-|negative|positive|弱阳性|强阳性|阴性|阳性|%?\d+%?)\)?", re.IGNORECASE)
MUTATION_REGEX = re.compile(r"(EGFR|ALK|KRAS|BRAF|HER2|ER|PR|PIK3CA|ROS1|MET|RET|NTRK)\s*[:：\-]?\s*([A-Za-z0-9.+\-_/]+)", re.IGNORECASE)

IHC_HINTS = {
    "TTF-1": "肺腺常阳性，提示肺来源/腺系",
    "Napsin": "肺腺或肾相关，可提示肺腺来源",
    "P40": "鳞系标志，鳞癌常阳性",
    "CK5/6": "鳞系/部分腺鳞，支持鳞分化",
    "ER": "乳腺/妇科相关，ER阳性提示激素相关",
    "PR": "乳腺/妇科相关，PR阳性提示激素相关",
    "HER2": "乳腺/胃腺相关，注意分级和FISH",
    "Ki67": "增殖指数，数值越高增殖越强",
}

MUTATION_HINTS = {
    "EGFR": "NSCLC 常见驱动，部分突变可用 EGFR-TKI",
    "ALK": "NSCLC 融合，ALK 抑制剂可选",
    "KRAS": "KRAS 驱动，特定亚型有靶向（如 G12C）",
    "BRAF": "BRAF V600 系列可考虑 BRAF/MEK 抑制",
    "HER2": "HER2 扩增/突变可能考虑抗 HER2 治疗",
    "PIK3CA": "乳腺等可见，部分场景有 PI3K 抑制剂",
}
IHC_ALIASES = {
    "TTF1": "TTF-1",
    "NAPSA": "Napsin",
    "NAPSIN": "Napsin",
    "CK5-6": "CK5/6",
    "CK5/6": "CK5/6",
    "CK5": "CK5/6",
}
MUT_ALIASES = {
    "ERBB2": "HER2",
}

# 血检项目关键词映射
BLOOD_TEST_KEYWORDS = {
    # 血常规
    "wbc": ["WBC", "白细胞", "白细胞计数", "white blood cell", "leukocyte"],
    "rbc": ["RBC", "红细胞", "红细胞计数", "red blood cell", "erythrocyte"],
    "hgb": ["HGB", "Hb", "血红蛋白", "hemoglobin"],
    "hct": ["HCT", "Ht", "红细胞压积", "hematocrit"],
    "plt": ["PLT", "血小板", "血小板计数", "platelet"],
    "mcv": ["MCV", "平均红细胞体积"],
    "mch": ["MCH", "平均血红蛋白量"],
    "mchc": ["MCHC", "平均血红蛋白浓度"],
    # 肝功能
    "alt": ["ALT", "GPT", "丙氨酸转氨酶", "alanine aminotransferase"],
    "ast": ["AST", "GOT", "天冬氨酸转氨酶", "aspartate aminotransferase"],
    "alp": ["ALP", "ALKP", "碱性磷酸酶", "alkaline phosphatase"],
    "ggt": ["GGT", "γ-GT", "γ-谷氨酰转肽酶", "gamma-glutamyl transferase"],
    "tbil": ["TBIL", "总胆红素", "total bilirubin"],
    "dbil": ["DBIL", "直接胆红素", "direct bilirubin"],
    "alb": ["ALB", "白蛋白", "albumin"],
    "tp": ["TP", "总蛋白", "total protein"],
    # 肾功能
    "crea": ["CREA", "Cr", "肌酐", "creatinine"],
    "bun": ["BUN", "urea", "尿素氮", "blood urea nitrogen"],
    "ua": ["UA", "uric acid", "尿酸"],
    "egfr": ["eGFR", "估算肾小球滤过率"],
    # 血糖
    "glucose": ["GLU", "GLUC", "血糖", "glucose", "blood glucose"],
    "hba1c": ["HbA1c", "糖化血红蛋白", "glycated hemoglobin"],
    # 血脂
    "chol": ["CHOL", "TC", "总胆固醇", "total cholesterol"],
    "tg": ["TG", "triglyceride", "甘油三酯", "triglycerides"],
    "hdl": ["HDL", "HDL-C", "高密度脂蛋白", "high-density lipoprotein"],
    "ldl": ["LDL", "LDL-C", "低密度脂蛋白", "low-density lipoprotein"],
    # 凝血功能
    "pt": ["PT", "凝血酶原时间", "prothrombin time"],
    "aptt": ["APTT", "PTT", "活化部分凝血活酶时间", "activated partial thromboplastin time"],
    "inr": ["INR", "国际标准化比值", "international normalized ratio"],
    "fib": ["FIB", "fibrinogen", "纤维蛋白原"],
    "ddimer": ["D-Dimer", "D-二聚体"],
}

# 激素项目关键词映射
HORMONE_KEYWORDS = {
    # 甲状腺激素
    "tsh": ["TSH", "促甲状腺激素", "thyroid stimulating hormone"],
    "ft3": ["FT3", "fT3", "游离T3", "free T3"],
    "ft4": ["FT4", "fT4", "游离T4", "free T4"],
    "t3": ["T3", "三碘甲状腺原氨酸", "triiodothyronine"],
    "t4": ["T4", "甲状腺素", "thyroxine"],
    "rt3": ["rT3", "reverse T3", "反T3"],
    "tgab": ["TgAb", "抗甲状腺球蛋白抗体"],
    "tpoab": ["TPOAb", "抗甲状腺过氧化物酶抗体"],
    "trab": ["TRAb", "促甲状腺激素受体抗体"],
    # 性激素
    "e2": ["E2", "estradiol", "雌二醇"],
    "p": ["P", "progesterone", "孕酮", "黄体酮"],
    "t": ["T", "testosterone", "睾酮", "睾丸素"],
    "lh": ["LH", "luteinizing hormone", "促黄体生成素"],
    "fsh": ["FSH", "follicle stimulating hormone", "促卵泡刺激素"],
    "prl": ["PRL", "prolactin", "催乳素", "泌乳素"],
    "shbg": ["SHBG", "性激素结合球蛋白"],
    # 皮质醇
    "cortisol": ["cortisol", "CORT", "皮质醇", "可的松"],
    "acth": ["ACTH", "促肾上腺皮质激素", "adrenocorticotropic hormone"],
    # 胰岛素相关
    "insulin": ["insulin", "INS", "胰岛素"],
    "cpeptide": ["C-Peptide", "C肽", "C-peptide"],
    # 生长激素
    "gh": ["GH", "growth hormone", "生长激素"],
    "igf1": ["IGF-1", "胰岛素样生长因子1"],
}

# 肿瘤标志物关键词映射
TUMOR_MARKER_KEYWORDS = {
    "cea": ["CEA", "癌胚抗原", "carcinoembryonic antigen"],
    "ca199": ["CA19-9", "CA199", "糖链抗原19-9"],
    "ca125": ["CA125", "糖链抗原125"],
    "ca153": ["CA15-3", "CA153", "糖链抗原15-3"],
    "ca724": ["CA72-4", "CA724", "糖链抗原72-4"],
    "psa": ["PSA", "前列腺特异性抗原", "prostate specific antigen"],
    "fpsa": ["fPSA", "游离PSA", "free PSA"],
    "afp": ["AFP", "甲胎蛋白", "alpha-fetoprotein"],
    "ca242": ["CA242", "糖链抗原242"],
    "cyfra211": ["CYFRA21-1", "细胞角蛋白19片段"],
    "nse": ["NSE", "神经元特异性烯醇化酶"],
    "scc": ["SCC", "鳞状细胞癌抗原"],
    "he4": ["HE4", "人附睾蛋白4"],
    "progrp": ["ProGRP", "胃泌素释放肽前体"],
}


def _normalize_text(text: str) -> str:
    """Basic normalization: lowercase, unify punctuation/spacing."""
    norm = text or ""
    norm = norm.replace("：", ":").replace("；", ";").replace("，", ",").replace("。", ".")
    norm = norm.replace("×", "x")
    norm = norm.lower()
    return norm


def _extract_lab_values(text: str) -> List[Dict[str, str]]:
    """
    通用实验室数值提取函数。
    支持多种格式：
    - 项目名: 数值 单位
    - 项目名 数值 单位
    - 项目名(数值) 单位
    - 项目名 数值 (参考范围)
    """
    values = []
    # 匹配格式：项目名: 数值 单位 (参考范围)
    pattern1 = re.compile(
        r"([A-Za-z0-9+\-\./]+)\s*[:：]\s*([0-9]+\.?[0-9]*)\s*([A-Za-z0-9^/μ×\-\.%]+)?\s*(?:\(([0-9]+\.?[0-9]*)\s*[-~至]\s*([0-9]+\.?[0-9]*)\))?",
        re.IGNORECASE
    )
    # 匹配格式：项目名 数值 单位
    pattern2 = re.compile(
        r"([A-Za-z0-9+\-\./]+)\s+([0-9]+\.?[0-9]*)\s+([A-Za-z0-9^/μ×\-\.%]+)",
        re.IGNORECASE
    )
    # 匹配格式：项目名(数值) 单位
    pattern3 = re.compile(
        r"([A-Za-z0-9+\-\./]+)\s*\(([0-9]+\.?[0-9]*)\)\s*([A-Za-z0-9^/μ×\-\.%]+)?",
        re.IGNORECASE
    )
    
    for pattern in [pattern1, pattern2, pattern3]:
        for m in pattern.finditer(text):
            item_name = m.group(1).strip()
            value = m.group(2).strip()
            unit = m.group(3).strip() if m.group(3) else ""
            ref_low = m.group(4) if len(m.groups()) >= 4 and m.group(4) else None
            ref_high = m.group(5) if len(m.groups()) >= 5 and m.group(5) else None
            
            item = {
                "item": item_name,
                "value": value,
                "unit": unit,
            }
            if ref_low and ref_high:
                item["reference_range"] = f"{ref_low}-{ref_high}"
                try:
                    val_float = float(value)
                    low_float = float(ref_low)
                    high_float = float(ref_high)
                    item["abnormal"] = val_float < low_float or val_float > high_float
                except ValueError:
                    item["abnormal"] = None
            else:
                item["abnormal"] = None
            
            # 避免重复添加
            if not any(v["item"] == item_name and v["value"] == value for v in values):
                values.append(item)
    
    return values


def _detect_report_type(text: str) -> str:
    """根据关键词识别报告类型"""
    text_lower = text.lower()
    
    # 血检关键词
    blood_keywords = ["血常规", "血检", "生化", "肝功能", "肾功能", "凝血", "wbc", "rbc", "hgb", "plt", "alt", "ast", "crea", "bun"]
    # 激素关键词
    hormone_keywords = ["激素", "tsh", "ft3", "ft4", "甲状腺", "性激素", "皮质醇", "insulin", "cortisol", "e2", "p", "t", "lh", "fsh"]
    # 肿瘤标志物关键词
    tumor_marker_keywords = ["肿瘤标志物", "cea", "ca19-9", "ca125", "psa", "afp", "ca153"]
    # 病理关键词
    pathology_keywords = ["病理", "病理诊断", "免疫组化", "ihc", "分化", "tnm", "carcinoma", "adenocarcinoma"]
    
    blood_score = sum(1 for kw in blood_keywords if kw in text_lower)
    hormone_score = sum(1 for kw in hormone_keywords if kw in text_lower)
    tumor_marker_score = sum(1 for kw in tumor_marker_keywords if kw in text_lower)
    pathology_score = sum(1 for kw in pathology_keywords if kw in text_lower)
    
    scores = {
        "blood_test": blood_score,
        "hormone": hormone_score,
        "tumor_marker": tumor_marker_score,
        "pathology": pathology_score,
    }
    
    max_score = max(scores.values())
    if max_score == 0:
        return "unknown"
    
    return max(scores.items(), key=lambda x: x[1])[0]


def _match_site(text: str) -> Optional[str]:
    low = _normalize_text(text)
    for site, aliases in SITE_SYNONYMS.items():
        for alias in aliases:
            if alias.lower() in low:
                return site
    return None


def _extract_grade(text: str) -> Optional[str]:
    # 先尝试在原始文本中搜索（保持大小写），因为 G3 等格式需要大写
    for pat, label in GRADE_PATTERNS:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            if label:
                return label
            if m.groups():
                return f"G{m.group(1)}"
    # 如果没找到，再尝试小写版本
    low = _normalize_text(text)
    for pat, label in GRADE_PATTERNS:
        m = re.search(pat, low)
        if m:
            if label:
                return label
            if m.groups():
                return f"G{m.group(1)}"
    return None


def _extract_ihc(text: str) -> List[Dict[str, str]]:
    items = []
    # 已知的 IHC 标记名称列表（用于过滤误匹配）
    known_markers = {
        "TTF-1", "TTF1", "NAPSIN", "NAPSA", "P40", "CK5/6", "CK5-6", "CK5", "CK6",
        "ER", "PR", "HER2", "KI67", "KI-67", "CD20", "CD3", "CD5", "CD10",
        "CD19", "CD23", "CD30", "CD45", "CD56", "CD79A", "CD138", "BCL2",
        "BCL6", "MYC", "P53", "P63", "P16", "VIMENTIN", "SMA", "DESMIN",
        "SYN", "CHROMOGRANIN", "CDX2", "Villin", "CEA", "PSA", "PSAP"
    }
    
    # 改进的正则：匹配 "标记名(结果)" 或 "标记名: 结果" 格式
    # 优先匹配已知标记名称
    patterns = [
        # 格式：TTF-1(+), Napsin(+), P40(-)
        re.compile(r"([A-Za-z][A-Za-z0-9\-/\.]+)\s*\(([0-3]\+|\+{1,3}|-|negative|positive|弱阳性|强阳性|阴性|阳性|%?\d+%?)\)", re.IGNORECASE),
        # 格式：TTF-1: positive, P40: negative
        re.compile(r"([A-Za-z][A-Za-z0-9\-/\.]+)\s*[:：]\s*([0-3]\+|\+{1,3}|-|negative|positive|弱阳性|强阳性|阴性|阳性|%?\d+%?)", re.IGNORECASE),
    ]
    
    for pattern in patterns:
        for m in pattern.finditer(text):
            raw = m.group(1).strip().upper()
            result = m.group(2).strip()
            
            # 过滤掉明显不是标记的内容
            if len(raw) < 2 or raw.isdigit() or raw in ["X", "CM", "TNM", "PT", "N", "M", "G3", "G2", "G1", "G4"]:
                continue
            
            # 过滤掉纯数字或单个字符的结果
            if result.isdigit() and len(result) > 2:  # 允许百分比数字如 "30"
                continue
            
            marker_key = raw.replace("-", "").replace("/", "")
            canonical = IHC_ALIASES.get(marker_key, raw)
            
            # 如果不在已知标记列表中，且不是通过别名匹配的，需要进一步验证
            if canonical not in known_markers and marker_key not in IHC_ALIASES:
                # 检查是否包含常见标记的关键词
                if not any(keyword in canonical for keyword in ["CD", "CK", "TTF", "NAPSIN", "P40", "ER", "PR", "HER", "KI"]):
                    continue
            
            # 清理结果：统一格式
            result_clean = result.replace("(", "").replace(")", "").strip()
            if result_clean.lower() in ["positive", "阳性", "弱阳性", "强阳性"]:
                result_clean = "+"
            elif result_clean.lower() in ["negative", "阴性"]:
                result_clean = "-"
            
            # 避免重复添加
            if not any(item["marker"] == canonical and item["result"] == result_clean for item in items):
                items.append({"marker": canonical, "result": result_clean})
    
    return items


def _extract_mutations(text: str) -> List[Dict[str, str]]:
    muts = []
    for m in MUTATION_REGEX.finditer(text):
        raw_gene = m.group(1).upper()
        gene = MUT_ALIASES.get(raw_gene, raw_gene)
        value = m.group(2).strip()
        muts.append({"gene": gene, "value": value})
    return muts


def _extract_size(text: str) -> Optional[str]:
    m = SIZE_REGEX.search(text)
    if m:
        return m.group(1)
    return None


def _extract_stage(text: str) -> Optional[str]:
    # 先尝试匹配连续格式（如 pT2N1M0）
    continuous_pattern = re.compile(r"pT\d+[a-z]?N\d+[a-z]?M[0-1]", re.IGNORECASE)
    m = continuous_pattern.search(text)
    if m:
        return m.group(0)
    
    # 再尝试匹配标准格式（如 pT2/pN1/pM0）
    m = STAGE_REGEX.search(text)
    if m:
        return m.group(0)
    return None


def _extract_blood_test_fields(text: str) -> Dict:
    """提取血检报告字段"""
    all_values = _extract_lab_values(text)
    text_upper = text.upper()
    
    # 分类提取
    wbc = None
    rbc = None
    hgb = None
    plt = None
    alt = None
    ast = None
    crea = None
    bun = None
    glucose = None
    chol = None
    tg = None
    hdl = None
    ldl = None
    pt = None
    aptt = None
    inr = None
    
    # 从 all_values 中查找特定项目
    for item in all_values:
        item_name_upper = item["item"].upper()
        for key, keywords in BLOOD_TEST_KEYWORDS.items():
            if any(kw.upper() in item_name_upper for kw in keywords):
                if key == "wbc" and wbc is None:
                    wbc = item
                elif key == "rbc" and rbc is None:
                    rbc = item
                elif key == "hgb" and hgb is None:
                    hgb = item
                elif key == "plt" and plt is None:
                    plt = item
                elif key == "alt" and alt is None:
                    alt = item
                elif key == "ast" and ast is None:
                    ast = item
                elif key == "crea" and crea is None:
                    crea = item
                elif key == "bun" and bun is None:
                    bun = item
                elif key == "glucose" and glucose is None:
                    glucose = item
                elif key == "chol" and chol is None:
                    chol = item
                elif key == "tg" and tg is None:
                    tg = item
                elif key == "hdl" and hdl is None:
                    hdl = item
                elif key == "ldl" and ldl is None:
                    ldl = item
                elif key == "pt" and pt is None:
                    pt = item
                elif key == "aptt" and aptt is None:
                    aptt = item
                elif key == "inr" and inr is None:
                    inr = item
    
    # 肝功能指标
    liver_function = []
    for item in all_values:
        item_name_upper = item["item"].upper()
        if any(kw.upper() in item_name_upper for kw in ["ALT", "AST", "ALP", "GGT", "TBIL", "DBIL", "ALB", "TP"]):
            liver_function.append(item)
    
    # 肾功能指标
    kidney_function = []
    for item in all_values:
        item_name_upper = item["item"].upper()
        if any(kw.upper() in item_name_upper for kw in ["CREA", "BUN", "UA", "eGFR"]):
            kidney_function.append(item)
    
    # 血脂指标
    lipid = []
    for item in all_values:
        item_name_upper = item["item"].upper()
        if any(kw.upper() in item_name_upper for kw in ["CHOL", "TG", "HDL", "LDL"]):
            lipid.append(item)
    
    # 凝血功能
    coagulation = []
    for item in all_values:
        item_name_upper = item["item"].upper()
        if any(kw.upper() in item_name_upper for kw in ["PT", "APTT", "INR", "FIB", "D-Dimer"]):
            coagulation.append(item)
    
    return {
        "wbc": wbc,
        "rbc": rbc,
        "hgb": hgb,
        "plt": plt,
        "liver_function": liver_function if liver_function else None,
        "kidney_function": kidney_function if kidney_function else None,
        "glucose": glucose,
        "lipid": lipid if lipid else None,
        "coagulation": coagulation if coagulation else None,
        "all_values": all_values,
    }


def _extract_hormone_fields(text: str) -> Dict:
    """提取激素报告字段"""
    all_values = _extract_lab_values(text)
    text_upper = text.upper()
    
    # 分类提取
    thyroid = []
    sex_hormones = []
    cortisol = None
    insulin = None
    growth_hormone = None
    
    for item in all_values:
        item_name_upper = item["item"].upper()
        # 甲状腺激素
        if any(kw.upper() in item_name_upper for kw in ["TSH", "FT3", "FT4", "T3", "T4", "rT3", "TgAb", "TPOAb", "TRAb"]):
            thyroid.append(item)
        # 性激素
        elif any(kw.upper() in item_name_upper for kw in ["E2", "ESTRADIOL", "P", "PROGESTERONE", "T", "TESTOSTERONE", "LH", "FSH", "PRL", "PROLACTIN", "SHBG"]):
            sex_hormones.append(item)
        # 皮质醇
        elif any(kw.upper() in item_name_upper for kw in ["CORTISOL", "CORT", "ACTH"]):
            if cortisol is None:
                cortisol = item
        # 胰岛素相关
        elif any(kw.upper() in item_name_upper for kw in ["INSULIN", "INS", "C-PEPTIDE", "CPEPTIDE"]):
            if insulin is None:
                insulin = item
        # 生长激素
        elif any(kw.upper() in item_name_upper for kw in ["GH", "GROWTH HORMONE", "IGF-1", "IGF1"]):
            if growth_hormone is None:
                growth_hormone = item
    
    return {
        "thyroid": thyroid if thyroid else None,
        "sex_hormones": sex_hormones if sex_hormones else None,
        "cortisol": cortisol,
        "insulin": insulin,
        "growth_hormone": growth_hormone,
        "all_values": all_values,
    }


def _extract_tumor_marker_fields(text: str) -> Dict:
    """提取肿瘤标志物报告字段"""
    all_values = _extract_lab_values(text)
    text_upper = text.upper()
    
    markers = []
    
    for item in all_values:
        item_name_upper = item["item"].upper()
        # 检查是否是肿瘤标志物
        is_marker = False
        for key, keywords in TUMOR_MARKER_KEYWORDS.items():
            if any(kw.upper() in item_name_upper for kw in keywords):
                is_marker = True
                break
        if is_marker:
            markers.append(item)
    
    return {
        "markers": markers if markers else None,
        "all_values": all_values,
    }


@mcp.tool(name="extract_pathology_fields", description="提取病理报告的结构化字段，返回 JSON 字符串")
def extract_pathology_fields(report_text: str) -> str:
    """Parse pathology text into structured fields (rule-based)."""
    text = report_text or ""
    norm = _normalize_text(text)
    site = _match_site(text) or "unknown"
    grade = _extract_grade(text)
    stage = _extract_stage(text)
    ihc = _extract_ihc(text)
    mutations = _extract_mutations(text)
    size = _extract_size(text)

    key_terms = []
    # 在原始文本中搜索关键术语（保持大小写不敏感）
    text_lower = text.lower()
    for term in ["invasive", "carcinoma", "adenocarcinoma", "squamous", "necrosis", "metastasis", "dysplasia", "sarcoma", "lymphoma"]:
        if term in text_lower:
            key_terms.append(term)

    data = {
        "site": site,
        "grade": grade,
        "stage": stage,
        "lesion_size": size,
        "ihc": ihc,
        "mutations": mutations,
        "key_terms": key_terms,
    }
    return json.dumps(data, ensure_ascii=False)


@mcp.tool(name="interpret_ihc", description="对常见 IHC 标记给出简单提示，输入 JSON 或逗号分隔的 marker:result")
def interpret_ihc(ihc_text: str) -> str:
    hints = []
    parsed: List[Dict[str, str]] = []
    try:
        parsed = json.loads(ihc_text)
        if isinstance(parsed, dict):
            parsed = [parsed]
    except Exception:
        # fallback: parse marker:result pairs
        parsed = _extract_ihc(ihc_text)

    for item in parsed:
        raw_marker = str(item.get("marker", "")).upper()
        marker_key = raw_marker.replace("-", "").replace("/", "")
        marker = IHC_ALIASES.get(marker_key, raw_marker)
        result = str(item.get("result", "")).strip()
        base = IHC_HINTS.get(marker)
        if base:
            hints.append(f"{marker}({result}): {base}")
        else:
            hints.append(f"{marker}({result}): 无预置提示，请结合上下文")
    return "\n".join(hints) if hints else "未能解析 IHC 输入"


@mcp.tool(name="map_mutations", description="将常见突变映射为简要意义，输入 JSON 或逗号分隔 gene:value")
def map_mutations(mutations_text: str) -> str:
    parsed: List[Dict[str, str]] = []
    try:
        parsed = json.loads(mutations_text)
        if isinstance(parsed, dict):
            parsed = [parsed]
    except Exception:
        for chunk in re.split(r"[\n,;]+", mutations_text):
            if not chunk.strip():
                continue
            parts = chunk.split(":")
            if len(parts) == 2:
                parsed.append({"gene": parts[0].strip(), "value": parts[1].strip()})
        # If still empty, try regex extraction from free text
        if not parsed:
            parsed = _extract_mutations(mutations_text)

    rows = []
    for item in parsed:
        raw_gene = str(item.get("gene", "")).upper()
        gene = MUT_ALIASES.get(raw_gene, raw_gene)
        value = str(item.get("value", "")).strip()
        hint = MUTATION_HINTS.get(gene, "无预置提示，需结合变异类型和指南")
        rows.append(f"{gene}: {value} -> {hint}")
    return "\n".join(rows) if rows else "未能解析突变输入"


@mcp.tool(name="extract_blood_test_fields", description="提取血检报告的结构化字段，包括血常规、生化、凝血功能等，返回 JSON 字符串")
def extract_blood_test_fields(report_text: str) -> str:
    """Parse blood test report into structured fields."""
    text = report_text or ""
    data = _extract_blood_test_fields(text)
    return json.dumps(data, ensure_ascii=False, default=str)


@mcp.tool(name="extract_hormone_fields", description="提取激素报告的结构化字段，包括甲状腺激素、性激素、皮质醇等，返回 JSON 字符串")
def extract_hormone_fields(report_text: str) -> str:
    """Parse hormone test report into structured fields."""
    text = report_text or ""
    data = _extract_hormone_fields(text)
    return json.dumps(data, ensure_ascii=False, default=str)


@mcp.tool(name="extract_tumor_marker_fields", description="提取肿瘤标志物报告的结构化字段，包括 CEA、CA19-9、PSA 等，返回 JSON 字符串")
def extract_tumor_marker_fields(report_text: str) -> str:
    """Parse tumor marker report into structured fields."""
    text = report_text or ""
    data = _extract_tumor_marker_fields(text)
    return json.dumps(data, ensure_ascii=False, default=str)


if __name__ == "__main__":
    # Bind on all interfaces, uncommon port to avoid conflicts
    mcp.run(transport="sse", host="0.0.0.0", port=18910)
