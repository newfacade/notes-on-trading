from time import sleep
import sqlite3
import json
import requests
import leetcode
import leetcode.auth
from leetcode.rest import ApiException
from leetcode.models import GraphqlResponse


def init_leetcode(leetcode_session, csrf_token):
    """init leetcode api"""
    #csrf_token = leetcode.auth.get_csrf_cookie(leetcode_session)
    #print(csrf_token)
    #csrf_token="aabUvjhMRQ6ceKqnzTPahkxQCFaKwNQxkSFoa9ieb6yB70wu2BB7Jvvo9E1qXrOw"
    #csrf_token="3fICsPHFce5GyxjlHaGbbSgCafvBJrtFIgg5vzA6CchfP0zMpZS14Oc9DDG1uJ8e"
    
    configuration = leetcode.Configuration()

    configuration.api_key["x-csrftoken"] = csrf_token
    configuration.api_key["csrftoken"] = csrf_token
    configuration.api_key["LEETCODE_SESSION"] = leetcode_session
    configuration.api_key["Referer"] = "https://leetcode.cn"
    configuration.debug = False
    api_instance = leetcode.DefaultApi(leetcode.ApiClient(configuration))
    api_instance.api_client.configuration.api_key["LEETCODE_SESSION"]
    return api_instance


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
    


def check(api_instance, id):

    try:
        api_response = api_instance.submissions_detail_id_check_get(id)
        return api_response, None
    except ApiException as e:
        print("[kg_leetcode][check]Exception when calling DefaultApi->submissions_detail_id_check_get: %s\n" % e)
        print(f"[kg_leetcode][check]{id}")
        return None, str(e)


def get_weekly_contest_question(week_num):
    url = f"https://leetcode.cn/contest/api/ranking/weekly-contest-{week_num}/?pagination=1&region=local"
    headers = {'User-Agent': 'PostmanRuntime/7.26.8'}
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        return res.json(), None
    else:
        print(res.content)
        return None, res.status_code


