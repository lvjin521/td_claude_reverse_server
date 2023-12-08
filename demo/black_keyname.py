# -*- coding: utf-8 -*-
# @Time : 2023/9/14 9:26 AM
# @Author : lvjin
# @File : black_keyname.py
# @Software: PyCharm

from db_utils.claude_db_utils import ClaudeDBUtils


def black_contains(black_list: list, message: str) -> bool:
    '''
    判断列表是否存在关键词
    :param black_list:
    :param message:
    :return:
    '''
    for black_key in black_list:
        key = black_key[0]
        if key is not None:
            key = key.lower()
        if key is not None and len(key) > 0 and key in message:
            print(key)
            return True
    return False

if __name__ == '__main__':
    chatgpt_db_utils = ClaudeDBUtils()

    question_msg = 'sat数学真题中文版合集, sat与 act的区别, ib是什么单位 缩写, 美国高考的申请条件, 美国高考的考试内容,软路由器和普通路由器区别,软路由的优点和缺点,现在为什么不用软路由了,有了软路由还要梯子吗,路由器如何搭梯子上外网,工作室用软路由搬砖封号吗,软路由如何实现一机一ip,工作室多个ip方法,一个模拟器一个ip免 费方法,群控怎么解决一机一IP,工作室手机ip解决办法,一个ip登几个dnf比较稳,一根网线可以分几个ip,华为云ip实现单机单ip,300台电脑如何设置ip,虚拟机多开ip怎么解决,同ip多账号怎么躲避检测,手机工作室多路由干扰,工作室多手机独立ip方法,带机1000台的路由器,开工作室怎么办大量的宽带,10个路由器放一起会干扰吗,改ip地址软件免费,领导者代理ip,安卓一键换ip免费版,天启影视2023年,天启网络,神龙ip代理,天启游戏,极光ip修改器,天启游戏小说,游戏叫天启的重生网游小说,工作室一根网100个ip,软路由怎么科学的上网,openwrt允许外网访问,刷好了openwrt怎么出国,买了梯子还要买节点吗,刷openwrt最稳的路由器,openwrt翻墙设置,openwrt科学上油管插件,pppoe pptp l2tp 选哪个,L2TP客户端,ipsec协议工作在哪一层,openwrt安装l2tp协议,支持l2tp协议的手机热点'

    # 获取redis黑名单
    chatgpt_black_list = chatgpt_db_utils.select_black_key_word()
    # 判断问题是否存在于黑名单
    is_black = black_contains(black_list=chatgpt_black_list, message=question_msg)