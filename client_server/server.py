import asyncio
import json
import random
import string

import websockets


user_ids = []
wses = {}
done_ids = []

addr = "localhost"
# addr = "192.168.100.4"

def generate_user_id():
	length = 5
	user_id = ''.join(random.choices(string.ascii_lowercase, k=length))

	while user_id in user_ids:
		user_id = ''.join(random.choices(string.ascii_lowercase, k=length))
	
	return user_id

async def on_message(websocket, msg):
	# respond to `hello` message with user id
	if msg["type"] == "hello":
		user_id = generate_user_id()

		user_ids.append(user_id)
		wses[user_id] = websocket
		print("== got hello. sent user_id", user_id)
		
		await websocket.send(json.dumps({"type": "hello", "id": user_id}))
		await websocket.send(json.dumps({"type": "init"}))
	
	elif msg["type"] == "close":
		user_id = msg["id"]
		user_ids.remove(user_id)
		wses.pop(user_id)

		print("== got close from user_id:", user_id)
				
	elif msg["type"] == "init_done":
		print("S: << init done")
		done_ids.append(msg["id"])
		if len(done_ids) == 2:
			await wses[done_ids[0]].send(json.dumps({"type": "create_offer"}))

	elif msg["type"] == "offer":
		print("S: << offer [1 -> 2]")
		await wses[done_ids[1]].send(json.dumps({"type": "offer", "sdp": msg["sdp"]}))

	elif msg["type"] == "answer":
		print("S: << answer [1 <- 2]")
		await wses[done_ids[0]].send(json.dumps({"type": "answer", "sdp": msg["sdp"]}))

	elif msg["type"] == "ice":
		# print("S: << ice", msg)
		user = msg["id"]
		ws = wses[user_ids[0]] if user==user_ids[1] else wses[user_ids[1]]
		await ws.send(json.dumps({"type": "ice", "candidate": msg["candidate"]}))


	else:
		print("!!!!!!!!!!! not ready")



async def handle_msg(websocket):
	async for message in websocket:
		msg = json.loads(message)
		try:
			await on_message(websocket, msg)
		except websockets.ConnectionClosedOK:
			print("websocket error: websockets.ConnectionClosedOK")
		except Exception as e:
			print("websocket error:", e)

async def main():
	async with websockets.serve(handle_msg, addr, 8001):
		await asyncio.Future()  # run forever

asyncio.run(main())