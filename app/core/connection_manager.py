from typing import Dict
from fastapi import WebSocket
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.user import User
from app.models.conversation import Conversation
from app.models.conversation_participant import ConversationParticipant
from app.models.message_response import MessageResponse
from datetime import datetime
import json
import traceback
class ConnectionManager:
    def __init__(self):
        # Track connections by user_id
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_message_to_user_using_websocket(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            message=json.dumps(message, indent=4, sort_keys=True, default=str)

            await self.active_connections[user_id].send_text(message)


    async def broadcast_to_conversation(self, message_data: dict, conversation_id: str, sender_id: str, db: Session) -> MessageResponse:
        """Broadcast message to all active participants in the conversation, respecting block status"""
        # Get the conversation
        conversation = db.exec(select(Conversation).where(Conversation.id == conversation_id)).scalar()

        if not conversation:
            return MessageResponse()
            
        conversation_creator_id = conversation.user_id
        
        # Get sender information
        sender = db.exec(select(User).where(User.UserID == sender_id)).scalar()
        
        # Create MessageResponse object with enhanced data
        response = MessageResponse(
            id=message_data.get("id"),
            sender_id=sender_id,
            conversation_id=conversation_id,
            content=message_data.get("content"),
            type=message_data.get("type"),
            created_at=datetime.fromisoformat(message_data.get("created_at")) if isinstance(message_data.get("created_at"), str) else message_data.get("created_at"),
            status=1,  # Default to delivered
            
            # Add sender profile information
            PhoneNumber=sender.PhoneNumber if sender else None,
            FirstName=sender.FirstName if sender else None,
            LastName=sender.LastName if sender else None,
            Email=sender.Email if sender else None,
            Username=sender.Username if sender else None,
            Bio=sender.Bio if sender else None,
            ProfilePhoto=sender.ProfilePhoto if sender else None,
            backgroundImage=sender.backgroundImage if sender else None,
            PrivacySettingsID=sender.PrivacySettingsID if sender else None,
            
            # Media reference from message
            image_key=message_data.get("image_key")
        )
        
        # Get all participants in this conversation
        participants = db.exec(
            select(ConversationParticipant).where(
                ConversationParticipant.conversation_id == conversation_id,
                ConversationParticipant.deleted == False
            )
        ).scalars().all()
        
        
        # Send to each active participant
        for participant in participants:
            recipient_id = participant.user_id
          
                
            # Skip if recipient isn't connected
            if recipient_id not in self.active_connections:
                continue
                
            
                
            # Send the enriched message data to this participant
            try:
                # Convert MessageResponse to dict for JSON serialization
                await self.send_message_to_user_using_websocket(response.model_dump(), recipient_id)
            except Exception:
                print(traceback.format_exc())
                
                
        return response  # Return the MessageResponse object