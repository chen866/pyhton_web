import logging
import asyncio
import aiomysql


# 全局数据库连接池
@asyncio.coroutine
def create_pool(Loop, **kwargs):
    logging.info('create database connection pool...')
    global __pool
    __pool = yield from aiomysql.create_pool(
        host=kwargs.get('host', 'localhost'),
        port=kwargs.get('port', 3306),
        user=kwargs['user'],
        password=kwargs['password'],
        db=kwargs['db'],
        charset=kwargs.get('charset', 'utf-8'),
        autocommit=kwargs.get('autocommit', True),
        maxsize=kwargs.get('maxsize', 10),
        loop=Loop
    )


# 查询通用方法
# size 获取制定数量的结果
@asyncio.coroutine
def select(sql, args, size=None):
    logging.log(sql, args)
    global __pool
    with (yield from __pool) as conn:
        # SQL语句的占位符是?，而MySQL的占位符是%s，select()函数在内部自动替换。
        # 注意要始终坚持使用带参数的SQL，而不是自己拼接SQL字符串，这样可以防止SQL注入攻击。
        curse = yield from conn.excute(sql.replace('?', '%s'), args or ())
        if size:
            result = yield from curse.fetchmany(size)
        else:
            result = yield from curse.fetchall()
        yield from curse.close()
        logging.info('rows returned %s' % len(result or ()))
        return result


# 通用修改方法
@asyncio.coroutine
def execute(sql, args):
    logging.log(sql, args)
    with (yield from __pool) as conn:
        try:
            curse = yield from conn.cursor()
            # SQL语句的占位符是?，而MySQL的占位符是%s，execute()函数在内部自动替换。
            yield from curse.execute(sql.replace('?', '%s'), args)
            affected = curse.rowcount
            yield from curse.close()
        except BaseException:
            raise
        return affected


# 表的信息映射
class ModelMetaclass(type):

    def __new__(mcs, name, bases, attrs):
        # 排除Model类自身
        if name == 'Model':
            return type.__new__(mcs, name, bases, attrs)
        # 获取table名称
        tableName = attrs.get('__table__', None) or name
        logging.info('found model: %s (table: %s' % (name, tableName))
        # 获取所有的Field和主键名
        mappings = dict()
        fields = []
        primaryKry = None
