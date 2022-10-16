import threading
import time

import schedule
import socketio


class RoomCleanerScheduler(threading.Thread):

    def __init__(self, thread_id):
        threading.Thread.__init__(self)
        self.sio = socketio.Client()
        self.thread_id = thread_id

    def run(self):
        print("Starting thread: " + str(self.thread_id))
        print("Connecting with server ...")
        self.sio.connect(url="http://localhost:5000", wait_timeout=10)
        schedule.every(1).minutes.do(self.__job)
        while True:
            schedule.run_pending()
            time.sleep(1)

    def __job(self):
        print("Attempting to remove inactive rooms")
        self.sio.emit("remove_inactive_rooms")
