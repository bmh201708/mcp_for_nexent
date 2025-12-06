<font style="color:rgb(0, 0, 0);">开发“图谱以图搜图 MCP”（Image-Based Retrieval / CBIR）的技术难度比单纯的分类要高一些，因为它不追求“识别这是什么”，而是追求“找出和它长得最像的已知病例”。</font>

<font style="color:rgb(0, 0, 0);">核心技术栈是：</font>**<font style="color:rgb(0, 0, 0);">特征提取模型 (Feature Extractor) + 向量数据库 (Vector Database)</font>**<font style="color:rgb(0, 0, 0);">。</font>

<font style="color:rgb(0, 0, 0);">以下是开发这个 MCP 的完整实操指南：</font>

### <font style="color:rgb(0, 0, 0);">1. 技术架构原理</font>
+ **<font style="color:rgb(0, 0, 0);">离线阶段 (构建图谱)</font>**<font style="color:rgb(0, 0, 0);">：准备成千上万张确诊的病理切片图（图谱），通过AI模型提取成“特征向量”（一串数字），存入向量数据库。</font>
+ **<font style="color:rgb(0, 0, 0);">在线阶段 (MCP运行)</font>**<font style="color:rgb(0, 0, 0);">：</font>
    1. <font style="color:rgb(0, 0, 0);">医生上传图片 -> MCP接收。</font>
    2. <font style="color:rgb(0, 0, 0);">MCP调用同一个AI模型将图片转为向量。</font>
    3. <font style="color:rgb(0, 0, 0);">在向量数据库中进行“最近邻搜索 (Nearest Neighbor Search)”。</font>
    4. <font style="color:rgb(0, 0, 0);">返回最相似的Top-5病例的诊断信息和对比图。</font>

---

### <font style="color:rgb(0, 0, 0);">2. 关键组件选择</font>
<font style="color:rgb(0, 0, 0);">这是成败的关键。普通的图像模型（如识别猫狗的ResNet）在病理图上效果一般。</font>

1. **<font style="color:rgb(0, 0, 0);">AI模型 (Embedding Model)</font>**<font style="color:rgb(0, 0, 0);">：</font>
    - **<font style="color:rgb(0, 0, 0);">强烈推荐</font>**<font style="color:rgb(0, 0, 0);">:</font><font style="color:rgb(0, 0, 0);"> </font>**<font style="color:rgb(0, 0, 0);">PLIP (Pathology Language-Image Pretraining)</font>**<font style="color:rgb(0, 0, 0);"> </font><font style="color:rgb(0, 0, 0);">或</font><font style="color:rgb(0, 0, 0);"> </font>**<font style="color:rgb(0, 0, 0);">CTransPath</font>**<font style="color:rgb(0, 0, 0);">。这是专门在大规模病理数据上训练的基础模型，它能理解“核异型性”、“腺管结构”等病理特征。</font>
    - _<font style="color:rgb(0, 0, 0);">替代方案</font>_<font style="color:rgb(0, 0, 0);">: 简单的 ResNet50 (ImageNet预训练)，效果稍差，但容易部署。</font>
2. **<font style="color:rgb(0, 0, 0);">向量数据库</font>**<font style="color:rgb(0, 0, 0);">:</font>
    - **<font style="color:rgb(0, 0, 0);">ChromaDB</font>**<font style="color:rgb(0, 0, 0);"> </font><font style="color:rgb(0, 0, 0);">或</font><font style="color:rgb(0, 0, 0);"> </font>**<font style="color:rgb(0, 0, 0);">FAISS</font>**<font style="color:rgb(0, 0, 0);">。对于MCP这种轻量级应用，ChromaDB非常适合，可以直接嵌入Python代码中，不需要额外部署服务器。</font>

---

### <font style="color:rgb(0, 0, 0);">3. 开发步骤详解</font>
#### <font style="color:rgb(0, 0, 0);">第一步：准备“图谱”数据 (Build the Atlas)</font>
<font style="color:rgb(0, 0, 0);">假设你有一个文件夹</font><font style="color:rgb(0, 0, 0);"> </font>`<font style="color:rgb(0, 0, 0);">atlas_images/</font>`<font style="color:rgb(0, 0, 0);">，里面按诊断分类存放着经典病例图片。我们需要先写一个脚本，把这些图片“向量化”并存起来。</font>

_<font style="color:rgb(0, 0, 0);">新建文件</font>__<font style="color:rgb(0, 0, 0);"> </font>_`_<font style="color:rgb(0, 0, 0);">indexer.py</font>_`_<font style="color:rgb(0, 0, 0);"> </font>__<font style="color:rgb(0, 0, 0);">(这是一次性运行的脚本)</font>_

