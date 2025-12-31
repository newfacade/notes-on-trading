import sys
import multiprocessing
from io import StringIO
from typing import Any, Dict, Tuple


def worker_process(
    queue: multiprocessing.Queue,
    code: str,
    entry_point: str,
    params: Dict
) -> None:
    """在子进程中执行用户代码的辅助函数"""
    try:
        sys.stdout = StringIO()
        namespace = {}
        
        # 执行用户代码
        exec(code, namespace)
        
        method = eval(entry_point, namespace)

        # 执行目标方法
        result = method(**params)

        output = sys.stdout.getvalue()

        queue.put((output, result, None))

        print('output:', output)
        print('result:', result)
        
    except Exception as e:
        queue.put(("", None, str(e)))


def get_output_given_entry_point_input(
    code: str,
    entry_point: str,
    params: Dict,
) -> str:
    """改进后的安全执行函数"""

    # 创建通信队列和子进程
    ctx = multiprocessing.get_context('spawn')
    queue = ctx.Queue()
    p = ctx.Process(
        target=worker_process,
        args=(queue, code, entry_point, params)
    )
    
    try:
        p.start()
        p.join(timeout=10)  # 10秒超时
        
        if p.is_alive():
            p.terminate()
            p.join()
            return "Execution timed out"
            
        if queue.empty():
            return "No output generated"
            
        output, result, error = queue.get()
        
        if error:
            return f"Error: {error}"
            
        return str(result)
        
    except Exception as e:
        return f"System error: {str(e)}"


if __name__ == '__main__':
    # 将主要代码移到 if __name__ == '__main__' 块中
    # 这样可以避免在导入模块时执行代码，解决多进程启动问题
    code = """def func(a: int, b: int):
    return a + b"""
    entry_point = "func"
    params = {'a': 2, 'b': 3}
    x = get_output_given_entry_point_input(code, entry_point, params)
    print(x)