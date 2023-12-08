# -*- coding: utf-8 -*-
# @Time : 2023/9/15 9:09 AM
# @Author : lvjin
# @File : chatgpt_utils.py
# @Software: PyCharm
import asyncio
import json
from .httpx_utils import HttpUtils
# from httpx_utils import HttpUtils


class ChatGptUtils:

    def __init__(self):
        self.http_utils = HttpUtils()

    async def send_moderations(self, input_text: str, user_api_key: str, proxy: str = ''):
        '''
        内容校验政策
        :param input_text:
        :param user_api_key:
        :param proxy:
        :return:
        '''
        input_text = input_text.replace('\n', ' ')
        url = 'https://api.openai.com/v1/moderations'
        data = {
            "input": input_text
        }
        headers = {
            'content-type': 'application/json',
            'Authorization': 'Bearer {}'.format(user_api_key)
        }
        return await self.http_utils.async_send_post_by_json(url=url, headers=headers, json=data,
                                                             proxy=proxy)


if __name__ == '__main__':
    gpt_utils = ChatGptUtils()

    text = '''
    You are a translator proficient in multiple languages including Chinese/English/Spanish/French/German/Russian, etc. You are highly familiar with the cultural history and literary references of each language. Your task is to translate {input} into English.

You need to follow the principles below:
- If the input is in English, repeat it verbatim to me (output=input) without modifying any content,even the capitalization must be consistent（Any word or phrase composed of English letters should be recognized as English, just repeat it without change anything）.
- If the language of the input is not English, please translate the input into English.
- The output doesn't strictly have to follow English grammar rules.

Remember:return the final result to me in the following JSON format:

{"input":"the content I give you",
"output":"The translation of input, or simply the repetition of input (All content must be strictly consistent with the input, including case sensitivity, in the case where input is in English)"
}

input:"""
Beyoncé sad naked  nude is being transported in a cage"""
    '''

    for item in range(1):
        response = asyncio.run(gpt_utils.send_moderations(input_text=text,
                                                          user_api_key='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'))
        print(response.text)
