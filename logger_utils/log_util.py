import os
import sys
import time
from loguru import logger


def creat_time_os():
    creat_time = time.strftime("%Y-%m-%d", time.localtime())

    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

    # log_path_dir = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

    current_file_path = os.path.abspath(__file__)
    # 获取当前文件所在的目录
    current_dir_path = os.path.dirname(current_file_path)
    # 获取项目的根目录
    log_path_dir = os.path.dirname(current_dir_path)

    logs_path = os.path.join(log_path_dir, "logs", creat_time)
    if os.path.exists(logs_path):
        return logs_path
    else:
        os.makedirs(logs_path)
        return logs_path


# 提供日志功能
class uru_logger:
    # 去除默认控制台输出
    # logger.remove()

    # 输出日志格式

    def __init__(self):
        logger_format = "{time:YYYY-MM-DD HH:mm:ss,SSS} | {level} | [{thread}]| {file}:{function}(): {line} | - {message}"
        logger.remove()  # 这里是不让他重复打印
        logger.add(sys.stderr,  # 这里是不让他重复打印
                   level="INFO"
                   )
        # 输出到文件，并按天分割和压缩
        logs_path = creat_time_os()
        # 日志文件名：由用例脚本的名称，结合日志保存路径，得到日志文件的绝对路径
        # logname = os.path.join(logs_path, sys.argv[0].split('/')[-1].split('.')[0]) + '.log'
        logname = os.path.join(logs_path, 'spider') + '.log'
        logger.add(
            logname,
            encoding="utf-8",
            format=logger_format,
            level="INFO",
            rotation="1500MB",
            retention="15 days",
            # colorize=True,
            compression="zip")
        self.creat_time = time.strftime("%Y-%m-%d", time.localtime())
        self.log = logger

    def check_format(self):
        if time.strftime("%Y-%m-%d", time.localtime()) != self.creat_time:
            self.__init__()


uru_logger_log = uru_logger()


def log_info(*args):
    '''
    info log信息
    :param message:
    :return:
    '''
    uru_logger_log.check_format()
    uru_logger_log.log.info(args[0] if len(args) == 1 else args)


def log_debug(*args):
    '''
    debug log信息
    :param message:
    :return:
    '''
    uru_logger_log.check_format()
    uru_logger_log.log.debug(args[0] if len(args) == 1 else args)


def log_error(*args):
    '''
    error log信息
    :param message:
    :return:
    '''
    uru_logger_log.check_format()
    uru_logger_log.log.error(args[0] if len(args) == 1 else args)
