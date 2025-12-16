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

const newCall = document.querySelector('.new-call');
const callId = document.querySelector('.call-id');

// rightSide.classList.remove('show');

var userId = null

var chatData = [
    {
        id: Date.now(),
        sender: "Ryan Patrick",
        userId: "pc4",
        message: "Helloo team!😍",
        img: "https://images.unsplash.com/photo-1581824283135-0666cf353f35?ixlib=rb-1.2.1&auto=format&fit=crop&w=1276&q=80",
        timestamp: new Date().toISOString()
    },
    {
        id: Date.now(),
        sender: "Andy Will",
        userId: "pc4",
        message: "Hello! Can you hear me?🤯",
        img: "https://images.unsplash.com/photo-1566821582776-92b13ab46bb4?ixlib=rb-1.2.1&auto=format&fit=crop&w=900&q=60",
        timestamp: new Date().toISOString()
    },
    {
        id: Date.now(),
        sender: "Jessica Bell",
        userId: "pc4",
        message: "Hi team! Let's get started it.",
        img: "https://images.unsplash.com/photo-1600207438283-a5de6d9df13e?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=1234&q=80",
        timestamp: new Date().toISOString()
    },
    {
        id: Date.now(),
        sender: "Emmy Lou",
        userId: "pc4",
        message: "Good morning!🌈",
        img: "https://images.unsplash.com/photo-1500917293891-ef795e70e1f6?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=1650&q=80",
        timestamp: new Date().toISOString()
    },
    {
        id: Date.now(),
        sender: "Tim Russel",
        userId: "pc4",
        message: "New design document⬇️",
        img: "https://images.unsplash.com/photo-1576110397661-64a019d88a98?ixlib=rb-1.2.1&auto=format&fit=crop&w=1234&q=80",
        timestamp: new Date().toISOString()
    },
    {
        id: Date.now(),
        sender: "Ryan Patrick",
        userId: "pc4",
        message: "Hi team!❤️",
        img: "https://images.unsplash.com/photo-1581824283135-0666cf353f35?ixlib=rb-1.2.1&auto=format&fit=crop&w=1276&q=80",
        timestamp: new Date().toISOString()
    },
    {
        id: Date.now(),
        sender: "Emmy Lou",
        userId: "pc1",
        message: "Woooww! Awesome❤️",
        img: "https://images.unsplash.com/photo-1500917293891-ef795e70e1f6?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=1650&q=80",
        timestamp: new Date().toISOString()
    },
]

// connectButton.onclick = () => {
videoActionStartCall.onclick = () => {
	console.log("== connect")
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

newCall.onclick = () => {
    callId.value = randomString(5)
}
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
        iceServers: [{ urls: ['stun:stun.l.google.com:19302'] }],
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
            // localVideoMini.srcObject = stream

            // mainVideo.srcObject = stream
            menuVideo.srcObject = stream
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

    dc.addEventListener('open', () => {
        console.log("+++ datachannel on open")
        dc.send(JSON.stringify({ type: "name", name: "aaaa" }));
    });

    dc.addEventListener('message', (evt) => {
        message = JSON.parse(evt.data)
        console.log("+++ on message:", message)
        if (message.type === "user_id") {
            userId = message.user_id

            chatData.forEach(c => {
                addMessage(c.userId, c.sender, c.message, c.img)
            })
        }
        // console.log("dc <-", evt.data)
        // if (evt.data.substring(0, 4) === 'pong') {
            // var elapsed_ms = current_stamp() - parseInt(evt.data.substring(5), 10);
            // console.log("dc rtt", elapsed_ms)

        // }
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


const chatArea = document.querySelector('.chat-area');

function addMessage(senderId, name, messageText, imageUrl) {
    const chatArea = document.querySelector('.chat-area');
    const messageWrapper = document.createElement('div');
    messageWrapper.classList.add('message-wrapper');

    if (senderId === userId) {
        messageWrapper.classList.add('reverse');
    }

    const profilePictureDiv = document.createElement('div');
    profilePictureDiv.classList.add('profile-picture');

    const profileImg = document.createElement('img');
    profileImg.src = imageUrl;
    profileImg.alt = '';

    const messageContentDiv = document.createElement('div');
    messageContentDiv.classList.add('message-content');

    const nameP = document.createElement('p');
    nameP.classList.add('name');
    nameP.textContent = name;

    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message');
    messageDiv.innerHTML = messageText;

    profilePictureDiv.appendChild(profileImg);

    messageContentDiv.appendChild(nameP);     
    messageContentDiv.appendChild(messageDiv);

    messageWrapper.appendChild(profilePictureDiv);
    messageWrapper.appendChild(messageContentDiv);

    chatArea.appendChild(messageWrapper);
}
