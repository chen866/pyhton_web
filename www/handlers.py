import re, time, json, logging, hashlib, base64, asyncio
import markdown2
from coreweb import get, post
from aiohttp import web
from models import User, Comment, Blog, next_id
from apis import APIError, APIResourceNotFoundError, APIValueError
from config_default import configs

COOKIE_NAME = 'awesession'
_COOKIE_KEY = configs["session"]["secret"]


def user2cookie(user, max_age):
    '''
    Generate cookie st by user
    '''
    # build cookie string by: id-expires-sha1
    expires = str(int(time.time() + max_age))
    s = '%s-%s-%s-%s' % (user.id, user.password, expires, _COOKIE_KEY)
    L = [user.id, expires, hashlib.sha1(s.encode('utf-8')).hexdigest()]
    return '-'.join(L)


@asyncio.coroutine
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
        s = '%s-%s-%s-%s' % (uid, user.password, expires, _COOKIE_KEY)
        if sha1 != hashlib.sha1(s.encode('utf-8')).hexdigest():
            logging.info('invalid sha1')
            return None
        user.password = '******'
        return user
    except Exception as e:
        logging.exception(e)
        return None


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


@get('/register')
async def register():
    return {
        '__templates__': 'register.html'
    }


@get('/signin')
async def signin():
    return {
        '__templates__': 'signin.html'
    }


@post('/api/authenticate')
async def authenticate(*, email, password):
    if not email:
        raise APIValueError('email', 'Invalid email.')
    if not password:
        raise APIValueError('password', 'Invalid password.')
    users = await User.findAll('email = ?', [email])
    if len(users) == 0:
        raise APIValueError('email', 'Email not exist.')
    user = users[0]
    # check password:
    sha1 = hashlib.sha1()
    sha1.update(user.id.encode('utf-8'))
    sha1.update(b':')
    sha1.update(password.encode('utf-8'))
    if user.password != sha1.hexdigest():
        raise APIValueError('password', 'Invalid password.')
    # authenticate ok , set cookie:
    r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
    user.password = '******'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r


@get('/signout')
async def signout(request):
    referer = request.headers.get('Referer')
    r.set_cookie(COOKIE_NAME, '-delete-', max_age=0, httponly=True)
    logging.info('user sigined out.')
    return r


_RE_EMAIL = re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
_RE_SHA1 = re.compile(r'^[0-9a-f]{40}$')


# @get('/api/users')
# async def api_get_users():
#     users = await User.findAll(orderBy='create_time desc')
#     for u in users:
#         u.password = '******'
#     return dict(users=users)


@post('/api/users')
async def api_register_user(*, email, name, password):
    if not name or not name.strip():
        raise APIValueError('name')
    if not email or not _RE_EMAIL.match(email):
        raise APIValueError('email')
    if not password or not _RE_SHA1.match(password):
        raise APIValueError('password')
    users = await User.findAll('email = ?', [email])
    if len(users) > 0:
        raise APIError('register:faild', 'Email', 'Email is already in use.')
    uid = next_id()
    sha1_passwd = '%s:%s' % (uid, password)
    user = User(id=uid, name=name.strip(), email=email, password=hashlib.sha1(sha1_passwd.encode('utf-8')).hexdigest(),
                image='http://www.gravatar.com/avatar/%s?d=mm&s=120' % hashlib.md5(email.encode('utf-8')).hexdigest())
    await user.save()
    # make session cookie:
    r = web.response()
    r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
    user.password = '******'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r

