"""
图谱索引构建脚本
遍历图谱目录，使用PLIP提取特征向量，存储到ChromaDB
"""
import os
import argparse
from pathlib import Path
import chromadb
from chromadb.config import Settings
from plip_model import get_extractor, PLIPEmbeddingFunction

DB_PATH = "./pathology_atlas_db"
COLLECTION_NAME = "pathology_cases"


def index_images(atlas_dir: str, db_path: str = DB_PATH):
    """
    构建图谱索引
    
    Args:
        atlas_dir: 图谱目录路径（按诊断分类的文件夹结构）
        db_path: ChromaDB数据库路径
    """
    atlas_path = Path(atlas_dir)
    if not atlas_path.exists():
        raise ValueError(f"图谱目录不存在: {atlas_dir}")
    
    print(f"开始构建索引，图谱目录: {atlas_dir}")
    print("正在初始化PLIP模型...")
    
    # 初始化embedding function
    embedding_func = PLIPEmbeddingFunction()
    
    # 初始化ChromaDB客户端
    print(f"正在连接ChromaDB数据库: {db_path}")
    chroma_client = chromadb.PersistentClient(path=db_path, settings=Settings(anonymized_telemetry=False))
    
    # 获取或创建collection
    try:
        collection = chroma_client.get_collection(name=COLLECTION_NAME)
        print(f"找到已存在的collection: {COLLECTION_NAME}")
        print(f"当前包含 {collection.count()} 条记录")
        response = input("是否清空现有数据并重新索引？(y/N): ")
        if response.lower() == 'y':
            chroma_client.delete_collection(name=COLLECTION_NAME)
            collection = chroma_client.create_collection(
                name=COLLECTION_NAME,
                embedding_function=embedding_func
            )
            print("已清空旧数据")
        else:
            print("将在现有数据基础上增量添加")
    except Exception:
        collection = chroma_client.create_collection(
            name=COLLECTION_NAME,
            embedding_function=embedding_func
        )
        print(f"创建新collection: {COLLECTION_NAME}")
    
    # 收集所有图片
    ids = []
    image_paths = []
    metadatas = []
    
    supported_formats = ('.jpg', '.jpeg', '.png', '.tif', '.tiff')
    
    print("\n正在扫描图片文件...")
    for folder_name in sorted(os.listdir(atlas_path)):
        folder_path = atlas_path / folder_name
        if not folder_path.is_dir():
            continue
        
        print(f"  处理类别: {folder_name}")
        image_count = 0
        
        for img_file in sorted(os.listdir(folder_path)):
            if img_file.lower().endswith(supported_formats):
                full_path = folder_path / img_file
                
                # 生成唯一ID
                img_id = f"{folder_name}_{img_file}"
                
                ids.append(img_id)
                image_paths.append(str(full_path))
                metadatas.append({
                    "diagnosis": folder_name,
                    "source": "Internal Atlas",
                    "image_path": str(full_path),
                    "filename": img_file
                })
                image_count += 1
        
        print(f"    找到 {image_count} 张图片")
    
    if not ids:
        print("错误: 未找到任何图片文件")
        return
    
    print(f"\n总共找到 {len(ids)} 张图片")
    print("开始提取特征向量并写入数据库...")
    
    # 批量处理（每次处理一批，避免内存溢出）
    batch_size = 10
    total_batches = (len(ids) + batch_size - 1) // batch_size
    
    # 初始化extractor
    extractor = get_extractor()
    
    for i in range(0, len(ids), batch_size):
        batch_ids = ids[i:i+batch_size]
        batch_paths = image_paths[i:i+batch_size]
        batch_metadatas = metadatas[i:i+batch_size]
        
        batch_num = i // batch_size + 1
        print(f"  处理批次 {batch_num}/{total_batches} ({len(batch_ids)} 张图片)...")
        
        try:
            # 提取特征向量
            batch_embeddings = extractor.extract_features_batch(batch_paths)
            
            # 添加到数据库
            # 注意：ChromaDB的add方法需要embeddings参数（已提取的向量）
            # 或者使用documents参数让embedding function自动处理
            # 这里我们直接传入embeddings，因为我们已经提取了
            collection.add(
                ids=batch_ids,
                embeddings=batch_embeddings.tolist(),
                metadatas=batch_metadatas
            )
        except Exception as e:
            print(f"  批次 {batch_num} 处理失败: {e}")
            # 尝试逐张添加
            for img_id, img_path, metadata in zip(batch_ids, batch_paths, batch_metadatas):
                try:
                    embedding = extractor.extract_features(img_path)
                    collection.add(
                        ids=[img_id],
                        embeddings=[embedding.tolist()],
                        metadatas=[metadata]
                    )
                except Exception as e2:
                    print(f"    跳过图片 {img_id}: {e2}")
    
    print(f"\n✅ 索引构建完成！")
    print(f"数据库路径: {db_path}")
    print(f"Collection: {COLLECTION_NAME}")
    print(f"总记录数: {collection.count()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="构建病理图谱索引")
    parser.add_argument(
        "--atlas_dir",
        type=str,
        required=True,
        help="图谱目录路径（按诊断分类的文件夹结构）"
    )
    parser.add_argument(
        "--db_path",
        type=str,
        default=DB_PATH,
        help=f"ChromaDB数据库路径（默认: {DB_PATH}）"
    )
    
    args = parser.parse_args()
    
    try:
        index_images(args.atlas_dir, args.db_path)
    except KeyboardInterrupt:
        print("\n\n索引构建被用户中断")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()

