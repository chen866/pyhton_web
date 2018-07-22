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
    log(sql, args)
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
    log(sql, args)
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


def create_args_string(num):
    L = []
    for n in range(num):
        L.append('?')
        return ', '.join(L)


def log(sql, args=()):
    logging.info('SQL: %s' % sql)


class Field(object):
    def __init__(self, name, column_type, primary_key, default):
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default

    def __str__(self):
        return '<%s, %s:%s>' % (self.__class__.__name__, self.column_type, self.name)


# 映射varchar的StringField
class StringField(Field):
    def __init__(self, name=None, primary_key=False, default=None, ddl='varchar(100)'):
        super().__init__(name, ddl, primary_key, default)


class BooleanField(Field):
    def __init__(self, name=None, default=False):
        super().__init__(name, 'boolean', False, default)


class InterField(Field):
    def __init__(self, name=None, primary_key=False, default=0):
        super().__init__(name, 'bigint', primary_key, default)


class FloatField(Field):
    def __init__(self, name=None, primary_key=False, default=0.0):
        super().__init__(name, 'real', primary_key, default)


class TextField(Field):
    def __init__(self, name=None, default=None):
        super().__init__(name, 'text', False, default)


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
        primaryKey = None
        for k, v in attrs.items():
            if isinstance(v, Field):
                logging.info('found mapping: %s ==> %s' % (k, v))
                mappings[k] = v
                if v.primary_key:
                    # 主键
                    if primaryKey:
                        raise RuntimeError('Duplicate primary key for field: %s' % k)
                    primaryKey = k
                else:
                    fields.append(k)
        if not primaryKey:
            raise RuntimeError('Primary key not found! ')
        for k in mappings.keys():
            attrs.pop(k)
        escaped_fields = list(map(lambda f: '`%s`' % f, fields))  # 其他属性名
        attrs['__mappings__'] = mappings  # 保存属性和列的映射关系
        attrs['__table__'] = tableName
        attrs['__primary_key__'] = primaryKey  # 主键属性名
        attrs['__fields__'] = fields  # 除主键以外的其他属性名
        # 构造默认的增删改查
        attrs['__select__'] = 'select `%s`, %s from `%s`' % (primaryKey, ','.join(escaped_fields), tableName)
        # attrs['__insert__'] = 'insert into `%s` (%s, `%s`) values (%s)' % (
        # tableName, ','.join(map(lambda f: '`%s` = ?' % (mappings.get(f).name or f), fields)), primaryKey)
        attrs['__insert__'] = 'insert into `%s` (%s, `%s`) values (%s)' % (
            tableName, ', '.join(escaped_fields), primaryKey, create_args_string(len(escaped_fields) + 1))
        attrs['__update__'] = 'update `%s` set %s where `%s` = ?' % (
            tableName, ','.join(map(lambda f: '`%s` = ?' % (mappings.get(f).name or f), fields)), primaryKey)
        attrs['__delete__'] = 'delete from `%s` where `%s` = ?' % (tableName, primaryKey)
        return type.__new__(mcs, name, bases, attrs)


# Model从dict继承，所以具备所有dict的功能，
# 同时又实现了特殊方法__getattr__()和__setattr__()，因此又可以像引用普通字段那样写
class Model(dict, metaclass=ModelMetaclass):
    def __init__(self, **kwargs):
        super(Model, self).__init__(**kwargs)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Model' object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        self[key] = value

    def __getValue__(self, key):
        return getattr(self, key, None)

    def getValueOrDefault(self, key):
        value = getattr(self, key, None)
        if value is None:
            field = self.__mappings__[key]
            if field.default is not None:
                value = field.default() if callable(field.default) else field.default
                logging.debug('using default value for %s: %s' % (key, str(value)))
                setattr(self, key, value)
        return value

    @classmethod
    @asyncio.coroutine
    def find(cls, primaryKey):
        # find object by primary key
        result = yield from select('%s where `%s` = ?' % (cls.__select__, cls.__primary_key__), [primaryKey], 1)
        if len(result) == 0:
            return None
        return cls(**result[0])

    @asyncio.coroutine
    def save(self):
        args = list(map(self.getValueOrDefault, self.__fields__))
        args.append(self.getValueOrDefault(self.__primary_key__))
        rows = yield from execute(self.__insert__, args)
        if rows != 1:
            logging.warning('failed to insert record: affected rows: %s' % rows)

    @classmethod
    @asyncio.coroutine
    def findAll(cls, where=None, args=None, **kwargs):
        # find objects by where clause
        sql = [cls.__select__]
        if where:
            sql.append('where')
            sql.append(where)
            if args is None:
                args = []
            orderBy = kwargs.get('orderBy', None)
            if orderBy:
                sql.append('order by')
                sql.append(orderBy)
            limit = kwargs.get('limit', None)
            if limit is not None:
                sql.append('limit')
                if isinstance(limit, int):
                    sql.append('?')
                    args.append(limit)
                elif isinstance(limit, tuple) and len(limit) == 2:
                    sql.append('?, ?')
                    args.extend(limit)
                else:
                    raise ValueError('Invalid limit value: %s' % str(limit))
            result = yield from select(' '.join(sql), args)
            return [cls(**r) for r in result]

    @classmethod
    @asyncio.coroutine
    def findNumber(cls, selectField, where=None, args=None):
        # find number by select and where
        sql = ['select %s _num_ from `%s`' % (selectField, cls.__table__)]
        if where:
            sql.append('where')
            sql.append(where)
        result = yield from select(' '.join(sql), args, 1)
        if len(result) == 0:
            return None
        return result[0]['_num_']

    @asyncio.coroutine
    def update(self):
        args = list(map(self.getValue, self.__fields__))
        args.append(self.getValue(self.__primary_key__))
        rows = yield from execute(self.__update__, args)
        if rows != 1:
            logging.warning('failed to update by primary key: affected rows: %s' % rows)

    @asyncio.coroutine
    def remove(self):
        args = [self.getValue(self.__primary_key__)]
        rows = yield from execute(self.__delete__, args)
        if rows != 1:
            logging.warning('failed to remove by primary key: affected rows: %s' % rows)
