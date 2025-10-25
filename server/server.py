import asyncio
import json
import os
import uuid

from aiohttp import web
from aiortc import (
    RTCPeerConnection,
    RTCSessionDescription
)
from aiortc.contrib.media import (
    MediaRelay
)

ROOT = os.path.dirname(__file__)
pcs = {}

async def index(request):
    content = open(os.path.join(ROOT, "index.html"), "r").read()
    return web.Response(content_type="text/html", text=content)


async def javascript(request):
    content = open(os.path.join(ROOT, "client.js"), "r").read()
    return web.Response(content_type="application/javascript", text=content)


async def offer(request):
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    pc_id = f"PeerConnection({uuid.uuid4()})"
    pcs[pc_id] = pc

    print(f"Created for {request.remote}")

    @pc.on("datachannel")
    def on_datachannel(channel):
        @channel.on("message")
        def on_message(message):
            if isinstance(message, str) and message.startswith("ping"):
                channel.send("pong" + message[4:])

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        print(f"Connection state is {pc.connectionState}")
        if pc.connectionState == "failed":
            await pc.close()
            pcs.pop(pc_id, None)

    @pc.on("track")
    def on_track(track):
        print(f"Track {track.kind} received")

        if track.kind == "audio":
            pc.addTrack(track)
        elif track.kind == "video":
            pc.addTrack(track)

        @track.on("ended")
        async def on_ended():
            print(f"Track {track.kind} ended")

    # handle offer
    await pc.setRemoteDescription(offer)

    # send answer
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.Response(
        content_type="application/json",
        text=json.dumps(
            {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
        ),
    )

async def on_shutdown(app):
    # close peer connections
    coros = [pc.close() for pc in pcs.values()]
    await asyncio.gather(*coros)
    pcs.clear()


if __name__ == "__main__":
    ssl_context = None
    app = web.Application()
    app.on_shutdown.append(on_shutdown)

    # Serve static files (images, favico, css, etc.)
    app.router.add_static('/static/', path=os.path.join(ROOT, 'static'), name='static')

    app.router.add_get("/", index)
    app.router.add_get("/client.js", javascript)
    app.router.add_post("/offer", offer)

    web.run_app(
        app, access_log=None, host="0.0.0.0", port=8000, ssl_context=ssl_context
    )