```python
import os
from PIL import Image
import chromadb
from chromadb.utils.embedding_functions import OpenCLIPEmbeddingFunction
import numpy as np

# 1. 初始化向量数据库 (保存在本地文件夹)
chroma_client = chromadb.PersistentClient(path="./pathology_atlas_db")

# 2. 选择嵌入模型 
# 为了演示简单，这里使用 OpenCLIP。
# 在生产环境中，你应该替换为加载 PLIP 或 CTransPath 的自定义函数。
embedding_func = OpenCLIPEmbeddingFunction() 

collection = chroma_client.get_or_create_collection(
    name="pathology_cases",
    embedding_function=embedding_func
)

# 3. 遍历文件夹建立索引
def index_images(root_dir):
    ids = []
    metadatas = []
    image_paths = []
    
    print("开始建立索引...")
    for folder_name in os.listdir(root_dir): # 文件夹名作为诊断结果，例如 "Lung_Adenocarcinoma"
        folder_path = os.path.join(root_dir, folder_name)
        if not os.path.isdir(folder_path): continue
            
        for img_file in os.listdir(folder_path):
            if img_file.endswith(('.jpg', '.png')):
                full_path = os.path.join(folder_path, img_file)
                
                # 记录数据
                ids.append(img_file) # 文件名作为ID
                image_paths.append(full_path)
                metadatas.append({
                    "diagnosis": folder_name,
                    "source": "Internal Atlas", 
                    "image_path": full_path
                })
    
    # 4. 写入数据库 (Chroma 会自动调用 embedding_func 处理图片)
    if ids:
        collection.add(
            ids=ids,
            images=[str(p) for p in image_paths], # Chroma支持直接传图片路径
            metadatas=metadatas
        )
        print(f"成功索引 {len(ids)} 张病例图片。")

# 运行索引 (假设你有一个叫 atlas_data 的文件夹)
# index_images("./atlas_data")
```

#### <font style="color:rgb(0, 0, 0);">第二步：编写 MCP Server</font>
<font style="color:rgb(0, 0, 0);">这个 Server 将加载上面建立的数据库，并提供搜索接口。</font>

_<font style="color:rgb(0, 0, 0);">新建文件</font>__<font style="color:rgb(0, 0, 0);"> </font>_`_<font style="color:rgb(0, 0, 0);">search_server.py</font>_`

```python
import base64
import io
from PIL import Image
import numpy as np
from mcp.server.fastmcp import FastMCP
import chromadb
from chromadb.utils.embedding_functions import OpenCLIPEmbeddingFunction
import json

# 初始化 MCP
mcp = FastMCP("Pathology_Atlas_Search")

# 连接到之前建立的数据库
chroma_client = chromadb.PersistentClient(path="./pathology_atlas_db")
embedding_func = OpenCLIPEmbeddingFunction()
collection = chroma_client.get_collection(
    name="pathology_cases", 
    embedding_function=embedding_func
)

def decode_image(image_data: str) -> np.ndarray:
    """将Base64转为numpy数组"""
    if "," in image_data:
        image_data = image_data.split(",")[1]
    image_bytes = base64.b64decode(image_data)
    return np.array(Image.open(io.BytesIO(image_bytes)))

@mcp.tool()
def search_similar_cases(query_image_base64: str, top_k: int = 3) -> str:
    """
    以图搜图工具。
    医生上传一张切片截图，在图谱库中搜索视觉特征最相似的历史确诊病例。
    
    Args:
        query_image_base64: 查询图片的Base64编码。
        top_k: 返回最相似的病例数量，默认为3。
    """
    print("正在进行图像检索...")
    
    try:
        # 注意：Chroma的API通常需要直接处理图片路径或numpy数组
        # 这里我们需要将base64转为模型能接受的格式
        # 为了适配OpenCLIPEmbeddingFunction，通常可以直接传numpy array或PIL Image
        # (此处代码为逻辑示意，具体取决于你的Embedding Function实现细节)
        
        # 执行查询
        # query_images 接收的是图像数据
        results = collection.query(
            query_images=[decode_image(query_image_base64)], 
            n_results=top_k,
            include=["metadatas", "distances"] # 返回元数据和相似度距离
        )
        
        # 格式化返回结果
        found_cases = []
        metadatas = results['metadatas'][0]
        distances = results['distances'][0]
        
        for meta, dist in zip(metadatas, distances):
            # 计算相似度得分 (距离越小越相似，这里简单转化为 0-100 分)
            similarity_score = max(0, (1 - dist) * 100) 
            
            found_cases.append({
                "diagnosis": meta['diagnosis'],
                "similarity_score": f"{similarity_score:.1f}%",
                "reference_image_path": meta['image_path'], # 实际返回给LLM时，可能需要转为URL
                "note": "Visual match based on tissue architecture."
            })
            
        return json.dumps(found_cases, indent=2, ensure_ascii=False)

    except Exception as e:
        return f"检索失败: {str(e)}"

if __name__ == "__main__":
    mcp.run()
```

