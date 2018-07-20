import logging

logging.basicConfig(level=logging.INFO)

import asyncio
from aiohttp import web


def index(request):
    return web.Response(body=b'<h1>This is the first page!</h1>', content_type='text/html')


@asyncio.coroutine
def init(Loop):
    app = web.Application(loop=Loop)
    app.router.add_route('GET', '/', index)
    server = yield from Loop.create_server(app.make_handler(), '127.0.0.1', '9000')
    logging.info('server started at http://127.0.0.1:9000...')
    return server


loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()
