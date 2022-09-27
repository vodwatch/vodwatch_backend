import uuid

def get_room_id_by_sid(sid, room_dict):
    for roomId in room_dict:
        for userId in room_dict[roomId]:
            if sid == userId:
                return roomId
    return "ROOM_NOT_FOUND"

def generate_random_uuid():
    return str(uuid.uuid4())[0:5].upper()
    