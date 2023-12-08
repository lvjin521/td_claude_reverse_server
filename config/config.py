import json


class DBConfig:
    def __init__(self):
        # mysql 链接地址 国外
        self.mysql_connect_host = 'rm-rj96v1d46wj5zawu9co.mysql.rds.aliyuncs.com'
        self.mysql_connect_port = 3306
        self.mysql_connect_user_name = 'gobackcn'
        self.mysql_connect_user_pwd = 'testdaily@1024'
        self.mysql_connect_user_db = 'td_chatgpt'


class RedisConfig:
    def __init__(self):
        # redis连接地址 国外
        self.redis_connect_host = 'r-rj9l0g0zs12vuf60mrpd.redis.rds.aliyuncs.com'
        self.redis_connect_port = 6379
        self.redis_connect_user_pwd = 'testdaily:testdaily!1024'


class ClaudeConfig:
    def __init__(self):
        # host
        self.host = 'https://proxy.finechat.ai'
        # 问答url
        self.append_message_url = f'{self.host}/api/append_message'
        # 登陆url
        self.user_login_url = f'{self.host}/getsession'

    def denied_message(self):
        '''
        默认的拒绝消息
        :return:
        '''
        data = {
            "code": 200,
            "message": '根据相关法律法规，你的问题或即将得到的答案不合规，我无法回应。'
        }
        yield bytes(json.dumps(data, ensure_ascii=False) + '\n', encoding="utf-8")
        yield '[DONE]'

    def banned_message(self):
        '''
        默认的拒绝消息
        :return:
        '''
        data = {
            "code": 200,
            "message": 'user_banned'
        }
        yield bytes(json.dumps(data, ensure_ascii=False) + '\n', encoding="utf-8")
        yield '[DONE]'
