# -*- coding: utf-8 -*-
import argparse
from datetime import datetime
import concurrent.futures
from typing import List, Dict, Callable, Union
import json
import re
import time
import concurrent.futures
import threading
import functools
import os
import random
import uuid
import sys

import requests
from tqdm import tqdm

# 全局流式输出锁，确保同一时间只有一个线程进行流式输出
stream_output_lock = threading.Lock()

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input_file", type=str, default="", help="输入文件")
parser.add_argument("-m", "--model", type=str, default="gpt-4-1106-preview", help="gpt模型版本")
parser.add_argument("--host", type=str, help="hostname")
parser.add_argument("--port", type=int, default=8000, help="port")

parser.add_argument("--topp", type=float, default=-1, help="topp")
parser.add_argument("--temperature", type=float, default=-1, help="temperature")
parser.add_argument("--num_threads", type=int, default=4, help="线程数")
parser.add_argument("--is_random", default=False, action="store_true", help="是否随机选择一个temperature和topp")
parser.add_argument("--thinking", default=False, action="store_true", help="是否显示思考过程")
parser.add_argument("--max_tokens", type=int, default=8192, help="最大token数")
parser.add_argument("--stream", default=False, action="store_true", help="是否使用流式输出")


def read_jsonl(filename: str):
    """
    Read a jsonl file (or a txt file), parse each line, and return a list.
    """
    with open(filename, "r", encoding="utf-8") as fp:
        return [json.loads(line) for line in fp]


def write_jsonl(filename: str, data: list):
    """
    Write iterable data to a jsonl file.
    """
    with open(filename, "w") as fp:
        for x in data:
            fp.write(json.dumps(x, ensure_ascii=False) + "\n")


def retry(max_attempts=10, delay=10):
    """
    Retry a function.
    """
    def decorator(func):
        # preserve the metadata of the original function when it is decorated
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    print(f"Occur {e}. Retrying...")
                    time.sleep(delay)
            return None
        return wrapper
    return decorator


def multi_thread_write(input_file: str, num_threads: int, process_func: Callable, output_file: str, **kwargs):
    """多线程写文件

    Args:
        input_file (str): 输入文件
        num_threads (int): 线程数
        process_func (Callable): 处理数据的函数
        output_file (str): 输出文件
    """
    lst = read_jsonl(input_file)
    print(len(lst))
    for i, item in enumerate(lst):
        item['idx'] = i
    lock = threading.Lock()
    tmp_output_file = output_file + '-tmp.jsonl'

    def write_one_line(item):
        x = process_func(item, **kwargs)
        with lock:
            with open(tmp_output_file, "a") as fp:
                # 非流式模式下才打印处理进度，避免与流式输出冲突
                if not kwargs.get('stream', False):
                    print(f"process {item['idx']}")
                fp.write(json.dumps(x, ensure_ascii=False) + "\n")

    # 使用线程池
    futures = []
    with concurrent.futures.ThreadPoolExecutor(num_threads) as executor:
        for item in lst:
            future = executor.submit(write_one_line, item)
            futures.append(future)

    # 恢复顺序
    result = read_jsonl(tmp_output_file)
    result.sort(key=lambda x: x['idx'])
    write_jsonl(output_file, result)
    os.remove(tmp_output_file)


