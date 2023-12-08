import uuid


class ClaudeTools:
    def __init__(self):
        self.pass_str = ''

    def black_contains(self, black_list: list, message: str) -> bool:
        '''
        判断列表是否存在关键词
        :param black_list:
        :param message:
        :return:
        '''
        for black_key in black_list:
            key = black_key
            if key is not None:
                key = key.lower()
            if key is not None and len(key) > 0 and key in message:
                # print(key)
                return True
        return False

    def get_random_uuid(self, num: int = 32):
        '''
        随机生成taskid
        :return:
        '''
        return str(uuid.uuid4()).replace('-', '')[:num]
