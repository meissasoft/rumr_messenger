from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, List
from sqlmodel import Session, select
import json
from datetime import datetime, timezone

from app.database import get_db
from app.models.message import Message
from app.models.conversation import Conversation
from app.models.conversation_participant import ConversationParticipant
from app.models.blocked_user import BlockedUser, check_block_status
from app.core.connection_manager import ConnectionManager
router = APIRouter()


# Track all connections with an instance of the manager
manager = ConnectionManager()

# Helper function to check if one user has blocked another
def check_block_status(db: Session, blocker_id: str, blocked_id: str) -> bool:
    """Check if blocker_id has blocked blocked_id"""
    block = db.exec(
        select(BlockedUser).where(
            BlockedUser.blocker_id == blocker_id,
            BlockedUser.blocked_id == blocked_id
        )
    ).first()
    return block is not None

def save_message(db: Session, conversation_id: str, sender_id: str, content: str, msg_type: str = "text") -> Message:
    """Save a message to the database and return the created message"""
    message = Message(
        conversation_id=conversation_id,
        sender_id=sender_id,
        content=content,
        type=msg_type,
        status=True,
        created_at=datetime.now(timezone.utc)
    )
    db.add(message)
    # Commit only once, don't refresh immediately
    db.commit()
    # Removed db.refresh(message) here
    db.refresh(message)
    return message

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    user_id: str, 
    db: Session = Depends(get_db)
):
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            # Receive message
            data_str = await websocket.receive_text()
            
            try:
                # Parse message data
                data = json.loads(data_str)
                conversation_id = data.get("conversation_id")
                content = data.get("content", "")
                msg_type = data.get("type", "text")
                
                # Verify conversation exists and user is a participant
                participant = db.exec(
                    select(ConversationParticipant).where(
                        ConversationParticipant.conversation_id == conversation_id,
                        ConversationParticipant.user_id == user_id,
                        ConversationParticipant.deleted == False
                    )
                ).first()
                conversation_owner = db.exec(
                    select(Conversation).where(
                        Conversation.id == conversation_id,
                    )
                ).first()
                # Check for blocks between users
                sender_blocked_owner = check_block_status(db, user_id, conversation_owner.user_id)
                owner_blocked_sender = check_block_status(db, conversation_owner.user_id, user_id)
                
                if not participant:
                    await websocket.send_json({
                        "status": "error",
                        "message": "Not a participant in this conversation"
                    })
                    continue
                if sender_blocked_owner or owner_blocked_sender:
                    await websocket.send_json({
                        "status": "error",
                        "message": "You are blocked by the conversation owner or you have blocked them"
                    })
                    continue

                
                
                # Save message to database
                message = save_message(db, conversation_id, user_id, content, msg_type)
                
                # Prepare message data for broadcasting
                message_data = {
                    "id": message.id,
                    "sender_id": user_id,
                    "content": content,
                    "type": msg_type,
                    "created_at": message.created_at.isoformat(),
                    "conversation_id": conversation_id
                }
                
                # Broadcast to other participants
                response = await manager.broadcast_to_conversation(
                    message_data, conversation_id, user_id, db
                )
                
                # # Send success acknowledgment to sender
                # await websocket.send_json({
                #     "id": message.id,
                #     "sender_id": user_id,
                #     "content": content,
                #     "type": msg_type,
                #     "created_at": message.created_at.isoformat(),
                #     "conversation_id": conversation_id,
                #     "delivered": True,
                # })
                
            except json.JSONDecodeError:
                await websocket.send_json({
                    "status": "error",
                    "message": "Invalid JSON format"
                })
            except KeyError:
                await websocket.send_json({
                    "status": "error",
                    "message": "Missing required fields"
                })
            
    except WebSocketDisconnect:
        manager.disconnect(user_id)