# Please install OpenAI SDK first: `pip3 install openai`
import argparse
import os
import json
import concurrent.futures
from tqdm import tqdm
from datetime import datetime
from eval_lcd.data import read_jsonl, write_jsonl
from openai import OpenAI
import time

def parse_args():
    parser = argparse.ArgumentParser(description='Query Aliyun API with data from a JSONL file')
    parser.add_argument('-i', '--input', type=str, required=True, help='Input JSONL file path')
    parser.add_argument('-o', '--output', type=str, help='Output JSONL file path (default: input_model_timestamp_results.jsonl)')
    parser.add_argument('-s', '--system', type=str, default="You are a helpful assistant", help='System prompt')
    parser.add_argument('-m', '--model', type=str, default="deepseek-chat", help='Model name (default: deepseek-chat)')
    parser.add_argument('-k', '--key', type=str, default='sk-2a42692ddd754193bf25ca3a819e59b3', help='API key')
    parser.add_argument('-b', '--base_url', type=str, default="https://dashscope.aliyuncs.com/compatible-mode/v1", help='API base URL')
    parser.add_argument('-t', '--threads', type=int, default=4, help='Number of threads (default: 4)')
    parser.add_argument('--stream', action='store_true', help='Use streaming API (default: False)')
    return parser.parse_args()

def process_item(item, client, model, system_prompt, tmp_file, use_stream=False):
    query = item.get("query", "")
    
    if use_stream:
        reasoning_content = ""
        answer_content = ""
        is_answering = False
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query},
            ],
            temperature=0.2,
            top_p=0.95,
            stream=True
        )
        
        for chunk in response:
            if not chunk.choices:
                if hasattr(chunk, 'usage'):
                    item["usage"] = chunk.usage.to_dict()
            else:
                delta = chunk.choices[0].delta
                if hasattr(delta, 'reasoning_content') and delta.reasoning_content is not None:
                    reasoning_content += delta.reasoning_content
                elif hasattr(delta, 'content') and delta.content is not None:
                    if not is_answering and delta.content != "":
                        is_answering = True
                    answer_content += delta.content
        
        item["output"] = answer_content
        item["reasoning"] = reasoning_content
    else:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query},
            ],
            temperature=0.2,
            top_p=0.95,
            stream=False
        )
        
        # Add response to the item
        item["output"] = response.choices[0].message.content
        item["meta"] = response.to_dict()
    
    # Write to temporary file immediately to prevent data loss
    with open(tmp_file, 'a') as f:
        f.write(json.dumps(item) + "\n")
    
    return item

def main():
    args = parse_args()
    
    # Get timestamp for file naming
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_id = args.model.replace("/", "-")
    
    # Set up output path
    if not args.output:
        input_base = args.input.replace('.jsonl', '')
        args.output = f"{input_base}_{model_id}_{timestamp}_results.jsonl"
        if args.output == args.input:
            args.output = f"{args.input}_{model_id}_{timestamp}_results.jsonl"
    
    # Create temporary file
    tmp_file = f"{args.output}.{model_id}_{timestamp}.tmp.jsonl"
    if os.path.exists(tmp_file):
        os.remove(tmp_file)
    
    # Get API key
    api_key = args.key
    
    # Initialize client
    client = OpenAI(api_key=api_key, base_url=args.base_url)
    
    # Read input data and add id if not present
    data = []
    for i, item in enumerate(read_jsonl(args.input)):
        if 'id' not in item:
            item['id'] = i
        data.append(item)
    
    results = []
    
    # Process queries in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
        futures = [executor.submit(process_item, item, client, args.model, args.system, tmp_file, args.stream) for item in data]
        
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="Processing queries"):
            results.append(future.result())
    
    # Sort results by id to maintain original order
    results.sort(key=lambda x: x['id'])
    
    # Write results
    write_jsonl(args.output, results)
    print(f"Results written to {args.output}")
    
    # Delete temporary file
    if os.path.exists(tmp_file):
        os.remove(tmp_file)
        print(f"Temporary file {tmp_file} has been deleted")

if __name__ == "__main__":
    # python infer/aliyun-infer.py -i LeetCodeDataset-v0.3.1-test.jsonl -m qwen-max --threads=20
    # python infer/aliyun-infer.py -i LeetCodeDataset-v0.3.1-test.jsonl -m qwq-plus --threads=20 --stream
    # python infer/aliyun-infer.py -i LeetCodeDataset-v0.3.1-test.jsonl -m deepseek-r1 --threads=20
    main()