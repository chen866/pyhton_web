import re, time, json, logging, hashlib, base64, asyncio

from coreweb import get, post

from models import User, Comment, Blog, next_id


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
