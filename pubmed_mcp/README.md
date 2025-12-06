# PubMed Search MCP

基于 FastMCP 的 PubMed 检索工具，便于在 Nexent 内搜索最新病理学文献（默认 Case Reports）。

## 功能
- `search_pubmed`：布尔/关键词检索 PubMed，默认过滤 Case Reports，可选限制近 N 天、按相关性或时间排序，支持附带摘要。

## 使用
```bash
cd ~/mcp/pubmed_mcp
# 建议独立环境
# conda create -n mcp-env python=3.11 -y
# conda activate mcp-env
pip install -r requirements.txt
# 可选：设置 NCBI API Key 提升速率限制
# export NCBI_API_KEY=xxxx
python server.py   # 监听 http://0.0.0.0:18920/sse
```
如果 Nexent 在 Docker 中运行，MCP URL 可配置为 `http://172.17.0.1:18920/sse` 或使用 `host.docker.internal`。

## 接口说明
- `search_pubmed(query: str, max_results: int = 10, pubtype: str = "Case Reports", days_back: int = 365, sort: str = "date", include_abstract: bool = True, humans_only: bool = True) -> str`
  - `query`: 关键词/布尔检索串（PubMed 的关键词+MeSH 自动映射逻辑）
  - `max_results`: 返回条数上限（1-50）
  - `pubtype`: 发表类型过滤，默认 Case Reports，可改为临床研究等
  - `days_back`: 近 N 天内发表
  - `sort`: `date` 或 `relevance`
  - `include_abstract`: 是否附带摘要（默认开启，会额外调用 EFetch）
  - `humans_only`: 是否限定人类研究
  - 返回：JSON 字符串，每条包含 `pmid/title/journal/year/authors/pubtype/doi/url`，附加摘要（可选）
