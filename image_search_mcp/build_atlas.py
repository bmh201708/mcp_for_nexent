"""
从NCT-CRC-HE-100K数据集构建迷你图谱
随机抽取每个类别的样本图片，构建用于测试的图谱库
"""
import os
import shutil
import random
import argparse
from pathlib import Path


def build_mini_atlas(
    source_dir: str,
    target_dir: str = "./atlas_data",
    categories: list = None,
    images_per_category: int = 20
):
    """
    从源数据集构建迷你图谱
    
    Args:
        source_dir: NCT-CRC-HE-100K数据集目录
        target_dir: 目标图谱目录
        categories: 要抽取的类别列表，None时使用默认类别
        images_per_category: 每个类别抽取的图片数量
    """
    source_path = Path(source_dir)
    target_path = Path(target_dir)
    
    if not source_path.exists():
        raise ValueError(f"源数据集目录不存在: {source_dir}")
    
    # 默认类别（NCT-CRC-HE-100K的9个类别）
    if categories is None:
        categories = [
            "ADI",   # Adipose - 脂肪组织
            "BACK",  # Background - 背景
            "DEB",   # Debris - 坏死碎片
            "LYM",   # Lymphocytes - 淋巴细胞
            "MUC",   # Mucus - 粘液
            "MUS",   # Muscle - 平滑肌
            "NORM",  # Normal - 正常粘膜
            "STR",   # Stroma - 肿瘤基质
            "TUM",   # Tumor - 腺癌上皮
        ]
    
    print(f"源数据集目录: {source_dir}")
    print(f"目标图谱目录: {target_dir}")
    print(f"每个类别抽取 {images_per_category} 张图片")
    print()
    
    # 创建目标目录
    target_path.mkdir(parents=True, exist_ok=True)
    
    total_copied = 0
    
    for cat in categories:
        cat_source = source_path / cat
        cat_target = target_path / cat
        
        if not cat_source.exists():
            print(f"⚠️  警告: 源文件夹 {cat_source} 不存在，跳过")
            continue
        
        if not cat_source.is_dir():
            print(f"⚠️  警告: {cat_source} 不是目录，跳过")
            continue
        
        # 创建目标分类文件夹
        cat_target.mkdir(parents=True, exist_ok=True)
        
        # 获取所有图片文件
        supported_formats = ('.tif', '.tiff', '.jpg', '.jpeg', '.png')
        all_images = [
            f for f in os.listdir(cat_source)
            if f.lower().endswith(supported_formats)
        ]
        
        if not all_images:
            print(f"⚠️  警告: {cat} 类别中没有找到图片文件")
            continue
        
        # 随机抽取
        n_samples = min(len(all_images), images_per_category)
        selected_images = random.sample(all_images, n_samples)
        
        # 复制文件
        copied_count = 0
        for img in selected_images:
            src_file = cat_source / img
            dst_file = cat_target / img
            
            try:
                shutil.copy2(src_file, dst_file)
                copied_count += 1
            except Exception as e:
                print(f"  错误: 复制 {img} 失败: {e}")
        
        print(f"✅ {cat:6s}: 从 {len(all_images):4d} 张中抽取 {copied_count:3d} 张")
        total_copied += copied_count
    
    print()
    print("=" * 60)
    print(f"✅ 迷你图谱构建完成！")
    print(f"   总计: {total_copied} 张图片")
    print(f"   目录: {target_dir}")
    print()
    print("下一步: 运行 indexer.py 构建索引")
    print(f"   python indexer.py --atlas_dir {target_dir}")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="从NCT-CRC-HE-100K数据集构建迷你图谱"
    )
    parser.add_argument(
        "--source_dir",
        type=str,
        required=True,
        help="NCT-CRC-HE-100K数据集目录路径"
    )
    parser.add_argument(
        "--target_dir",
        type=str,
        default="./atlas_data",
        help="目标图谱目录路径（默认: ./atlas_data）"
    )
    parser.add_argument(
        "--images_per_category",
        type=int,
        default=20,
        help="每个类别抽取的图片数量（默认: 20）"
    )
    parser.add_argument(
        "--categories",
        type=str,
        nargs="+",
        default=None,
        help="要抽取的类别列表（默认: 所有9个类别）"
    )
    
    args = parser.parse_args()
    
    try:
        build_mini_atlas(
            source_dir=args.source_dir,
            target_dir=args.target_dir,
            categories=args.categories,
            images_per_category=args.images_per_category
        )
    except KeyboardInterrupt:
        print("\n\n构建被用户中断")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()

