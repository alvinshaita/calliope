import asyncio
import json
import os
import uuid

import cv2
from aiohttp import web
from aiortc import (
    RTCPeerConnection,
    RTCSessionDescription,
    VideoStreamTrack,
    MediaStreamTrack
)
from aiortc.contrib.media import (
    MediaRelay
)
from av import VideoFrame

ROOT = os.path.dirname(__file__)
import attridict

peer_data = attridict()
count=0
MAX_TRANSCEIVERS = 1
relay = MediaRelay()

class LabelVideoStream(VideoStreamTrack):
    def __init__(self, source_track, username, pc_id):
        super().__init__()
        self.source = source_track
        self.username = username
        self.pc_id = pc_id


    async def recv(self):
        # Get next frame from incoming track
        frame = await self.source.recv()

        # Convert to numpy for processing
        img = frame.to_ndarray(format="bgr24")
        # print("aaaaaaaaaaaaaaaaaaaaaaa", peer_data[pc_id])
        # print("aaaaaaaaaaaaaaaaaaaaaaa", pc_id)
        # Add text overlay
        cv2.putText(
            img, 
            # self.name,
            peer_data[self.pc_id]["name"],
            (40, 40),                      # position
            cv2.FONT_HERSHEY_SIMPLEX, 
            1.2,                            # size
            (0, 255, 0),                    # color (green)
            3
        )

        # Convert back to VideoFrame
        new_frame = VideoFrame.from_ndarray(img, format="bgr24")
        new_frame.pts = frame.pts
        new_frame.time_base = frame.time_base
        return new_frame


async def index(request):
    content = open(os.path.join(ROOT, "index.html"), "r").read()
    return web.Response(content_type="text/html", text=content)


async def javascript(request):
    content = open(os.path.join(ROOT, "client.js"), "r").read()
    return web.Response(content_type="application/javascript", text=content)


async def offer(request):
    global count
    count+=1
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    pc_id = f"pc{count}"
    print("peer connection id: ", pc_id)

    peer_data[pc_id] = {
        "peer_connection": pc,
        "tracks": {"video": None, "audio": None},
        "transceivers": [],
        "name": None,
    }

    for i in range(MAX_TRANSCEIVERS):
        transceiver = pc.addTransceiver("video", direction="sendrecv")
        peer_data[pc_id]["transceivers"].append(transceiver)

    print(f"Created for {request.remote}")

    @pc.on("datachannel")
    def on_datachannel(channel):
        @channel.on("message")
        def on_message(message):
            data = json.loads(message)
            print("message", data)

            if data.get("type") == "name":
                # print(data["name"], "==============")
                peer_data[pc_id]["name"] = data["name"]


    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        print(f"Connection state is {pc.connectionState}")
        if pc.connectionState == "failed":
            await pc.close()
            peer_data.pop(pc_id, None)

    @pc.on("track")
    def on_track(track):
        print(f"Track {track.kind} received")

        if track.kind == "audio":
            ...
        elif track.kind == "video":
            peer_data[pc_id]["tracks"]["video"] = track

            # peer_data[pc_id]["transceiver"].sender.replaceTrack(
            #     # track
            #     peer_data["pc1"]["tracks"]["video"]
            # )

            # for sender in peer_data[pc_id]["senders"]:
            #     sender.replaceTrack(track)


            # pc.addTrack(track)

            overlay = LabelVideoStream(track, username=f"Alvin", pc_id=pc_id)
            pc.addTrack(overlay)

            # pc.addTrack(
            #     VideoTransformTrack(
            #         relay.subscribe(track)
            #     )
            # )

        @track.on("ended")
        async def on_ended():
            print(f"Track {track.kind} ended")

    print("setRemoteDescription")
    # handle offer
    await pc.setRemoteDescription(offer)
    print("createAnswer")
    # send answer
    answer = await pc.createAnswer()
    print("setLocalDescription")
    await pc.setLocalDescription(answer)
    print("555")

    return web.Response(
        content_type="application/json",
        text=json.dumps(
            {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
        ),
    )

async def on_shutdown(app):
    # close peer connections
    coros = [pd["peer_connection"].close() for pd in peer_data.values()]
    await asyncio.gather(*coros)
    peer_data.clear()



def generate_random_name():
    length = 4
    chars = "abcdefghijklmnopqrstuvwxyz"
    return ''.join(random.choice(chars) for _ in range(length))


if __name__ == "__main__":
    app = web.Application(debug=True)
    app.on_shutdown.append(on_shutdown)

    # Serve static files (images, favico, css, etc.)
    app.router.add_static('/static/', path=os.path.join(ROOT, 'static'), name='static')

    app.router.add_get("/", index)
    app.router.add_get("/client.js", javascript)
    app.router.add_post("/offer", offer)

    web.run_app(app, access_log=None, host="0.0.0.0", port=8000)
