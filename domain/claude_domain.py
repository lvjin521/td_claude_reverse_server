# coding=utf-8
import json
import time
import asyncio
import httpx
# from logger_utils.loguru_utils import logger
from logger_utils.log_util import log_info, log_error
from config.config import ClaudeConfig
from db_utils.claude_db_utils import ClaudeDBUtils
from db_utils.claude_redis_utils import ClaudeRedisUtils


class ClaudeDomain:
    def __init__(self):
        self.claude_config = ClaudeConfig()
        self.claude_db_utils = ClaudeDBUtils()
        self.claude_redis_utils = ClaudeRedisUtils()

    def get_header(self, cookies: str):
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
        return headers

    def is_json(self, myjson: str):
        try:
            json_object = json.loads(myjson)
        except ValueError as e:
            return False
        return True

    async def rob_lock_user(self, user_config_id: str, user_id: str):
        '''
        抢账号同步锁
        :param user_config_id:
        :param user_id:
        :return:
        '''
        for _ in range(600):
            # 账号同步锁
            set_lock_result = self.claude_redis_utils.set_lock_user(user_config_id=user_config_id)
            log_info(f"user_id:{user_id} user_config_id:{user_config_id} rob_lock_user:{set_lock_result}")
            if set_lock_result:
                break
            else:
                # 睡眠1秒钟
                await asyncio.sleep(1)

    async def handle_cancellation(self, user_id: str, user_config_id: str):
        # 这里处理客户端断开连接的情况
        log_error("Client disconnected, stopping data stream. sleep 30s.")
        await asyncio.sleep(30)
        self.claude_redis_utils.release_lock_user(user_config_id=user_config_id)
        log_info(
            f"user_id:{user_id} user_config_id:{user_config_id} rob_lock_user:release CancelledError")

    async def handle_cancellation2(self):
        await asyncio.sleep(60)
        print('success')

    async def conversation_stream(self, user_config_id: str, user_id: str, question_id: str, question_msg: str,
                                  model: str, session_id: str, user_source: str, session_exist: bool, cookies: str,
                                  data: dict, is_lock_user: bool, conversation_uuid: str, organization_uuid: str):
        start_time_str = time.time()
        if is_lock_user:
            # 抢账号同步锁
            await self.rob_lock_user(user_config_id=user_config_id, user_id=user_id)

        try:
            # 开始访问
            async with httpx.AsyncClient() as client:
                async with client.stream("POST", url=self.claude_config.append_message_url, json=data,
                                         headers=self.get_header(cookies=cookies),
                                         timeout=300) as stream_response:

                    stream_response_status_code = stream_response.status_code
                    log_info(f"user_id:{user_id} stream_response_status_code:{stream_response_status_code}")

                    buffer = b""  # 缓冲区
                    separator = b"\n"  # 数据块分隔符（示例中使用换行符）
                    total_message_content = ""  # 存储全部消息的内容
                    # latest_message = ""  # 存储最后一条消息的内容
                    first_message_flag = True  # 打印第一条消息标记位

                    # 读取流响应结果
                    async for chunk in stream_response.aiter_bytes():

                        # 如果返回了错误的状态码
                        if stream_response_status_code != 200:
                            # 释放同步锁
                            self.claude_redis_utils.release_lock_user(user_config_id=user_config_id)
                            log_info(
                                f"user_id:{user_id} user_config_id:{user_config_id} rob_lock_user:release stream_response_status_code:{stream_response_status_code}")
                            message = '大家太热情了，被挤爆了，请稍后再试试呢 ~'
                            if stream_response_status_code == 429:
                                message = 'too_many_completions'
                                # 如果session存在
                                if session_exist:
                                    # 删除session
                                    self.claude_db_utils.delete_session(user_id=user_id,
                                                                        conversation_uuid=conversation_uuid)
                                # 账号锁定6小时
                                self.claude_redis_utils.set_lock_user_by_rate_limit_error(user_config_id=user_config_id)
                            # 如果存在失败消息
                            if chunk:
                                stream_response_result = chunk.decode("utf-8")
                                log_error(
                                    f"user_id:{user_id} stream_response_error_result:{stream_response_result}")

                            # 返回失败消息模板
                            error_message_data = {
                                "code": 200,
                                "message": message
                            }
                            yield bytes(json.dumps(error_message_data, ensure_ascii=False) + '\n', encoding="utf-8")
                            # 流式返回结束
                            yield bytes('[DONE]\n', encoding="utf-8")
                            # 问答耗时
                            end_time_str = time.time() - start_time_str
                            log_info(
                                f"user_id:{user_id} user_config_id:{user_config_id}  问答耗时:{str(int(end_time_str))}秒")

                            # 问答内容入库
                            self.claude_db_utils.insert_message(user_config_id=user_config_id, user_id=user_id,
                                                                question_id=question_id,
                                                                question_msg=question_msg,
                                                                conversation_uuid='',
                                                                organization_uuid=organization_uuid,
                                                                session_id=session_id, answer_id='',
                                                                answer_text='', source=user_source,
                                                                model=model,
                                                                response_status=stream_response_status_code)
                            log_info(
                                f'user_id:{user_id} insert_message user_config_id:{user_config_id} user_source:{user_source} question_id:{question_id} response_status:{stream_response_status_code}')
                            # 睡眠1秒防止没有完全断开
                            await asyncio.sleep(1)
                            return

                        # 打印第一条记录
                        if first_message_flag and chunk:
                            log_info(f"user_id:{user_id} first_message:{chunk.decode('utf-8')}")
                            first_message_flag = False

                        # 防止流输出不完整
                        buffer += chunk
                        while separator in buffer:
                            index = buffer.index(separator)
                            message_bytes, buffer = buffer[:index], buffer[index + len(separator):]
                            message_str = message_bytes.decode("utf-8")
                            # 计算消息差异
                            message_content_json, message_content, stop_reason = self.get_parses_message(
                                message_str=message_str)
                            # 如果存在消息
                            if message_content_json:
                                total_message_content += message_content
                                if stop_reason and stop_reason == 'stop_sequence':
                                    # 输出最后一条记录
                                    log_info(f"user_id:{user_id} total_message_content:{total_message_content}")

                                    # 判断账号被封逻辑
                                    if 'Your account has been disabled after an automatic review of your recent activities that violate our Terms of Service.' in total_message_content:
                                        # 标记数据库中账号被封
                                        self.claude_db_utils.update_user_status(user_config_id=user_config_id,
                                                                                is_enable=-1, info='账号被封')
                                        # 加载账号列表
                                        user_list = self.claude_db_utils.select_user_list()
                                        self.claude_redis_utils.reload_user_list(user_list=user_list)
                                        log_info(f'reload user_list:{user_list}')

                                        # 删除session
                                        self.claude_db_utils.delete_session_by_user(user_config_id=user_config_id)

                                    # 流程结束
                                    self.finish_message(user_config_id=user_config_id, user_id=user_id,
                                                        question_id=question_id,
                                                        question_msg=question_msg, model=model, session_id=session_id,
                                                        user_source=user_source, conversation_uuid=conversation_uuid,
                                                        organization_uuid=organization_uuid,
                                                        message_content=total_message_content,
                                                        response_status=stream_response_status_code)

                                    # 睡眠1秒防止没有完全断开
                                    await asyncio.sleep(1)
                                    # 释放同步锁
                                    self.claude_redis_utils.release_lock_user(user_config_id=user_config_id)
                                    log_info(
                                        f"user_id:{user_id} user_config_id:{user_config_id} rob_lock_user:release")
                                    # 流式返回结束
                                    yield bytes('[DONE]\n', encoding="utf-8")

                                    # 问答耗时
                                    end_time_str = time.time() - start_time_str
                                    log_info(
                                        f"user_id:{user_id} user_config_id:{user_config_id}  问答耗时:{str(int(end_time_str))}秒")
                                else:
                                    # 流式返回结果
                                    yield bytes(json.dumps(message_content_json, ensure_ascii=False) + '\n',
                                                encoding="utf-8")

        except asyncio.CancelledError:
            # 这里处理客户端断开连接的情况
            asyncio.create_task(self.handle_cancellation(user_id=user_id, user_config_id=user_config_id))

    def finish_message(self, user_config_id: str, user_id: str, question_id: str, question_msg: str,
                       model: str, session_id: str, user_source: str, conversation_uuid: str, organization_uuid: str,
                       message_content: str, response_status: int):
        '''
        处理消息
        :param user_config_id:
        :param user_id:
        :param question_id:
        :param question_msg:
        :param model:
        :param session_id:
        :param user_source:
        :param session_exist:
        :param latest_message:
        :return:
        '''
        # insert 会话id信息
        self.claude_db_utils.insert_session(user_config_id=user_config_id, user_id=user_id,
                                            user_source=user_source, session_id=session_id,
                                            conversation_uuid=conversation_uuid, organization_uuid=organization_uuid)
        log_info(
            f'user_id:{user_id} insert_session user_config_id:{user_config_id} user_source:{user_source} session_id:{session_id} conversation_id:{conversation_uuid} organization_uuid:{organization_uuid}')

        # 问答内容入库
        self.claude_db_utils.insert_message(user_config_id=user_config_id, user_id=user_id, question_id=question_id,
                                            question_msg=question_msg,
                                            conversation_uuid=conversation_uuid, organization_uuid=organization_uuid,
                                            session_id=session_id, answer_id='0',
                                            answer_text=message_content, source=user_source, model=model,
                                            response_status=response_status)
        log_info(
            f'user_id:{user_id} insert_message user_config_id:{user_config_id} user_source:{user_source} question_id:{question_id} conversation_id:{conversation_uuid}')

    def get_parses_message(self, message_str: str):
        '''
         解析并对比消息差值
        :param message_str:
        :return:
        '''
        # 解析正确gpt的结果
        if message_str and self.is_json(message_str.replace('data:', '')):
            message_json = json.loads(message_str.replace('data:', ''))
            if message_json.get('completion') is not None:
                message_content = message_json['completion']
                stop_reason = message_json['stop_reason']
                # if stop_reason and stop_reason == 'stop_reason':
                #     stop_reason
                # diff_content = message_content.replace(previous_message_content, '')
                content_json = {
                    "code": 200,
                    "message": message_content
                }
                return content_json, message_content, stop_reason
        # 其他情况
        return None, None, None

    async def test_stream(self, cookies: str, data: dict):
        '''
        测试
        :param cookies:
        :param data:
        :return:
        '''

        try:
            async with httpx.AsyncClient() as client:
                async with client.stream("POST", self.claude_config.append_message_url, json=data,
                                         headers=self.get_header(cookies=cookies),
                                         timeout=600) as stream_response:

                    print(stream_response.status_code)

                    buffer = b""  # 缓冲区
                    separator = b"\n"  # 数据块分隔符（示例中使用换行符）
                    previous_message_content = ""  # 存储前一条消息的内容

                    async for chunk in stream_response.aiter_bytes():

                        if stream_response.status_code != 200:
                            print(chunk.decode("utf-8"))

                        # print(chunk)
                        buffer += chunk

                        while separator in buffer:
                            index = buffer.index(separator)
                            message_bytes, buffer = buffer[:index], buffer[index + len(separator):]
                            message_str = message_bytes.decode("utf-8")
                            print(message_str)

                            # 计算消息差异
                            message_content_json, message_content, stop_reason = self.get_parses_message(
                                message_str=message_str)
                            if message_content:
                                # previous_message_content = message_content
                                yield bytes(json.dumps(message_content, ensure_ascii=False) + '\n', encoding="utf-8")
        except asyncio.CancelledError:
            # 这里处理客户端断开连接的情况
            print("Client disconnected, stopping data stream.")
            # 这里你可以添加任何必要的清理代码

            print('sleep 10')
            asyncio.create_task(self.handle_cancellation2())
