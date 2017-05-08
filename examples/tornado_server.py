import asyncio
import logging
from aredis import StrictRedis
from tornado.web import RequestHandler, Application
from tornado.httpserver import HTTPServer
from tornado.platform.asyncio import AsyncIOMainLoop


class GetRedisKeyHandler(RequestHandler):

    def __init__(self, application, request, **kwargs):
        super(GetRedisKeyHandler, self).__init__(application, request, **kwargs)
        self.redis_client = StrictRedis()

    async def get(self):
        key = self.get_argument('key')
        res = await self.redis_client.get(key)
        print('key: {} val: {} in redis'.format(key, res))
        self.write(res)



if __name__ == '__main__':
    AsyncIOMainLoop().install()
    app = Application([('/', GetRedisKeyHandler)])
    server = HTTPServer(app)
    server.bind(8000)
    server.start()
    asyncio.get_event_loop().run_forever()