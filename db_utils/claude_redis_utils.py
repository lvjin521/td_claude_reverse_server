import redis
import json
from config.config import RedisConfig


class ClaudeRedisUtils:

    def __init__(self):
        redis_config = RedisConfig()
        # 实现一个连接池
        redis_pool = redis.ConnectionPool(host=redis_config.redis_connect_host, port=redis_config.redis_connect_port,
                                          password=redis_config.redis_connect_user_pwd)
        self.redis_conn = redis.Redis(connection_pool=redis_pool)
        self.redis_number = 6

        # 账号队列
        self.claude_user_redis_name = 'td:claude:user:list'

        # 黑名单
        self.chatgpt_message_black_list_name = 'td:chatgpt:black:list'

        # 账号锁前缀
        self.claude_user_lock_prefix_name = 'td:claude:user:lock:prefix:'
        # 账号额度用完锁前缀
        self.claude_user_limit_prefix_name = 'td:claude:user:limit:prefix:'

        # GPT API key name
        self.chatgpt_user_api_key_name = 'td:chatgpt:user:api:key:name'

    def reload_user_list(self, user_list: list):
        '''
        刷新用户队列
        :param user_list:
        :return:
        '''
        self.redis_conn.select(self.redis_number)
        self.redis_conn.delete(self.claude_user_redis_name)
        for user_item in user_list:
            user_id = user_item[0]
            self.redis_conn.rpush(self.claude_user_redis_name, user_id)

    def reload_black_list(self, chatgpt_select_black_list: list):
        '''
        重新加载黑名单
        :param chatgpt_select_black_list:
        :return:
        '''
        chatgpt_black_key_list = []
        for item in chatgpt_select_black_list:
            chatgpt_black_key_list.append(item[0])

        self.redis_conn.select(self.redis_number)
        self.redis_conn.set(self.chatgpt_message_black_list_name,
                            json.dumps(chatgpt_black_key_list, ensure_ascii=False))

    def get_black_list(self) -> list:
        # 黑名单逻辑
        self.redis_conn.select(self.redis_number)
        chatgpt_black_list = json.loads(self.redis_conn.get(self.chatgpt_message_black_list_name).decode('utf-8'))
        return chatgpt_black_list

    def lpop_user(self):
        self.redis_conn.select(self.redis_number)
        redis_name = self.claude_user_redis_name
        user_id = self.redis_conn.lpop(redis_name)
        user_id = user_id.decode('utf-8')
        self.redis_conn.rpush(redis_name, user_id)
        return user_id

    def set_lock_user(self, user_config_id: str):
        '''
        存入账号同步锁逻辑
        :param user_config_id:
        :return: 存入成功返回True 失败返回None
        '''
        self.redis_conn.select(self.redis_number)
        key = self.claude_user_lock_prefix_name + user_config_id
        return self.redis_conn.set(name=key, value='123', ex=120, px=None, nx=True, xx=False)

    def get_lock_user_ttl(self, user_config_id: str):
        self.redis_conn.select(self.redis_number)
        key = self.claude_user_limit_prefix_name + user_config_id
        return self.redis_conn.ttl(key)

    def set_lock_user_by_rate_limit_error(self, user_config_id: str):
        '''
        存入账号同步锁逻辑
        :param user_config_id:
        :return: 存入成功返回True 失败返回None
        '''
        self.redis_conn.select(self.redis_number)
        key = self.claude_user_limit_prefix_name + user_config_id
        return self.redis_conn.set(name=key, value='123', ex=60 * 61 * 6, px=None, nx=True, xx=False)

    def release_lock_user(self, user_config_id: str):
        self.redis_conn.select(self.redis_number)
        key = self.claude_user_lock_prefix_name + user_config_id
        self.redis_conn.delete(key)

    def set_chatgpt_user_api_key(self, user_api_key: str):
        self.redis_conn.select(self.redis_number)
        self.redis_conn.set(self.chatgpt_user_api_key_name, user_api_key)

    def get_chatgpt_user_api_key(self):
        self.redis_conn.select(self.redis_number)
        result = self.redis_conn.get(self.chatgpt_user_api_key_name)
        if result:
            return result.decode('utf-8')
        return None


if __name__ == '__main__':
    redis_utils = ClaudeRedisUtils()
    # redis_utils.set_chatgpt_user_api_key('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')
    # # redis_utils.redis_conn.select(6)
    # print(redis_utils.get_chatgpt_user_api_key())
    user_config_id = '999999'
    redis_utils.set_lock_user_by_rate_limit_error(user_config_id)

    user_config_id = '999998'
    result = redis_utils.get_lock_user_ttl(user_config_id)
    print(result)
    print(result > 0)

    # name: KeyT,
    # value: EncodableT,
    # ex: Union[ExpiryT, None] = None,
    # px: Union[ExpiryT, None] = None,
    # nx: bool = False,
    # xx: bool = False,
    # keepttl: bool = False,
    # get: bool = False,
    # exat: Union[AbsExpiryT, None] = None,
    # pxat: Union[AbsExpiryT, None] = None,
    # redis_utils.redis_conn.delete('test')

    # result = redis_utils.redis_conn.set(name='test', value='123', ex=60, px=None, nx=True, xx=False)
    # print(result)
    # redis_utils.redis_conn.set('test', '456')
    # print(redis_utils.redis_conn.get('test'))
    # print(redis_utils.redis_conn.keys('td_chatgpt:user:lock:prefix:*'))
    # user_list = redis_utils.redis_conn.keys('td_chatgpt:user:lock:prefix:*')
    # for item in user_list:
    #     redis_utils.redis_conn.delete(item.decode('utf-8'))
