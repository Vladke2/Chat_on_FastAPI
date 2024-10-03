from fastapi import WebSocket, WebSocketDisconnect, WebSocketException
from typing import List, Dict
from authorization.endpoint import *


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


class ConnectionManagerForRoom:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room: str):
        await websocket.accept()
        if room not in self.active_connections:
            self.active_connections[room] = []
        self.active_connections[room].append(websocket)

    def disconnect(self, websocket: WebSocket, room: str):
        self.active_connections[room].remove(websocket)
        if len(self.active_connections[room]) == 0:
            del self.active_connections[room]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str, room: str):
        if room in self.active_connections:
            for connection in self.active_connections[room]:
                await connection.send_text(message)


manager_for_room = ConnectionManagerForRoom()


@app.websocket("/ws/global_chat/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise WebSocketException(code=status.WS_1013_TRY_AGAIN_LATER)
    await manager.connect(websocket)
    try:
        await manager.broadcast(f"Користувач {user.username} приєднався до чату!")
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"{user.username}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"{user.username} left the chat")


@app.websocket("/ws/{room}/{username}")
async def websocket_endpoint(websocket: WebSocket, room: str, username: str):
    await manager_for_room.connect(websocket, room)
    try:

        await manager_for_room.broadcast(f"{username} приєднався до кімнати.", room)
        while True:
            data = await websocket.receive_text()
            await manager_for_room.broadcast(f"{username}: {data}", room)
    except WebSocketDisconnect:
        manager_for_room.disconnect(websocket, room)
        await manager_for_room.broadcast(f"{username} покинув кімнату {room}.", room)


@app.get('/helo_world')
def helo_world():
    return {'message': 'helo_world'}
