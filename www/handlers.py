import re, time, json, logging, hashlib, base64, asyncio
import markdown2
from coreweb import get, post
from aiohttp import web
from models import User, Comment, Blog, next_id
from apis import APIError, APIResourceNotFoundError
from config_default import configs

COOKIE_NAME = 'awesession'
_COOKIE_KEY = configs.session.secret


def user2cookie(user, max_age):
    '''
    Generate cookie st by user
    '''
    # build cookie string by: id-expires-sha1
    expires = str(int(time.time() + max_age))
    s = '%s-%s-%s-%s' % (user.id, user.passwd, expires, _COOKIE_KEY)
    L = [user.id, expires, hashlib.sha1(s.encode('utf-8')).hexdigest()]
    return '-'.join(L)


@get('/')
async def index(request):
    summary = 'login ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magne qliqa.'
    blogs = [
        Blog(id='1', name='Test Blog 1', summary=summary, create_time=time.time() - 120),
        Blog(id='2', name='Test Blog 3', summary=summary, create_time=time.time() - 3600),
        Blog(id='3', name='Test Blog 3', summary=summary, create_time=time.time() - 7200)
    ]
    return {
        '__templates__': 'blogs.html',
        'blogs': blogs
    }


@get('/api/users')
async def api_get_users():
    users = await User.findAll(orderBy='create_time desc')
    for u in users:
        u.password = '******'
    return dict(users=users)


async def cookie2user(cookie_str):
    '''
    Parse cookie and load user if cookie is valid.
    '''
    if not cookie_str:
        return None
    try:
        L = cookie_str.split('-')
        if len(L) != 3:
            return None
        uid, expires, sha1 = L
        if int(expires) < time.time():
            return None
        user = await User.find(uid)
        if user is None:
            return None
        s = '%s-%s-%s-%s' % (uid, user.passwd, expires, _COOKIE_KEY)
        if sha1 != hashlib.sha1(s.encode('utf-8')).hexdigest():
            logging.info('invalid sha1')
            return None
        user.passwd = '******'
        return user
    except Exception as e:
        logging.exception(e)
        return None
