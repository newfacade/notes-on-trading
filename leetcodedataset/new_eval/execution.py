import re
import multiprocessing
import argparse
import os
from typing import Dict, List, Union, Any
from tqdm import tqdm

from eval_lcd.execution import create_tempdir, swallow_io
from data_process.compute_output import process_input, format_result
from eval_lcd.data import read_jsonl, write_jsonl, show_list


def worker_process(
    queue: multiprocessing.Queue,
    code: str,
    entry_point: str,
    params: Union[Dict, List],
    is_dict_params: bool
) -> None:
    """Helper function to execute user code in a subprocess"""
    try:        
        # Use a temporary directory for code execution to enhance security
        with create_tempdir():
            # Use swallow_io to capture all input and output
            with swallow_io():
                namespace = {}
                
                # Execute user code
                exec(code, namespace)
                
                # Parse class method calls using regex, e.g., "Solution().twoSum"
                # Regex explanation:
                # (\w+) - matches one or more letters, digits, or underscores (class name)
                # \(\) - matches the characters "()" (class instantiation)
                # (\.(\w+))? - optional part, matches a dot followed by one or more letters, digits, or underscores (method name)
                class_method_pattern = re.match(r'(\w+)\(\)(\.(\w+))?', entry_point)
                
                if class_method_pattern and class_method_pattern.group(3):
                    # Get class name and method name
                    # group(1) is the content matched in the first parentheses (class name)
                    # group(3) is the content matched in the third parentheses (method name)
                    class_name = class_method_pattern.group(1)
                    method_name = class_method_pattern.group(3)
                    
                    # Instantiate class and get method
                    instance = namespace[class_name]()
                    method = getattr(instance, method_name)
                else:
                    # Handle regular function calls
                    method = eval(entry_point, namespace)

                # Execute target method based on parameter type
                if is_dict_params:
                    result = method(**params)
                else:
                    result = method(*params)

                queue.put((format_result(result), None))
        
    except TypeError as e:
        if "'NoneType' object is not callable" in str(e):
            queue.put((None, f"Error: Attempted to call a disabled function. Specific error: {e}"))
        else:
            queue.put((None, str(e)))
    except Exception as e:
        queue.put((None, str(e)))


def execute_function(
    code: str,
    entry_point: str,
    params: Union[Dict, List],
    timeout: int = 10
) -> Dict[str, Any]:
    """Improved safe execution function that returns status and result"""

    # Determine parameter type
    is_dict_params = isinstance(params, dict)

    # Create communication queue and subprocess
    ctx = multiprocessing.get_context('spawn')
    queue = ctx.Queue()
    p = ctx.Process(
        target=worker_process,
        args=(queue, code, entry_point, params, is_dict_params)
    )
    
    try:
        p.start()
        p.join(timeout=timeout)  # Configurable timeout
        
        if p.is_alive():
            p.terminate()
            p.join()
            return {
                "status": "timeout",
                "result": "Execution timed out"
            }
            
        if queue.empty():
            return {
                "status": "no_output",
                "result": "No output generated"
            }
            
        result, error = queue.get()
        
        if error:
            return {
                "status": "error",
                "result": f"Error: {error}"
            }
            
        return {
            "status": "success",
            "result": result
        }
        
    except Exception as e:
        return {
            "status": "system_error",
            "result": f"System error: {str(e)}"
        }


def process_data(input_file, output_file=None, start=0, end=None):
    """Process data from input file and write results to output file"""
    lst = read_jsonl(input_file)
    show_list(lst)
    
    # Determine the end index if not provided
    if end is None:
        end = len(lst)
    
    # Ensure start and end are within valid range
    start = max(0, min(start, len(lst)))
    end = max(start, min(end, len(lst)))
    
    # Auto-generate output file name if not provided
    if output_file is None:
        base_name = os.path.splitext(input_file)[0]
        range_suffix = f"-{start}-{end}" if start > 0 or end < len(lst) else ""
        output_file = f"{base_name}{range_suffix}-with-outputs.jsonl"
    
    result = []
    for item in tqdm(lst[start:end]):
        code = item['prompt'] + '\n' + item['completion']
        lang_code = item['lang_code']
        entry_point = item['entry_point']
        tmp = []
        for input_str in item['extra_inputs']:
            params = process_input(input_str, lang_code, entry_point)
            output = execute_function(code, entry_point, params)
            tmp.append(output)
        item['extra_outputs'] = tmp
        result.append(item)
    
    show_list(result)
    write_jsonl(output_file, result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process LeetCode problems and execute solutions')
    parser.add_argument('--input_file', type=str, default='../data/leetcode-0312-single-2926-with-inputs-prompt.jsonl',
                        help='Input JSONL file path')
    parser.add_argument('--output_file', type=str, default=None,
                        help='Output JSONL file path (auto-generated if not specified)')
    parser.add_argument('--start', type=int, default=0,
                        help='Start index for processing (inclusive)')
    parser.add_argument('--end', type=int, default=None,
                        help='End index for processing (exclusive)')
    
    args = parser.parse_args()
    
    process_data(args.input_file, args.output_file, args.start, args.end)
