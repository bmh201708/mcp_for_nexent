"""
PubMed Search MCP
- search_pubmed: query PubMed (defaults to Case Reports) and return structured metadata/abstracts.

Usage:
  pip install -r requirements.txt
  NCBI_API_KEY=<optional> python server.py

Transport: SSE on 0.0.0.0:18920
"""
import json
import os
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional

import requests
from fastmcp import FastMCP


mcp = FastMCP(name="PubMed Search MCP")
BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
API_KEY = os.getenv("NCBI_API_KEY")
USER_AGENT = "nexent-mcp-pubmed/0.1 (contact@example.com)"


def _clamp_retmax(value: int) -> int:
    return max(1, min(value, 50))


def _add_api_key(params: Dict[str, str]) -> Dict[str, str]:
    if API_KEY:
        params["api_key"] = API_KEY
    return params


def _esearch(term: str, max_results: int, days_back: int, sort: str) -> List[str]:
    params = _add_api_key(
        {
            "db": "pubmed",
            "retmode": "json",
            "term": term,
            "retmax": str(_clamp_retmax(max_results)),
            "sort": sort,
            "reldate": str(max(0, days_back)),
        }
    )
    resp = requests.get(f"{BASE_URL}/esearch.fcgi", params=params, headers={"User-Agent": USER_AGENT}, timeout=12)
    resp.raise_for_status()
    data = resp.json()
    return data.get("esearchresult", {}).get("idlist", [])


def _esummary(pmids: List[str]) -> Dict[str, Dict]:
    params = _add_api_key(
        {
            "db": "pubmed",
            "retmode": "json",
            "id": ",".join(pmids),
        }
    )
    resp = requests.get(f"{BASE_URL}/esummary.fcgi", params=params, headers={"User-Agent": USER_AGENT}, timeout=12)
    resp.raise_for_status()
    data = resp.json()
    return data.get("result", {})


def _efetch_abstracts(pmids: List[str]) -> Dict[str, str]:
    if not pmids:
        return {}
    params = _add_api_key(
        {
            "db": "pubmed",
            "retmode": "xml",
            "id": ",".join(pmids),
        }
    )
    resp = requests.get(f"{BASE_URL}/efetch.fcgi", params=params, headers={"User-Agent": USER_AGENT}, timeout=15)
    resp.raise_for_status()
    abstracts: Dict[str, str] = {}
    root = ET.fromstring(resp.text)
    for article in root.findall(".//PubmedArticle"):
        pmid_elem = article.find(".//PMID")
        pmid = pmid_elem.text if pmid_elem is not None else None
        if not pmid:
            continue
        abstract_texts = []
        for elem in article.findall(".//AbstractText"):
            if elem.text:
                abstract_texts.append(elem.text.strip())
        if abstract_texts:
            abstracts[pmid] = " ".join(abstract_texts)
    return abstracts


def _build_term(query: str, pubtype: Optional[str], humans_only: bool) -> str:
    parts = [query]
    if pubtype:
        parts.append(f'("{pubtype}"[Publication Type])')
    if humans_only:
        parts.append("humans[MeSH Terms]")
    return " AND ".join(parts)


@mcp.tool(name="search_pubmed", description="搜索 PubMed（默认 Case Reports），返回文献元数据+摘要（可选）")
def search_pubmed(
    query: str,
    max_results: int = 10,
    pubtype: str = "Case Reports",
    days_back: int = 365,
    sort: str = "date",
    include_abstract: bool = True,
    humans_only: bool = True,
) -> str:
    """
    查询参数:
      query: 关键词/布尔检索串
      max_results: 返回条数上限 (1-50)
      pubtype: 发表类型过滤，默认 Case Reports
      days_back: 近 N 天内发表
      sort: date/relevance
      include_abstract: 是否附带摘要（默认开启）
      humans_only: 是否限定人类研究
    """
    term = _build_term(query, pubtype, humans_only)
    try:
        ids = _esearch(term, max_results, days_back, sort)
    except Exception as exc:  # noqa: BLE001
        return json.dumps({"error": f"esearch failed: {exc}"}, ensure_ascii=False)

    if not ids:
        return "[]"

    try:
        meta = _esummary(ids)
    except Exception as exc:  # noqa: BLE001
        return json.dumps({"error": f"esummary failed: {exc}"}, ensure_ascii=False)

    abstracts = {}
    if include_abstract:
        try:
            abstracts = _efetch_abstracts(ids)
        except Exception as exc:  # noqa: BLE001
            abstracts = {}
            meta["abstract_error"] = str(exc)

    results = []
    for pmid in ids:
        rec = meta.get(pmid, {})
        abstract = abstracts.get(pmid)
        item = {
            "pmid": pmid,
            "title": rec.get("title"),
            "journal": rec.get("fulljournalname"),
            "year": (rec.get("pubdate") or "")[:4],
            "authors": [a.get("name") for a in rec.get("authors", []) if a.get("name")],
            "pubtype": rec.get("pubtype"),
            "doi": rec.get("elocationid"),
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        }
        if include_abstract:
            item["abstract"] = abstract
        results.append(item)
    return json.dumps(results, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=18920)
