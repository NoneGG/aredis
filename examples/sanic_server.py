import asyncio
import aredis
from sanic.app import Sanic
from sanic.response import json, stream

app = Sanic()

@app.route("/")
async def test(request):
    return json({"hello": "world"})

@app.route("/notifications")
async def notification(request):
    async def _stream(res):
        redis = aredis.StrictRedis()
        pub = redis.pubsub()
        await pub.subscribe('test')
        while True:
            await redis.publish('test', 111)
            message = await pub.get_message()
            if message:
                res.write(message)
            asyncio.sleep(5)
    return stream(_stream)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)