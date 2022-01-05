import asyncio
import coredis
from sanic.app import Sanic
from sanic.response import json, stream

app = Sanic()

@app.route("/")
async def test(request):
    return json({"hello": "world"})

@app.route("/notifications")
async def notification(request):
    async def _stream(res):
        redis = coredis.StrictRedis()
        pub = redis.pubsub()
        await pub.subscribe('test')
        end_time = app.loop.time() + 30
        while app.loop.time() < end_time:
            await redis.publish('test', 111)
            message = None
            while not message:
                message = await pub.get_message()
            res.write(message)
            await asyncio.sleep(0.1)
    return stream(_stream)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
