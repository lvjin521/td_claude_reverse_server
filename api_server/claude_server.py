# coding=utf-8
import uuid
import json
from config.config import ClaudeConfig
from domain.claude_domain import ClaudeDomain
from fastapi import FastAPI, UploadFile, File, Request, status
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from logger_utils.log_util import log_info, log_error
from tools_utils.tools import ClaudeTools
from db_utils.claude_db_utils import ClaudeDBUtils
from db_utils.claude_redis_utils import ClaudeRedisUtils
from http_utils.httpx_utils import HttpUtils

app = FastAPI()
http_utils = HttpUtils()
claude_config = ClaudeConfig()
claude_domain = ClaudeDomain()
claude_tools = ClaudeTools()
claude_db_utils = ClaudeDBUtils()
claude_redis_utils = ClaudeRedisUtils()


# chatgpt_utils = ChatGptUtils()


class ChatItem(BaseModel):
    user_id: str = '123456'
    question_id: str = '123456'
    question_msg: str = 'hello'
    source: str = 'app'
    session_id = 'default_session_id'
    model = 'claude-2.0'
    extracted_contents: list = []


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/reload")
def read_root():
    '''
    reload数据库
    :return:
    '''
    reload_config()
    # 获取redis黑名单
    chatgpt_black_list = claude_redis_utils.get_black_list()
    # 返回结果
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            'chatgpt_black_list': chatgpt_black_list
        }
    )


def reload_config():
    # 加载账号列表
    user_list = claude_db_utils.select_user_list()
    claude_redis_utils.reload_user_list(user_list=user_list)
    log_info(f'reload user_list:{user_list}')

    # 加载黑名单
    chatgpt_black_list = claude_db_utils.select_black_key_word()
    log_info(f'reload chatgpt_black_list:{json.dumps(chatgpt_black_list, ensure_ascii=False)}')
    claude_redis_utils.reload_black_list(chatgpt_black_list)


reload_config()


def lpop_user():
    user_config_id = '1'
    for _ in range(30):
        user_config_id = claude_redis_utils.lpop_user()
        user_ttl = claude_redis_utils.get_lock_user_ttl(user_config_id=user_config_id)
        if user_ttl > 0:
            log_info(f'user_config_id:{user_config_id} 该账号还在锁定冷却状态，换号...')
            continue
    user_info = claude_db_utils.select_user_info(user_config_id=user_config_id)
    cookies = user_info[0]
    organization_uuid = user_info[1]
    user_name = user_info[2]
    nick_name = user_info[3]
    return user_config_id, cookies, organization_uuid, user_name, nick_name


