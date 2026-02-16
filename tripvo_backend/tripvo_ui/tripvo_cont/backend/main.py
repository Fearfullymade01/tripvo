
# --- Imports ---
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Set
from uuid import uuid4
from datetime import datetime, timedelta
from threading import Timer


# --- App and Data Model ---
# import django_notify  # Disabled for tests
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import Request
from fastapi.exception_handlers import request_validation_exception_handler

app = FastAPI()

# Custom handler to log validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print("Validation error:", exc, flush=True)
    return await request_validation_exception_handler(request, exc)

class PollOption(BaseModel):
    id: str
    text: str
    votes: int = 0

class Poll(BaseModel):
    id: str
    question: str
    options: List[PollOption]
    deadline: Optional[datetime] = None
    creator: Optional[str] = None
    is_closed: bool = False
    votes_by_user: Dict[str, str] = Field(default_factory=dict)  # user_id -> option_id

# In-memory poll storage (replace with DB in production)
polls: Dict[str, Poll] = {}

# --- WebSocket Manager for Real-Time Updates ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, poll_id: str, websocket: WebSocket):
        await websocket.accept()
        # Special channel for all-poll notifications
        if poll_id not in self.active_connections:
            self.active_connections[poll_id] = set()
        self.active_connections[poll_id].add(websocket)

    def disconnect(self, poll_id: str, websocket: WebSocket):
        if poll_id in self.active_connections:
            self.active_connections[poll_id].discard(websocket)
            if not self.active_connections[poll_id]:
                del self.active_connections[poll_id]

    async def broadcast(self, poll_id: str, message: dict):
        if poll_id in self.active_connections:
            for connection in list(self.active_connections[poll_id]):
                try:
                    await connection.send_json(message)
                except Exception:
                    self.disconnect(poll_id, connection)

    async def broadcast_global(self, message: dict):
        # Broadcast to all connections for all polls
        for connections in self.active_connections.values():
            for connection in list(connections):
                try:
                    await connection.send_json(message)
                except Exception:
                    # Remove dead connection from all sets
                    for poll_id in self.active_connections:
                        self.disconnect(poll_id, connection)

manager = ConnectionManager()

# --- Poll Closing Logic ---
def schedule_poll_close(poll_id: str, deadline: datetime):
    now = datetime.utcnow()
    delay = (deadline - now).total_seconds()
    if delay > 0:
        Timer(delay, close_poll_by_id, args=[poll_id]).start()

def close_poll_by_id(poll_id: str):
    poll = polls.get(poll_id)
    if poll and not poll.is_closed:
        poll.is_closed = True
        import asyncio
        asyncio.create_task(manager.broadcast(poll_id, {"event": "poll_closed", "poll": poll.dict()}))
        asyncio.create_task(manager.broadcast_global({"event": "poll_closed", "poll_id": poll_id, "poll": poll.dict()}))

# Schedule auto-close for polls with deadlines
for poll in polls.values():
    if poll.deadline and not poll.is_closed:
        schedule_poll_close(poll.id, poll.deadline)

# --- Endpoints ---
@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI backend!"}

class PollCreateRequest(BaseModel):
    question: str
    options: List[str]
    deadline: Optional[datetime] = None
    creator: Optional[str] = None

@app.post("/polls")
def create_poll(poll_req: PollCreateRequest):
    poll_id = str(uuid4())
    poll_options = [PollOption(id=str(uuid4()), text=opt) for opt in poll_req.options]
    poll = Poll(
        id=poll_id,
        question=poll_req.question,
        options=poll_options,
        deadline=poll_req.deadline,
        creator=poll_req.creator,
        is_closed=False,
    )
    polls[poll_id] = poll
    # Schedule auto-close if deadline is set
    if poll.deadline:
        schedule_poll_close(poll_id, poll.deadline)
    # Notify all clients about new poll
    import asyncio
    asyncio.create_task(manager.broadcast_global({"event": "new_poll", "poll": poll.dict()}))
    return poll

class PollVoteRequest(BaseModel):
    user_id: str
    option_id: str

@app.post("/polls/{poll_id}/vote")
def vote_poll(poll_id: str, vote_req: PollVoteRequest):
    poll = polls.get(poll_id)
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")
    if poll.is_closed:
        raise HTTPException(status_code=400, detail="Poll is closed")
    if vote_req.user_id in poll.votes_by_user:
        raise HTTPException(status_code=400, detail="User has already voted")
    # Find option
    option = next((opt for opt in poll.options if opt.id == vote_req.option_id), None)
    if not option:
        raise HTTPException(status_code=404, detail="Option not found")
    option.votes += 1
    poll.votes_by_user[vote_req.user_id] = option.id
    # Broadcast updated poll to all WebSocket clients
    import asyncio
    asyncio.create_task(manager.broadcast(poll_id, {"poll": poll.dict()}))
    return {"success": True, "poll": poll}

@app.get("/polls/{poll_id}")
def get_poll(poll_id: str):
    poll = polls.get(poll_id)
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")
    return poll

@app.post("/polls/{poll_id}/close")
def close_poll(poll_id: str):
    poll = polls.get(poll_id)
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")
    if poll.is_closed:
        raise HTTPException(status_code=400, detail="Poll already closed")
    poll.is_closed = True
    import asyncio
    asyncio.create_task(manager.broadcast(poll_id, {"poll": poll.dict()}))
    asyncio.create_task(manager.broadcast_global({"event": "poll_closed", "poll_id": poll_id, "poll": poll.dict()}))
    # Notify Django backend
    # try:
    #     django_notify.notify_django_poll_event("closed", poll.dict())
    # except Exception as e:
    #     print(f"Django notification failed: {e}")
    return {"success": True, "poll": poll}

@app.websocket("/ws/polls/{poll_id}")
async def poll_ws(websocket: WebSocket, poll_id: str):
    await manager.connect(poll_id, websocket)
    try:
        while True:
            await websocket.receive_text()  # Keep connection alive
    except WebSocketDisconnect:
        manager.disconnect(poll_id, websocket)