def get_question_cn_content(api_instance, title_slug="add-two-numbers"):
    """获取问题中文描述"""
    body = {
        "query": "\n    query questionTranslations($titleSlug: String!) {\n  question(titleSlug: $titleSlug) {\n    translatedTitle\n    difficulty\n    translatedContent\n  }\n}\n    ",
        "variables": {
            "titleSlug": title_slug
        },
        "operationName": "questionTranslations"
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


def get_similar_question(api_instance, title_slug="binary-tree-inorder-traversal"):
    body = {
        "query": "\n    query similarQuestion($titleSlug: String!) {\n  question(titleSlug: $titleSlug) {\n    similarQuestions\n  }\n}\n    ",
        "variables": {
            "titleSlug": title_slug
        },
        "operationName": "similarQuestion"
    }
    try:
        api_response = api_instance.graphql_post(body=body)
        if isinstance(api_response, GraphqlResponse):
            try:
                question_list = json.loads(api_response.data.question.similar_questions)
                return question_list, None
            except Exception as e:
                print(api_response)
                return [], str(e)
        else:
            return [], str(e)
    except ApiException as e:
        print("Exception when calling DefaultApi->api_problems_topic_get: %s\n" % e)
        return [], str(e)


def get_question_info(api_instance, question_title):
    body = {"query": "\n    query questionTitle($titleSlug: String!) {\n  question(titleSlug: $titleSlug) {\n    questionId\n    questionFrontendId\n    title\n    titleSlug\n    isPaidOnly\n    difficulty\n    likes\n    dislikes\n    categoryTitle\n  }\n}\n    ",
        "variables": {
        "titleSlug": question_title
        },
    "operationName": "questionTitle"
    }
    
    try:
        api_response = api_instance.graphql_post(body=body)
        if isinstance(api_response, GraphqlResponse):
            try:
                question_dict = api_response.data.question
                print(question_dict)
                return {"id": question_dict.question_id, 
                        "title": question_dict.title_slug,
                        "difficulty": question_dict.difficulty, 
                        "topic_tag": question_dict.topic_tags,
                        "describe": ""}, None
            except Exception as e:
                print(api_response)
                print(str(e))
                return [], str(e)
        else:
            return [], str(e)
    except ApiException as e:
        print("Exception when calling DefaultApi->api_problems_topic_get: %s\n" % e)
        return [], str(e)

if __name__ == "__main__":
    #import multiprocessing

    #leetcode_session = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJfYXV0aF91c2VyX2lkIjoiMTg1NTg3NSIsIl9hdXRoX3VzZXJfYmFja2VuZCI6ImRqYW5nby5jb250cmliLmF1dGguYmFja2VuZHMuTW9kZWxCYWNrZW5kIiwiX2F1dGhfdXNlcl9oYXNoIjoiZTg0M2I5Mjg5NDJhZjAzZDZjOTI4MmFmMjBiMTBkNTA2NGI0M2RiNzA1MjlhYWJkZDE1NTBhMWZkYmIzNTAyMyIsImlkIjoxODU1ODc1LCJlbWFpbCI6IndhbmdzaHVhaTIwMTdAaWEuYWMuY24iLCJ1c2VybmFtZSI6ImZvY3VzZWQtNmVybWFpbiIsInVzZXJfc2x1ZyI6ImZvY3VzZWQtNmVybWFpbiIsImF2YXRhciI6Imh0dHBzOi8vYXNzZXRzLmxlZXRjb2RlLmNuL2FsaXl1bi1sYy11cGxvYWQvdXNlcnMvZm9jdXNlZC02ZXJtYWluL2F2YXRhcl8xNTkzNDIyNzcyLnBuZyIsInBob25lX3ZlcmlmaWVkIjp0cnVlLCJfdGltZXN0YW1wIjoxNzA0OTU0MzU2LjI1NzU2NzYsImV4cGlyZWRfdGltZV8iOjE3MDc1MDUyMDAsInZlcnNpb25fa2V5XyI6MCwibGF0ZXN0X3RpbWVzdGFtcF8iOjE3MDQ5NTUxNjV9.8G1pR3d0lwKaHK8-qDCAYlyaCqQT4sc2WtVOP3VTbE8"
    #leetcode_session = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJfYXV0aF91c2VyX2lkIjoiMTAxOTYyOSIsIl9hdXRoX3VzZXJfYmFja2VuZCI6ImRqYW5nby5jb250cmliLmF1dGguYmFja2VuZHMuTW9kZWxCYWNrZW5kIiwiX2F1dGhfdXNlcl9oYXNoIjoiMTk1MmFjNmZiOTcyZGE2NDIzZTZlMGQ3OTBhM2JlNDFhZjQyODI5OWM5NzlmZjE0MmY1OTY0OTI4YTAwMzE5MiIsImlkIjoxMDE5NjI5LCJlbWFpbCI6IiIsInVzZXJuYW1lIjoibmV3ZmFjYWRlIiwidXNlcl9zbHVnIjoibmV3ZmFjYWRlIiwiYXZhdGFyIjoiaHR0cHM6Ly9hc3NldHMubGVldGNvZGUuY24vYWxpeXVuLWxjLXVwbG9hZC91c2Vycy9uZXdmYWNhZGUvYXZhdGFyXzE2MzQwNDk1MjkucG5nIiwicGhvbmVfdmVyaWZpZWQiOnRydWUsIl90aW1lc3RhbXAiOjE3MTUyMjI4NjEuNDY3MDQ3LCJleHBpcmVkX3RpbWVfIjoxNzE3Nzg2ODAwLCJ2ZXJzaW9uX2tleV8iOjJ9.BfuSC4lTWwGhbYNul2LS5NN2mjuE-xWhSqkQ236zWvQ"
    #leetcode_session = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJfYXV0aF91c2VyX2lkIjoiMTUyNTMyIiwiX2F1dGhfdXNlcl9iYWNrZW5kIjoiZGphbmdvLmNvbnRyaWIuYXV0aC5iYWNrZW5kcy5Nb2RlbEJhY2tlbmQiLCJfYXV0aF91c2VyX2hhc2giOiI0ZDZmNDdjNGE0NTg0ZTI4ZjBiMzEzMWZlZGFmNGZhNmJlOTFmNjA2YWIyZTdlYWM1ZjcwODA1MDlhYzY3ODljIiwiaWQiOjE1MjUzMiwiZW1haWwiOiIiLCJ1c2VybmFtZSI6Imphc2FwZXIiLCJ1c2VyX3NsdWciOiJqYXNhcGVyIiwiYXZhdGFyIjoiaHR0cHM6Ly9hc3NldHMubGVldGNvZGUuY24vYWxpeXVuLWxjLXVwbG9hZC9kZWZhdWx0X2F2YXRhci5wbmciLCJwaG9uZV92ZXJpZmllZCI6dHJ1ZSwiZGV2aWNlX2lkIjoiMzU1ZDA2ZWJmYmQ1MjQ1N2NlYTFkNTc2MWMyMDExNWYiLCJpcCI6IjIyMC4xODEuMy4xNTEiLCJfdGltZXN0YW1wIjoxNzE3Njc4NTM1LjIzMDg0MywiZXhwaXJlZF90aW1lXyI6MTcyMDIwNjAwMCwidmVyc2lvbl9rZXlfIjowfQ.MvYc14Z_rURtiSpku0wCF4mI16EblAd5I3QI81Qfc3E"
    #leetcode_session = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJfYXV0aF91c2VyX2lkIjoiMTI5MDk4IiwiX2F1dGhfdXNlcl9iYWNrZW5kIjoiZGphbmdvLmNvbnRyaWIuYXV0aC5iYWNrZW5kcy5Nb2RlbEJhY2tlbmQiLCJfYXV0aF91c2VyX2hhc2giOiJhZGE3MGYyNjJhYjNlMDg1ZThhYmRjZjMwM2Y3MGNkYTlkYmVjYmMyMTc2NzUyOWNmNzgxNDVhYzRlMmQzY2RiIiwiaWQiOjEyOTA5OCwiZW1haWwiOiIiLCJ1c2VybmFtZSI6IjE4MDAxMzM0NTI3IiwidXNlcl9zbHVnIjoiMTgwMDEzMzQ1MjciLCJhdmF0YXIiOiJodHRwczovL2Fzc2V0cy5sZWV0Y29kZS5jbi9hbGl5dW4tbGMtdXBsb2FkL2RlZmF1bHRfYXZhdGFyLnBuZyIsInBob25lX3ZlcmlmaWVkIjp0cnVlLCJfdGltZXN0YW1wIjoxNzEzNzc2NzI5LjYzMjc0OCwiZXhwaXJlZF90aW1lXyI6MTcxNjMxODAwMCwidmVyc2lvbl9rZXlfIjowfQ.IioGPe68YmLszFh7JDmZ5ST5oQ1C22N1H2fTHVCWshs"
    #leetcode_session = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJfYXV0aF91c2VyX2lkIjoiNjkwMzQxOCIsIl9hdXRoX3VzZXJfYmFja2VuZCI6ImRqYW5nby5jb250cmliLmF1dGguYmFja2VuZHMuTW9kZWxCYWNrZW5kIiwiX2F1dGhfdXNlcl9oYXNoIjoiMmY1YzVlMjIxNzNmODM4MmZlY2FiYTFmNmVlOTEyNDIzYTA0ZjdkOWVmZTU2N2FiODdlY2YzYjY0M2M1M2UzNiIsImlkIjo2OTAzNDE4LCJlbWFpbCI6IiIsInVzZXJuYW1lIjoiY3Jhbmt5LXNhbW1ldHdxeSIsInVzZXJfc2x1ZyI6ImNyYW5reS1zYW1tZXR3cXkiLCJhdmF0YXIiOiJodHRwczovL2Fzc2V0cy5sZWV0Y29kZS5jbi9hbGl5dW4tbGMtdXBsb2FkL2RlZmF1bHRfYXZhdGFyLnBuZyIsInBob25lX3ZlcmlmaWVkIjp0cnVlLCJkZXZpY2VfaWQiOiI3MjlmNTljNzYxYzBjYzlkNGMyMGY1ZDA3OTIzM2RhNSIsImlwIjoiMjIwLjE4MS4zLjE1MiIsIl90aW1lc3RhbXAiOjE3MTc3MjkxNDMuMDU4MTgxNSwiZXhwaXJlZF90aW1lXyI6MTcyMDI5MjQwMCwidmVyc2lvbl9rZXlfIjowfQ.4ez-ww2tweEoiFxcTdgqgD1yMXICLvuaFdGdVZVCjtg"
    #csrf_token = "FKAENUogCY3qZBonbiXMDYpc77SIG3cvxVTIO491iDEBdM78PvWdjv6pxiz5Y1vu"
    #leetcode_session = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJfYXV0aF91c2VyX2lkIjoiMTUyNTMyIiwiX2F1dGhfdXNlcl9iYWNrZW5kIjoiZGphbmdvLmNvbnRyaWIuYXV0aC5iYWNrZW5kcy5Nb2RlbEJhY2tlbmQiLCJfYXV0aF91c2VyX2hhc2giOiI0ZDZmNDdjNGE0NTg0ZTI4ZjBiMzEzMWZlZGFmNGZhNmJlOTFmNjA2YWIyZTdlYWM1ZjcwODA1MDlhYzY3ODljIiwiaWQiOjE1MjUzMiwiZW1haWwiOiIiLCJ1c2VybmFtZSI6Imphc2FwZXIiLCJ1c2VyX3NsdWciOiJqYXNhcGVyIiwiYXZhdGFyIjoiaHR0cHM6Ly9hc3NldHMubGVldGNvZGUuY24vYWxpeXVuLWxjLXVwbG9hZC9kZWZhdWx0X2F2YXRhci5wbmciLCJwaG9uZV92ZXJpZmllZCI6dHJ1ZSwiZGV2aWNlX2lkIjoiMzU1ZDA2ZWJmYmQ1MjQ1N2NlYTFkNTc2MWMyMDExNWYiLCJpcCI6IjIyMC4xODEuMy4xNTEiLCJfdGltZXN0YW1wIjoxNzE3Njc4NTM1LjIzMDg0MywiZXhwaXJlZF90aW1lXyI6MTcyMDIwNjAwMCwidmVyc2lvbl9rZXlfIjowLCJsYXRlc3RfdGltZXN0YW1wXyI6MTcxNzcyODMzMX0.eMq-u3PUTshDfFppo61yWPXope-XMQ0mIvyrrkNPBOc"
    #csrf_token = "aabUvjhMRQ6ceKqnzTPahkxQCFaKwNQxkSFoa9ieb6yB70wu2BB7Jvvo9E1qXrOw"
    #leetcode_session = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJfYXV0aF91c2VyX2lkIjoiMTAxOTYyOSIsIl9hdXRoX3VzZXJfYmFja2VuZCI6ImRqYW5nby5jb250cmliLmF1dGguYmFja2VuZHMuTW9kZWxCYWNrZW5kIiwiX2F1dGhfdXNlcl9oYXNoIjoiMTk1MmFjNmZiOTcyZGE2NDIzZTZlMGQ3OTBhM2JlNDFhZjQyODI5OWM5NzlmZjE0MmY1OTY0OTI4YTAwMzE5MiIsImlkIjoxMDE5NjI5LCJlbWFpbCI6IiIsInVzZXJuYW1lIjoibmV3ZmFjYWRlIiwidXNlcl9zbHVnIjoibmV3ZmFjYWRlIiwiYXZhdGFyIjoiaHR0cHM6Ly9hc3NldHMubGVldGNvZGUuY24vYWxpeXVuLWxjLXVwbG9hZC91c2Vycy9uZXdmYWNhZGUvYXZhdGFyXzE2MzQwNDk1MjkucG5nIiwicGhvbmVfdmVyaWZpZWQiOnRydWUsImRldmljZV9pZCI6IjcyOWY1OWM3NjFjMGNjOWQ0YzIwZjVkMDc5MjMzZGE1IiwiaXAiOiIyMjIuMTI4LjE4MC4xNDYiLCJfdGltZXN0YW1wIjoxNzE4MTgwNzAzLjUwNTI1LCJleHBpcmVkX3RpbWVfIjoxNzIwNzI0NDAwLCJ2ZXJzaW9uX2tleV8iOjIsImxhdGVzdF90aW1lc3RhbXBfIjoxNzE4NjEwMjU2fQ.GbMScvJLAWCwIYcMjZrhBDJ_RfpHSTh5bB8zJ8vGvrk"
    #csrf_token = "3fICsPHFce5GyxjlHaGbbSgCafvBJrtFIgg5vzA6CchfP0zMpZS14Oc9DDG1uJ8e"
    #leetcode_session = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJfYXV0aF91c2VyX2lkIjoiNzU5NzI0IiwiX2F1dGhfdXNlcl9iYWNrZW5kIjoiZGphbmdvLmNvbnRyaWIuYXV0aC5iYWNrZW5kcy5Nb2RlbEJhY2tlbmQiLCJfYXV0aF91c2VyX2hhc2giOiI5MGVhNGZlYTEwYTJjOWIwNTk3ZTAyOTc4Y2IwMjBmY2JhOTI3ZTA5MjViMTg5ZTYxNjI1NDMwYmI2MGM3NDY1IiwiaWQiOjc1OTcyNCwiZW1haWwiOiIiLCJ1c2VybmFtZSI6InN3dGhla2luZyIsInVzZXJfc2x1ZyI6InN3dGhla2luZyIsImF2YXRhciI6Imh0dHBzOi8vYXNzZXRzLmxlZXRjb2RlLmNuL2FsaXl1bi1sYy11cGxvYWQvZGVmYXVsdF9hdmF0YXIucG5nIiwicGhvbmVfdmVyaWZpZWQiOnRydWUsImRldmljZV9pZCI6IjcyOWY1OWM3NjFjMGNjOWQ0YzIwZjVkMDc5MjMzZGE1IiwiaXAiOiIyMjAuMTgxLjMuMTUyIiwiX3RpbWVzdGFtcCI6MTcxODc4NDA2Ni42MDM5MzgsImV4cGlyZWRfdGltZV8iOjE3MjEzMjkyMDAsInZlcnNpb25fa2V5XyI6MH0.YFKofn6L5s0AnAepXZlREVwnCHVBVpWflJZbF19c13Y"
    #csrf_token = "YSs0gEMlzwKTnErT8dKgxYPAbJwMWGoCwMvyhOhq5gJtEaMTbbIyVnsh9hjAcyUZ"
    #csrf_token = "pBV0CdqsehkZfzZj4d0dLRjDRs2kxXK3wJ42jdpMu51uRLVKa4ijn9D3V2dVB7ZV"
    #leetcode_session = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJfYXV0aF91c2VyX2lkIjoiMTAxOTYyOSIsIl9hdXRoX3VzZXJfYmFja2VuZCI6ImRqYW5nby5jb250cmliLmF1dGguYmFja2VuZHMuTW9kZWxCYWNrZW5kIiwiX2F1dGhfdXNlcl9oYXNoIjoiMTk1MmFjNmZiOTcyZGE2NDIzZTZlMGQ3OTBhM2JlNDFhZjQyODI5OWM5NzlmZjE0MmY1OTY0OTI4YTAwMzE5MiIsImlkIjoxMDE5NjI5LCJlbWFpbCI6IiIsInVzZXJuYW1lIjoibmV3ZmFjYWRlIiwidXNlcl9zbHVnIjoibmV3ZmFjYWRlIiwiYXZhdGFyIjoiaHR0cHM6Ly9hc3NldHMubGVldGNvZGUuY24vYWxpeXVuLWxjLXVwbG9hZC91c2Vycy9uZXdmYWNhZGUvYXZhdGFyXzE2MzQwNDk1MjkucG5nIiwicGhvbmVfdmVyaWZpZWQiOnRydWUsImRldmljZV9pZCI6IjI4YTliZDUzMWYxMDlkNWVkYzI0OGU5YjQ1MWEyYzhlIiwiaXAiOiIyMjAuMTgxLjMuMTUyIiwiX3RpbWVzdGFtcCI6MTcyMTAxMjU3NS4wNDIwMDQ4LCJleHBpcmVkX3RpbWVfIjoxNzIzNTc1NjAwLCJ2ZXJzaW9uX2tleV8iOjJ9.hUSTLM-vjMwet_VTl34ew2O2xvIF-M7bGIn9KQytc7Q"
    #csrf_token = "JTODyFDy8KvfGRKuUreS1kUpNjAxyx5epGBLtLCb6Rx7679Slovdyd1lTadyRgNH"
    #leetcode_session = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJfYXV0aF91c2VyX2lkIjoiMTUyNTMyIiwiX2F1dGhfdXNlcl9iYWNrZW5kIjoiZGphbmdvLmNvbnRyaWIuYXV0aC5iYWNrZW5kcy5Nb2RlbEJhY2tlbmQiLCJfYXV0aF91c2VyX2hhc2giOiI0ZDZmNDdjNGE0NTg0ZTI4ZjBiMzEzMWZlZGFmNGZhNmJlOTFmNjA2YWIyZTdlYWM1ZjcwODA1MDlhYzY3ODljIiwiaWQiOjE1MjUzMiwiZW1haWwiOiIiLCJ1c2VybmFtZSI6Imphc2FwZXIiLCJ1c2VyX3NsdWciOiJqYXNhcGVyIiwiYXZhdGFyIjoiaHR0cHM6Ly9hc3NldHMubGVldGNvZGUuY24vYWxpeXVuLWxjLXVwbG9hZC9kZWZhdWx0X2F2YXRhci5wbmciLCJwaG9uZV92ZXJpZmllZCI6dHJ1ZSwiZGV2aWNlX2lkIjoiMjhhOWJkNTMxZjEwOWQ1ZWRjMjQ4ZTliNDUxYTJjOGUiLCJpcCI6IjIyMC4xODEuMy4xNTEiLCJfdGltZXN0YW1wIjoxNzIwNzgyNTg3LjMyMTE2ODQsImV4cGlyZWRfdGltZV8iOjE3MjMzMTY0MDAsInZlcnNpb25fa2V5XyI6MH0.QuZkchk2Ucoix64g4V5L9hhE5mSaU4JmZ-9KBsP0v4o"
    #leetcode_session = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJfYXV0aF91c2VyX2lkIjoiMTUyNTMyIiwiX2F1dGhfdXNlcl9iYWNrZW5kIjoiZGphbmdvLmNvbnRyaWIuYXV0aC5iYWNrZW5kcy5Nb2RlbEJhY2tlbmQiLCJfYXV0aF91c2VyX2hhc2giOiI0ZDZmNDdjNGE0NTg0ZTI4ZjBiMzEzMWZlZGFmNGZhNmJlOTFmNjA2YWIyZTdlYWM1ZjcwODA1MDlhYzY3ODljIiwiaWQiOjE1MjUzMiwiZW1haWwiOiIiLCJ1c2VybmFtZSI6Imphc2FwZXIiLCJ1c2VyX3NsdWciOiJqYXNhcGVyIiwiYXZhdGFyIjoiaHR0cHM6Ly9hc3NldHMubGVldGNvZGUuY24vYWxpeXVuLWxjLXVwbG9hZC9kZWZhdWx0X2F2YXRhci5wbmciLCJwaG9uZV92ZXJpZmllZCI6dHJ1ZSwiZGV2aWNlX2lkIjoiZWEyOWE1NWZmYTRlZDUyZTFlMWZjMDQ5NGVkMTkwNGMiLCJpcCI6IjIyMC4xODEuMy4xNTEiLCJfdGltZXN0YW1wIjoxNzIzODA1MTk3LjAxNTQ2MTQsImV4cGlyZWRfdGltZV8iOjE3MjYzNDA0MDAsInZlcnNpb25fa2V5XyI6MH0.eb23Cu8tn0YQT63uS2Y83HuJdLiCsBTeW2MlLzAQUT0"
    #csrf_token = "1gsaG6TjlUmljo9CYA6rsfLabnPgUYGDHO86OaIEjnVp29aZ11t4iF6lC7E8QSom"
    #leetcode_session = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpcCI6IjIyMC4xODEuMy4xNTIiLCJkZXZpY2VfaWQiOiJlYTI5YTU1ZmZhNGVkNTJlMWUxZmMwNDk0ZWQxOTA0YyIsIl9hdXRoX3VzZXJfaWQiOiIxMDE5NjI5IiwiX2F1dGhfdXNlcl9iYWNrZW5kIjoiZGphbmdvLmNvbnRyaWIuYXV0aC5iYWNrZW5kcy5Nb2RlbEJhY2tlbmQiLCJfYXV0aF91c2VyX2hhc2giOiIxOTUyYWM2ZmI5NzJkYTY0MjNlNmUwZDc5MGEzYmU0MWFmNDI4Mjk5Yzk3OWZmMTQyZjU5NjQ5MjhhMDAzMTkyIiwiaWQiOjEwMTk2MjksImVtYWlsIjoiIiwidXNlcm5hbWUiOiJuZXdmYWNhZGUiLCJ1c2VyX3NsdWciOiJuZXdmYWNhZGUiLCJhdmF0YXIiOiJodHRwczovL2Fzc2V0cy5sZWV0Y29kZS5jbi9hbGl5dW4tbGMtdXBsb2FkL3VzZXJzL25ld2ZhY2FkZS9hdmF0YXJfMTYzNDA0OTUyOS5wbmciLCJwaG9uZV92ZXJpZmllZCI6dHJ1ZSwiX3RpbWVzdGFtcCI6MTcyNDMwODA5Ni45NDY1MjA4LCJleHBpcmVkX3RpbWVfIjoxNzI2ODU4ODAwLCJ2ZXJzaW9uX2tleV8iOjJ9.0gDvy-XVOrPOs25yk6Dbq8Jb_OAOBbXJ60GdPmodSns"
    #csrf_token = "AuU5r7BQ6tEL8VZlLWYjbWhM2as2wiJiYJSi2jeGHzHNja4HpnWPCB1Kt7FK2UnJ"
    #leetcode_session = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJfYXV0aF91c2VyX2lkIjoiNzU5NzI0IiwiX2F1dGhfdXNlcl9iYWNrZW5kIjoiZGphbmdvLmNvbnRyaWIuYXV0aC5iYWNrZW5kcy5Nb2RlbEJhY2tlbmQiLCJfYXV0aF91c2VyX2hhc2giOiI5MGVhNGZlYTEwYTJjOWIwNTk3ZTAyOTc4Y2IwMjBmY2JhOTI3ZTA5MjViMTg5ZTYxNjI1NDMwYmI2MGM3NDY1IiwiaWQiOjc1OTcyNCwiZW1haWwiOiIiLCJ1c2VybmFtZSI6InN3dGhla2luZyIsInVzZXJfc2x1ZyI6InN3dGhla2luZyIsImF2YXRhciI6Imh0dHBzOi8vYXNzZXRzLmxlZXRjb2RlLmNuL2FsaXl1bi1sYy11cGxvYWQvZGVmYXVsdF9hdmF0YXIucG5nIiwicGhvbmVfdmVyaWZpZWQiOnRydWUsImRldmljZV9pZCI6ImVhMjlhNTVmZmE0ZWQ1MmUxZTFmYzA0OTRlZDE5MDRjIiwiaXAiOiIyMjAuMTgxLjMuMTUyIiwiX3RpbWVzdGFtcCI6MTcyNDMxMTYwMC40ODMzNiwiZXhwaXJlZF90aW1lXyI6MTcyNjg1ODgwMCwidmVyc2lvbl9rZXlfIjowfQ.ZDcJ4SE3l7xh08DYnF-_sBXJmsiJDFhO_YeTAiHLZ54"
    #leetcode_session = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJfYXV0aF91c2VyX2lkIjoiNzcxNzYxOSIsIl9hdXRoX3VzZXJfYmFja2VuZCI6ImRqYW5nby5jb250cmliLmF1dGguYmFja2VuZHMuTW9kZWxCYWNrZW5kIiwiX2F1dGhfdXNlcl9oYXNoIjoiM2NlMjkzZGNhOGJlMGNiMjg4NjRhYTE1MTJiMDY1YTZkMTQzYmU4YjQ4Y2VjODM5NDFiM2I5NGM0OTJmMjY5YyIsImlkIjo3NzE3NjE5LCJlbWFpbCI6IiIsInVzZXJuYW1lIjoiZm9jdXNlZC1ibGFja3Z2ZWxsbXk1IiwidXNlcl9zbHVnIjoiZm9jdXNlZC1ibGFja3Z2ZWxsbXk1IiwiYXZhdGFyIjoiaHR0cHM6Ly9hc3NldHMubGVldGNvZGUuY24vYWxpeXVuLWxjLXVwbG9hZC9kZWZhdWx0X2F2YXRhci5wbmciLCJwaG9uZV92ZXJpZmllZCI6dHJ1ZSwiZGV2aWNlX2lkIjoiMTBmMzFkZDhhZTY5OTkxYTVmZjcxZWU1OTRmMjIyMTUiLCJpcCI6IjIyMC4xODEuMy4xNTIiLCJfdGltZXN0YW1wIjoxNzM5MTU2NDE2LjUzODY2MjcsImV4cGlyZWRfdGltZV8iOjE3NDE3MTk2MDAsInZlcnNpb25fa2V5XyI6MX0.D2GhUap1YxOPRp78F8IRWDYICsLnYXfgLzVK60cOvlA"
    #csrf_token = "AdkHxkmujtOE5w3tZEyRkmGOuCdjqEZQEXilKDTtssROCfNwMclxeH3EX5mkm4W7"
    leetcode_session = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJfYXV0aF91c2VyX2lkIjoiNzcxNzYxOSIsIl9hdXRoX3VzZXJfYmFja2VuZCI6ImRqYW5nby5jb250cmliLmF1dGguYmFja2VuZHMuTW9kZWxCYWNrZW5kIiwiX2F1dGhfdXNlcl9oYXNoIjoiM2NlMjkzZGNhOGJlMGNiMjg4NjRhYTE1MTJiMDY1YTZkMTQzYmU4YjQ4Y2VjODM5NDFiM2I5NGM0OTJmMjY5YyIsImlkIjo3NzE3NjE5LCJlbWFpbCI6IiIsInVzZXJuYW1lIjoiZm9jdXNlZC1ibGFja3Z2ZWxsbXk1IiwidXNlcl9zbHVnIjoiZm9jdXNlZC1ibGFja3Z2ZWxsbXk1IiwiYXZhdGFyIjoiaHR0cHM6Ly9hc3NldHMubGVldGNvZGUuY24vYWxpeXVuLWxjLXVwbG9hZC9kZWZhdWx0X2F2YXRhci5wbmciLCJwaG9uZV92ZXJpZmllZCI6dHJ1ZSwiZGV2aWNlX2lkIjoiNGNhYWMzMzQxN2RhZDRlZWYwMzNmOGE2NzZkMzViOTMiLCJpcCI6IjIyMC4xODEuMy4xNTIiLCJfdGltZXN0YW1wIjoxNzQxNzYyODIyLjUxNzc4MDMsImV4cGlyZWRfdGltZV8iOjE3NDQzMTE2MDAsInZlcnNpb25fa2V5XyI6MSwibGF0ZXN0X3RpbWVzdGFtcF8iOjE3NDE3NjI5MDl9.aajxO8B6J2dOgkTCUuUNh4gjFr5p32thWUe0HhL9yi4"
    csrf_token = "NFOAf8074ipbgcUPLuBURpHTdf3spZj7gYUxSNmxtn6Qd9TyIZE7XItfLlMVPLzX"
    api1 = init_leetcode(leetcode_session, csrf_token)
    
    graphql_request = leetcode.GraphqlQuery(
        query="""
      	{
        user {
          username
          isCurrentUserPremium
        }
        }
        """,variables=leetcode.GraphqlQueryVariables(),)

    print(api1.graphql_post(body=graphql_request))
    
    #api_instance.api_client.user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
    #api_list = [api_instance2, api_instance]
    res = get_question_info(api1, "sum-of-consecutive-subsequences")[0]
    #res = get_question_cn_content(api1, "find-subarray-with-bitwise-or-closest-to-k")
    #res = get_question_content(api1, "add-two-numbers")
    #print(res)
    #res = get_question_editor_info_by_lang(api1, "find-subarray-with-bitwise-or-closest-to-k", "cpp")
    #print(res)

    # import sys  
    # if int(sys.argv[1]) == 1:
    #     api_instance = api1
    #     print(leetcode_session)
    # elif int(sys.argv[1]) == 2:
    #     api_instance = api2
    #     print(leetcode_session2)
    #res = submit(api1, "add-two-numbers", "cpp", "1","class Solution {public:vector<int> twoSum(vector<int>& nums, int target) {return 2;}};")
    #res = get_question_editor_info_by_lang(api_instance, "average-selling-price", "python3")
    #res=check(api1,566158880)
    print(res)
    #print(res[0]["data"]) 
    # res = get_weekly_contest_question(374)
    # print(res[0]["questions"])
    # print(type(res[0]["questions"]))``


    