---

### <font style="color:rgb(0, 0, 0);">4. 如何在 Nexent 界面展示结果？</font>
<font style="color:rgb(0, 0, 0);">这是一个关键的用户体验问题。MCP 返回的是 JSON 文本，医生需要看到图片对比。</font>

<font style="color:rgb(0, 0, 0);">在</font><font style="color:rgb(0, 0, 0);"> </font>`<font style="color:rgb(0, 0, 0);">search_similar_cases</font>`<font style="color:rgb(0, 0, 0);"> </font><font style="color:rgb(0, 0, 0);">的返回 JSON 中，你有两个选择来展示图片：</font>

1. **<font style="color:rgb(0, 0, 0);">如果你的图谱在公网 (如 S3/OSS)</font>**<font style="color:rgb(0, 0, 0);">：</font><font style="color:rgb(0, 0, 0);">  
</font><font style="color:rgb(0, 0, 0);">在 JSON 中返回</font><font style="color:rgb(0, 0, 0);"> </font>`<font style="color:rgb(0, 0, 0);">https://.../case123.jpg</font>`<font style="color:rgb(0, 0, 0);">。LLM 会自动将其渲染为 Markdown 图片。</font>
2. **<font style="color:rgb(0, 0, 0);">如果是本地文件</font>**<font style="color:rgb(0, 0, 0);">:</font><font style="color:rgb(0, 0, 0);">  
</font><font style="color:rgb(0, 0, 0);">你需要把检索到的“相似图片”也转成 Base64 字符串放进 JSON 返回里（注意：这会消耗大量 Token，建议只返回 1-2 张缩略图）。</font>

**<font style="color:rgb(0, 0, 0);">优化后的返回格式示例：</font>**

```json
[
  {
    "diagnosis": "Papillary Thyroid Carcinoma (甲状腺乳头状癌)",
    "similarity": "92%",
    "reasoning": "Found similar nuclear clearing and grooves.",
    "image_url": "https://your-hospital-server.com/atlas/img_882.jpg" 
  }
]
```

### <font style="color:rgb(0, 0, 0);">5. 进阶技巧：增强检索效果</font>
+ **<font style="color:rgb(0, 0, 0);">混合检索 (Hybrid Search)</font>**<font style="color:rgb(0, 0, 0);">：</font><font style="color:rgb(0, 0, 0);">  
</font><font style="color:rgb(0, 0, 0);">单纯靠图片有时候不准（比如染色差异大）。</font><font style="color:rgb(0, 0, 0);">  
</font><font style="color:rgb(0, 0, 0);">建议让医生输入一段文字描述（如“甲状腺”）。在搜索时，先过滤出</font><font style="color:rgb(0, 0, 0);"> </font>`<font style="color:rgb(0, 0, 0);">diagnosis</font>`<font style="color:rgb(0, 0, 0);"> </font><font style="color:rgb(0, 0, 0);">包含 "Thyroid" 的向量，再在这些向量里做图像相似度比对。效果会提升 10 倍。</font>
+ **<font style="color:rgb(0, 0, 0);">关于 PathologyOutlines</font>**<font style="color:rgb(0, 0, 0);">:</font><font style="color:rgb(0, 0, 0);">  
</font><font style="color:rgb(0, 0, 0);">由于版权原因，你不能直接把 PathologyOutlines 的网站做成 MCP 实时爬取（速度太慢且不稳定）。</font><font style="color:rgb(0, 0, 0);">  
</font>**<font style="color:rgb(0, 0, 0);">正确做法</font>**<font style="color:rgb(0, 0, 0);">：作为医院内部项目，你应该联系病理科主任，导出医院内部积累的“教学切片库”或“数字病理库”，用这些高质量数据构建属于你们自己的 Private Atlas。</font>

### <font style="color:rgb(0, 0, 0);">总结</font>
<font style="color:rgb(0, 0, 0);">制作“搜图 MCP”的核心不在于写代码，而在于**“向量化”**。</font>

