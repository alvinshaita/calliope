// peer connection
var peerConn = null;

// data channel
var dc = null

var localVideoStream = null;


var remoteAudio = document.getElementById('audio');

const setupMenu = document.querySelector('.setup-menu');
const menuVideo = document.querySelector('.menu-video');
const mainVideo = document.querySelector('.main-video');
const localVideoMini = document.querySelector('.local-video-mini');
const videoCallActions = document.querySelector('.video-call-actions')
const rightSide = document.querySelector('.right-side');
const videoActionEndCall = document.querySelector('.video-action-button.endcall');
const videoActionStartCall = document.querySelector('.video-action-button.startcall');

const callIdView = document.querySelector('.call-id-view');
const callerName = document.querySelector('.caller-name');

const chatArea = document.querySelector('.chat-area');
const chatInput = document.querySelector('.chat-input');
const sendButton = document.querySelector('.send-button');

const participants = document.querySelector('.participants');


const micButton = document.querySelector('.video-action-button.mic');
const cameraButton = document.querySelector('.video-action-button.camera');


micButton.onclick = () => {
    const isMicMuted = micButton.classList[2] === "muted"
    if (isMicMuted) {
        // set to mic unmuted
        micButton.classList.toggle('muted', false);
    } else {
        // set to mic muted
        micButton.classList.toggle('muted', true);
    }
}

cameraButton.onclick = () => {
    const videoTrack = localVideoStream?.getVideoTracks()[0]
    const isCameraOff = cameraButton.classList[2] === "off"
    if (isCameraOff) {
        // set to camera on
        cameraButton.classList.toggle('off', false);
        videoTrack.enabled = true
    } else {
        // set to camera off
        cameraButton.classList.toggle('off', true);
        videoTrack.enabled = false
    }
}

const callId = window.location.pathname.replace("/", "")

var activeParticipants = {}

function refreshParticipants() {
    noOfParticipantsToDisplay = 4
    participants.innerHTML = ""
    var extraParticipants = 0

    const activeParticipantsValues = Object.values(activeParticipants)
    activeParticipantsValues.slice(0,noOfParticipantsToDisplay).forEach(participant => {
        participants.innerHTML += `<div class="participant profile-picture">${participant.name[0].toUpperCase()}</div>`
    })

    extraParticipants = activeParticipantsValues.length - noOfParticipantsToDisplay
    if (extraParticipants > 0) {
        participants.innerHTML += `<div class="participant-more">+${extraParticipants}</div>`
    }
}

// rightSide.classList.remove('show');

var userId = null
var prevMessageSender = null

// connectButton.onclick = () => {
videoActionStartCall.onclick = () => {
	console.log("== connect")

    if (callerName.value.trim() == "" || callId.trim() == "") {
        callerName.style.border = "2px solid red"
        return
    }

	connect()
    // videoCallActions.style.display = "flex";
    rightSide.style.display = "flex";
    mainVideo.style.display = "flex"
    localVideoMini.srcObject = localVideoStream

    menuVideo.srcObject = null

    videoActionEndCall.style.display = "block"
    videoActionStartCall.style.display = "none"
}

// stopButton.onclick = () => {
videoActionEndCall.onclick = () => {
	console.log("== stop")
	stop()
    localVideoMini.srcObject = null;
    mainVideo.srcObject = null;

    menuVideo.srcObject = localVideoStream
    // mainVideo.srcObject = localVideoStream;
    rightSide.style.display = "none";
    videoActionEndCall.style.display = "none"
    videoActionStartCall.style.display = "block"
}

sendButton.onclick = () => {
    message = chatInput.value
    if (message.trim() === "") {
        return
    }
    dc.send(JSON.stringify({ type: "chat", message: message }));
    chatInput.value = ""
}
// dc.send(JSON.stringify({ type: "name", name: callerName.value }));


chatInput.addEventListener("keydown", function(event) {
    if (event.key === "Enter") {
        sendButton.click()
    }
})

callIdView.innerHTML = callId
start()

function randomString(length = 10) {
  return Math.random().toString(36).substring(2, 2 + length);
}

window.onbeforeunload = function (event) {
    stop()
};

