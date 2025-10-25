const configuration = {
	iceServers: [{urls: "stun:stun.1.google.com:19302"}]
};

// let peerConnection1 = null
// let peerConnection2 = null
let stream = null
let localVideo = document.getElementById('video1')
let remoteVideo = document.getElementById('video2')
let userIdInput = document.getElementById('user_id')
userIdInput.value = ""



let addr = "localhost"
// let addr = "192.168.100.4"


var userId = null;
startButton.onclick = () => {
	var ws = new WebSocket("ws://"+addr+":8001");

	// send hello message on open to get user_id
	ws.onopen = function() {
		let data = JSON.stringify({ type: "hello"});
		ws.send(data)
	}

	ws.onmessage = function (evt) {
		var msg = evt.data;
		msg = JSON.parse(msg)
		if (msg.type == "hello") {
			// get user_id
			userIdInput.value = msg.id
			userId = msg.id
		} else if (msg.type == "init") {
			peerConnection = new RTCPeerConnection(configuration);
			console.log("create peerConnection")

			peerConnection.ontrack = function (event) {
				console.log("peerConnection received a track:", event.track.kind)

				if (event.track.kind == 'video') {
					remoteVideo.srcObject = event.streams[0]
					remoteVideo.autoplay = true
					remoteVideo.controls = true
					remoteVideo.muted = true
				}
			}

			peerConnection.onicecandidate = function (event) {
				let data = JSON.stringify({type: "ice", candidate: event.candidate, id: userId})
				ws.send(data)
			}

			// navigator.mediaDevices.getUserMedia({ video: true, audio: false })
			navigator.mediaDevices.getUserMedia({ video: true, audio: true })
			.then(s => {
				stream = s
				localVideo.srcObject = s
				localVideo.autoplay = true
				localVideo.controls = true
				localVideo.muted = true

				var tracks = stream.getTracks()
				tracks.forEach(track => peerConnection.addTrack(track, stream))

				let data = JSON.stringify({type: "init_done", id: userId})
				ws.send(data)

				console.log("initialization done")
			})
			.catch(error => console.log(error));

		} else if (msg.type == "ice") {
			console.log("iceeeeeeeeeee")
			peerConnection.addIceCandidate(msg.candidate)
		} else if (msg.type == "create_offer") {
			console.log("create offer")
			peerConnection.createOffer()
			.then(offer => {

				peerConnection.setLocalDescription(offer)
				console.log("peerConnection sets local description")
				
				let data = JSON.stringify({type: "offer", sdp: offer.sdp, id: userId})
				ws.send(data)
			})
		} else if (msg.type == "offer") {
			// peerConnection.setRemoteDescription(msg.sdp)
			peerConnection.setRemoteDescription(msg)
			console.log("peerConnection sets remote description")


			peerConnection.createAnswer()
			.then(answer => {
				peerConnection.setLocalDescription(answer)
				console.log("peerConnection sets local description")
				// peerConnection1.setRemoteDescription(answer)
				// console.log("peerConnection2 sets remote description")

				let data = JSON.stringify({type: "answer", sdp: answer.sdp, id: userId})
				ws.send(data)
			})
		} else if (msg.type == "answer") {
			// peerConnection.setRemoteDescription(msg.sdp)
			peerConnection.setRemoteDescription(msg)
			console.log("peerConnection sets remote description")
		}


	}

	ws.onclose = function() {
		let data = JSON.stringify({type: "close", id: userId})
		ws.send(data)
		userId = null;
		console.log("websocket connection closed")
	}
}