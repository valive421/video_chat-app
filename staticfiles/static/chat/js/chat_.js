console.log("in main.js");

var username_label = document.querySelector("#usernamel");

var btnjoin = document.querySelector("#join-btn");

var username = username_label.innerHTML;
var websocket;
var map_peers = {};
config = {
    "iceServers": [
        {"urls": "stun:stun.l.google.com:19302"},
        {
            "urls": "turn:global.relay.metered.ca:80",
            "username": "0752578b1e5e4008875932ab",
            "credential": "GbAiImhyBdmMC300"
        }
    ]
}

function WebSocketonMessage(event) {
    var parsed_data = JSON.parse(event.data);
    console.log("WebSocket message received:", parsed_data);
    console.log("Current map_peers before processing message:", map_peers);

    var peername = parsed_data['peer'];
    var action = parsed_data['action'];

    if (peername === username) {
        return;
    }

    var receiver_channel_name = parsed_data['message']['receiver_channel_name'];

    if (action === 'new-peer') {
        createOffer(peername, receiver_channel_name);
    }
    if (action === 'new-offer') {
        var offer = parsed_data['message']['sdp'];
        createAnswer(offer, peername, receiver_channel_name);
    }
    if (action === "new-answer") {
        var answer = parsed_data["message"]["sdp"];
        var peer = map_peers[peername]?.[0];

        if (!peer) {
            console.error("Peer not found for", peername);
            return;
        }

        if (peer.signalingState !== "have-local-offer") {
            console.warn(`Cannot set remote description. Expected state: "have-local-offer", Found: "${peer.signalingState}"`);
            return;
        }

        peer.setRemoteDescription(new RTCSessionDescription(answer))
            .then(() => console.log("Remote description set successfully"))
            .catch(err => console.error("Failed to set remote description:", err));
    }

    console.log("Current map_peers after processing message:", map_peers);
}

var btn_sm = document.querySelector('#send_btn')
var message_list = document.querySelector("#message-list");
var msg_input = document.querySelector('#message_input')
btn_sm.addEventListener('click',sendmsgonclick)

function sendmsgonclick(){
        var message = msg_input.value
        var li = document.createElement('li')
        li.appendChild(document.createTextNode('me: '+message))
        message_list.appendChild(li)
        var dataChannels = getdatachannels()

        message = username +":"+ message
        for(index in dataChannels){
            dataChannels[index].send(message)
        }
        msg_input.innerHTML=""
}

btnjoin.addEventListener('click', () => {
    
    

   
    btnjoin.disabled = true;
    btnjoin.style.visibility = 'hidden';

    

    var loc = window.location;
    var ws = "ws://";
    if (loc.protocol === "https:") {
        ws = 'wss://';
    }
    var endpoint = ws + loc.host + loc.pathname;
    console.log(endpoint);
    console.log(endpoint);

    websocket = new WebSocket('ws://' + window.location.host + '/ws/chat/');
    console.log('ws://' + window.location.host + '/ws/chat/')

    websocket.addEventListener('open', (e) => {
        console.log("WebSocket connection opened");
        console.log("Initial map_peers:", map_peers);
        sendSignal("new-peer", {});
    });

    websocket.addEventListener('message', WebSocketonMessage);

    websocket.addEventListener('close', (e) => {
        console.log("WebSocket connection closed");
    });

    websocket.addEventListener('error', (e) => {
        console.log("WebSocket connection error");
    });
});

var localstream = new MediaStream();

const constraints = {
    audio: true,
    video: true, // Optional: Add video if needed
  };

var local_video = document.querySelector("#local_video");
var audio_toggle = document.querySelector('#btn_audio_mute');
var video_toggle = document.querySelector('#btn_video_mute');

navigator.mediaDevices.getUserMedia(constraints).then(
    stream => {
        localstream = stream;
        local_video.srcObject = localstream;
        local_video.muted = true;

        var audio_tracks = stream.getAudioTracks();
        var video_tracks = stream.getVideoTracks();

        audio_tracks[0].enabled = true;
        video_tracks[0].enabled = true;

        audio_toggle.addEventListener("click", () => {
            const audio_track = audio_tracks[0];
            if (audio_track) {
                audio_track.enabled = !audio_track.enabled;
                audio_toggle.innerHTML = audio_track.enabled ? "audio mute" : "audio unmute";
            }
        });

        video_toggle.addEventListener("click", () => {
            const video_track = video_tracks[0];
            if (video_track) {
                video_track.enabled = !video_track.enabled;
                video_toggle.innerHTML = video_track.enabled ? "video mute" : "video unmute";
            }
        });

    }
).catch(error => {
    console.log("Error accessing media devices:", error);
});

function sendSignal(action, message) {
    console.log("Sending signal:", { action, message });
    console.log("Current map_peers:", map_peers);
    var jsonstr = JSON.stringify({
        'peer': username,
        'action': action,
        'message': message
    });
    websocket.send(jsonstr);
}