function createPeerConnection() {
    var config = {
        sdpSemantics: 'unified-plan',
        iceServers: [
            { urls: ['stun:stun.l.google.com:19302'] },
            {
                urls: 'turn:openrelay.metered.ca:443',
                username: 'openrelayproject',
                credential: 'openrelayproject'
            }
        ],
    };

    peerConn = new RTCPeerConnection(config);
    peerConn.ontrack = function(event) {
        console.log("++++ ON TRACK", event.track.kind)
        if (event.track.kind == 'video') {
            // const video = document.createElement("video");
            // video.srcObject = event.streams[0];
            // video.autoplay = true;
            // video.playsInline = true;
            // video.controls = true;
            // video.classList.add('main-video');
            // remoteVideos.appendChild(video)


            mainVideo.srcObject = event.streams[0];
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

        return fetch('offer', {
            body: JSON.stringify({
                sdp: offer.sdp,
                type: offer.type,
                call_id: callId,
                caller_name: callerName.value,
            }),
            headers: {
                'Content-Type': 'application/json'
            },
            method: 'POST'
        });
    })
    // .then(response => response.json())
    .then((response) => {
        const resp = response.json()
        console.log(resp)
        return resp;
    })
    .then((answer) => {
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
            localVideoStream = stream
            menuVideo.srcObject = stream
            menuVideo.muted = true
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
        console.log("+++ datachannel on close")
    });
    console.log("dddddddd", callerName.value)

    dc.addEventListener('open', () => {
        console.log("+++ datachannel on open")
        dc.send(JSON.stringify({ type: "name", name: callerName.value }));
    });

    dc.addEventListener('message', (evt) => {
        message = JSON.parse(evt.data)
        console.log("+++ on message:", message)
        if (message.type === "user_id") {
            userId = message.user_id

            // chatData.forEach(c => {
            //     addMessage(c.userId, c.sender, c.message, c.img)
            // })
        } else if (message.type === "chat") {
            addMessage(
                message.user_id,
                message.sender,
                message.message,
                "https://images.unsplash.com/photo-1566821582776-92b13ab46bb4?ixlib=rb-1.2.1&auto=format&fit=crop&w=900&q=60"
            )
        } else if (message.type === "join") {
            activeParticipants[message.user_id] = {
                name: message.name
            }
            refreshParticipants()
        } else if (message.type === "leave") {
            delete activeParticipants[message.user_id]
        }
    });

    localVideoStream.getTracks().forEach((track) => {
        peerConn.addTrack(track, localVideoStream);
    });
    
    negotiate();
}

function stop() {
    mainVideo.style.display = "none"
    mainVideo.srcObject = null;
    setupMenu.style.display = "flex"

    // close data channel
    if (dc) {
        dc.send(JSON.stringify({ type: "close", close: true }));
        dc.close();
    }

    // close transceivers
    if (peerConn?.getTransceivers) {
        peerConn.getTransceivers().forEach((transceiver) => {
            if (transceiver.stop) {
                transceiver.stop();
            }
        });
    }

    // // close local audio / video
    // peerConn.getSenders().forEach((sender) => {
    //     sender.track.stop();
    // });

    // close peer connection
    setTimeout(() => {
        console.log("close pc====", peerConn)
        peerConn.close();
    }, 500);
}






const switchMode = document.querySelector('button.mode-switch'),
  body = document.querySelector('body'),
  closeBtn = document.querySelector('.btn-close-right'),
  expandBtn = document.querySelector('.expand-btn');

switchMode.addEventListener('click', () => {
  body.classList.toggle('dark');
});
closeBtn.addEventListener('click', () => {
  rightSide.classList.remove('show');
  expandBtn.classList.add('show');
});
expandBtn.addEventListener('click', () => {
  rightSide.classList.add('show');
  expandBtn.classList.remove('show');
});


function addMessage(senderId, name, messageText, imageUrl) {
    const messageWrapper = document.createElement('div');
    messageWrapper.classList.add('message-wrapper');

    if (senderId === userId) {
        messageWrapper.classList.add('reverse');
    }

    if (senderId === prevMessageSender) {
        messageWrapper.classList.add('bundle');
    }

    const profilePictureDiv = document.createElement('div');
    profilePictureDiv.classList.add('profile-picture');

    const messageContentDiv = document.createElement('div');
    messageContentDiv.classList.add('message-content');

    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message');
    messageDiv.innerHTML = messageText;

    if (prevMessageSender != senderId) {
        // const profileImg = document.createElement('img');
        // profileImg.src = imageUrl;
        // profileImg.alt = '';
        // profilePictureDiv.appendChild(profileImg);

        profilePictureDiv.innerHTML = `<div class="participant profile-picture">${name[0].toUpperCase()}</div>`

        const nameP = document.createElement('p');
        nameP.classList.add('name');
        nameP.textContent = name;
        messageContentDiv.appendChild(nameP);
    }
    prevMessageSender = message.user_id

    messageContentDiv.appendChild(messageDiv);
    messageWrapper.appendChild(profilePictureDiv);
    messageWrapper.appendChild(messageContentDiv);

    chatArea.appendChild(messageWrapper);
    chatArea.scrollTop = chatArea.scrollHeight;
}
