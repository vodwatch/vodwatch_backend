import eventlet
import os
import socketio

from dict import PERMISSIONS_ADMIN, PERMISSIONS_USER
from helper import generate_random_uuid, get_room_id_by_sid

sio = socketio.Server(cors_allowed_origins='https://www.netflix.com')
app = socketio.WSGIApp(sio)

room_dict = dict()

@sio.event
def connect(sid, environ):
    print('connect ', sid)
    sio.enter_room(sid, 'room')
    return "OK"


@sio.event
def send_message(sid, message):
    my_room_id = get_room_id_by_sid(sid, room_dict)
    if my_room_id == "ROOM_NOT_FOUND":
        return "ROOM_NOT_FOUND"
    sio.emit(
        event="receive_message",
        data={
            'from': sid,
            'content': message,
        },
        room=my_room_id,
        skip_sid=sid,
    )

    return "OK"


@sio.event
def send_video_event(sid, eventInfo):
    print(sid, eventInfo)
    my_room_id = get_room_id_by_sid(sid, room_dict)
    if my_room_id == "ROOM_NOT_FOUND":
        return "ROOM_NOT_FOUND"
    sio.emit(event="receive_video_event", data=eventInfo, room=my_room_id, skip_sid=sid)
    return "OK"


@sio.event
def join_room(sid, room_id):
    print(sid, room_id)
    if room_id not in room_dict:
        return "ROOM_NOT_FOUND"

    sio.enter_room(sid, room_id)
    
    room_dict[room_id][sid] = {}
    room_dict[room_id][sid]['permissions'] = PERMISSIONS_USER.copy()
    sio.emit(event='permissions', data=room_dict[room_id])
    return "OK"


@sio.event
def create_room(sid):
    room_id = generate_random_uuid();
    if room_id in room_dict:
        return "ROOM_ALREADY_EXISTS"
    
    sio.enter_room(sid, room_id)
    
    room_dict[room_id] = {
        sid: {}
    }
    room_dict[room_id][sid]['permissions'] = PERMISSIONS_ADMIN.copy()
    sio.emit(event='permissions', data=room_dict[room_id])
    return room_id


@sio.event
def set_users_permissions(sid, user_permissions):
    print(user_permissions)
    my_room_id = get_room_id_by_sid(sid, room_dict)
    if my_room_id == "ROOM_NOT_FOUND":
        return "ROOM_NOT_FOUND"
    
    room_dict[my_room_id] = user_permissions
    sio.emit(event='permissions', data=room_dict[my_room_id])
    return "OK"

@sio.event
def disconnect(sid):
    print('disconnect ', sid)
    my_room_id = get_room_id_by_sid(sid, room_dict)
    if my_room_id == "ROOM_NOT_FOUND":
        return "OK"
    else:
        # remove user from a dict and update permissions
        room_dict[my_room_id][sid] = {}
        sio.emit(event='permissions', data=room_dict[my_room_id]) #TODO: send only to specific room
        return "OK"

if __name__ == '__main__':
    eventlet.wsgi.server(eventlet.listen(('', int(os.environ.get('PORT', '5000')))), app)
