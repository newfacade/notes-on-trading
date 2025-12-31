import os
import re
import json
import html
import datetime
from typing import List, Dict, Any, Optional

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from eval_lcd.data import write_jsonl


def get_leetcode_problems() -> list:
    """
    Fetch the complete problem list from LeetCode's API.
    
    Returns:
        list: A list containing all LeetCode problems and their metadata
    """
    url = "https://leetcode.com/api/problems/all/"
    response = requests.get(url)
    response.raise_for_status()  # Raise an exception for bad status codes
    info = response.json()
    
    result = []
    for item in info['stat_status_pairs']:
        if item['difficulty']['level'] == 1:
            difficulty = 'Easy'
        elif item['difficulty']['level'] == 2:
            difficulty = 'Medium'
        else:
            assert item['difficulty']['level'] == 3
            difficulty = 'Hard'
        result.append({
            'slug': item['stat']['question__title_slug'], 
            'difficulty': difficulty})
    return result


def get_doocs_leetcode_metadata(root_dir: str) -> Dict[str, Dict[str, Any]]:
    """
    Get metadata for all LeetCode problems from the Doocs solution directory.
    
    Args:
        root_dir (str): The root directory path of Doocs leetcode repository
        
    Returns:
        Dict[str, Dict[str, Any]]: A dictionary with slug as key and metadata as value
    """
    solution_dir = os.path.join(root_dir, 'solution')
    if not os.path.exists(solution_dir):
        return {}
    
    # Get all first-level directories in the solution directory
    first_level_dirs = [
        os.path.join(solution_dir, item) 
        for item in os.listdir(solution_dir) 
        if os.path.isdir(os.path.join(solution_dir, item))
    ]
    
    # Get all second-level directories and extract metadata
    problem_metadata = {}
    for first_dir in tqdm(first_level_dirs):
        for item in os.listdir(first_dir):
            full_path = os.path.join(first_dir, item)
            if os.path.isdir(full_path):
                # Extract problem ID from directory name (e.g., "0001.Two Sum" -> 1)
                match = re.match(r'(\d+)\.', item)
                if match:
                    problem_id = int(match.group(1))
                    
                    # Read README.md content if it exists
                    readme_path = os.path.join(full_path, 'README.md')
                    slug = ""
                    if os.path.exists(readme_path):
                        with open(readme_path, 'r', encoding='utf-8') as f:
                            readme_content = f.read()
                            
                        # Extract slug from leetcode URL in README
                        url_match = re.search(r'https://leetcode\.(?:com|cn)/problems/([^/\)]+)', readme_content)
                        if url_match:
                            slug = url_match.group(1)
                    
                    # Look for Python solution files
                    solutions = []
                    for file in os.listdir(full_path):
                        if file.lower() == 'solution.py':
                            solution_path = os.path.join(full_path, file)
                            with open(solution_path, 'r', encoding='utf-8') as f:
                                solution_content = f.read()
                            solutions.append(solution_content)
                    
                    if slug:
                        problem_metadata[slug] = {
                            'problem_id': problem_id,
                            'solutions': solutions
                        }
    
    return problem_metadata


def get_walkccc_leetcode_metadata(root_dir: str) -> Dict[int, List[str]]:
    """
    Get metadata for all LeetCode problems from the walkccc solution directory.
    
    Args:
        root_dir (str): The root directory path of walkccc leetcode repository
        
    Returns:
        Dict[int, List[str]]: A dictionary with problem_id as key and solutions as value
    """
    solutions_dir = os.path.join(root_dir, 'solutions')
    if not os.path.exists(solutions_dir):
        return {}
    
    problem_solutions = {}
    for item in tqdm(os.listdir(solutions_dir)):
        full_path = os.path.join(solutions_dir, item)
        if os.path.isdir(full_path):
            # Extract problem ID from directory name (e.g., "1.Two Sum" -> 1)
            match = re.match(r'(\d+)\.', item)
            if match:
                problem_id = int(match.group(1))
                
                # Look for Python solution file
                for file in os.listdir(full_path):
                    if file.endswith('.py'):
                        solution_path = os.path.join(full_path, file)
                        with open(solution_path, 'r', encoding='utf-8') as f:
                            solution_content = f.read()
                        
                        if problem_id not in problem_solutions:
                            problem_solutions[problem_id] = []
                        
                        problem_solutions[problem_id].append(solution_content)
    
    return problem_solutions


