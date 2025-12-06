# 扩大图谱范围指南

## 当前状态

当前图谱使用 `build_atlas.py` 从 NCT-CRC-HE-100K 数据集中抽取样本构建，默认每个类别20张图片。

## 扩大图谱的方法

### 方法1：增加每个类别的图片数量（推荐）

使用 `build_atlas.py` 增加每个类别抽取的图片数量：

```bash
cd ~/mcp/image_search_mcp
source $(conda info --base)/etc/profile.d/conda.sh
conda activate mcp-image-search-env

# 从每个类别抽取100张图片（而不是默认的20张）
python build_atlas.py \
    --source_dir ~/NCT-CRC-HE-100K \
    --target_dir ./atlas_data_full \
    --images_per_category 100

# 然后重新构建索引
python indexer.py --atlas_dir ./atlas_data_full
```

**优点：**
- 简单快速
- 保持现有类别结构
- 提高搜索准确度

**缺点：**
- 索引构建时间会增加
- 数据库文件会变大

### 方法2：使用全部数据集

直接使用整个 NCT-CRC-HE-100K 数据集（约10万张图片）：

```bash
# 直接对整个数据集构建索引
python indexer.py --atlas_dir ~/NCT-CRC-HE-100K
```

**注意：**
- 这会需要很长时间（可能需要数小时）
- 数据库文件会非常大（可能超过10GB）
- 建议使用GPU加速

### 方法3：增量添加新类别

如果数据集中有新的类别文件夹，可以增量添加到现有索引：

```bash
# 增量添加（不会清空现有数据）
python indexer.py --atlas_dir ~/新数据目录
```

当脚本询问是否清空现有数据时，选择 `N`（否），新数据会被添加到现有索引中。

### 方法4：添加其他数据源

#### 4.1 添加新的数据集目录

准备新的数据集目录，按诊断分类组织：

```
新数据集/
├── ADENOCARCINOMA/
│   ├── image1.jpg
│   ├── image2.jpg
│   └── ...
├── SQUAMOUS_CELL_CARCINOMA/
│   ├── image1.jpg
│   └── ...
└── BENIGN/
    └── ...
```

然后运行：

```bash
python indexer.py --atlas_dir ~/新数据集
```

#### 4.2 合并多个数据源

可以创建符号链接或复制多个数据源到一个目录：

```bash
# 创建合并目录
mkdir -p ~/merged_atlas

# 复制或链接多个数据源
cp -r ~/NCT-CRC-HE-100K/* ~/merged_atlas/
cp -r ~/其他数据集/* ~/merged_atlas/

# 构建索引
python indexer.py --atlas_dir ~/merged_atlas
```

### 方法5：使用自定义类别和数量

使用 `build_atlas.py` 的 `--categories` 参数选择特定类别：

```bash
# 只抽取特定类别，每个类别更多图片
python build_atlas.py \
    --source_dir ~/NCT-CRC-HE-100K \
    --target_dir ./atlas_data_custom \
    --categories TUM STR LYM NORM \
    --images_per_category 200
```

## 性能优化建议

### 1. 批量大小调整

如果内存充足，可以修改 `indexer.py` 中的 `batch_size`（默认10）：

```python
# 在 indexer.py 第103行
batch_size = 50  # 增加到50或更大
```

### 2. GPU加速

确保使用GPU加速（PLIP模型会自动使用GPU）：

```bash
# 检查GPU是否可用
python -c "import torch; print(f'CUDA可用: {torch.cuda.is_available()}')"
```

### 3. 并行处理

对于非常大的数据集，可以考虑修改 `indexer.py` 使用多进程：

```python
from multiprocessing import Pool
# 实现并行特征提取
```

## 数据库管理

### 查看当前索引统计

```python
import chromadb
from chromadb.config import Settings
from plip_model import PLIPEmbeddingFunction

client = chromadb.PersistentClient(
    path="./pathology_atlas_db",
    settings=Settings(anonymized_telemetry=False)
)
coll = client.get_collection(
    "pathology_cases",
    embedding_function=PLIPEmbeddingFunction()
)

print(f"总记录数: {coll.count()}")

# 按诊断分类统计
results = coll.get()
diagnoses = {}
for meta in results['metadatas']:
    diag = meta.get('diagnosis', 'Unknown')
    diagnoses[diag] = diagnoses.get(diag, 0) + 1

print("\n按诊断分类统计:")
for diag, count in sorted(diagnoses.items()):
    print(f"  {diag}: {count} 张")
```

### 清空并重建索引

如果需要完全重建索引：

```bash
# 删除数据库目录
rm -rf ~/mcp/image_search_mcp/pathology_atlas_db

# 重新构建
python indexer.py --atlas_dir ./atlas_data
```

## 推荐配置

### 小型图谱（快速测试）
- 每个类别：20-50张
- 总图片数：约200-500张
- 构建时间：5-15分钟

### 中型图谱（推荐生产环境）
- 每个类别：100-200张
- 总图片数：约1000-2000张
- 构建时间：30-60分钟

### 大型图谱（完整数据集）
- 每个类别：全部图片
- 总图片数：约10万张
- 构建时间：数小时（建议使用GPU）

## 示例命令

### 快速扩大（从20张增加到100张）

```bash
cd ~/mcp/image_search_mcp
source $(conda info --base)/etc/profile.d/conda.sh
conda activate mcp-image-search-env

# 1. 构建更大的图谱
python build_atlas.py \
    --source_dir ~/NCT-CRC-HE-100K \
    --target_dir ./atlas_data_expanded \
    --images_per_category 100

# 2. 构建索引（选择不清空，增量添加）
python indexer.py --atlas_dir ./atlas_data_expanded
# 当询问是否清空时，输入 N
```

### 完全重建（使用更多图片）

```bash
# 1. 构建图谱（200张/类别）
python build_atlas.py \
    --source_dir ~/NCT-CRC-HE-100K \
    --target_dir ./atlas_data_large \
    --images_per_category 200

# 2. 重建索引（清空旧数据）
python indexer.py --atlas_dir ./atlas_data_large
# 当询问是否清空时，输入 y
```

## 注意事项

1. **磁盘空间**：确保有足够的磁盘空间存储数据库文件
2. **内存**：大批量处理需要足够的内存
3. **时间**：大规模索引构建需要较长时间
4. **备份**：重建索引前建议备份现有数据库
5. **服务器重启**：索引更新后，需要重启MCP服务器才能使用新数据

## 验证扩大结果

索引构建完成后，检查结果：

```bash
# 重启服务器
ps aux | grep "python server.py" | grep -v grep | awk '{print $2}' | xargs kill -9
cd ~/mcp/image_search_mcp
source $(conda info --base)/etc/profile.d/conda.sh
conda activate mcp-image-search-env
nohup python server.py > server.log 2>&1 &

# 查看日志确认记录数
tail -20 server.log | grep "条记录"
```

