from typing import Dict, Set

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: Dict[int, WebSocket] = {}
        self.group_connections: Dict[int, Set[int]] = {}

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: int) -> None:
        self.active_connections.pop(user_id, None)
        for group_id in list(self.group_connections.keys()):
            self.group_connections[group_id].discard(user_id)
            if not self.group_connections[group_id]:
                self.group_connections.pop(group_id, None)

    def join_group(self, user_id: int, group_id: int) -> None:
        self.group_connections.setdefault(group_id, set()).add(user_id)

    def leave_group(self, user_id: int, group_id: int) -> None:
        if group_id in self.group_connections:
            self.group_connections[group_id].discard(user_id)
            if not self.group_connections[group_id]:
                self.group_connections.pop(group_id, None)

    async def send_personal(self, user_id: int, message: dict) -> None:
        websocket = self.active_connections.get(user_id)
        if websocket:
            await websocket.send_json(message)

    async def send_group(self, group_id: int, message: dict) -> None:
        for member_id in self.group_connections.get(group_id, set()):
            await self.send_personal(member_id, message)
