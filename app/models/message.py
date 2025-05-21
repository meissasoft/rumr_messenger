from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
import uuid
from datetime import datetime, timezone
from sqlmodel import Session, select



class Message(SQLModel, table=True):
    __tablename__ = "messages_rumr_app"  # Explicit table name for existing table

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, index=True)
    conversation_id: str = Field(nullable=False, index=True, foreign_key="conversation_rumr_app.id")
    sender_id: str = Field(nullable=False, index=True, foreign_key="user_rumr_app.UserID")
    content: str = Field(nullable=False)
    type: str = Field(nullable=False, max_length=255)
    status: bool = Field(nullable=False)  # MySQL BIT(1) maps to boolean
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    image_key: Optional[str] = Field(default=None, max_length=255)


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
