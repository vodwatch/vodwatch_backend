import uvicorn
from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

class EventInfo(BaseModel):
    event: str
    currentTime: float

origins = ["*"]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return { "message": "Hello World" }

@app.post("/eventInfo/")
def write_event_info(event_info: EventInfo):
    print("event type: " + event_info.event)
    print("current time: " + event_info.currentTime)
    return event_info


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
