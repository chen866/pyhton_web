import asyncio
import orm
from models import User


def test(Loop):
    yield from orm.create_pool(Loop=Loop, user='root', password='password', db='awesome')
    u = User(name='test3', email='test4@test.com', passwd='test', admin=True, image='')
    yield from u.save()


loop = asyncio.get_event_loop()
loop.run_until_complete(test(loop))
