# MCP Services for Nexent Platform

This repository contains MCP (Model Context Protocol) services designed for the Nexent platform, specifically for pathology diagnosis workflows.

## Services Overview

### 1. Pathology MCP Server (`pathology_mcp/`)

Rule-based pathology report parsing and interpretation service.

**Features:**
- `extract_pathology_fields`: Parse raw pathology text into structured JSON
- `interpret_ihc`: Interpret IHC (Immunohistochemistry) markers
- `map_mutations`: Map mutations to clinical meaning

**Usage:**
```bash
cd pathology_mcp
pip install -r requirements.txt
python server.py
```

### 2. PubMed Search MCP (`pubmed_mcp/`)

Literature search tool using NCBI E-utilities API.

**Features:**
- `search_pubmed`: Search PubMed database for medical literature

**Usage:**
```bash
cd pubmed_mcp
pip install -r requirements.txt
python server.py
```

### 3. Image Search MCP (`image_search_mcp/`)

Content-Based Image Retrieval (CBIR) service for pathology images using PLIP model.

**Features:**
- `search_similar_cases`: Search similar pathology cases by image
- `search_similar_cases_from_file`: Search from file path
- Supports Base64 encoded images, file paths, and HTTP/HTTPS URLs
- Uses PLIP (Pathology Language-Image Pretraining) for feature extraction
- ChromaDB vector database for similarity search

**Setup:**
```bash
cd image_search_mcp
conda create -n mcp-image-search-env python=3.11
conda activate mcp-image-search-env
pip install -r requirements.txt

# Build atlas index
python build_atlas.py --source_dir /path/to/NCT-CRC-HE-100K --images_per_category 200
python indexer.py --atlas_dir ./atlas_data_200

# Start server
python server.py
```

**Server:** Runs on `http://0.0.0.0:18930/sse`

## Repository Structure

```
mcp/
├── pathology_mcp/          # Pathology report parsing service
├── pubmed_mcp/             # PubMed literature search service
├── image_search_mcp/       # Image-based case retrieval service
├── mcp_server.py           # Example MCP server
└── README.md               # This file
```

## Requirements

- Python 3.11+
- FastMCP >= 2.13.0
- CUDA-capable GPU (recommended for image_search_mcp)
- ChromaDB (for image_search_mcp)

## License

See individual service directories for license information.

## Contributing

Please refer to individual service README files for contribution guidelines.