@app.post("/claude/api/conversation", status_code=status.HTTP_200_OK)
async def claude_api_conversation(item: ChatItem):
    # 以后的扩展 一个用户对应多个session
    session_id = item.session_id
    model = item.model
    log_info(f'claude_api_conversation:{item.json(ensure_ascii=False)}')
    user_id = item.user_id
    source = item.source
    question_id = item.question_id
    question_msg = item.question_msg
    extracted_contents = item.extracted_contents

    # 获取redis黑名单
    chatgpt_black_list = claude_redis_utils.get_black_list()
    # 判断问题是否存在于黑名单
    is_black = claude_tools.black_contains(black_list=chatgpt_black_list, message=question_msg)
    log_info(f'user_id:{user_id} question_id:{question_id} is_black:{is_black}')
    # 如果存在黑名单
    if is_black:
        # 返回拒绝回答话术
        return StreamingResponse(
            claude_config.denied_message(),
            status_code=200,
            media_type="text/event-stream")

    # 查询会话是否存在
    session_exist = claude_db_utils.session_exist(user_id=user_id, session_id=session_id, source=source)
    log_info(f'user_id:{user_id} question_id:{question_id} session_exist:{session_exist}')
    # 如果存在历史会话
    if session_exist:
        # 存在历史会话
        conversation_uuid, organization_uuid, user_config_id = claude_db_utils.select_session_id(user_id=user_id,
                                                                                                 session_id=session_id,
                                                                                                 source=source)
        log_info(
            f'user_id:{user_id} select_session_id conversation_uuid:{conversation_uuid} organization_uuid:{organization_uuid} user_config_id:{user_config_id}')

        user_info = claude_db_utils.select_user_info(user_config_id=user_config_id)
        cookies = user_info[0]
        organization_uuid = user_info[1]
        user_name = user_info[2]
        nick_name = user_info[3]
        is_enable = user_info[4]

        log_info(
            f'user_id:{user_id} select_user_info user_name:{user_name} nick_name:{nick_name} organization_uuid:{organization_uuid} cookies:{cookies} is_enable:{is_enable}')

        if is_enable != 1:
            log_info(f'user_id:{user_id} 账号已经挂了，重新reload账号。')
            reload_config()
            # 返回拒绝回答话术
            return StreamingResponse(
                claude_config.banned_message(),
                status_code=200,
                media_type="text/event-stream")

    else:
        # 不存在历史会话 新用户
        # redis按顺序获取账号信息
        user_config_id, cookies, organization_uuid, user_name, nick_name = lpop_user()
        log_info(
            f'user_id:{user_id} user_config_id:{user_config_id} user_name:{user_name} nick_name:{nick_name} organization_uuid:{organization_uuid} cookies:{cookies}')
        # 新建一个会话
        conversation_uuid = str(uuid.uuid4())
        log_info(f'user_id:{user_id} new_conversation_uuid:{conversation_uuid}')
        data = {"uuid": conversation_uuid, "name": ""}
        url = f'{claude_config.host}/api/organizations/{organization_uuid}/chat_conversations'
        headers = {
            "authority": "claude.ai",
            "accept": "text/event-stream, text/event-stream",
            "accept-language": "en,zh-CN;q=0.9,zh;q=0.8",
            "baggage": "sentry-environment=production,sentry-release=d679276e324057e8ec573bb16fc0aebfa3937f26,sentry-public_key=58e9b9d0fc244061a1b54fe288b0e483,sentry-trace_id=8209eb6ebbf9451d82e46fcae3f80058",
            "cache-control": "no-cache",
            "content-type": "application/json",
            "origin": "https://claude.ai",
            "pragma": "no-cache",
            "referer": "https://claude.ai/chats",
            "sec-ch-ua": "\"Chromium\";v=\"116\", \"Not)A;Brand\";v=\"24\", \"Google Chrome\";v=\"116\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"macOS\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "sentry-trace": "8209eb6ebbf9451d82e46fcae3f80058-a4c42ccdedf52907-0",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
            'Cookie': cookies,
        }
        response = await http_utils.async_send_post_by_json(url=url, headers=headers, json=data)
        log_info(f'user_id:{user_id} new_conversation_uuid:{conversation_uuid} response:{response.json()}')
    attachments = []
    if len(extracted_contents) > 0:
        for item in extracted_contents:
            if len(item) > 0:
                data = {
                    'extracted_content': item,
                    'file_name': f'{claude_tools.get_random_uuid(24)}.txt',
                    'file_size': len(item),
                    'file_type': 'txt',
                }
                attachments.append(data)
    data = {
        "completion": {
            "prompt": question_msg,
            "timezone": "Asia/Shanghai",
            "model": "claude-2.1"
        },
        "organization_uuid": organization_uuid,
        "conversation_uuid": conversation_uuid,
        "text": question_msg,
        "attachments": attachments
    }

    log_info(f'user_id:{user_id} conversation_data:{json.dumps(data, ensure_ascii=False)}')

    return StreamingResponse(
        claude_domain.conversation_stream(user_config_id=user_config_id, user_id=user_id, question_id=question_id,
                                          question_msg=question_msg, model=model, session_id=session_id,
                                          user_source=source, session_exist=session_exist,
                                          cookies=cookies, data=data, is_lock_user=True,
                                          conversation_uuid=conversation_uuid, organization_uuid=organization_uuid),
        media_type="text/event-stream")


@app.get("/conversation", status_code=status.HTTP_200_OK)
async def start_conversation():
    cookies = 'sessionKey=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;'
    data = {"completion": {"prompt": "hello", "timezone": "Asia/Shanghai", "model": "claude-2.1"},
            "organization_uuid": "f867e19a-8903-49e9-b83d-dbdc31ce5a69",
            "conversation_uuid": "964b2386-61c8-4274-870a-7afdfc818456", "text": "hello", "attachments": []}

    return StreamingResponse(claude_domain.test_stream(cookies=cookies, data=data),
                             media_type="text/event-stream")