function createOffer(p_name, rc_name) {
    if (map_peers[p_name]) {
        console.log(`Peer ${p_name} already exists in map_peers.`);
        return;
    }

    
    var peer = new RTCPeerConnection(config);
    

    peer.addEventListener("signalingstatechange", () => console.log("Signaling state:", peer.signalingState));
    peer.addEventListener("connectionstatechange", () => console.log("Connection state:", peer.connectionState));

    addLocalTrack(peer);

    var dc = peer.createDataChannel('channel');
    dc.addEventListener('open', () => console.log("Data channel opened"));
    dc.addEventListener('message', donMessage);

    var remotevideo = createVideo(p_name);
    setOnTrack(peer, remotevideo);

    map_peers[p_name] = [peer, dc];
    console.log("After adding peer in createOffer:", map_peers);

    peer.addEventListener("iceconnectionstatechange", () => {
        var iceconnectionstate = peer.iceConnectionState;
        if (iceconnectionstate === 'closed' || iceconnectionstate === 'failed' || iceconnectionstate === 'disconnected') {
            delete map_peers[p_name];
            console.log("After removing peer due to ICE state change:", map_peers);
            if (iceconnectionstate !== 'closed') {
                peer.close();
            }
            removeVideo(remotevideo);
        }
    });

    peer.addEventListener('icecandidate', (event) => {
        if (event.candidate) {
            sendSignal('new-offer', {
                'sdp': peer.localDescription,
                'receiver_channel_name': rc_name
            });
        }
    });

    peer.createOffer()
        .then(o => peer.setLocalDescription(o))
        .then(() => console.log("Local description set successfully"))
        .catch(err => console.error("Error creating or setting offer:", err));
}

function createAnswer(offer, p_name, receiver_channel_name) {
    
    var peer = new RTCPeerConnection(config);
    

    

    peer.addEventListener("signalingstatechange", () => console.log("Signaling state:", peer.signalingState));
    peer.addEventListener("connectionstatechange", () => console.log("Connection state:", peer.connectionState));

    addLocalTrack(peer);

    var remotevideo = createVideo(p_name);
    setOnTrack(peer, remotevideo);

    peer.addEventListener('datachannel', (e) => {
        peer.dc = e.channel;
        peer.dc.addEventListener('open', () => console.log("Data channel opened"));
        peer.dc.addEventListener('message', donMessage);
        map_peers[p_name] = [peer, peer.dc];
        console.log("After adding peer in createAnswer:", map_peers);
    });

    peer.addEventListener("iceconnectionstatechange", () => {
        var iceconnectionstate = peer.iceConnectionState;
        if (iceconnectionstate === 'closed' || iceconnectionstate === 'failed' || iceconnectionstate === 'disconnected') {
            delete map_peers[p_name];
            console.log("After removing peer due to ICE state change:", map_peers);
            if (iceconnectionstate !== 'closed') {
                peer.close();
            }
            removeVideo(remotevideo);
        }
    });

    peer.addEventListener('icecandidate', (event) => {
        if (event.candidate) {
            sendSignal('new-answer', {
                'sdp': peer.localDescription,
                'receiver_channel_name': receiver_channel_name
            });
        }
    });

    peer.setRemoteDescription(offer)
        .then(() => {
            console.log("Remote description set successfully for", p_name);
            return peer.createAnswer();
        })
        .then(answer => peer.setLocalDescription(answer))
        .then(() => {
            sendSignal('new-answer', {
                'sdp': peer.localDescription,
                'receiver_channel_name': receiver_channel_name
            });
        })
        .catch(err => console.error("Error setting remote description or creating answer:", err));
}

function addLocalTrack(peer) {
    localstream.getTracks().forEach(track => {
        peer.addTrack(track, localstream);
    });
}


function donMessage(event) {
    var message = event.data;
    var li = document.createElement('li');
    li.appendChild(document.createTextNode(message));
    message_list.appendChild(li);
}

function createVideo(p_name) {
    var videocontainer = document.querySelector('#video_container');
    var remotevideo = document.createElement('video');
    remotevideo.id = p_name + '-video';
    remotevideo.autoplay = true;
    remotevideo.playsInline = true;

    var videowrapper = document.createElement('div');
    videocontainer.appendChild(videowrapper);
    videowrapper.appendChild(remotevideo);

    return remotevideo;
}

function setOnTrack(peer, remotevideo) {
    peer.addEventListener('track', (event) => {
        console.log("Track event received:", event);
        if (event.track.kind === 'video') {
            remotevideo.srcObject = event.streams[0];
        }
    });
}

function removeVideo(remotevideo) {
    remotevideo.parentElement.remove();
    remotevideo.remove();
}
function getdatachannels(){
    var dataChannels = []
    for(peername in map_peers){
        var datachannel = map_peers[peername][1];
        dataChannels.push(datachannel)
    }
    return dataChannels
}