def dump_basic_leetcode_metadata(doocs_dir: str, walkccc_dir: str) -> None:
    """
    Collect and dump basic LeetCode metadata to a JSONL file.
    
    Args:
        doocs_dir (str): Path to the Doocs LeetCode repository
        walkccc_dir (str): Path to the walkccc LeetCode repository
    """
    # Get basic problem information
    problems = get_leetcode_problems()
    
    # Get solutions from Doocs repository
    doocs_metadata = get_doocs_leetcode_metadata(doocs_dir)
    
    # Get solutions from walkccc repository
    walkccc_solutions = get_walkccc_leetcode_metadata(walkccc_dir)
    
    # Merge the data
    for problem in problems:
        slug = problem['slug']
        
        # Add solutions from Doocs
        if slug in doocs_metadata:
            problem['problem_id'] = doocs_metadata[slug]['problem_id']
            problem['solutions'] = doocs_metadata[slug]['solutions']
        else:
            problem['solutions'] = []
        
        # Add solutions from walkccc if problem_id exists
        if 'problem_id' in problem and problem['problem_id'] in walkccc_solutions:
            problem['solutions'].extend(walkccc_solutions[problem['problem_id']])
    
    # Filter out problems without problem_id
    problems = [p for p in problems if 'problem_id' in p]
    
    # Sort by problem_id
    problems.sort(key=lambda x: x['problem_id'])
    
    # Generate filename with timestamp
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    output_file = f"/Users/xiayunhui/github/LeetCodeDataset/data/leetcode-basic-metadata-{timestamp}.jsonl"
    
    # Ensure the directory exists
    os.makedirs("data", exist_ok=True)
    
    # Write to JSONL file
    write_jsonl(output_file, problems)
    print(f"Wrote {len(problems)} problems to {output_file}")


# LeetCode authentication cookies (obtained from browser)
cookies = {
    "LEETCODE_SESSION": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJfYXV0aF91c2VyX2lkIjoiNzcxNzYxOSIsIl9hdXRoX3VzZXJfYmFja2VuZCI6ImRqYW5nby5jb250cmliLmF1dGguYmFja2VuZHMuTW9kZWxCYWNrZW5kIiwiX2F1dGhfdXNlcl9oYXNoIjoiM2NlMjkzZGNhOGJlMGNiMjg4NjRhYTE1MTJiMDY1YTZkMTQzYmU4YjQ4Y2VjODM5NDFiM2I5NGM0OTJmMjY5YyIsImlkIjo3NzE3NjE5LCJlbWFpbCI6IiIsInVzZXJuYW1lIjoiZm9jdXNlZC1ibGFja3Z2ZWxsbXk1IiwidXNlcl9zbHVnIjoiZm9jdXNlZC1ibGFja3Z2ZWxsbXk1IiwiYXZhdGFyIjoiaHR0cHM6Ly9hc3NldHMubGVldGNvZGUuY24vYWxpeXVuLWxjLXVwbG9hZC9kZWZhdWx0X2F2YXRhci5wbmciLCJwaG9uZV92ZXJpZmllZCI6dHJ1ZSwiZGV2aWNlX2lkIjoiNmYxYTY2NjM0YmIyMzkwZWZiMmMzY2VjZjUzMTg1NmEiLCJpcCI6IjIyMS4yMjEuMTU4LjIzOCIsIl90aW1lc3RhbXAiOjE3NDI5NzI5MzguMzYyMTY4LCJleHBpcmVkX3RpbWVfIjoxNzQ1NTIxMjAwLCJ2ZXJzaW9uX2tleV8iOjEsImxhdGVzdF90aW1lc3RhbXBfIjoxNzQzMTQzNjYyfQ.jzQq8WaxmIft_BM2d26iMuNHsXRJQt7ugNI5FGuJWkg",
    "csrftoken": "Wk62Zoh2IzKuhWJP57NdEm1wh9wX5gOoQwxMDbJNDZUQinsjYqFxbXeEZmOKRAPv",
}
# Request headers (simulating browser, some websites validate User-Agent)
headers = {
    "User-Agent": "Chrome/133.0.6943.143",
    "Referer": "https://leetcode.cn/",  # Optional, some requests require Referer
}


