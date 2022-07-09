import pytest
import socketio

PORT = 5000
ADDR = "127.0.0.1"
BASE_URL = f"http://{ADDR}:{PORT}"


def test_connect():
    client = socketio.Client()
    client.connect(BASE_URL)
    assert client.connected
    client.disconnect()

def test_connect_response():
    client = socketio.Client()
    client.connect(BASE_URL)
    assert client.call("connect", {"data": "test"}) == "OK"
    client.disconnect()

def test_disconnect():
    client = socketio.Client()
    client.connect(BASE_URL)
    assert client.connected
    client.disconnect()
    assert not client.connected

def test_disconnect_response():
    client = socketio.Client()
    client.connect(BASE_URL)
    assert client.connected
    assert client.call("disconnect") == "OK"
    client.disconnect()

def test_message():
    client = socketio.Client()
    client.connect(BASE_URL)
    assert client.call("message", {"message": "message"}) == "OK"
    client.disconnect()

def test_send_video_event():
    client = socketio.Client()
    client.connect(BASE_URL)
    client.emit("send_video_event", { "event": "eventInfo", "currentTime": "time"})
    assert client.on("recive_video_event")
    client.disconnect()

def test_send_video_event_response():
    client = socketio.Client()
    client.connect(BASE_URL)
    assert client.call("send_video_event", { "event": "eventInfo", "currentTime": "time"}) == "OK"
    client.disconnect()