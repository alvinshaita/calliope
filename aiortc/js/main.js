const configuration = {
	iceServers: [{urls: "stun:stun.1.google.com:19302"}]
};

let peerConnection = null
let stream = null
let video1 = document.getElementById('video1')
let video2 = document.getElementById('video2')







startButton.onclick = () => {
	peerConnection = new RTCPeerConnection(configuration);
	console.log("create peerConnection")

	peerConnection.ontrack = function (event) {
		console.log("peerConnection received a track:", event.track.kind)

		if (event.track.kind == 'video') {
			video2.srcObject = event.streams[0]
			video2.autoplay = true
			video2.controls = true
			video2.muted = true
		}
	}


	peerConnection.onicecandidate = function (event) {
		console.log("=================ice")
	}


	navigator.mediaDevices.getUserMedia({ video: true, audio: true })
	.then(s => {
		stream = s
		video1.srcObject = s
		video1.autoplay = true
		video1.controls = true
		video1.muted = true
	})
	.catch(error => console.log(error));
}

connect.onclick = () => {

	console.log("connect")

	var tracks = stream.getTracks();
	tracks.forEach(track => peerConnection.addTrack(track, stream))



	peerConnection.createOffer().then(function(offer) {
        return peerConnection.setLocalDescription(offer);
    }).then(function() {
        console.log("bbb")

        var offer = peerConnection.localDescription;
        console.log("send localDescription(offer)")

		return fetch('/offer', {
	        body: JSON.stringify({
	            sdp: offer.sdp,
	            type: offer.type,
	            // video_transform: document.getElementById('video-transform').value
	        }),
	        headers: {
	            'Content-Type': 'application/json'
	        },
	        method: 'POST'
	    });
	}).then(function(response) {
        return response.json();
    }).then(function(answer) {
    	console.log("setRemoteDescription(answer)")
        return peerConnection.setRemoteDescription(answer);
    }).catch(function(e) {
        alert(e);
    });

}

stopit.onclick = () => {
	peerConnection = null

	// remove local video
	video1.autoplay = false
	video1.controls = false
	video1.srcObject = null

	// remove remote video
	video2.autoplay = false
	video2.controls = false
	video2.srcObject = null
}