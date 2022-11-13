from datetime import datetime, timedelta
import eventlet
import os
import socketio

from dict import PERMISSIONS_ADMIN, PERMISSIONS_USER
from helper import generate_random_uuid, get_room_id_by_sid

sio = socketio.Server(cors_allowed_origins=['http://localhost:5000', 'https://www.netflix.com', 'https://play.hbomax.com', 'https://www.youtube.com'])
app = socketio.WSGIApp(sio)

room_dict = dict()

# key: room id
# value: datetime from last event that occurred in the room
room_last_event_datetime_dict = dict()

# timestamp for last room clean attempt
last_cleaning_attempt_timestamp = datetime.now()


@sio.event
def connect(sid, environ):
    return "OK"


@sio.event
def send_message(sid, message):
    my_room_id = get_room_id_by_sid(sid, room_dict)
    if my_room_id == "ROOM_NOT_FOUND":
        return "ROOM_NOT_FOUND"

    # check if user has chat permissions
    if not room_dict[my_room_id][sid]['permissions']['chat']:
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
def send_video_event(sid, event_info):
    print(sid, event_info)
    my_room_id = get_room_id_by_sid(sid, room_dict)
    if my_room_id == "ROOM_NOT_FOUND":
        return "ROOM_NOT_FOUND"
    sio.emit(event="receive_video_event", data=event_info, room=my_room_id, skip_sid=sid)
    room_last_event_datetime_dict[my_room_id] = datetime.now()
    return "OK"


@sio.event
def join_room(sid, room_id, streaming_platform, video_id, video_title):
    print(sid, room_id, streaming_platform, video_id, video_title)

    if room_id not in room_dict:
        return "ROOM_NOT_FOUND" 

    if not check_if_the_same_video_played_in_room(room_id, streaming_platform, video_id, video_title):
        return "VIDEO_NOT_MATCHING"

    sio.enter_room(sid, room_id)

    room_dict[room_id][sid] = {}
    room_dict[room_id][sid]['permissions'] = PERMISSIONS_USER.copy()

    print(room_dict[room_id])
    sio.emit(event='permissions', data=room_dict[room_id], room=room_id)
    room_last_event_datetime_dict[room_id] = datetime.now()
    try_to_remove_inactive_rooms()
    return "OK"


@sio.event
def create_room(sid, streaming_platform, video_id, video_title):
    print(sid, streaming_platform, video_id, video_title)
    room_id = generate_random_uuid()
    if room_id in room_dict:
        return "ROOM_ALREADY_EXISTS"

    sio.enter_room(sid, room_id)

    room_dict[room_id] = {}
    room_dict[room_id] = {
        sid: {}
    }
    room_dict[room_id][sid]['permissions'] = PERMISSIONS_ADMIN.copy()
    room_dict[room_id]['videoInfo'] = { 'streamingPlatform': streaming_platform, 'videoId': video_id, 'videoTitle': video_title }
    sio.emit(event='permissions', data=room_dict[room_id], room=room_id)
    room_last_event_datetime_dict[room_id] = datetime.now()
    try_to_remove_inactive_rooms()
    return room_id


@sio.event
def set_users_permissions(sid, user_permissions):
    my_room_id = get_room_id_by_sid(sid, room_dict)
    if my_room_id == "ROOM_NOT_FOUND":
        return "ROOM_NOT_FOUND"

    # prevent user from changing his own permissions
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
def kick_user(my_sid, kicked_user_sid, is_room_cleaner=False):
    # find room id of user to be kicked
    room_id = get_room_id_by_sid(kicked_user_sid, room_dict)
    if room_id == "ROOM_NOT_FOUND":
        sio.emit(event='permissions', data=room_dict[room_id], room=room_id)
        return "ROOM_NOT_FOUND"

    if not is_room_cleaner:
        # prevent user from kicking himself
        if my_sid == kicked_user_sid:
            sio.emit(event='permissions', data=room_dict[room_id], room=room_id)
            return "OPERATION_NOT_ALLOWED"

        # check if user has kick permissions
        if not room_dict[room_id][my_sid]['permissions']['kick']:
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


def try_to_remove_inactive_rooms():
    print("attempting to clear rooms")
    global last_cleaning_attempt_timestamp
    max_time_from_last_attempt_minutes = 30
    should_be_cleaned = datetime.now() - last_cleaning_attempt_timestamp > timedelta(
        minutes=max_time_from_last_attempt_minutes)
    if should_be_cleaned:
        remove_inactive_rooms()
        last_cleaning_attempt_timestamp = datetime.now()


def remove_inactive_rooms():
    max_room_inactivity_time_hours = 3
    for room_id in list(room_last_event_datetime_dict.keys()):
        last_event_datetime = room_last_event_datetime_dict[room_id]
        is_room_inactive = datetime.now() - last_event_datetime > timedelta(hours=max_room_inactivity_time_hours)
        if is_room_inactive:
            # kick all users in the room and delete room
            print("Deleting room: " + room_id + " due to inactivity!")
            for user_id in list(room_dict[room_id].keys()):
                kick_user(my_sid=None, kicked_user_sid=user_id, is_room_cleaner=True)
            del room_dict[room_id]
            del room_last_event_datetime_dict[room_id]


def check_if_the_same_video_played_in_room(room_id, streaming_platform, video_id, video_title):
    if room_id in room_dict:
        if room_dict[room_id]['videoInfo']['streamingPlatform'] == streaming_platform and \
                room_dict[room_id]['videoInfo']['videoId'] == video_id:
            return True
        elif room_dict[room_id]['videoInfo']['streamingPlatform'] in ['Netflix', "HBO Max"] and \
                streaming_platform in ['Netflix', "HBO Max"] and \
                room_dict[room_id]['videoInfo']['videoTitle'] == video_title:
            return True
        elif streaming_platform == "YouTube":
            return True
    return False


if __name__ == '__main__':
    eventlet.wsgi.server(eventlet.listen(('', int(os.environ.get('PORT', '5000')))), app)