1. **<font style="color:rgb(0, 0, 0);">找数据</font>**<font style="color:rgb(0, 0, 0);">：先搞 100 张分好类的病理图。</font>
2. **<font style="color:rgb(0, 0, 0);">建索引</font>**<font style="color:rgb(0, 0, 0);">：用 Python 脚本把它们变成 ChromaDB 里的数据。</font>
3. **<font style="color:rgb(0, 0, 0);">做接口</font>**<font style="color:rgb(0, 0, 0);">：MCP 接收图片 -> 查库 -> 返回诊断名称。</font>

<font style="color:rgb(0, 0, 0);">这个功能一旦做成，对年轻医生的辅助作用非常大，相当于随时有一本“会自己翻页的图谱书”。</font>获取**100张分好类的病理图**并不难，但获取**高质量、有标注、无版权纠纷**的图片需要找对地方。对于开发MVP（最小可行性产品）来说，你不需要去医院申请伦理审批，可以直接使用**开源的学术数据集**。

<font style="color:rgb(0, 0, 0);">以下是获取这些数据的三种最快途径，按推荐程度排序：</font>

### <font style="color:rgb(0, 0, 0);">途径一：下载现成的“补丁级”开源数据集（最推荐 </font>🌟<font style="color:rgb(0, 0, 0);">）</font>
<font style="color:rgb(0, 0, 0);">这是最省事的办法。学术界已经把巨大的全切片（WSI）切成了几千张 224x224 或 512x512 像素的小图（Patches），并按文件夹分好了类。这完美契合我之前给你的 </font>`<font style="color:rgb(0, 0, 0);">indexer.py</font>`<font style="color:rgb(0, 0, 0);"> 代码结构。</font>

**推荐数据集：NCT-CRC-HE-100K (Kather Dataset)**<font style="color:rgb(0, 0, 0);">  
</font><font style="color:rgb(0, 0, 0);">这是一个经典的结直肠癌组织病理数据集，质量非常高，且分类清晰。</font>

+ **数据内容**<font style="color:rgb(0, 0, 0);">：包含9种组织类型（肿瘤、基质、淋巴细胞、粘液、脂肪等）。</font>
+ **获取方式**<font style="color:rgb(0, 0, 0);">：</font>
    1. <font style="color:rgb(0, 0, 0);">访问 </font>**Kaggle**<font style="color:rgb(0, 0, 0);"> 或 </font>**Zenodo**<font style="color:rgb(0, 0, 0);"> 搜索 </font>`<font style="color:rgb(0, 0, 0);">NCT-CRC-HE-100K</font>`<font style="color:rgb(0, 0, 0);">。</font>
    2. <font style="color:rgb(0, 0, 0);">或者直接搜索 </font>`<font style="color:rgb(0, 0, 0);">Kather texture dataset</font>`<font style="color:rgb(0, 0, 0);">。</font>
    3. <font style="color:rgb(0, 0, 0);">下载 </font>`<font style="color:rgb(0, 0, 0);">NCT-CRC-HE-100K-NONORM.zip</font>`<font style="color:rgb(0, 0, 0);"> (约 500MB - 1GB)。</font>

**解压后的目录结构是这样的（直接能用）：**

```latex
/NCT-CRC-HE-100K
    /ADI (Adipose - 脂肪组织)
        - ADI_01.tif
        - ADI_02.tif
    /DEB (Debris - 坏死碎片)
    /LYM (Lymphocytes - 淋巴细胞)
    /MUC (Mucus - 粘液)
    /MUS (Muscle - 平滑肌)
    /NORM (Normal - 正常粘膜)
    /STR (Stroma - 肿瘤基质)
    /TUM (Tumor - 腺癌上皮)
```

**操作**<font style="color:rgb(0, 0, 0);">：你只需要从中每个文件夹挑 10-20 张图，复制出来放到你的 </font>`<font style="color:rgb(0, 0, 0);">atlas_data</font>`<font style="color:rgb(0, 0, 0);"> 文件夹里，你的 100 张图谱就做好了。</font>

---

### <font style="color:rgb(0, 0, 0);">途径二：从 Kaggle 竞赛数据中获取</font>
<font style="color:rgb(0, 0, 0);">Kaggle 上有大量病理比赛，数据都是处理好的。</font>

1. **PatchCamelyon (PCam)**
    - **内容**<font style="color:rgb(0, 0, 0);">：乳腺癌淋巴结转移切片。</font>
    - **特点**<font style="color:rgb(0, 0, 0);">：二分类（有转移 vs 无转移）。适合做简单的 Demo。</font>
    - **搜索关键词**<font style="color:rgb(0, 0, 0);">：</font>`<font style="color:rgb(0, 0, 0);">Histopathologic Cancer Detection</font>`<font style="color:rgb(0, 0, 0);">。</font>
