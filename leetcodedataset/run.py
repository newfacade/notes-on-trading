#!/usr/bin/env python3
# -*- coding:utf-8 -*-
from gevent import monkey
from gevent import pywsgi
monkey.patch_all()


from flask import Flask, g
from flask import request
from leetcode.models import GraphqlResponse
import time
import sqlite3
import json
from bs4 import BeautifulSoup
from datetime import datetime
import random

import kgqa_leetcode
import kgqa_codeforce

# vip
leetcode_session = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJfYXV0aF91c2VyX2lkIjoiNzcxNzYxOSIsIl9hdXRoX3VzZXJfYmFja2VuZCI6ImRqYW5nby5jb250cmliLmF1dGguYmFja2VuZHMuTW9kZWxCYWNrZW5kIiwiX2F1dGhfdXNlcl9oYXNoIjoiM2NlMjkzZGNhOGJlMGNiMjg4NjRhYTE1MTJiMDY1YTZkMTQzYmU4YjQ4Y2VjODM5NDFiM2I5NGM0OTJmMjY5YyIsImlkIjo3NzE3NjE5LCJlbWFpbCI6IiIsInVzZXJuYW1lIjoiZm9jdXNlZC1ibGFja3Z2ZWxsbXk1IiwidXNlcl9zbHVnIjoiZm9jdXNlZC1ibGFja3Z2ZWxsbXk1IiwiYXZhdGFyIjoiaHR0cHM6Ly9hc3NldHMubGVldGNvZGUuY24vYWxpeXVuLWxjLXVwbG9hZC9kZWZhdWx0X2F2YXRhci5wbmciLCJwaG9uZV92ZXJpZmllZCI6dHJ1ZSwiZGV2aWNlX2lkIjoiNGNhYWMzMzQxN2RhZDRlZWYwMzNmOGE2NzZkMzViOTMiLCJpcCI6IjIyMC4xODEuMy4xNTIiLCJfdGltZXN0YW1wIjoxNzQxNzYyODIyLjUxNzc4MDMsImV4cGlyZWRfdGltZV8iOjE3NDQzMTE2MDAsInZlcnNpb25fa2V5XyI6MSwibGF0ZXN0X3RpbWVzdGFtcF8iOjE3NDE3NjI5MDl9.aajxO8B6J2dOgkTCUuUNh4gjFr5p32thWUe0HhL9yi4"
csrf_token = "NFOAf8074ipbgcUPLuBURpHTdf3spZj7gYUxSNmxtn6Qd9TyIZE7XItfLlMVPLzX"
#leetcode_session = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJfYXV0aF91c2VyX2lkIjoiNzcxNzYxOSIsIl9hdXRoX3VzZXJfYmFja2VuZCI6ImRqYW5nby5jb250cmliLmF1dGguYmFja2VuZHMuTW9kZWxCYWNrZW5kIiwiX2F1dGhfdXNlcl9oYXNoIjoiM2NlMjkzZGNhOGJlMGNiMjg4NjRhYTE1MTJiMDY1YTZkMTQzYmU4YjQ4Y2VjODM5NDFiM2I5NGM0OTJmMjY5YyIsImlkIjo3NzE3NjE5LCJlbWFpbCI6IiIsInVzZXJuYW1lIjoiZm9jdXNlZC1ibGFja3Z2ZWxsbXk1IiwidXNlcl9zbHVnIjoiZm9jdXNlZC1ibGFja3Z2ZWxsbXk1IiwiYXZhdGFyIjoiaHR0cHM6Ly9hc3NldHMubGVldGNvZGUuY24vYWxpeXVuLWxjLXVwbG9hZC9kZWZhdWx0X2F2YXRhci5wbmciLCJwaG9uZV92ZXJpZmllZCI6dHJ1ZSwiZGV2aWNlX2lkIjoiMTBmMzFkZDhhZTY5OTkxYTVmZjcxZWU1OTRmMjIyMTUiLCJpcCI6IjIyMC4xODEuMy4xNTIiLCJfdGltZXN0YW1wIjoxNzM5MTU2NDE2LjUzODY2MjcsImV4cGlyZWRfdGltZV8iOjE3NDE3MTk2MDAsInZlcnNpb25fa2V5XyI6MX0.D2GhUap1YxOPRp78F8IRWDYICsLnYXfgLzVK60cOvlA"
#csrf_token = "AdkHxkmujtOE5w3tZEyRkmGOuCdjqEZQEXilKDTtssROCfNwMclxeH3EX5mkm4W7"
#leetcode_session = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJfYXV0aF91c2VyX2lkIjoiNzU5NzI0IiwiX2F1dGhfdXNlcl9iYWNrZW5kIjoiZGphbmdvLmNvbnRyaWIuYXV0aC5iYWNrZW5kcy5Nb2RlbEJhY2tlbmQiLCJfYXV0aF91c2VyX2hhc2giOiI5MGVhNGZlYTEwYTJjOWIwNTk3ZTAyOTc4Y2IwMjBmY2JhOTI3ZTA5MjViMTg5ZTYxNjI1NDMwYmI2MGM3NDY1IiwiaWQiOjc1OTcyNCwiZW1haWwiOiIiLCJ1c2VybmFtZSI6InN3dGhla2luZyIsInVzZXJfc2x1ZyI6InN3dGhla2luZyIsImF2YXRhciI6Imh0dHBzOi8vYXNzZXRzLmxlZXRjb2RlLmNuL2FsaXl1bi1sYy11cGxvYWQvZGVmYXVsdF9hdmF0YXIucG5nIiwicGhvbmVfdmVyaWZpZWQiOnRydWUsImRldmljZV9pZCI6ImE4NTg5Yjk5ZjIzMjMzNjkxMDVkMmIwNjZkZTIyN2RiIiwiaXAiOiIyMjAuMTgxLjMuMTUyIiwiX3RpbWVzdGFtcCI6MTcyNjcyOTg4MC42NDA1NTcsImV4cGlyZWRfdGltZV8iOjE3MjkyNzgwMDAsInZlcnNpb25fa2V5XyI6MCwibGF0ZXN0X3RpbWVzdGFtcF8iOjE3MjcwOTE4MTd9.1mrTYU7hvTLH5UF7V8griSo2ZvWbQ6vskRXwgk4evJ0"
#csrf_token = "1wxaFO4TwkxHSsoEXFdzszbJmrVbMCpAFfySVQ7fuaDVcXUkxmZce5g9RitVQg1Y"
#leetcode_session = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJfYXV0aF91c2VyX2lkIjoiMTAxOTYyOSIsIl9hdXRoX3VzZXJfYmFja2VuZCI6ImRqYW5nby5jb250cmliLmF1dGguYmFja2VuZHMuTW9kZWxCYWNrZW5kIiwiX2F1dGhfdXNlcl9oYXNoIjoiMTk1MmFjNmZiOTcyZGE2NDIzZTZlMGQ3OTBhM2JlNDFhZjQyODI5OWM5NzlmZjE0MmY1OTY0OTI4YTAwMzE5MiIsImlkIjoxMDE5NjI5LCJlbWFpbCI6IiIsInVzZXJuYW1lIjoibmV3ZmFjYWRlIiwidXNlcl9zbHVnIjoibmV3ZmFjYWRlIiwiYXZhdGFyIjoiaHR0cHM6Ly9hc3NldHMubGVldGNvZGUuY24vYWxpeXVuLWxjLXVwbG9hZC91c2Vycy9uZXdmYWNhZGUvYXZhdGFyXzE2MzQwNDk1MjkucG5nIiwicGhvbmVfdmVyaWZpZWQiOnRydWUsImRldmljZV9pZCI6IjI4YTliZDUzMWYxMDlkNWVkYzI0OGU5YjQ1MWEyYzhlIiwiaXAiOiIyMjAuMTgxLjMuMTUyIiwiX3RpbWVzdGFtcCI6MTcyMTAxMjU3NS4wNDIwMDQ4LCJleHBpcmVkX3RpbWVfIjoxNzIzNTc1NjAwLCJ2ZXJzaW9uX2tleV8iOjJ9.hUSTLM-vjMwet_VTl34ew2O2xvIF-M7bGIn9KQytc7Q"
#csrf_token = "pBV0CdqsehkZfzZj4d0dLRjDRs2kxXK3wJ42jdpMu51uRLVKa4ijn9D3V2dVB7ZV"
#leetcode_session = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJfYXV0aF91c2VyX2lkIjoiMTI5MDk4IiwiX2F1dGhfdXNlcl9iYWNrZW5kIjoiZGphbmdvLmNvbnRyaWIuYXV0aC5iYWNrZW5kcy5Nb2RlbEJhY2tlbmQiLCJfYXV0aF91c2VyX2hhc2giOiJhZGE3MGYyNjJhYjNlMDg1ZThhYmRjZjMwM2Y3MGNkYTlkYmVjYmMyMTc2NzUyOWNmNzgxNDVhYzRlMmQzY2RiIiwiaWQiOjEyOTA5OCwiZW1haWwiOiIiLCJ1c2VybmFtZSI6IjE4MDAxMzM0NTI3IiwidXNlcl9zbHVnIjoiMTgwMDEzMzQ1MjciLCJhdmF0YXIiOiJodHRwczovL2Fzc2V0cy5sZWV0Y29kZS5jbi9hbGl5dW4tbGMtdXBsb2FkL2RlZmF1bHRfYXZhdGFyLnBuZyIsInBob25lX3ZlcmlmaWVkIjp0cnVlLCJfdGltZXN0YW1wIjoxNzEzNzc2NzI5LjYzMjc0OCwiZXhwaXJlZF90aW1lXyI6MTcxNjMxODAwMCwidmVyc2lvbl9rZXlfIjowfQ.IioGPe68YmLszFh7JDmZ5ST5oQ1C22N1H2fTHVCWshs"
#leetcode_session = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJfYXV0aF91c2VyX2lkIjoiNjkwMzQxOCIsIl9hdXRoX3VzZXJfYmFja2VuZCI6ImRqYW5nby5jb250cmliLmF1dGguYmFja2VuZHMuTW9kZWxCYWNrZW5kIiwiX2F1dGhfdXNlcl9oYXNoIjoiMmY1YzVlMjIxNzNmODM4MmZlY2FiYTFmNmVlOTEyNDIzYTA0ZjdkOWVmZTU2N2FiODdlY2YzYjY0M2M1M2UzNiIsImlkIjo2OTAzNDE4LCJlbWFpbCI6IiIsInVzZXJuYW1lIjoiY3Jhbmt5LXNhbW1ldHdxeSIsInVzZXJfc2x1ZyI6ImNyYW5reS1zYW1tZXR3cXkiLCJhdmF0YXIiOiJodHRwczovL2Fzc2V0cy5sZWV0Y29kZS5jbi9hbGl5dW4tbGMtdXBsb2FkL2RlZmF1bHRfYXZhdGFyLnBuZyIsInBob25lX3ZlcmlmaWVkIjp0cnVlLCJkZXZpY2VfaWQiOiI3MjlmNTljNzYxYzBjYzlkNGMyMGY1ZDA3OTIzM2RhNSIsImlwIjoiMjIwLjE4MS4zLjE1MiIsIl90aW1lc3RhbXAiOjE3MTc3MjkxNDMuMDU4MTgxNSwiZXhwaXJlZF90aW1lXyI6MTcyMDI5MjQwMCwidmVyc2lvbl9rZXlfIjowfQ.4ez-ww2tweEoiFxcTdgqgD1yMXICLvuaFdGdVZVCjtg"
#csrf_token = "FKAENUogCY3qZBonbiXMDYpc77SIG3cvxVTIO491iDEBdM78PvWdjv6pxiz5Y1vu"
#leetcode_session = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJfYXV0aF91c2VyX2lkIjoiMTUyNTMyIiwiX2F1dGhfdXNlcl9iYWNrZW5kIjoiZGphbmdvLmNvbnRyaWIuYXV0aC5iYWNrZW5kcy5Nb2RlbEJhY2tlbmQiLCJfYXV0aF91c2VyX2hhc2giOiI0ZDZmNDdjNGE0NTg0ZTI4ZjBiMzEzMWZlZGFmNGZhNmJlOTFmNjA2YWIyZTdlYWM1ZjcwODA1MDlhYzY3ODljIiwiaWQiOjE1MjUzMiwiZW1haWwiOiIiLCJ1c2VybmFtZSI6Imphc2FwZXIiLCJ1c2VyX3NsdWciOiJqYXNhcGVyIiwiYXZhdGFyIjoiaHR0cHM6Ly9hc3NldHMubGVldGNvZGUuY24vYWxpeXVuLWxjLXVwbG9hZC9kZWZhdWx0X2F2YXRhci5wbmciLCJwaG9uZV92ZXJpZmllZCI6dHJ1ZSwiZGV2aWNlX2lkIjoiMjhhOWJkNTMxZjEwOWQ1ZWRjMjQ4ZTliNDUxYTJjOGUiLCJpcCI6IjIyMC4xODEuMy4xNTEiLCJfdGltZXN0YW1wIjoxNzIwNzgyNTg3LjMyMTE2ODQsImV4cGlyZWRfdGltZV8iOjE3MjMzMTY0MDAsInZlcnNpb25fa2V5XyI6MH0.QuZkchk2Ucoix64g4V5L9hhE5mSaU4JmZ-9KBsP0v4o"
#csrf_token = "JTODyFDy8KvfGRKuUreS1kUpNjAxyx5epGBLtLCb6Rx7679Slovdyd1lTadyRgNH"
#leetcode_session = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJfYXV0aF91c2VyX2lkIjoiMTAxOTYyOSIsIl9hdXRoX3VzZXJfYmFja2VuZCI6ImRqYW5nby5jb250cmliLmF1dGguYmFja2VuZHMuTW9kZWxCYWNrZW5kIiwiX2F1dGhfdXNlcl9oYXNoIjoiMTk1MmFjNmZiOTcyZGE2NDIzZTZlMGQ3OTBhM2JlNDFhZjQyODI5OWM5NzlmZjE0MmY1OTY0OTI4YTAwMzE5MiIsImlkIjoxMDE5NjI5LCJlbWFpbCI6IiIsInVzZXJuYW1lIjoibmV3ZmFjYWRlIiwidXNlcl9zbHVnIjoibmV3ZmFjYWRlIiwiYXZhdGFyIjoiaHR0cHM6Ly9hc3NldHMubGVldGNvZGUuY24vYWxpeXVuLWxjLXVwbG9hZC91c2Vycy9uZXdmYWNhZGUvYXZhdGFyXzE2MzQwNDk1MjkucG5nIiwicGhvbmVfdmVyaWZpZWQiOnRydWUsImRldmljZV9pZCI6IjcyOWY1OWM3NjFjMGNjOWQ0YzIwZjVkMDc5MjMzZGE1IiwiaXAiOiIyMjIuMTI4LjE4MC4xNDYiLCJfdGltZXN0YW1wIjoxNzE4MTgwNzAzLjUwNTI1LCJleHBpcmVkX3RpbWVfIjoxNzIwNzI0NDAwLCJ2ZXJzaW9uX2tleV8iOjIsImxhdGVzdF90aW1lc3RhbXBfIjoxNzE4NjEwMjU2fQ.GbMScvJLAWCwIYcMjZrhBDJ_RfpHSTh5bB8zJ8vGvrk"
#csrf_token = "3fICsPHFce5GyxjlHaGbbSgCafvBJrtFIgg5vzA6CchfP0zMpZS14Oc9DDG1uJ8e"
# wzx
#leetcode_session = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJuZXh0X2FmdGVyX29hdXRoIjoiLyIsIl9hdXRoX3VzZXJfaWQiOiIxMjkwOTgiLCJfYXV0aF91c2VyX2JhY2tlbmQiOiJkamFuZ28uY29udHJpYi5hdXRoLmJhY2tlbmRzLk1vZGVsQmFja2VuZCIsIl9hdXRoX3VzZXJfaGFzaCI6ImFkYTcwZjI2MmFiM2UwODVlOGFiZGNmMzAzZjcwY2RhOWRiZWNiYzIxNzY3NTI5Y2Y3ODE0NWFjNGUyZDNjZGIiLCJpZCI6MTI5MDk4LCJlbWFpbCI6IiIsInVzZXJuYW1lIjoiMTgwMDEzMzQ1MjciLCJ1c2VyX3NsdWciOiIxODAwMTMzNDUyNyIsImF2YXRhciI6Imh0dHBzOi8vYXNzZXRzLmxlZXRjb2RlLmNuL2FsaXl1bi1sYy11cGxvYWQvZGVmYXVsdF9hdmF0YXIucG5nIiwicGhvbmVfdmVyaWZpZWQiOnRydWUsIl90aW1lc3RhbXAiOjE3MDI0NTcyMDIuMjMyNzMzLCJleHBpcmVkX3RpbWVfIjoxNzA0OTk5NjAwLCJ2ZXJzaW9uX2tleV8iOjB9.ZpfCsNwGAdVgzuoUQxeguzOMZdAH40nAWr5_hSKEZvs"

