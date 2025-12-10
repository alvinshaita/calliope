// peer connection
var peerConn = null;

// data channel
var dc = null
var dcInterval = null;

var localStream = null;
var localVideo = document.getElementById('local-video');
var remoteVideos = document.getElementById('remote-videos');
var remoteVideo = document.getElementById('remote-video');
var remoteAudio = document.getElementById('audio');

startButton.onclick = () => {
	console.log("== start")
	start()
}

connectButton.onclick = () => {
	console.log("== connect")
	connect()
}

stopButton.onclick = () => {
	console.log("== stop")
	stop()
}

function createPeerConnection() {
    var config = {
        sdpSemantics: 'unified-plan',
        iceServers: [{ urls: ['stun:stun.l.google.com:19302'] }],
    };

    peerConn = new RTCPeerConnection(config);
    peerConn.ontrack = function(event) {
        console.log("++++ ON TRACK", event.track.kind)
        if (event.track.kind == 'video') {
            const video = document.createElement("video");
            video.srcObject = event.streams[0];
            video.autoplay = true;
            video.playsInline = true;
            video.controls = true;
            video.classList.add('remote-video');
            remoteVideos.appendChild(video)
            // remoteVideo.srcObject = event.streams[0];
        } else {
            remoteAudio.srcObject = event.streams[0];
        }
    };

    return peerConn;
}

function negotiate() {
    return peerConn.createOffer().then((offer) => {
        return peerConn.setLocalDescription(offer);
    }).then(() => {
        // wait for ICE gathering to complete
        return new Promise((resolve) => {
            if (peerConn.iceGatheringState === 'complete') {
                resolve();
            } else {
                function checkState() {
                    if (peerConn.iceGatheringState === 'complete') {
                        peerConn.removeEventListener('icegatheringstatechange', checkState);
                        resolve();
                    }
                }
                peerConn.addEventListener('icegatheringstatechange', checkState);
            }
        });
    }).then(() => {
        var offer = peerConn.localDescription;

        return fetch('/offer', {
            body: JSON.stringify({
                sdp: offer.sdp,
                type: offer.type,
            }),
            headers: {
                'Content-Type': 'application/json'
            },
            method: 'POST'
        });
    }).then((response) => {
        const resp = response.json()
        console.log(resp)
        return resp;
    }).then((answer) => {
        // console.log("answer", answer)
        return peerConn.setRemoteDescription(answer);
    }).catch((e) => {
        alert(e);
    });
}

function start() {
	const constraints = {
        audio: true,
        video: true
    };

    if (constraints.audio || constraints.video) {
        navigator.mediaDevices.getUserMedia(constraints).then((stream) => {
            localStream = stream
            localVideo.srcObject = stream
        }, (err) => {
            alert('Could not acquire media: ' + err);
        });
    }
}

function connect() {
    peerConn = createPeerConnection();

    var time_start = null;

    const current_stamp = () => {
        if (time_start === null) {
            time_start = new Date().getTime();
            return 0;
        } else {
            return new Date().getTime() - time_start;
        }
    };

    var parameters = {
        ordered: true,
        // ordered: false,
        // maxRetransmits: 0,
        // maxPacketLifetime: 500,
    }

    dc = peerConn.createDataChannel('chat', parameters);
    dc.addEventListener('close', () => {
        clearInterval(dcInterval);
        console.log("dc close")
    });
    dc.addEventListener('open', () => {
        // dc.send({name: "Shaita"})
        dc.send(JSON.stringify({ type: "name", name: "Rombora" }));
        // dcInterval = setInterval(() => {
        //     var message = 'ping ' + current_stamp();
        //     // console.log("dc ->", message)
        //     dc.send(message);
        // }, 1000);
    });
    dc.addEventListener('message', (evt) => {
        console.log("message", evt.data)
        // console.log("dc <-", evt.data)
        if (evt.data.substring(0, 4) === 'pong') {
            var elapsed_ms = current_stamp() - parseInt(evt.data.substring(5), 10);
            // console.log("dc rtt", elapsed_ms)

        }
    });

    localStream.getTracks().forEach((track) => {
        peerConn.addTrack(track, localStream);
    });
    
    negotiate();
}

function stop() {
    // close data channel
    if (dc) {
        dc.close();
    }

    // close transceivers
    if (peerConn.getTransceivers) {
        peerConn.getTransceivers().forEach((transceiver) => {
            if (transceiver.stop) {
                transceiver.stop();
            }
        });
    }

    // close local audio / video
    peerConn.getSenders().forEach((sender) => {
        sender.track.stop();
    });

    // close peer connection
    setTimeout(() => {
        peerConn.close();
    }, 500);
}
