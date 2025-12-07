#!/bin/bash
# 快速安装和设置脚本

set -e

echo "=========================================="
echo "图谱以图搜图 MCP - 安装脚本"
echo "=========================================="
echo

# 检查conda是否安装
if ! command -v conda &> /dev/null; then
    echo "错误: 未找到conda，请先安装Anaconda或Miniconda"
    exit 1
fi

# 创建conda环境
echo "1. 创建conda环境..."
if conda env list | grep -q "mcp-image-search-env"; then
    echo "   环境已存在，跳过创建"
else
    conda create -n mcp-image-search-env python=3.11 -y
    echo "   ✅ 环境创建完成"
fi

# 激活环境并安装依赖
echo
echo "2. 安装Python依赖..."
source $(conda info --base)/etc/profile.d/conda.sh
conda activate mcp-image-search-env

cd "$(dirname "$0")"
pip install -r requirements.txt

echo "   ✅ 依赖安装完成"
echo
echo "=========================================="
echo "安装完成！"
echo "=========================================="
echo
echo "下一步："
echo "1. 激活环境: conda activate mcp-image-search-env"
echo "2. 构建图谱索引: python indexer.py --atlas_dir ./atlas_data"
echo "3. 启动服务器: python server.py"
echo