@retry(max_attempts=20, delay=10)
def process_data(obj: dict, model: str, host: str, port=8000, topp=-1, temperature=-1, is_random=False, max_tokens=8192, stream=False):
    content = ""
    if 'query' in obj:
        content = obj['query']
    elif 'src' in obj:
        if isinstance(obj['src'], str):
            content = obj['src']
        elif isinstance(obj['src'], list):
            content = obj['src'][0]
    elif 'instruction' in obj:
        content = obj['instruction']
    assert content

    url = f"http://{host}:{port}/v1/chat/completions"

    headers = {
        "Content-Type": "application/json"
    }

    # 请求数据
    data = {
        "model": model,  # 使用你指定的模型名
        "messages": [
            {
                "role": "user", 
                "content": content
            }
        ],
        "max_tokens": max_tokens,
        "temperature": 0.8 if temperature <= 0 else temperature,
        "top_p": 0.8 if topp <= 0 else topp,  # 修复了这里的bug，原来写的是temperature
        # "repetition_penalty": 1.1
        "stream": stream  # 根据参数决定是否流式输出
    }
    if is_random:
        data["temperature"] = random.uniform(0.2, 1.0)
        data["top_p"] = random.uniform(0.6, 1.0)

    if stream:
        # 使用全局锁确保流式输出的连贯性
        with stream_output_lock:
            # 流式输出处理
            print(f"\n{'='*60}")
            print(f"🚀 开始处理第 {obj['idx']} 条数据")
            print(f"📝 内容预览: {content[:100]}{'...' if len(content) > 100 else ''}")
            print(f"{'='*60}")
            sys.stdout.flush()
            
            response = requests.post(url, headers=headers, json=data, timeout=3600, stream=True)
            response.raise_for_status()
            
            output = ""
            print(f"【第 {obj['idx']} 条】流式输出开始：")
            print("-" * 40)
            sys.stdout.flush()
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        line = line[6:]  # 移除 'data: ' 前缀
                        if line.strip() == '[DONE]':
                            break
                        try:
                            chunk = json.loads(line)
                            if 'choices' in chunk and len(chunk['choices']) > 0:
                                delta = chunk['choices'][0].get('delta', {})
                                if 'content' in delta:
                                    content_chunk = delta['content']
                                    output += content_chunk
                                    print(content_chunk, end='', flush=True)  # 实时输出每个chunk
                        except json.JSONDecodeError:
                            continue  # 跳过无法解析的行
            
            print(f"\n{'-'*40}")
            print(f"✅ 【第 {obj['idx']} 条】流式输出完成 (共 {len(output)} 字符)")
            print(f"{'='*60}\n")
            sys.stdout.flush()
        
    else:
        # 非流式输出处理（原来的逻辑）
        response = requests.post(url, headers=headers, json=data, timeout=3600)
        response.raise_for_status()
        result = response.json()
        print(f"✅ process {obj['idx']} completed")
        output = result["choices"][0]["message"]["content"]
    
    assert output
    obj['output'] = output
    obj['model_id'] = model
    obj['top_p'] = data['top_p']
    obj['temperature'] = data['temperature']
    obj['max_tokens'] = data['max_tokens']
    return obj


def gpt_fetch(input_file: str, num_threads: int, model: str, host: str, port=8000, topp=-1, temperature=-1, is_random=False, max_tokens=8192, stream=False):
    """
    多线程获取gpt的tgt

    Args:
        input_file (str): format {'query': ...}
        num_threads (int): 线程数
        model (str): gpt模型id
    """
    output_file = input_file.replace(
        ".jsonl", "") + "-" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S") + "-" + str(topp) + '-'  + model + ".jsonl"
    # output_file = input_file.replace('.jsonl', f'-{model}.jsonl')
    print(output_file)
    
    if stream:
        print("🌊 流式输出模式已启用")
        print("📝 提示：流式输出将按顺序逐个显示，确保输出连贯性")
        print("⚡ 后台仍然使用多线程处理，但显示会排队进行")
        print("="*60)
    
    multi_thread_write(input_file=input_file,
                       num_threads=num_threads,
                       process_func=process_data,
                       output_file=output_file,
                       model=model,
                       host=host,
                       port=port,
                       topp=topp, 
                       temperature=temperature,
                       is_random=is_random,
                       max_tokens=max_tokens,
                       stream=stream)
    return output_file


if __name__ == "__main__":
    args = parser.parse_args()
    gpt_fetch(args.input_file, args.num_threads, args.model, args.host, args.port, args.topp, args.temperature, args.is_random, args.max_tokens, args.stream) 