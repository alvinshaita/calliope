# Calliope
Calliope is a real-time, browser based video conferencing application. It is built with **WebRTC**, **Python (aiohttp + aiortc)**, and **vanilla JavaScript**

It supports multi-participant video calls, live audio, chat messaging, participant lists, and **server-side video compositing**, all without relying on external media servers.

This project demonstrates modern real-time communication concepts including signaling, ICE negotiation, media streaming, and scalable architecture.

## Overview
Calliope allows two or more users to establish a **direct real-time communication** for video and audio communication using **WebRTC**.

A lightweight **signaling server** is used to exchange connection metadata (SDP offers/answers and ICE candidates), after which all media flows **peer-to-peer**, minimizing server load and latency.

## Features

- Real-time video & audio calls using WebRTC
- Multi-participant rooms via shared call IDs
- Server-side video compositing
  - Dynamic grid layout
  - Automatic resizing
  - Participant name overlays
- Chat messaging via WebRTC DataChannels
- Live participant list
- Light / Dark mode UI
- STUN & TURN support for NAT traversal
- Microphone mute / unmute
- Camera on / off

## Tech Stack
### Backend
- Python
- aiohttp - asynchronous HTTP server
- aiortc - WebRTC implementation
- OpenCV - video frame processing
- av — media frame handling

### Frontend
- HTML5 / CSS3
- JavaScript
- WebRTC Browser APIs


## Architecture Overview
Calliope follows a **server-assisted WebRTC architecture** where the server performs media processing instead of acting purely as a signaling layer.

```
Browser (WebRTC)
   ↕ SDP / ICE
aiohttp Server
   ├── RTCPeerConnection (aiortc)
   ├── MediaRelay
   ├── Composite Video Track
   └── DataChannels (chat, presence)
```
- Each participant connects using a call ID
- Video tracks are received server-side
- Frames are combined into a dynamic grid
- Final composited video is sent back to clients
- Audio streams are relayed via the server
- Chat & presence use WebRTC DataChannels

## Getting Started
### Clone the Repository
```
git clone https://github.com/alvinshaita/calliope.git
cd calliope
```

### Install Dependencies
```
pip install -r requirements.txt
```

Note:
`aiortc` requires FFmpeg.
On Ubuntu:

`sudo apt install ffmpeg`

### Run the Server
`python app.py`
Server will be accessible at:
`http://0.0.0.0:8050`

## Networking
Calliope uses:
- Google STUN
- OpenRelay TURN (for restrictive networks)
```
iceServers: [
  { urls: 'stun:stun.l.google.com:19302' },
  {
    urls: 'turn:openrelay.metered.ca:443',
    username: 'openrelayproject',
    credential: 'openrelayproject'
  }
]
```
## Implementation Details
### Server-Side Video Mixing
- Frames are received from all peers
- Automatically arranged into a grid
- Names are rendered directly onto frames
- Output is sent as a single video stream
