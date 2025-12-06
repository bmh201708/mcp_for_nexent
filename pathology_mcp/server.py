"""
Pathology MCP Server (rule-based starter).
- extract_pathology_fields: parse raw pathology text into structured JSON.
- interpret_ihc: simple rule-based hints for common IHC markers/panels.
- map_mutations: simple mapping for common mutations.

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
    (r"G([1-4])", None),
]
STAGE_REGEX = re.compile(r"pT\d[a-z]?(?:\s*/\s*pN\d[a-z]?)?(?:\s*/\s*pM[0-1])?", re.IGNORECASE)
SIZE_REGEX = re.compile(r"(\d+(?:\.\d+)?\s*(?:x|×)\s*\d+(?:\.\d+)?\s*(?:cm|mm))", re.IGNORECASE)
IHC_ITEM_REGEX = re.compile(r"([A-Za-z0-9+\-\.]+)\s*[:：]?\s*([0-3]\+|\+{1,3}|-?|positive|negative|弱阳性|强阳性|阴性|阳性)", re.IGNORECASE)
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


def _normalize_text(text: str) -> str:
    """Basic normalization: lowercase, unify punctuation/spacing."""
    norm = text or ""
    norm = norm.replace("：", ":").replace("；", ";").replace("，", ",").replace("。", ".")
    norm = norm.replace("×", "x")
    norm = norm.lower()
    return norm


def _match_site(text: str) -> Optional[str]:
    low = _normalize_text(text)
    for site, aliases in SITE_SYNONYMS.items():
        for alias in aliases:
            if alias.lower() in low:
                return site
    return None


def _extract_grade(text: str) -> Optional[str]:
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
    for m in IHC_ITEM_REGEX.finditer(text):
        raw = m.group(1).strip().upper()
        marker_key = raw.replace("-", "").replace("/", "")
        canonical = IHC_ALIASES.get(marker_key, raw)
        result = m.group(2).strip()
        items.append({"marker": canonical, "result": result})
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
    m = STAGE_REGEX.search(text)
    if m:
        return m.group(0)
    return None


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
    for term in ["invasive", "carcinoma", "adenocarcinoma", "squamous", "necrosis", "metastasis", "dysplasia", "sarcoma", "lymphoma"]:
        if term in norm:
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


if __name__ == "__main__":
    # Bind on all interfaces, uncommon port to avoid conflicts
    mcp.run(transport="sse", host="0.0.0.0", port=18910)
