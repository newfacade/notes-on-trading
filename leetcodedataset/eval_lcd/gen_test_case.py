import sys
from io import StringIO
from typing import Any, Dict
import signal
import json
from collections import defaultdict
import re
import ast


def prompt_generate_input(item: dict):
    prompt = "You are an expert Python programmer. You will be given a question (including a problem specification and starter code) along with a few sample inputs. Your task is to generate additional inputs that are consistent with the question and the provided sample inputs.\n\n"
    question = item['meta']['query']
    sample_inputs = "```json\n" + json.dumps([item["input"] for item in item['examples']], ensure_ascii=False, indent=4) + '\n```'

    prompt += "#### Question:\n" + question + "\n\n"
    prompt += "#### Sample inputs (using json format):\n" + sample_inputs + "\n\n"
    prompt += "#### Generate 5 additional inputs that are more complex than the sample inputs (using json format):\n"
    return prompt


def extract_code_blocks(text: str, lang="") -> list:
    """
    Vanilla extract code blocks.
    """
    lang = "python" if lang == "python3" else lang
    # 假如你需要匹配文本中的字符"\"，那么使用编程语言表示的正则表达式里将需要4个反斜杠"\\\\"：前两个和后两个分别用于在编程语言里转义成反斜杠，
    # 转换成两个反斜杠后再在正则表达式里转义成一个反斜杠。Python里的原生字符串很好地解决了这个问题，这个例子中的正则表达式可以使用r"\\"表示。
    # try print(r"Hello\nWorld") and print("Hello\nWorld")
    # (.*?) is a non-greedy match, so it will match the shortest possible string
    if lang:
        pattern = rf"```{lang}\n(.*?)```"
    else:
        pattern = r"```[^\n]*\n(.*?)```"
    # re.S makes the dot match newlines
    return re.findall(pattern, text, re.S)


def get_task2inputs(lst1, lst2):
    task2inputs = defaultdict(set)
    for a, b in zip(lst1, lst2):
        task_id = a['task_id']
        code_blocks = extract_code_blocks(b['output'], 'json')
        for block in code_blocks:
            try:
                tmp = json.loads(block)
                for s in tmp:
                    task2inputs[task_id].add(s)
            except:
                continue
    return task2inputs


def parse_input(input_str: str) -> Dict:
    params = {}
    # 使用正则匹配键值对（兼容嵌套结构）
    pattern = r"(\w+)\s*=\s*(.+?)(?=,\s*\w+\s*=|$)"
    matches = re.finditer(pattern, input_str)
    
    for match in matches:
        key = match.group(1).strip()
        value_str = match.group(2).strip()
        try:
            # 安全解析（替代eval）
            params[key] = ast.literal_eval(value_str)
        except (SyntaxError, ValueError) as e:
            # raise ValueError(f"参数'{key}'解析失败: {str(e)}")
            continue
    return params


def parse_no_key_input(input_str: str) -> list:
    try:
        obj = ast.literal_eval(input_str.strip())
        return [obj]
    except:
        return []


def get_output_given_entry_point_input(
    code: str, 
    entry_point: str, 
    input_str: str
) -> str:
    # 创建临时命名空间隔离执行环境
    namespace = {}

    def timeout_handler(signum, frame):
        raise TimeoutError("Function execution timed out")
    
    try:
        # 执行代码（网页1提到的模块化思想）
        exec(code, namespace)
        
        # 解析输入参数（网页6/7/8的字符串处理技术）
        params = parse_input(input_str=input_str)
        list_params = parse_no_key_input(input_str=input_str) if not params else []
            
        # 解析入口点（网页5的函数入口地址思想）
        if '(' in entry_point and ')' in entry_point:
            # 处理类似 "Solution().twoSum" 的实例方法调用
            class_name = entry_point.split('.')[0].replace('(', '').replace(')', '')
            method_name = entry_point.split('.')[1]
            
            # 实例化类（网页4提到的入口点获取逻辑）
            instance = namespace[class_name]()
            method = getattr(instance, method_name)
        else:
            # 处理普通函数调用
            method = eval(entry_point, namespace)
            
        # 执行并捕获输出（网页2提到的错误处理）
        original_stdout = sys.stdout
        sys.stdout = StringIO()
        
        try:
            # 设置10秒超时信号
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(3)

            if params:
                result = method(**params)
            else:
                result = method(*list_params)
            output = str(result)
        except Exception as e:
            output = f"Error: {str(e)}"
        finally:
            sys.stdout = original_stdout
            signal.alarm(0)  # 必须重置信号
            
        return output
        
    except Exception as e:
        return f"Execution Error: {str(e)}"
    



