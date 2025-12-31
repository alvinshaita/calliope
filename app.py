import os
import rtc
from aiohttp import web

ROOT = os.path.dirname(__file__)

async def register(request):
    content = open(os.path.join(ROOT, "public/register.html"), "r").read()
    return web.Response(content_type="text/html", text=content)


async def index(request):
    call_id = request.match_info.get("call_id", "")
    content = open(os.path.join(ROOT, "public/index.html"), "r").read()
    return web.Response(content_type="text/html", text=content)


async def javascript(request):
    content = open(os.path.join(ROOT, "public/client.js"), "r").read()
    return web.Response(content_type="application/javascript", text=content)


async def css(request):
    content = open(os.path.join(ROOT, "public/style.css"), "r").read()
    return web.Response(content_type="text/css", text=content)


async def offer(request):
    return await rtc.offer(request)


async def on_shutdown(app):
    await rtc.shutdown(app)


def generate_random_name():
    length = 4
    chars = "abcdefghijklmnopqrstuvwxyz"
    return ''.join(random.choice(chars) for _ in range(length))


if __name__ == "__main__":
    app = web.Application(debug=True)
    app.on_shutdown.append(on_shutdown)

    # Serve static files (images, favico, css, etc.)
    app.router.add_static('/static/', path=os.path.join(ROOT, 'static'), name='static')

    app.router.add_get("/", register)
    app.router.add_get("/{call_id:[a-zA-Z0-9_-]{5}}", index)

    app.router.add_get("/client.js", javascript)
    app.router.add_get("/style.css", css)
    app.router.add_post("/offer", offer)

    web.run_app(app, access_log=None, host="0.0.0.0", port=8050)
