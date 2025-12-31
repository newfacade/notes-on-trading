import os
import sys
from datetime import datetime
from collections import defaultdict
import argparse
import json

# 添加项目根目录到系统路径，以便导入eval_lcd模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from eval_lcd.data import read_jsonl, write_jsonl

def calculate_monthly_pass_rate(dct, lst):
    """
    根据dct(通过情况)和lst(题目信息)计算每月的通过率
    
    Args:
        dct: 包含任务ID和通过情况的字典 {task_id: passed}
        lst: 包含题目详细信息的列表
        
    Returns:
        按月份排序的通过率统计
    """
    # 按月份分类的题目数量和通过数量
    monthly_total = defaultdict(int)
    monthly_passed = defaultdict(int)
    
    # 无有效日期的题目数量和通过数量
    no_date_total = 0
    no_date_passed = 0
    
    # 按照题目难度分类的统计
    difficulty_stats = {
        'Easy': {'total': 0, 'passed': 0},
        'Medium': {'total': 0, 'passed': 0},
        'Hard': {'total': 0, 'passed': 0},
        'Unknown': {'total': 0, 'passed': 0}
    }
    
    # 遍历所有题目
    for item in lst:
        task_id = item.get('task_id')
        if not task_id or task_id not in dct:
            continue
        
        # 获取题目难度
        difficulty = item.get('difficulty', 'Unknown')
        difficulty_stats[difficulty]['total'] += 1
        if dct[task_id]:
            difficulty_stats[difficulty]['passed'] += 1
        
        # 获取日期，格式为 YYYY-MM-DD
        date_str = item.get('estimated_date')
        
        if date_str and date_str.strip():
            try:
                # 解析日期
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                # 获取年月
                month_key = f"{date_obj.year}-{date_obj.month:02d}"
                
                # 累计每月的题目总数和通过数
                monthly_total[month_key] += 1
                if dct[task_id]:
                    monthly_passed[month_key] += 1
            except ValueError:
                # 如果日期格式不正确，归类到无有效日期
                no_date_total += 1
                if dct[task_id]:
                    no_date_passed += 1
        else:
            # 无日期信息的题目
            no_date_total += 1
            if dct[task_id]:
                no_date_passed += 1
    
    # 计算每月的通过率
    monthly_stats = []
    for month in sorted(monthly_total.keys()):
        total = monthly_total[month]
        passed = monthly_passed[month]
        pass_rate = (passed / total) * 100 if total > 0 else 0
        monthly_stats.append({
            'month': month,
            'total': total,
            'passed': passed,
            'pass_rate': pass_rate
        })
    
    # 添加无有效日期的统计
    if no_date_total > 0:
        no_date_pass_rate = (no_date_passed / no_date_total) * 100 if no_date_total > 0 else 0
        monthly_stats.append({
            'month': 'No Date',
            'total': no_date_total,
            'passed': no_date_passed,
            'pass_rate': no_date_pass_rate
        })
    
    return monthly_stats, difficulty_stats

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='统计LeetCode数据集的通过率')
    
    parser.add_argument('-i', '--input', type=str, 
                        default='data/2772-tail-386-deepseek-v3.jsonl_results.jsonl',
                        help='结果文件路径，默认为data/2772-tail-386-deepseek-v3.jsonl_results.jsonl')
    
    parser.add_argument('-d', '--data', type=str,
                        default='LeetCodeDataset-v0.3.0.jsonl',
                        help='数据集文件路径，默认为LeetCodeDataset-v0.3.0.jsonl')
    
    return parser.parse_args()

def main():
    """主函数，读取数据并计算按月份和难度的通过率"""
    # 解析命令行参数
    args = parse_args()
    
    # # 获取项目根目录
    # root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # # 处理文件路径
    # if not os.path.isabs(args.input):
    #     results_path = os.path.join(root_dir, args.input)
    # else:
    #     results_path = args.input
        
    # if not os.path.isabs(args.data):
    #     data_path = os.path.join(root_dir, args.data)
    # else:
    #     data_path = args.data
    results_path = args.input
    data_path = args.data
    
    # 生成统计结果输出文件名
    stats_output = os.path.splitext(results_path)[0] + "_stats.json"
    
    # 读取通过信息和题目信息
    try:
        print(f"读取结果文件: {results_path}")
        results = read_jsonl(results_path)
        print(f"读取结果数据完成，共{len(results)}条记录")
        
        # 构建task_id到passed的映射
        dct = {item['task_id']: item['passed'] for item in results}
        print(f"构建通过情况字典完成，共{len(dct)}个任务")
        
        # 读取题目信息
        print(f"读取数据集文件: {data_path}")
        lst = read_jsonl(data_path)
        print(f"读取题目数据完成，共{len(lst)}条记录")
        
        # 计算每月通过率和难度通过率
        monthly_stats, difficulty_stats = calculate_monthly_pass_rate(dct, lst)
        
        # 打印按月份统计的结果
        print("\n按月份统计的通过率:")
        print("=" * 50)
        print(f"{'月份':<10} {'总数':<8} {'通过':<8} {'通过率':<8}")
        print("-" * 50)
        for stat in monthly_stats:
            print(f"{stat['month']:<10} {stat['total']:<8} {stat['passed']:<8} {stat['pass_rate']:.2f}%")
        print("=" * 50)
        
        # 打印按题目难度统计的结果
        print("\n按题目难度统计的通过率:")
        print("=" * 50)
        print(f"{'难度':<10} {'总数':<8} {'通过':<8} {'通过率':<8}")
        print("-" * 50)
        
        difficulty_stats_list = []
        for difficulty, stats in difficulty_stats.items():
            if stats['total'] > 0:
                pass_rate = (stats['passed'] / stats['total']) * 100
                print(f"{difficulty:<10} {stats['total']:<8} {stats['passed']:<8} {pass_rate:.2f}%")
                difficulty_stats_list.append({
                    'difficulty': difficulty,
                    'total': stats['total'],
                    'passed': stats['passed'],
                    'pass_rate': pass_rate
                })
        print("=" * 50)
        
        # 计算总体通过率
        total_problems = sum(stat['total'] for stat in monthly_stats)
        total_passed = sum(stat['passed'] for stat in monthly_stats)
        overall_pass_rate = (total_passed / total_problems) * 100 if total_problems > 0 else 0
        print(f"\n总体通过率: {overall_pass_rate:.2f}% ({total_passed}/{total_problems})")
        
        # 将统计结果保存到文件
        stats_data = {
            'monthly_stats': monthly_stats,
            'difficulty_stats': difficulty_stats_list,
            'overall': {
                'total': total_problems,
                'passed': total_passed,
                'pass_rate': overall_pass_rate
            }
        }
        
        with open(stats_output, 'w', encoding='utf-8') as f:
            json.dump(stats_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n统计结果已保存到: {stats_output}")
        
    except Exception as e:
        print(f"处理数据时出错: {e}")

if __name__ == "__main__":
    main() 