api_instance = kgqa_leetcode.init_leetcode(leetcode_session, csrf_token)


app = Flask(__name__)

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect('questions.db')
        g.db.row_factory = sqlite3.Row  # 以字典形式返回查询结果
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


@app.before_request
def before_request():
    g.db = get_db()


@app.teardown_request
def teardown_request(exception):
    close_db()


def html_to_text(html_string):
    soup = BeautifulSoup(html_string, 'html.parser')
    #text = soup.get_text(separator='\n', strip=False)
    text = soup.get_text(strip=False)
    return text


@app.route("/v1/leetcode/get_question_info", methods=['POST'])
def leet_code_get_question_info():
    """获取题目信息以及指定语言的函数定义信息"""
    request_data = request.get_json()
    base_response = {"code": 0, "message": "Success", "data": {}}
    if not request_data:
        return {"code": 1, "message": "request_data is empty", "data": None}
    question = request_data.get("question")
    lang = request_data.get("lang")
    cn = request_data.get("cn", True)

    if cn:
        res, error_info = kgqa_leetcode.get_question_cn_content(api_instance, question)
    else:
        res, error_info = kgqa_leetcode.get_question_content(api_instance, question)
    if error_info:
        return {"code": 1, "message": error_info, "data": None}
    if isinstance(res, GraphqlResponse):
        if cn:
            question_content = res.data.question.translated_content
        else:
            question_content = res.data.question.content

        if question_content is None:
            print(res)
            return {"code": 1, "message": "translate content is None", "data": None}
        base_response["data"]["difficulty"] = res.data.question.difficulty
        base_response["data"]["question_title"] = html_to_text(question_content)
    else:
        return {"code": 1, "message": error_info, "data": None}
    res, error_info = kgqa_leetcode.get_question_editor_info_by_lang(api_instance, question, lang)
    if error_info:
        if isinstance(res, list):
            return {"code": 1, "message": f"error: {error_info}, only supported: {res}", "data": None}
        else:
            return {"code": 1, "message": error_info, "data": None}
    base_response["data"]["lang_code"] = res
    return base_response


