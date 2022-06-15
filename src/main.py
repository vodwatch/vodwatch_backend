import eventlet
import socketio

sio = socketio.Server(cors_allowed_origins='*')
app = socketio.WSGIApp(sio)

@sio.event
def connect(sid, environ):
    print('connect ', sid)
    return "OK"

@sio.event
def message(sid, data):
    print(sid, data)
    return "OK"

@sio.event
def send_video_event(sid, data):
    print(data)
    sio.emit(event="receive_video_event", data=data)
    return "OK"

@sio.event
def disconnect(sid):
    print('disconnect ', sid)
    return "OK"

if __name__ == '__main__':
    eventlet.wsgi.server(eventlet.listen(('127.0.0.1', 5000)), app)
