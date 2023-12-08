from .db_helper import DBHelper


class ClaudeDBUtils:
    def __init__(self):
        self.db_helper = DBHelper()

    def session_exist(self, user_id: str, session_id: str, source: str) -> bool:
        '''
        查询用户对应的会话是否存在
        :param user_id:用户id
        :param session_id:会话id
        :return:存在True 不存在False
        '''
        select_sql = f'select count(1) from td_claude_server_session where user_id="{user_id}" and session_id="{session_id}" and user_source="{source}" and is_enable=1'
        result = self.db_helper.find_one(select_sql)[0]
        if result > 0:
            return True
        return False

    def select_session_id(self, user_id: str, session_id: str, source: str):
        '''
        查询用户对应的会话相关id
        :param user_id:
        :param session_id:
        :param source:
        :return:
        '''
        select_sql = f'select conversation_uuid,organization_uuid,user_config_id from td_claude_server_session where user_id="{user_id}" and session_id="{session_id}" and user_source="{source}" and is_enable=1'
        find_result = self.db_helper.find_one(select_sql)
        return find_result[0], find_result[1], find_result[2]

    def insert_session(self, user_config_id: str, user_id: str, user_source: str, session_id: str,
                       conversation_uuid: str,
                       organization_uuid: str):
        insert_sql = 'INSERT INTO td_claude_server_session (`user_config_id`, `user_id`, `user_source`, `session_id`, `conversation_uuid`, `organization_uuid`, `is_enable`, `update_time`, `create_time`) VALUES (%s, %s, %s, %s, %s, %s, 1, NOW(), NOW())'
        self.db_helper.modify_para(insert_sql, [user_config_id, user_id, user_source, session_id, conversation_uuid,
                                                organization_uuid])

    # def update_session(self, user_config_id: str, user_id: str, user_source: str, session_id: str, conversation_uuid: str,
    #                    parent_message_id: str):
    #     update_sql = 'update td_claude_server_session set conversation_uuid=%s,update_time=NOW() where user_config_id=%s and user_id=%s and user_source=%s and session_id=%s and conversation_id=%s'
    #     self.db_helper.modify_para(update_sql, [conversation_uuid, user_config_id, user_id, user_source, session_id,
    #                                             conversation_id])

    def insert_message(self, user_config_id: str, user_id: str, question_id: str, question_msg: str,
                       conversation_uuid: str, organization_uuid: str, session_id: str, answer_id: str,
                       answer_text: str, source: str, model: str, response_status: int):
        insert_sql = 'INSERT INTO `td_claude_server_message` (`user_config_id`, `user_id`, `question_id`, `question_msg`, `conversation_uuid`, `organization_uuid`, `session_id`, `answer_id`, `answer_text`, `source`, `model`, `create_time`,`response_status`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(),%s);'
        self.db_helper.modify_para(insert_sql,
                                   [user_config_id, user_id, question_id, question_msg, conversation_uuid,
                                    organization_uuid, session_id, answer_id,
                                    answer_text, source, model, response_status])

    def delete_session(self, user_id: str, conversation_uuid: str):
        delete_sql = 'delete from td_claude_server_session where user_id=%s and conversation_uuid=%s'
        self.db_helper.modify_para(delete_sql, [user_id, conversation_uuid])

    def delete_session_by_user(self, user_config_id: str):
        delete_sql = 'delete from td_claude_server_session where user_config_id=%s'
        self.db_helper.modify_para(delete_sql, [user_config_id])

    def select_user_list(self):
        '''
        查询可用的账号
        :return:
        '''
        select_sql = 'select id from td_claude_server_user_config where is_enable=1 and cookies !="" and organization_uuid!=""'
        return self.db_helper.find(select_sql)

    def update_user_status(self, user_config_id: str, is_enable: int, info: str):
        '''
        更改账号状态
        :param user_config_id:
        :return:
        '''
        update_sql = f'update td_claude_server_user_config set is_enable=%s,info=%s where id=%s'
        self.db_helper.modify_para(update_sql, [is_enable, info, user_config_id])

    def select_user_info(self, user_config_id: str):
        '''
        查询账号信息
        :return:
        '''
        select_sql = f'select cookies,organization_uuid,user_name,nick_name,is_enable from td_claude_server_user_config where id={user_config_id}'
        return self.db_helper.find_one(select_sql)

    def select_black_key_word(self):
        chatgpt_select_black_sql = 'select key_name from td_chatgpt_message_black_config where is_enable = 1;'
        return self.db_helper.find(chatgpt_select_black_sql)


if __name__ == '__main__':
    chatgpt_db_utils = ClaudeDBUtils()
    # result = chatgpt_db_utils.session_exist(user_id='123', session_id='123')
    result = chatgpt_db_utils.select_session_id(user_id='123', session_id='123', source='test')
    print(result)
