import logging
import asyncio, os, json, time
from datetime import datetime

from aiohttp import web
from jinja2 import Environment, FileSystemLoader
import orm
from coreweb import add_routers, add_static

logging.basicConfig(level=logging.INFO)


def init_jinja2(app, **kwargs):
    logging.info('init jinja2...')
    options = dict(
        autoescape=kwargs.get('autoescape', True),
        block_start_string=kwargs.get('block_start_string', '{%'),
        block_end_string=kwargs.get('block_end_string', '%}'),
        variable_start_string=kwargs.get('variable_start_string', '{{'),
        variable_end_string=kwargs.get('variable_end_string', '}}'),
        auto_reload=kwargs.get('auto_reload', True)
    )

    path = kwargs.get('path', None)
    if path is None:
        Path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    logging.info('set jinja2 template path: %s' % path)
    env = Environment(loader=FileSystemLoader(path), **options)
    filters = kwargs.get('filters', None)
    if filters is not None:
        for name, f in filters.items():
            env.filters[name] = f
    app['__templating__'] = env


async def logger_factory(app, handler):
    async def logger(request):
        logging.info('Request: %s %s' % (request.method, request.path))
        # await asyncio.sleep(0.3)
        return (await handler(request))
    return parse_data


# TODO


def index(request):
    return web.Response(body=b'<h1>This is the first page!</h1>', content_type='text/html')


# Web App骨架
@asyncio.coroutine
async def init(Loop):
    app = web.Application(loop=Loop)
    app.router.add_route('GET', '/', index)
    server = await Loop.create_server(app.make_handler(), '127.0.0.1', '9000')
    logging.info('server started at http://127.0.0.1:9000...')
    return server


loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()