@app.route("/v1/leetcode/submit", methods=['POST'])
def leet_code_submit():
    """提交"""
    request_data = request.get_json()
    base_response = {"code": 0, "message": "Success", "data": {}}
    if not request_data:
        return {"code": 1, "message": "request_data is empty", "data": None}
    question = request_data.get("question")
    lang = request_data.get("lang")
    code = request_data.get("code")

    cursor = g.db.cursor()
    
    # 查询id

    cursor.execute('''
        SELECT question_id FROM leetcode
        WHERE title = ?
    ''', (question,))

    # 获取查询结果
    result = cursor.fetchall()
    
    # 打印查询结果
    try:
        question_id =  result[0][0]
    except Exception as e:
        res, error_info = kgqa_leetcode.get_question_info(api_instance, question)
        if error_info:
            return None, error_info
        cursor.execute("INSERT INTO leetcode (question_id, title, difficulty, topic_tag, describe) VALUES (?, ?, ?, ?, ?)", (res["id"], res["title"], res["difficulty"], res["topic_tag"], res["describe"]))
        g.db.commit()
        cursor.execute('''
            SELECT question_id FROM leetcode
            WHERE title = ?
        ''', (question,))

        # 获取查询结果
        result = cursor.fetchall()
        question_id =  result[0][0]
    
    res, error_info = kgqa_leetcode.submit(api_instance, question, lang, question_id, typed_code=code)

    if error_info:
        # cursor.close()
        return {"code": 1, "message": error_info, "data": None}

    # 获取id
    job_id = res.submission_id
    while True:
        res, error_info = kgqa_leetcode.check(api_instance, job_id)
        if error_info:
            # cursor.close()
            return {"code": 1, "message": error_info, "data": None}
        if res["state"] not in  ["STARTED", "PENDING"]:
            break
        time.sleep(5)
    
    base_response["data"] = res
    try:
        cursor.execute('''
            INSERT INTO leetcode_case_perf (
                question, submit_time, lang, memory, memory_percentile,
                pretty_lang, question_id, run_success, runtime_percentile,
                state, status_code, status_memory, status_msg, status_runtime,
                submission_id, task_finish_time, task_name, total_correct, total_testcases
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            question, datetime.now(), res["lang"], res["memory"],
            res["memory_percentile"], res["pretty_lang"], res["question_id"],
            res["run_success"], res["runtime_percentile"], res["state"],
            res["status_code"], res["status_memory"], res["status_msg"],
            res["status_runtime"], res["submission_id"], res["task_finish_time"],
            res["task_name"], res["total_correct"], res["total_testcases"]
        ))
    except Exception as e:
        print(str(e))
    # cursor.close()
    return base_response


@app.route("/v1/leetcode/submit_batch", methods=['POST'])
def leet_code_submit_batch():
    """提交"""
    request_data = request.get_json()
    base_response = {"code": 0, "message": "Success", "data": {}}
    if not request_data:
        return {"code": 1, "message": "request_data is empty", "data": None}
    question_file = request_data.get("question_file")
    queue_name = request_data.get("queue", "rd_facade")
    cursor = g.db.cursor()

    if queue_name == "rd_facade":
        table_name = "leetcode_job"
    elif "public" in queue_name.lower():
        table_name = "leetcode_job_public"

    # 查询id
    
    # 提交到例行任务队列
    cursor.execute(f'''
        INSERT INTO {table_name} (question_file, status)
        VALUES (?, ?)
    ''', (question_file, "doing"))
    # 获取查询结果
    new_user_id = cursor.lastrowid
    g.db.commit()

    base_response["data"]["job_id"] = new_user_id if "public" not in queue_name.lower() else f"public_{new_user_id}"
    
    return base_response


@app.route("/v1/leetcode/retry_job", methods=['POST'])
def retry_leetcode_job():
    """重试任务"""
    request_data = request.get_json()
    base_response = {"code": 0, "message": "Success", "data": {}}
    if not request_data:
        return {"code": 1, "message": "request_data is empty", "data": None}
    job_id = request_data.get("job_id")
    queue_name = request_data.get("queue", "rd_facade")

    cursor = g.db.cursor()
    if queue_name == "rd_facade":
        table_name = "leetcode_job"
    elif "public" in queue_name.lower():
        table_name = "leetcode_job_public"
        job_id = int(job_id.replace("public_", ""))
    
        
    cursor.execute(f'''
        SELECT status FROM {table_name}
        WHERE id = ?
    ''', (job_id, ))

    # 获取查询结果
    result = cursor.fetchall()
    try:
        status = result[0][0]
    except IndexError as _e_index:
        return {"code": 1, "message": f"job[{job_id}] not exist", "data": None}
    except Exception as e:
        return {"code": 1, "message": str(e), "data": None}
    if status in ["doing", "fail", "running", "success"]:
        cursor.execute(f"UPDATE {table_name} SET status = 'doing', create_time = ?  WHERE id = ?", (datetime.now(), job_id))
        g.db.commit()
    return base_response


@app.route("/v1/leetcode/update_account", methods=['POST'])
def update_leetcode_account_session():
    """更新leetcode 账户session"""
    request_data = request.get_json()
    base_response = {"code": 0, "message": "Success", "data": {}}
    if not request_data:
        return {"code": 1, "message": "request_data is empty", "data": None}
    user_name = request_data.get("user_name")
    _session = request_data.get("session")
    _token = request_data.get("token")

    cursor = g.db.cursor()
    try:
        cursor.execute("UPDATE leetcode_account SET session = ?, token = ? WHERE user_name = ?", (_session, _token, user_name))
        g.db.commit()
    except Exception as e:
        return {"code": 1, "message": str(e), "data": None}
    return base_response


@app.route("/v1/leetcode/get_batch_job_status", methods=['POST'])
def get_leetcode_batch_job_status():
    """通过类型获取题目"""
    request_data = request.get_json()
    base_response = {"code": 0, "message": "Success", "data": {}}
    if not request_data:
        return {"code": 1, "message": "request_data is empty", "data": None}
    job_id = request_data.get("job_id")

    if isinstance(job_id, int):
        table_name = "leetcode_job"
    elif isinstance(job_id, str) and "public" in job_id.lower():
        table_name = "leetcode_job_public"
        job_id = int(job_id.replace("public_", ""))
    cursor = g.db.cursor()
    cursor.execute(f'''
        SELECT id, result_file, status, question_file, process, accepted_file, create_time, finish_time FROM {table_name}
        WHERE id = ?
    ''', (job_id, ))

    # 获取查询结果
    result = cursor.fetchall()
    
    # cursor.close()
    # 打印查询结果
    for row in result:
        base_response["data"]["id"] = row[0]
        base_response["data"]["result_file"] = row[1]
        base_response["data"]["status"] = row[2]
        base_response["data"]["question_file"] = row[3]
        base_response["data"]["process"] = row[4]
        base_response["data"]["accepted_file"] = row[5]
        base_response["data"]["create_time"] = row[6]
        base_response["data"]["finish_time"] = row[7]
    return base_response


@app.route("/v1/leetcode/delete_job", methods=['POST'])
def get_leetcode_delete_job():
    """删除任务"""
    request_data = request.get_json()
    base_response = {"code": 0, "message": "Success", "data": {}}
    if not request_data:
        return {"code": 1, "message": "request_data is empty", "data": None}
    job_id = request_data.get("job_id")

    if isinstance(job_id, int):
        table_name = "leetcode_job"
    elif isinstance(job_id, str) and "public" in job_id.lower():
        table_name = "leetcode_job_public"
        job_id = int(job_id.replace("public_", ""))

    cursor = g.db.cursor()
    cursor.execute(f'''
        SELECT status FROM {table_name}
        WHERE id = ?
    ''', (job_id, ))

    # 获取查询结果
    result = cursor.fetchall()
    # cursor.close()
    # 打印查询结果
    for row in result:
        if row == []:
             return {"code": 0, "message": f"job[{job_id}] not exist", "data": None}
        _status = row[0]
        if _status in ["doing", "fail", "success"]:
            cursor.execute(f'''
                DELETE FROM {table_name} WHERE id = ?
            ''', (job_id, ))
            g.db.commit()
            base_response
        else:
            return {"code": 1, "message": f"job[{job_id}] is running", "data": None}

    return base_response


@app.route("/v1/leetcode/get_all_job", methods=['POST', "GET"])
def get_leetcode_get_all_job():
    """通过所有任务"""
    base_response = {"code": 0, "message": "Success", "data": []}

    #request_data = request.get_json()
    queue_name = "rd_facade" # request_data.get("queue", "rd_facade")

    cursor = g.db.cursor()
    if queue_name == "rd_facade":
        table_name = "leetcode_job"
    elif "public" in queue_name.lower():
        table_name = "leetcode_job_public"

    cursor = g.db.cursor()
    cursor.execute(f'''
        SELECT id, result_file, status, question_file, process, accepted_file, create_time, finish_time FROM {table_name}
    ''', ())

    # 获取查询结果
    result = cursor.fetchall()
    # cursor.close()
    # 打印查询结果
    for row in result:
        _body = {}
        _body["id"] = row[0]
        _body["result_file"] = row[1]
        _body["status"] = row[2]
        _body["question_file"] = row[3]
        _body["process"] = row[4]
        _body["accepted_file"] = row[5]
        _body["create_time"] = row[6]
        _body["finish_time"] = row[7]
        base_response["data"].append(_body)
    return base_response


@app.route("/v1/leetcode/get_week_contest_question_title", methods=['POST'])
def leet_code_get_week_contest_question_title():
    """获取周赛题目"""
    request_data = request.get_json()
    base_response = {"code": 0, "message": "Success", "data": {"question": []}}
    if not request_data:
        return {"code": 1, "message": "request_data is empty", "data": None}
    week_num = request_data.get("week")

    res, error_info = kgqa_leetcode.get_weekly_contest_question(week_num)
    if error_info:
        return {"code": 1, "message": error_info, "data": None}

    for _q in res["questions"]:
        q_body = {}
        q_body["question_id"] = _q.get("question_id")
        q_body["title_cn"] = _q.get("title")
        q_body["title"] = _q.get("title_slug")
        q_body["credit"] = _q.get("credit")
        base_response["data"]["question"].append(q_body)
    return base_response


@app.route("/v1/leetcode/get_question_title_by_id", methods=['POST'])
def leet_code_get_question_title_by_id():
    """通过题号获取题目"""
    request_data = request.get_json()
    base_response = {"code": 0, "message": "Success", "data": {}}
    if not request_data:
        return {"code": 1, "message": "request_data is empty", "data": None}
    question_id = request_data.get("id")
    
    cursor = g.db.cursor()
    cursor.execute('''
        SELECT title FROM leetcode
        WHERE question_id = ?
    ''', (question_id,))

    # 获取查询结果
    result = cursor.fetchall()
    # cursor.close()
    # 打印查询结果
    _result = []
    for row in result:
        _result.append(row[0])

    base_response["data"]["question"] = _result
    return base_response


@app.route("/v1/leetcode/get_question_title_by_difficulty", methods=['POST'])
def get_question_title_by_difficulty():
    """通过难易度获取题目"""
    request_data = request.get_json()
    base_response = {"code": 0, "message": "Success", "data": {}}
    if not request_data:
        return {"code": 1, "message": "request_data is empty", "data": None}
    difficulty = request_data.get("difficulty")
    max_num = request_data.get("max_num")

    cursor = g.db.cursor()
    cursor.execute('''
        SELECT title, question_id FROM leetcode
        WHERE difficulty = ?
    ''', (difficulty,))

    # 获取查询结果
    result = cursor.fetchall()
    # cursor.close()
    # 打印查询结果
    _result = []
    for row in result:
        if row[1] < 1000000:
            _result.append({"question": row[0], "question_id": row[1]})

    if len(_result) > max_num:
        base_response["data"]["question"] = random.sample(_result, max_num)
    else:
        base_response["data"]["question"] = _result
    return base_response


@app.route("/v1/leetcode/get_question_title_by_topic", methods=['POST'])
def get_question_title_by_topic():
    """通过类型获取题目"""
    request_data = request.get_json()
    base_response = {"code": 0, "message": "Success", "data": {}}
    if not request_data:
        return {"code": 1, "message": "request_data is empty", "data": None}
    topic = request_data.get("topic")
    max_num = request_data.get("max_num")

    cursor = g.db.cursor()
    cursor.execute('''
        SELECT title, question_id FROM leetcode
        WHERE topic_tag LIKE ?
    ''', (f"%{topic}%",))

    # 获取查询结果
    result = cursor.fetchall()
    # cursor.close()
    # 打印查询结果
    _result = []
    for row in result:
        if row[1] < 1000000:
            _result.append({"question": row[0], "question_id": row[1]})


    base_response["data"]["question"] = random.sample(_result, max_num)
    return base_response


@app.route("/v1/leetcode/get_sim_question", methods=['POST'])
def leet_code_get_sim_question():
    """获取相似问题"""
    request_data = request.get_json()
    base_response = {"code": 0, "message": "Success", "data": {}}
    if not request_data:
        return {"code": 1, "message": "request data is empty", "data": None}
    question = request_data.get("question")


    res, error_info = kgqa_leetcode.get_similar_question(api_instance, question)
    
    if error_info:
        return {"code": 1, "message": error_info, "data": None}
    if isinstance(res, list):
        for _q in res:
            q_body = {}
            q_body["title_cn"] = _q.get("translatedTitle")
            q_body["title"] = _q.get("titleSlug")
            q_body["difficulty"] = _q.get('difficulty')
            base_response["data"]["question"].append(q_body)
        
    else:
        return {"code": 1, "message": error_info, "data": None}

    return base_response



###############################
###############################
########## codeforce ##########
###############################
###############################

@app.route("/v1/codeforce/get_question_info", methods=['POST'])
def codeforce_get_question_info():
    """codeforce获取题目信息"""
    request_data = request.get_json()
    base_response = {"code": 0, "message": "Success", "data": {}}
    if not request_data:
        return {"code": 1, "message": "request_data is empty", "data": None}
    question = request_data.get("question")
    # lang = request_data.get("lang", None)
    # cn = request_data.get("cn", False)

    res, error_info = kgqa_codeforce.get_question_content_by_question_id(question_id=question)
    if error_info:
        return {"code": 1, "message": error_info, "data": None}
    base_response["data"]["question_title"] = res["content"]
    base_response["data"]["question_header"] = res["header"]
    return base_response


@app.route("/v1/codeforce/submit_batch", methods=['POST'])
def codeforce_submit_batch():
    """提交"""
    request_data = request.get_json()
    base_response = {"code": 0, "message": "Success", "data": {}}
    if not request_data:
        return {"code": 1, "message": "request_data is empty", "data": None}
    question_file = request_data.get("question_file")


    cursor = g.db.cursor()
    # 查询id

    cursor.execute('''
        INSERT INTO codeforce_job (question_file, status, create_time)
        VALUES (?, ?, ?)           
    ''', (question_file, "doing", datetime.now()))
    # 获取查询结果
    new_user_id = cursor.lastrowid
    g.db.commit()

    base_response["data"]["job_id"] = new_user_id
    
    return base_response


@app.route("/v1/codeforce/get_all_job", methods=['POST', "GET"])
def get_codeforce_get_all_job():
    """通过所有任务"""
    base_response = {"code": 0, "message": "Success", "data": []}

    cursor = g.db.cursor()
    cursor.execute('''
        SELECT id, result_file, status, question_file, process, accepted_file, create_time, finish_time FROM codeforce_job
    ''', ())

    # 获取查询结果
    result = cursor.fetchall()
    # 打印查询结果
    for row in result:
        _body = {}
        _body["id"] = row[0]
        _body["result_file"] = row[1]
        _body["status"] = row[2]
        _body["question_file"] = row[3]
        _body["process"] = row[4]
        _body["accepted_file"] = row[5]
        _body["create_time"] = row[6]
        _body["finish_time"] = row[7]
        base_response["data"].append(_body)
    return base_response


@app.route("/v1/codeforce/retry_job", methods=['POST'])
def retry_codeforce_job():
    """重试任务"""
    request_data = request.get_json()
    base_response = {"code": 0, "message": "Success", "data": {}}
    if not request_data:
        return {"code": 1, "message": "request_data is empty", "data": None}
    job_id = request_data.get("job_id")

    if not isinstance(job_id, int):
        return {"code": 1, "message": "job_id must int", "data": None}
    cursor = g.db.cursor()

    cursor.execute('''
        SELECT id, result_file, status, question_file FROM codeforce_job
        WHERE id = ?
    ''', (job_id, ))

    # 获取查询结果
    result = cursor.fetchall()
    try:
        status = result[0][2]
    except IndexError as _e_index:
        return {"code": 1, "message": f"job[{job_id}] not exist", "data": None}
    except Exception as e:
        return {"code": 1, "message": str(e), "data": None}
    if status in ["doing", "fail", "running", "success"]:
        cursor.execute("UPDATE codeforce_job SET status = 'doing'  WHERE id = ?", (job_id, ))
        g.db.commit()
        
    return base_response


@app.route("/v1/codeforce/delete_job", methods=['POST'])
def get_codeforce_delete_job():
    """删除任务"""
    request_data = request.get_json()
    base_response = {"code": 0, "message": "Success", "data": {}}
    if not request_data:
        return {"code": 1, "message": "request_data is empty", "data": None}
    job_id = request_data.get("job_id")

    if not isinstance(job_id, int):
        return {"code": 1, "message": "job_id must int", "data": None}
    
    cursor = g.db.cursor()
    cursor.execute('''
        SELECT status FROM codeforce_job
        WHERE id = ?
    ''', (job_id, ))

    # 获取查询结果
    result = cursor.fetchall()
    # 打印查询结果
    for row in result:
        if row == []:
             return {"code": 0, "message": f"job[{job_id}] not exist", "data": None}
        _status = row[0]
        if _status in ["doing", "fail", "success"]:
            cursor.execute('''
                DELETE FROM codeforce_job WHERE id = ?
            ''', (job_id, ))
            g.db.commit()
            base_response
        else:
            return {"code": 1, "message": f"job[{job_id}] is running", "data": None}

    return base_response


@app.route("/v1/codeforce/get_question_info_batch", methods=['POST'])
def get_codeforce_get_question_info_batch():
    """批量获取问题描述"""
    request_data = request.get_json()
    base_response = {"code": 0, "message": "Success", "data": {}}
    if not request_data:
        return {"code": 1, "message": "request_data is empty", "data": None}
    start_contest = int(request_data.get("start_contest"))
    end_contest = int(request_data.get("end_contest"))
    
    # 保证start < end
    if end_contest < start_contest:
        start_contest, end_contest = end_contest, start_contest
    abc = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T"]

    fname = "codeforce_question_{}to{}_{}.txt".format(start_contest, end_contest, time.strftime("%Y-%m-%d_%H_%M", time.localtime()))
    with open(fname, "w") as f:
        for _contest in range(start_contest, end_contest + 1):
            for _abc in abc:
                _contest_id = f"{_contest}{_abc}"
                _result = {}
                res, error_info = kgqa_codeforce.get_question_content_by_question_id(_contest_id)

                if error_info:
                    break
                _result["question_id"] = _contest_id
                _result["question_title"] = res["content"]
                _result["question_header"] = res["header"]
                json.dump(_result, f)
                f.write("\n")
    base_response["data"]["result"] = f"http://10.214.54.87:8112/{fname}"
    return base_response


@app.route("/v1/codeforce/get_batch_job_status", methods=['POST'])
def get_codeforce_batch_job_status():
    """通过类型获取题目"""
    request_data = request.get_json()
    base_response = {"code": 0, "message": "Success", "data": {}}
    if not request_data:
        return {"code": 1, "message": "request_data is empty", "data": None}
    job_id = request_data.get("job_id")

    cursor = g.db.cursor()
    cursor.execute('''
        SELECT id, result_file, status, question_file, process, accepted_file, create_time, finish_time FROM codeforce_job
        WHERE id = ?
    ''', (job_id, ))

    # 获取查询结果
    result = cursor.fetchall()
    
    # cursor.close()
    # 打印查询结果
    for row in result:
        base_response["data"]["id"] = row[0]
        base_response["data"]["result_file"] = row[1]
        base_response["data"]["status"] = row[2]
        base_response["data"]["question_file"] = row[3]
        base_response["data"]["process"] = row[4]
        base_response["data"]["accepted_file"] = row[5]
        base_response["data"]["create_time"] = row[6]
        base_response["data"]["finish_time"] = row[7]
    return base_response

if __name__ == '__main__':
    #app.run(debug=True, port=8111, host="0.0.0.0")
    server = pywsgi.WSGIServer(('0.0.0.0', 8111), app)
    server.serve_forever()
