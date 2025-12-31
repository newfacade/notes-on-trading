import leetcode
from leetcode.rest import ApiException
from leetcode.models import GraphqlResponse
from bs4 import BeautifulSoup


leetcode_session = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJfYXV0aF91c2VyX2lkIjoiNzcxNzYxOSIsIl9hdXRoX3VzZXJfYmFja2VuZCI6ImRqYW5nby5jb250cmliLmF1dGguYmFja2VuZHMuTW9kZWxCYWNrZW5kIiwiX2F1dGhfdXNlcl9oYXNoIjoiM2NlMjkzZGNhOGJlMGNiMjg4NjRhYTE1MTJiMDY1YTZkMTQzYmU4YjQ4Y2VjODM5NDFiM2I5NGM0OTJmMjY5YyIsImlkIjo3NzE3NjE5LCJlbWFpbCI6IiIsInVzZXJuYW1lIjoiZm9jdXNlZC1ibGFja3Z2ZWxsbXk1IiwidXNlcl9zbHVnIjoiZm9jdXNlZC1ibGFja3Z2ZWxsbXk1IiwiYXZhdGFyIjoiaHR0cHM6Ly9hc3NldHMubGVldGNvZGUuY24vYWxpeXVuLWxjLXVwbG9hZC9kZWZhdWx0X2F2YXRhci5wbmciLCJwaG9uZV92ZXJpZmllZCI6dHJ1ZSwiZGV2aWNlX2lkIjoiNmYxYTY2NjM0YmIyMzkwZWZiMmMzY2VjZjUzMTg1NmEiLCJpcCI6IjIyMS4yMjEuMTU4LjIzOCIsIl90aW1lc3RhbXAiOjE3NDI5NzI5MzguMzYyMTY4LCJleHBpcmVkX3RpbWVfIjoxNzQ1NTIxMjAwLCJ2ZXJzaW9uX2tleV8iOjEsImxhdGVzdF90aW1lc3RhbXBfIjoxNzQzMTQzNjYyfQ.jzQq8WaxmIft_BM2d26iMuNHsXRJQt7ugNI5FGuJWkg"
csrf_token = "Wk62Zoh2IzKuhWJP57NdEm1wh9wX5gOoQwxMDbJNDZUQinsjYqFxbXeEZmOKRAPv"


def init_leetcode(leetcode_session, csrf_token):
    """init leetcode api"""
    configuration = leetcode.Configuration()

    configuration.api_key["x-csrftoken"] = csrf_token
    configuration.api_key["csrftoken"] = csrf_token
    configuration.api_key["LEETCODE_SESSION"] = leetcode_session
    configuration.api_key["Referer"] = "https://leetcode.cn"
    configuration.debug = False
    api_instance = leetcode.DefaultApi(leetcode.ApiClient(configuration))
    api_instance.api_client.configuration.api_key["LEETCODE_SESSION"]
    return api_instance


def html_to_text(html_string):
    soup = BeautifulSoup(html_string, 'html.parser')
    #text = soup.get_text(separator='\n', strip=False)
    text = soup.get_text(strip=False)
    return text


def get_question_content(api_instance, title_slug="add-two-numbers"):
    """获取问题描述"""
    body = {
        "query": "\n    query questionContent($titleSlug: String!) {\n  question(titleSlug: $titleSlug) {\n    content\n    mysqlSchemas\n    difficulty\n    dataSchemas\n  }\n}\n    ",
        "variables": {
            "titleSlug": title_slug
        },
        "operationName": "questionContent"
    }
    try:
        api_response = api_instance.graphql_post(body=body)
        return api_response, None
    except ApiException as e:
        print("Exception when calling DefaultApi->api_problems_topic_get: %s\n" % e)
        return None, str(e)
    

def get_question_editor_info(api_instance, title_slug):
    body = {
        "query": "\n    query questionEditorData($titleSlug: String!) {\n  question(titleSlug: $titleSlug) {\n    questionId\n    questionFrontendId\n    codeSnippets {\n      lang\n      langSlug\n      code\n    }\n    envInfo\n    enableRunCode\n    hasFrontendPreview\n    frontendPreviews\n  }\n}\n    ",
        "variables": {
            "titleSlug": title_slug
        },
        "operationName": "questionEditorData"
    }
    try:
        api_response = api_instance.graphql_post(body=body)
        return api_response, None
    except ApiException as e:
        print("Exception when calling DefaultApi->api_problems_topic_get: %s\n" % e)
        return None, str(e)


def get_question_editor_info_by_lang(api_instance, title_slug, lang):
    res, error_info = get_question_editor_info(api_instance, title_slug)
    if isinstance(res, GraphqlResponse):
        code_list = res.data.question.code_snippets
    else:
        return None, error_info
    for c in code_list:
        if c.lang_slug == lang:
            return c.code, None
    return [i.lang_slug for i in code_list], f"not supported language[{lang}]"


def submit(api_instance, problem, lang, question_id, typed_code):

    body = leetcode.Submission(lang=lang,
                        judge_type="large",
                        question_id=str(question_id),
                        test_mode=False,
                        typed_code=typed_code)
    try:
        api_response = api_instance.problems_problem_submit_post(problem, body=body)
        return api_response, None

    except ApiException as e:
        print("[kg_leetcode][submit]Exception when calling DefaultApi->problems_problem_submit_post: %s\n" % e)
        print(f"[kg_leetcode][submit]{body}")
        return None, str(e)

