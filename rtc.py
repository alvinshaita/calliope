import asyncio
import json

from aiohttp import web
from aiortc import (
    RTCPeerConnection,
    RTCSessionDescription,
)
from aiortc.contrib.media import (
    MediaPlayer, MediaRelay
)

import attridict

connection_data = attridict()
# peer_data = attridict()
count=0
MAX_TRANSCEIVERS = 1
relay = MediaRelay()


from video import CompositeTrack


async def offer(request):
    global count
    count+=1
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    caller_name = params["caller_name"]
    call_id = params["call_id"]

    pc = RTCPeerConnection()
    pc_id = f"pc{count}"
    print("peer connection id: ", pc_id)

    if connection_data.get(call_id) is None:
        connection_data[call_id] = {}

    connection_data[call_id][pc_id] = attridict({
        "peer_connection": pc,
        "tracks": {"video": None, "audio": None},
        "transceivers": [],
        "name": caller_name,
        "id": pc_id,
        "datachannel": None,
        # "latest_frame": None,
    })

    for i in range(MAX_TRANSCEIVERS):
        transceiver = pc.addTransceiver("video", direction="sendrecv")
        connection_data[call_id][pc_id]["transceivers"].append(transceiver)

    print("----------", connection_data)

    @pc.on("datachannel")
    def on_datachannel(channel):
        connection_data[call_id][pc_id].datachannel = channel

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

                for other_pc_id, other_pc_data in list(connection_data[call_id].items()):
                    if other_pc_id == pc_id:
                        continue

                    # let everyone know that you joined
                    msg = json.dumps({
                        "type": "join",
                        "name": caller_name,
                        "user_id": pc_id,
                    })
                    other_pc_data.datachannel.send(msg)

                    # let you know who's in the meeting
                    msg = json.dumps({
                        "type": "join",
                        "name": other_pc_data.name,
                        "user_id": other_pc_id,
                    })
                    channel.send(msg)

            elif data.get("type") == "close":
                print("datachannel message - close")

                for other_pc_id, other_pc_data in list(connection_data[call_id].items()):
                    if other_pc_id == pc_id:
                        continue

                    msg = json.dumps({
                        "type": "leave",
                        "name": caller_name,
                        "user_id": pc_id,
                    })
                    other_pc_data.datachannel.send(msg)

                await pc.close()
                connection_data[call_id].pop(pc_id, None)

            elif data.get("type") == "chat":
                for other_pc_id, other_pc_data in list(connection_data[call_id].items()):
                    message = json.dumps({
                        "type": "chat",
                        "sender": caller_name,
                        "message": data["message"],
                        "img": None,
                        "user_id": pc_id,
                    })
                    other_pc_data.datachannel.send(message)

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        print(f"Connection state is {pc.connectionState} == {pc.iceConnectionState}")
        if pc.connectionState == "failed":
            await pc.close()
            connection_data[call_id].pop(pc_id, None)
        if pc.connectionState == "closed":
            await pc.close()
            connection_data[call_id].pop(pc_id, None)

    @pc.on("track")
    def on_track(track):
        print(f"track {track.kind} received")

        async def track_worker(track, pc_id):
            try:
                while True:
                    frame = await track.recv()
                    connection_data[call_id][pc_id]["latest_frame"] = frame
                    # connection_data[call_id][pc_id]["latest_frame"] = frame.to_ndarray(format="bgr24")
            except Exception as e:
                print("Error:", e)

        if track.kind == "audio":
            # ...
            for other_pc_id, other_pc_data in list(connection_data[call_id].items()):
                if other_pc_id != pc_id:
                    other_pc_data.peer_connection.addTrack(relay.subscribe(track))

            # peer_data[pc_id]["tracks"]["audio"] = track
            # pc.addTrack(relay.subscribe(track))
        elif track.kind == "video":
            # asyncio.create_task(track_worker(track, pc_id))

            connection_data[call_id][pc_id]["tracks"]["video"] = track
            overlay = CompositeTrack(track, connection_data[call_id], pc_id)
            pc.addTrack(overlay)

            # player = MediaPlayer(
            #     "workshop.mp4",
            #     format="mp4",
            #     options={"framerate": "30"}
            # )
            # pc.addTrack(player.video)

            # @player.video.on("ended")
            # async def on_ended():
            #     print("player video track ended")

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

    return web.Response(
        content_type="application/json",
        text=json.dumps(
            {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
        ),
    )

async def shutdown(app):
    # close peer connections
    coros = [pd["peer_connection"].close() for pds in connection_data.values() for pd in pds.values()]
    await asyncio.gather(*coros)
    connection_data.clear()


def generate_random_name():
    length = 4
    chars = "abcdefghijklmnopqrstuvwxyz"
    return ''.join(random.choice(chars) for _ in range(length))