def get_problem_text(slug: str) -> Optional[str]:
    """
    Fetch the HTML content of a LeetCode problem page.
    
    Args:
        slug (str): The problem slug identifier
        
    Returns:
        Optional[str]: The HTML content of the problem page, or None if request fails
    """
    url = f"https://leetcode.cn/problems/{slug}/description/"
    response = requests.get(url, headers=headers, cookies=cookies)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        return str(soup)
    return None
    

def trans_format(escaped_code):
    """
    Transform escaped code from JSON format to readable text.
    
    Args:
        escaped_code (str): The escaped code string
        
    Returns:
        str: The unescaped, readable code
    """
    # Replace JSON Unicode escapes
    code = re.sub(r'\\u([0-9a-fA-F]{4})', 
                    lambda m: chr(int(m.group(1), 16)), 
                    escaped_code)
    
    # Handle other common escape sequences
    code = code.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"').replace('\\\\', '\\')
    
    # Handle HTML entities
    code = html.unescape(code)
    
    return code


def html_to_text(html_string):
    """
    Convert HTML string to plain text.
    
    Args:
        html_string (str): The HTML content
        
    Returns:
        str: The extracted plain text
    """
    soup = BeautifulSoup(html_string, 'html.parser')
    #text = soup.get_text(separator='\n', strip=False)
    text = soup.get_text(strip=False)
    return text
    

def get_problem_topic_tags(text: str) -> List[str]:
    """
    Extract topic tags from problem HTML.
    
    Args:
        text (str): The problem HTML content
        
    Returns:
        List[str]: List of topic tags for the problem
    """
    pattern = r'"topicTags"\s*:\s*(\[[^\]]*\])'
    match = re.search(pattern, text)
    if match:
        m = match.group(1)
        topic_tags = [item['name'] for item in json.loads(m)]
        return topic_tags
    return []


def get_problem_lang_code(text: str) -> str:
    """
    Extract Python starter code from problem HTML.
    
    Args:
        text (str): The problem HTML content
        
    Returns:
        str: The Python starter code for the problem
    """
    if r'","lang":"Python3","langSlug":"python3"' in text:
        pattern = r'.*"code":"(.*?)","lang":"Python3","langSlug":"python3"'
        match = re.search(pattern, text, re.DOTALL)
        if match:
            m = match.group(1)
            return html_to_text(trans_format(m))
    return ''
    

def get_problem_question_title(text: str) -> str:
    """
    Extract problem description from HTML.
    
    Args:
        text (str): The problem HTML content
        
    Returns:
        str: The problem description text
    """
    pattern = r'.*"content":"(.*?)","translatedContent"'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        m = match.group(1)
        return html_to_text(trans_format(m))
    return ''


if __name__ == "__main__":
    # Execute the metadata collection process
    doocs_dir = '/Users/xiayunhui/github/leetcode'
    walkccc_dir = '/Users/xiayunhui/Projects/LeetCode'
    dump_basic_leetcode_metadata(doocs_dir, walkccc_dir)
