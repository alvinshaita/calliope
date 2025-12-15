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

import numpy as np
import time
from fractions import Fraction
import math

peer_data = attridict()
count=0
MAX_TRANSCEIVERS = 1
relay = MediaRelay()


class CompositeTrack(VideoStreamTrack):
    def __init__(self, track, peer_data, pc_id):
        super().__init__()
        self.track = track
        self.peer_data = peer_data
        self.pc_id = pc_id
        self.full_height = 1000
        self.full_width = 1000

    async def recv(self):
        frames = []

        # if len(self.peer_data) == 1:
        #     print("1111111111")
        #     return None
        # # else:
        # #     print("2222222222222")

        for pc_id, pdata in list(self.peer_data.items()):   

            if self.pc_id == pc_id:
                continue

            track = pdata.tracks.video
            if track is None:
                continue
            try:
                frame = await track.recv()
                img = frame.to_ndarray(format="bgr24")

                cv2.putText(
                    img, 
                    pdata.name,
                    (40, 40),                       # position
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    1.2,                            # size
                    (0, 255, 0),                    # color (green)
                    3
                )

                frames.append(img)
            except Exception as e:
                pass

        if not frames:
            # return a black frame
            black = np.zeros((480, 640, 3), dtype=np.uint8)
            out = VideoFrame.from_ndarray(black, format="bgr24")
            out.pts = int(time.time() * 90000)
            out.time_base = Fraction(1, 90000)
            return out

        try:
            # h = 480
            # resized = [cv2.resize(f, (h, h)) for f in frames]
            # combined = cv2.hconcat(resized)

            # new_frame = VideoFrame.from_ndarray(combined, format="bgr24")
            # new_frame.pts = int(time.time() * 90000)
            # new_frame.time_base = Fraction(1, 90000)
            # return new_frame


            num_clients = len(frames)
            cols = math.ceil(math.sqrt(num_clients))
            rows = math.ceil(num_clients / cols)
            cell_width = self.full_width // cols
            cell_height = self.full_height // rows

            # Resize frames
            resized_frames = [cv2.resize(f, (cell_width, cell_height)) for f in frames]

            # Build the grid row by row
            grid_rows = []
            for r in range(rows):
                row_frames = []
                for c in range(cols):
                    idx = r * cols + c
                    if idx < num_clients:
                        row_frames.append(resized_frames[idx])
                    else:
                        # empty cell
                        row_frames.append(np.zeros((cell_height, cell_width, 3), dtype=np.uint8))
                grid_rows.append(cv2.hconcat(row_frames))

            combined = cv2.vconcat(grid_rows)

            # Convert to VideoFrame
            new_frame = VideoFrame.from_ndarray(combined, format="bgr24")
            new_frame.pts = int(time.time() * 90000)
            new_frame.time_base = Fraction(1, 90000)
            return new_frame
        except Exception as e:
            return None


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
        # Add text overlay
        cv2.putText(
            img, 
            self.username,
            # peer_data[self.pc_id]["name"],
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


async def css(request):
    content = open(os.path.join(ROOT, "style.css"), "r").read()
    return web.Response(content_type="text/css", text=content)


async def offer(request):
    global count
    count+=1
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    pc_id = f"pc{count}"
    print("peer connection id: ", pc_id)

    peer_data[pc_id] = attridict({
        "peer_connection": pc,
        "tracks": {"video": None, "audio": None},
        "transceivers": [],
        "name": pc_id,
    })

    for i in range(MAX_TRANSCEIVERS):
        transceiver = pc.addTransceiver("video", direction="sendrecv")
        peer_data[pc_id]["transceivers"].append(transceiver)

    print("----------", peer_data)

    @pc.on("datachannel")
    def on_datachannel(channel):
        @channel.on("open")
        def on_open():
            print("datachannel open")

        @channel.on("close")
        def on_close():
            print("datachannel closed")

        @channel.on("message")
        async def on_message(message):
            data = json.loads(message)
            print("datachannel message: ", data)

            if data.get("type") == "name":
                print("datachannel message  name")
                user_id = json.dumps({
                    "type": "user_id",
                    "user_id": pc_id
                })
                channel.send(user_id)
            elif data.get("type") == "close":
                print("datachannel message - close")
                await pc.close()
                peer_data.pop(pc_id, None)

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        print(f"Connection state is {pc.connectionState} == {pc.iceConnectionState}")
        if pc.connectionState == "failed":
            await pc.close()
            peer_data.pop(pc_id, None)
        if pc.connectionState == "closed":
            await pc.close()
            peer_data.pop(pc_id, None)

    @pc.on("track")
    def on_track(track):
        print(f"track {track.kind} received")

        if track.kind == "audio":
            # ...
            for other_pc_id, other_pc_data in list(peer_data.items()):
                if other_pc_id != pc_id:
                    print("bbbbbbbbbbb", other_pc_id, pc_id)
                    other_pc_data.peer_connection.addTrack(relay.subscribe(track))



            # peer_data[pc_id]["tracks"]["audio"] = track
            # pc.addTrack(relay.subscribe(track))
        elif track.kind == "video":
            peer_data[pc_id]["tracks"]["video"] = track
            overlay = CompositeTrack(track, peer_data, pc_id)
            pc.addTrack(overlay)

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
    app.router.add_get("/style.css", css)
    app.router.add_post("/offer", offer)

    web.run_app(app, access_log=None, host="0.0.0.0", port=8000)