2. **PANDA Challenge (Prostate cANcer graDe Assessment)**
    - **内容**<font style="color:rgb(0, 0, 0);">：前列腺癌 Gleason 分级。</font>
    - **特点**<font style="color:rgb(0, 0, 0);">：虽然原图很大，但讨论区通常有人提供“Cropped Dataset”下载链接。</font>

---

### <font style="color:rgb(0, 0, 0);">途径三：手动构建（针对特定罕见病/教学演示）</font>
<font style="color:rgb(0, 0, 0);">如果你想做更有针对性的 Demo（比如“甲状腺乳头状癌”），不想用通用的肠癌数据，可以手动“采集”。</font>

**推荐来源：PathologyOutlines 或 The Human Protein Atlas**

1. <font style="color:rgb(0, 0, 0);">访问 </font>[PathologyOutlines](https://www.pathologyoutlines.com/)<font style="color:rgb(0, 0, 0);">。</font>
2. <font style="color:rgb(0, 0, 0);">搜索某个具体的病（如 "Papillary thyroid carcinoma"）。</font>
3. <font style="color:rgb(0, 0, 0);">进入 "Images" 章节。</font>
4. **手动保存**<font style="color:rgb(0, 0, 0);"> 10-20 张典型图片。</font>
5. **关键步骤**<font style="color:rgb(0, 0, 0);">：</font>
    - <font style="color:rgb(0, 0, 0);">在本地新建文件夹 </font>`<font style="color:rgb(0, 0, 0);">Thyroid_Papillary</font>`<font style="color:rgb(0, 0, 0);">，把图放进去。</font>
    - <font style="color:rgb(0, 0, 0);">再搜一个易混淆的良性病变（如 "Nodular hyperplasia"），新建文件夹 </font>`<font style="color:rgb(0, 0, 0);">Thyroid_Benign</font>`<font style="color:rgb(0, 0, 0);">，放进去。</font>

_注意：这种方式仅限于内部演示（Demo）或个人学习，严禁用于商业产品发布，因为有版权保护。_

---

### ⚡<font style="color:rgb(0, 0, 0);">️ 快速启动脚本</font>
<font style="color:rgb(0, 0, 0);">如果你下载了 </font>**NCT-CRC-HE-100K**<font style="color:rgb(0, 0, 0);"> 数据集，这里有一个 Python 脚本帮你随机抽取 100 张图，构建出你的“迷你图谱库”：</font>

```python
import os
import shutil
import random

# 配置路径
source_dir = "./NCT-CRC-HE-100K"  # 你下载并解压的数据集路径
target_dir = "./atlas_data"       # 你的MCP图谱文件夹

# 想要抽取的类别
categories = ["ADI", "LYM", "MUC", "TUM", "STR"] 
images_per_category = 20

def build_mini_atlas():
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    for cat in categories:
        # 1. 创建目标分类文件夹
        cat_source = os.path.join(source_dir, cat)
        cat_target = os.path.join(target_dir, cat)
        
        if not os.path.exists(cat_source):
            print(f"警告: 源文件夹 {cat_source} 不存在，跳过。")
            continue
            
        if not os.path.exists(cat_target):
            os.makedirs(cat_target)
            
        # 2. 获取所有图片并随机抽取
        all_images = [f for f in os.listdir(cat_source) if f.endswith('.tif')]
        selected_images = random.sample(all_images, min(len(all_images), images_per_category))
        
        # 3. 复制文件
        for img in selected_images:
            shutil.copy(
                os.path.join(cat_source, img),
                os.path.join(cat_target, img)
            )
        
        print(f"已从 {cat} 类别抽取 {len(selected_images)} 张图片。")

    print("\n✅ 迷你图谱构建完成！总计约 100 张图片。")
    print(f"请运行之前的 indexer.py 指向目录: {target_dir}")

if __name__ == "__main__":
    # 请确保路径正确再运行
    # build_mini_atlas()
    pass
```

### <font style="color:rgb(0, 0, 0);">总结建议</font>
**不要一开始就去处理几十GB的 WSI 全切片大图**<font style="color:rgb(0, 0, 0);">（那是后期工程化的事）。</font>

<font style="color:rgb(0, 0, 0);">现在立刻去搜索下载 </font>**"Kather colorectal dataset"**<font style="color:rgb(0, 0, 0);">，它已经帮你把“病理图”变成了“分类好的小图片”，这是你训练 Agent 识别能力和测试以图搜图功能最快、最稳的起步方式。</font>

