# coding=utf-8
import httpx
from logger_utils.log_util import log_info


class HttpUtils:
    def __init__(self):
        pass

    async def async_send_post_by_json(self, url, headers, json, proxy='', timeout=600):
        '''
        封装async post请求
        :param url:url
        :param headers:header
        :param json:json数据
        :return:状态码，json
        '''
        if proxy is None or proxy == '':
            proxies = None
        else:
            proxies = httpx.Proxy(url="http://{}".format(proxy), )
        timeout = httpx.Timeout(timeout)
        log_info('async_send_post_by_json--> url:{}'.format(url))
        try:
            async with httpx.AsyncClient(proxies=proxies, timeout=timeout) as client:
                response = await client.post(url=url, json=json, headers=headers)
                status_code = response.status_code
                log_info('async_send_post_by_json--> status_code:{}'.format(str(status_code)))
                return response
        except httpx.ReadTimeout:
            log_info('请求超时.')
            return None
        except Exception as e:
            log_info('其他异常:{}'.format(str(e)))
            return None

    async def async_send_post_by_data(self, url, headers, data, proxy='', timeout=600):
        '''
        封装async post请求
        :param url:url
        :param headers:header
        :param data:data数据
        :return:状态码，json
        '''
        if proxy is None or proxy == '':
            proxies = None
        else:
            proxies = httpx.Proxy(url="http://{}".format(proxy), )
        timeout = httpx.Timeout(timeout)
        log_info('async_send_post_by_data--> url:{}'.format(url))
        try:
            async with httpx.AsyncClient(proxies=proxies, timeout=timeout) as client:
                response = await client.post(url=url, data=data, headers=headers)
                status_code = response.status_code
                log_info('async_send_post_by_data--> status_code:{}'.format(str(status_code)))
                return response
        except httpx.ReadTimeout:
            log_info('请求超时.')
            return None
        except Exception as e:
            log_info('其他异常:{}'.format(str(e)))
            return None

    async def async_send_get(self, url, headers, proxy='', timeout=600):
        '''
        封装async get请求
        :param url:url
        :param headers:header
        :return: 状态码，文本
        '''
        try:
            if proxy is None or proxy == '':
                proxies = None
            else:
                proxies = httpx.Proxy(url="http://{}".format(proxy), )
            log_info('async_send_get--> url:{}'.format(url))
            timeout = httpx.Timeout(timeout)
            async with httpx.AsyncClient(proxies=proxies, timeout=timeout) as client:
                response = await client.get(url=url, headers=headers)
                status_code = response.status_code
                log_info('async_send_get--> status_code:{}'.format(str(status_code)))
                return response
        except httpx.ReadTimeout:
            log_info('请求超时.')
            return None
        except Exception as e:
            log_info('其他异常:{}'.format(str(e)))
            return None
