# Pathology MCP Server

A lightweight FastMCP server for pathology report structuring and basic interpretation.

## Features
- `extract_pathology_fields`: parse raw pathology text into structured JSON (site, morphology, grade/stage, IHC markers, mutations, lesion size, key terms).
- `interpret_ihc`: provide a quick interpretation for common IHC panels (rule-based examples).
- `map_mutations`: map common mutations to simple clinical meaning (rule-based examples).

## Run (conda example)
```bash
cd ~/mcp/pathology_mcp
conda activate mcp-env  # or any env with Python>=3.9
pip install fastmcp
python server.py
```
Server listens on `0.0.0.0:18910/sse` by default.
If Nexent is in Docker, configure MCP URL as `http://172.17.0.1:18910/sse` (or add extra_hosts for host.docker.internal).

## Notes
- Logic is rule-based, intended as a starter. You can swap in your own NLP/model/DB calls inside the tools.
- All dependencies are stdlib + fastmcp.
