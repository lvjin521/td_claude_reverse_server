# coding=utf-8
import pymysql
from config.config import DBConfig


class Connect:
    def __enter__(self):
        db_config = DBConfig()
        self.conn = pymysql.connect(host=db_config.mysql_connect_host, port=db_config.mysql_connect_port,
                                    user=db_config.mysql_connect_user_name,
                                    password=db_config.mysql_connect_user_pwd,
                                    database=db_config.mysql_connect_user_db, charset='utf8')
        self.cur = self.conn.cursor()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):  # 函数结束完自动执行关闭连接
        self.cur.close()
        self.conn.close()


class DBHelper:

    def find(self, sql):
        """ 无参数查询 """
        with Connect() as db:  # 打开Connect获取一个连接，执行完时自动关闭连接
            db.cur.execute(sql)
            result = db.cur.fetchall()
            return result

    def find_one(self, sql):
        """ 无参数查询 """
        with Connect() as db:  # 打开Connect获取一个连接，执行完时自动关闭连接
            db.cur.execute(sql)
            result = db.cur.fetchone()
            return result

    def find_para(self, sql, tup):  # 传入元组
        """ 有参数查询 """
        with Connect() as db:
            db.cur.execute(sql, tup)
            result = db.cur.fetchall()
            return result

    def modify(self, sql):
        """ 无参增删改 """
        with Connect() as db:
            db.cur.execute(sql)
            db.conn.commit()

    def modify_para(self, sql, tup):
        """ 有参增删改 """
        with Connect() as db:
            db.cur.execute(sql, tup)
            db.conn.commit()

    def modify_para_return_id(self, sql, tup):
        with Connect() as db:
            db.cur.execute(sql, tup)
            insert_id = db.conn.insert_id()
            db.conn.commit()
            return insert_id


if __name__ == '__main__':
    pass
