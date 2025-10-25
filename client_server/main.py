#!/usr/bin/env python3

import os

from aiohttp import web

ROOT = os.path.dirname(__file__)

app = web.Application()

app.router.add_get("/", lambda response: web.Response(
		content_type="text/html",
		text=open(os.path.join(ROOT, "index.html"), "r").read()
	)
)

app.router.add_get("/js/main.js", lambda response: web.Response(
		content_type="application/javascript",
		text=open(os.path.join(ROOT, "js/main.js"), "r").read()
	)
)

app.router.add_static("/", "..")
web.run_app(app, host="0.0.0.0", port=8000)
print("777")