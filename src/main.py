import eventlet
import os
import socketio

from dict import PERMISSIONS_ADMIN, PERMISSIONS_USER

sio = socketio.Server(cors_allowed_origins='https://www.netflix.com')
app = socketio.WSGIApp(sio)

room_dict = dict()

@sio.event
def connect(sid, environ):
    print('connect ', sid)
    sio.enter_room(sid, 'room')
    return "OK"


@sio.event
def send_message(sid, data):
    if data['roomId'] not in room_dict:
        return "ROOM_NOT_FOUND"
    sio.emit(

        event="receive_message",
        data={
            'from': sid,
            'content': data['message']
        },
        room=data['roomId'],
        skip_sid=sid,
    )

    return "OK"


@sio.event
def send_video_event(sid, data):
    print(sid, data)
    sio.emit(event="receive_video_event", data=data['eventInfo'], room=data['roomId'], skip_sid=sid)
    return "OK"


@sio.event
def join_room(sid, roomId):
    print(sid, roomId)
    if roomId not in room_dict:
        return "ROOM_NOT_FOUND"

    sio.enter_room(sid, roomId)
    
    room_dict[roomId][sid] = {}
    room_dict[roomId][sid]['permissions'] = PERMISSIONS_USER.copy()
    sio.emit(event='permissions', data=room_dict[roomId])
    return "OK"


@sio.event
def create_room(sid, roomId):
    print(sid, roomId)
    if roomId in room_dict:
        return "ROOM_ALREADY_EXISTS"
    
    sio.enter_room(sid, roomId)
    
    room_dict[roomId] = {
        sid: {}
    }
    room_dict[roomId][sid]['permissions'] = PERMISSIONS_ADMIN.copy()
    sio.emit(event='permissions', data=room_dict[roomId])
    return "OK"


@sio.event
def find_all_users_in_room(sid, roomId):
    if room_dict[roomId] is None:
        return "ROOM_NOT_FOUND"
    return room_dict[roomId]


@sio.event
def set_users_permissions(sid, data):
    print(data)
    roomId = data["roomId"]
    userPermissions = data["userPermissions"]
    if room_dict[roomId] is None:
        return "ROOM_NOT_FOUND"
    room_dict[roomId] = userPermissions
    sio.emit(event='permissions', data=room_dict[roomId])
    return "OK"

@sio.event
def disconnect(sid):
    print('disconnect ', sid)
    return "OK"


if __name__ == '__main__':
    eventlet.wsgi.server(eventlet.listen(('', int(os.environ.get('PORT', '5000')))), app)
