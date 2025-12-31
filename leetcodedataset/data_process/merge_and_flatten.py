import os
import sys
import argparse

# 添加项目根目录到系统路径，以便导入eval_lcd模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from eval_lcd.data import read_jsonl, write_jsonl, show_list

def merge_and_flatten_data(lst1, lst2):
    """
    合并lst1和lst2的内容，并平铺'meta'字段（同时去掉多余的meta字段）
    
    Args:
        lst1: 第一个列表
        lst2: 第二个列表
        
    Returns:
        合并并平铺后的列表
    """
    merged_list = lst1 + lst2
    flattened_list = []
    
    for item in merged_list:
        # 创建新项，不包含原始的meta字段
        new_item = {k: v for k, v in item.items() if k != 'meta'}
        
        # 如果存在meta字段，将其内容平铺到新项中
        if 'meta' in item and isinstance(item['meta'], dict):
            for meta_key, meta_value in item['meta'].items():
                # 确保不覆盖已有字段
                if meta_key not in new_item:
                    new_item[meta_key] = meta_value
        
        flattened_list.append(new_item)
    
    return flattened_list

def parse_args():
    parser = argparse.ArgumentParser(description='合并两个JSONL文件并平铺meta字段')
    
    parser.add_argument('--lst1', type=str, required=True,
                        help='第一个JSONL文件的路径')
    
    parser.add_argument('--lst2', type=str, required=True,
                        help='第二个JSONL文件的路径')
    
    parser.add_argument('--output', type=str, default='LeetCodeDataset-v0.3.0.jsonl',
                        help='输出文件名 (默认: LeetCodeDataset-v0.3.0.jsonl)')
    
    return parser.parse_args()

def main():
    # 解析命令行参数
    args = parse_args()
    
    # 获取项目根目录
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 处理输入文件路径
    lst1_path = args.lst1
    if not os.path.isabs(lst1_path):
        lst1_path = os.path.join(root_dir, lst1_path)
    
    lst2_path = args.lst2
    if not os.path.isabs(lst2_path):
        lst2_path = os.path.join(root_dir, lst2_path)
    
    # 处理输出文件路径
    output_path = args.output
    if not os.path.isabs(output_path):
        output_path = os.path.join(root_dir, 'data', output_path)
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 读取输入文件
    print(f"Reading lst1 from {lst1_path}")
    try:
        lst1 = read_jsonl(lst1_path)
        print("读取lst1完成:")
        first_item_lst1 = show_list(lst1)
    except Exception as e:
        print(f"Error reading lst1: {e}")
        return
    
    print(f"Reading lst2 from {lst2_path}")
    try:
        lst2 = read_jsonl(lst2_path)
        print("读取lst2完成:")
        first_item_lst2 = show_list(lst2)
    except Exception as e:
        print(f"Error reading lst2: {e}")
        return
    
    # 合并并平铺数据
    merged_data = merge_and_flatten_data(lst1, lst2)
    print("合并并平铺数据完成:")
    first_merged_item = show_list(merged_data)
    
    # 写入新文件
    try:
        write_jsonl(output_path, merged_data)
        print(f"已将合并数据写入: {output_path}")
        print(f"合并后的数据项总数: {len(merged_data)}")
    except Exception as e:
        print(f"Error writing output: {e}")

if __name__ == "__main__":
    main() 