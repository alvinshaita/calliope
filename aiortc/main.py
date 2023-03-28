#!/usr/bin/env python3

import os
import uuid

import logging
from aiohttp import web
import json
# import cv2

ROOT = os.path.dirname(__file__)




from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaBlackhole, MediaPlayer, MediaRecorder, MediaRelay

logger = logging.getLogger("pc")


relay = MediaRelay()







class VideoTransformTrack(MediaStreamTrack):
    """
    A video stream track that transforms frames from an another track.
    """

    kind = "video"

    # def __init__(self, track, transform):
    def __init__(self, track):
        super().__init__()  # don't forget this!
        self.track = track
        # self.transform = transform

    async def recv(self):
        frame = await self.track.recv()
        return frame


async def offer(request):
	print("offer")
	params = await request.json()

	print(params)
	offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

	pc = RTCPeerConnection()
	pc_id = "PeerConnection(%s)" % uuid.uuid4()
	# pcs.add(pc)

	def log_info(msg, *args):
		logger.info(pc_id + " " + msg, *args)

 
	log_info("Created for %s", request.remote)

	# prepare local media
	# player = MediaPlayer(os.path.join(ROOT, "demo-instruct.wav"))
	# if args.record_to:
	# 	recorder = MediaRecorder(args.record_to)
	# else:
	# 	recorder = MediaBlackhole()

	@pc.on("datachannel")
	def on_datachannel(channel):
		@channel.on("message")
		def on_message(message):
			if isinstance(message, str) and message.startswith("ping"):
				channel.send("pong" + message[4:])

	@pc.on("connectionstatechange")
	async def on_connectionstatechange():
		log_info("Connection state is %s", pc.connectionState)
		if pc.connectionState == "failed":
			await pc.close()
			# pcs.discard(pc)

	@pc.on("track")
	def on_track(track):
		log_info("Track %s received", track.kind)

		if track.kind == "audio":
			# pc.addTrack(player.audio)
			# recorder.addTrack(track)
			pass
		elif track.kind == "video":
			pc.addTrack(
				VideoTransformTrack(
					# relay.subscribe(track), transform=params["video_transform"]
					relay.subscribe(track)
				)
			)
			# if args.record_to:
				# recorder.addTrack(relay.subscribe(track))

		@track.on("ended")
		async def on_ended():
			log_info("Track %s ended", track.kind)
			# await recorder.stop()

	# handle offer
	await pc.setRemoteDescription(offer)
	print("setRemoteDescription(offer)")
	# await recorder.start()

	# send answer
	answer = await pc.createAnswer()
	print("createAnswer")
	await pc.setLocalDescription(answer)
	print("setLocalDescription")

	print("retrun response (answer)")
	return web.Response(
		content_type="application/json",
		text=json.dumps(
			{"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
		),
	)




















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

app.router.add_post("/offer", offer)

app.router.add_static("/", "..")
web.run_app(app, host="0.0.0.0", port=8000)
