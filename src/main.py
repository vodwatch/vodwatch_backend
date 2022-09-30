from datetime import datetime, timedelta
import eventlet
import os
import socketio

from dict import PERMISSIONS_ADMIN, PERMISSIONS_USER
from helper import generate_random_uuid, get_room_id_by_sid

sio = socketio.Server(cors_allowed_origins='https://www.netflix.com')
app = socketio.WSGIApp(sio)

room_dict = dict()

# key: room id
# value: datetime from last event that occurred in the room
room_last_event_datetime_dict = dict() 

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

    # check if user has chat permissions
    if room_dict[my_room_id][sid]['permissions']['chat'] == False:
        return "OPERATION_NOT_ALLOWED"

    sio.emit(
        event="receive_message",
        data={
            'from': sid,
            'content': message,
        },
        room=my_room_id,
        skip_sid=sid,
    )
    room_last_event_datetime_dict[my_room_id] = datetime.now()
    return "OK"


@sio.event
def send_video_event(sid, eventInfo):
    print(sid, eventInfo)
    my_room_id = get_room_id_by_sid(sid, room_dict)
    if my_room_id == "ROOM_NOT_FOUND":
        return "ROOM_NOT_FOUND"
    sio.emit(event="receive_video_event", data=eventInfo, room=my_room_id, skip_sid=sid)
    room_last_event_datetime_dict[my_room_id] = datetime.now()
    return "OK"


@sio.event
def join_room(sid, room_id):
    print(sid, room_id)
    if room_id not in room_dict:
        return "ROOM_NOT_FOUND"

    sio.enter_room(sid, room_id)
    
    room_dict[room_id][sid] = {}
    room_dict[room_id][sid]['permissions'] = PERMISSIONS_USER.copy()
    
    print(room_dict[room_id])
    sio.emit(event='permissions', data=room_dict[room_id], room=room_id)
    room_last_event_datetime_dict[room_id] = datetime.now()
    return "OK"


@sio.event
def create_room(sid):
    room_id = generate_random_uuid()
    if room_id in room_dict:
        return "ROOM_ALREADY_EXISTS"
    
    sio.enter_room(sid, room_id)
    
    room_dict[room_id] = {}
    room_dict[room_id] = {
        sid: {}
    }
    room_dict[room_id][sid]['permissions'] = PERMISSIONS_ADMIN.copy()
    sio.emit(event='permissions', data=room_dict[room_id], room=room_id)
    room_last_event_datetime_dict[room_id] = datetime.now()
    return room_id


@sio.event
def set_users_permissions(sid, user_permissions):
    my_room_id = get_room_id_by_sid(sid, room_dict)
    if my_room_id == "ROOM_NOT_FOUND":
        return "ROOM_NOT_FOUND"
    
    sid_server_permissions = room_dict[my_room_id][sid]['permissions']
    sid_received_permissions = user_permissions[sid]['permissions']
    
    # check if user is admin
    if sid_server_permissions != PERMISSIONS_ADMIN:
        sio.emit(event='permissions', data=room_dict[my_room_id], room=my_room_id)
        return "OPERATION_NOT_ALLOWED"
    
    # prevent user from changing his own permissions
    if sid_server_permissions != sid_received_permissions:
        sio.emit(event='permissions', data=room_dict[my_room_id], room=my_room_id)
        return "OPERATION_NOT_ALLOWED"

    room_dict[my_room_id] = user_permissions
    sio.emit(event='permissions', data=room_dict[my_room_id], room=my_room_id)
    room_last_event_datetime_dict[my_room_id] = datetime.now()
    return "OK"


@sio.event
def kick_user(my_sid, kicked_user_sid):
    # prevent user from kicking himself
    if my_sid == kicked_user_sid:
        sio.emit(event='permissions', data=room_dict[room_id], room=room_id)
        return "OPERATION_NOT_ALLOWED"

    # find room id of user to be kicked
    room_id = get_room_id_by_sid(kicked_user_sid, room_dict)
    if room_id == "ROOM_NOT_FOUND":
        sio.emit(event='permissions', data=room_dict[room_id], room=room_id)
        return "ROOM_NOT_FOUND"

    # check if user has kick permissions
    if room_dict[room_id][my_sid]['permissions']['kick'] == False:
        sio.emit(event='permissions', data=room_dict[room_id], room=room_id)
        return "OPERATION_NOT_ALLOWED"
    
    # prevent user from kicking room admin
    if room_dict[room_id][kicked_user_sid]['permissions'] == PERMISSIONS_ADMIN:
        sio.emit(event='permissions', data=room_dict[room_id], room=room_id)
        return "OPERATION_NOT_ALLOWED"
    
    
    del room_dict[room_id][kicked_user_sid]
    sio.emit(event='permissions', data=room_dict[room_id], room=room_id)
    sio.disconnect(kicked_user_sid)
    room_last_event_datetime_dict[room_id] = datetime.now()
    return "OK"
    

@sio.event
def disconnect(sid):
    print('disconnect ', sid)
    my_room_id = get_room_id_by_sid(sid, room_dict)
    if my_room_id == "ROOM_NOT_FOUND":
        return "OK"
    else:
        # remove user from a dict and update permissions
        del room_dict[my_room_id][sid]
        sio.emit(event='permissions', data=room_dict[my_room_id], room=my_room_id)
        room_last_event_datetime_dict[my_room_id] = datetime.now()
        return "OK"

# this event should only be triggered
# by external scheduler that will be responsible
# for deleting inactive rooms periodically
@sio.event
def remove_inactive_rooms(sid):
    max_room_inactivity_time_minutes = 1
    for room_id in room_last_event_datetime_dict:
        last_event_datetime = room_last_event_datetime_dict[room_id]
        is_room_inactive = datetime.now() - last_event_datetime > timedelta(minutes=max_room_inactivity_time_minutes)
        if is_room_inactive:
            # kick all users in the room and delete room
            for user_id in room_dict[room_id]:
                kick_user(sid=sid, kicked_user_sid=user_id)
            del room_dict[room_id]


if __name__ == '__main__':
    eventlet.wsgi.server(eventlet.listen(('', int(os.environ.get('PORT', '5000')))), app)
