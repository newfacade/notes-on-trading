import sys
from io import StringIO
from typing import Any, Dict, List, Tuple, Union
import signal
import re
import ast
from functools import lru_cache

from .data_structure import tree_node, tree_node_to_list, list_node, linked_list_to_list, TreeNode, ListNode


def parse_input(input_str: str) -> Dict:
    params = {}
    pattern = r"(\w+)\s*=\s*(.+?)(?=,\s*\w+\s*=|$)"
    matches = re.finditer(pattern, input_str)
    
    for match in matches:
        key = match.group(1).strip()
        value_str = match.group(2).strip()
        try:
            params[key] = ast.literal_eval(value_str)
        except (SyntaxError, ValueError) as e:
            continue
    return params


def parse_no_key_input(input_str: str) -> list:
    try:
        obj = ast.literal_eval(input_str.strip())
        return [obj]
    except:
        return []


# 预编译的正则表达式
CLASS_METHOD_PATTERN = re.compile(r'(\w+)\(\)(\.(\w+))?')
CLASS_PATTERN = re.compile(r'class\s+(\w+)\b')
METHOD_PATTERN = re.compile(r'def\s+(\w+)\s*\(\s*self\s*,\s*(.*?)\s*\)\s*(?:->|:)', re.DOTALL)
PARAM_PATTERN = re.compile(r'(\w+)\s*:\s*(\'?[^,\)]+\'?)')
SIMPLE_PARAM_PATTERN = re.compile(r'(\w+)\s*(?:,|$)')

# 缓存最近使用的1000个结果
@lru_cache(maxsize=1000)
def extract_param_types(lang_code: str, entry_point: str) -> Dict[str, str]:
    """
    Extract parameter types from lang_code for a class method
    
    Args:
        lang_code: Language code containing type annotations
        entry_point: Entry point in the format "Solution().methodName"
        
    Returns:
        Dictionary mapping parameter names to their type strings
    """
    param_types = {}
    
    # 解析类名和方法名
    match = CLASS_METHOD_PATTERN.match(entry_point)
    if not match or not match.group(3):
        return param_types
        
    class_name = match.group(1)
    method_name = match.group(3)
    
    # 查找类定义
    class_matches = CLASS_PATTERN.finditer(lang_code)
    for class_match in class_matches:
        if class_match.group(1) == class_name:
            # 在类定义之后查找方法
            method_matches = METHOD_PATTERN.finditer(lang_code[class_match.start():])
            for method_match in method_matches:
                if method_match.group(1) == method_name:
                    # 提取参数
                    params_str = method_match.group(2)
                    
                    # 尝试提取带类型注解的参数
                    for param_match in PARAM_PATTERN.finditer(params_str):
                        param_name = param_match.group(1)
                        param_type = param_match.group(2)
                        param_types[param_name] = param_type
                    
                    # 如果没有找到带类型的参数，尝试只提取参数名
                    if not param_types:
                        for simple_match in SIMPLE_PARAM_PATTERN.finditer(params_str):
                            param_name = simple_match.group(1)
                            if param_name and param_name not in param_types:
                                param_types[param_name] = 'any'
                    
                    # 找到方法后返回
                    return param_types
    
    return param_types


def format_result(result: Any, assertion: str) -> str:
    """
    Format the result to the appropriate string representation
    
    Args:
        result: The result to format
        
    Returns:
        String representation of the result
    """
    # Check if result is a TreeNode
    if isinstance(result, TreeNode) or (hasattr(result, 'left') and hasattr(result, 'right')):
        result = tree_node_to_list(result)
        assertion = f"    assert is_same_tree({assertion}, tree_node({result}))\n"
    # Check if result is a ListNode
    elif isinstance(result, ListNode) or hasattr(result, 'val'):
        result = linked_list_to_list(result)
        assertion = f'    assert is_same_list({assertion}, list_node({result}))\n'
    elif isinstance(result, str):
        assertion = f'    assert {assertion} == "{result}"\n'
    else:
        assertion = f'    assert {assertion} == {result}\n'
    
    return str(result), assertion


def process_input(input_str: str, lang_code: str = '', entry_point: str = '') -> Tuple[Dict, str]:
    """
    Process input string and return parameters
    
    Args:
        input_str: The input string to parse
        lang_code: Language code to determine special handling
        entry_point: Entry point function or method to analyze parameter types
        
    Returns:
        Dictionary of parameters, assertion string
    """
    input_str = input_str.replace('null', 'None')
    
    # Parse input into parameters
    params = parse_input(input_str=input_str)
    assertion = ""
    
    # Get parameter types from lang_code and entry_point
    param_types = extract_param_types(lang_code, entry_point)
    
    # Convert parameters based on their types
    for param_name, param_value in params.items():
        if param_name in param_types:
            param_type = param_types[param_name]
            if isinstance(param_value, list):
                if 'TreeNode' in param_type:
                    params[param_name] = tree_node(param_value)
                    assertion += f"{param_name} = tree_node({param_value}),"
                elif 'ListNode' in param_type:
                    params[param_name] = list_node(param_value)
                    assertion += f"{param_name} = list_node({param_value}),"
                else:
                    assertion += f'{param_name} = {param_value},'
            elif isinstance(param_value, str):
                assertion += f'{param_name} = "{param_value}",'
            else:
                assertion += f'{param_name} = {param_value},'
    return params, f"candidate({assertion[:-1]})"

