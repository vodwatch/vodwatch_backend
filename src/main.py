import eventlet 
import socketio

from dict import PERMISSIONS_ADMIN, PERMISSIONS_USER

sio = socketio.Server(cors_allowed_origins='*')
app = socketio.WSGIApp(sio)

user_room_dict = dict()

@sio.event
def connect(sid, environ):
    print('connect ', sid)
    sio.enter_room(sid, 'room')
    return "OK"

@sio.event
def message(sid, data):
    print(sid, data)
    return "OK"

@sio.event
def send_video_event(sid, data):
    print(sid, data)
    sio.emit(event="receive_video_event", data=data['eventInfo'], room=data['myRoomId'], skip_sid=sid)
    return "OK"

@sio.event
def join_room(sid, roomId):
    print(sid, roomId)
    if(sio.manager.rooms.get("/").get(roomId) is None):
        return "ROOM_NOT_FOUND"    
    sio.enter_room(sid, roomId)
    user_room_dict[sid] = {
        'room': roomId
    }
    user_room_dict[sid]['permissions'] = PERMISSIONS_USER.copy()
    sio.emit(event='permissions', data={'permissions': user_room_dict[sid]['permissions']}, to=sid)
    return "OK"

@sio.event
def create_room(sid, roomId):
    print(sid, roomId)
    if(sio.manager.rooms.get("/").get(roomId) is not None): 
        return "ROOM_ALREADY_EXISTS"    
    sio.enter_room(sid, roomId)
    user_room_dict[sid] = {
        'room': roomId
    }
    user_room_dict[sid]['permissions'] = PERMISSIONS_ADMIN.copy()
    sio.emit(event='permissions', data={'permissions': user_room_dict[sid]['permissions']}, to=sid)
    return "OK"

@sio.event
def find_room_by_client(sid):
    if sid not in user_room_dict:
        return "ROOM_NOT_FOUND"
    return user_room_dict[sid]['room']

@sio.event
def disconnect(sid):
    print('disconnect ', sid)
    return "OK"

if __name__ == '__main__':
    eventlet.wsgi.server(eventlet.listen(('127.0.0.1', 5000)), app)