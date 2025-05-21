from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone

class MessageResponse(SQLModel):
    id: Optional[str] = Field(default=None, primary_key=True)
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    sender_id: Optional[str] = None
    conversation_id: Optional[str] = None
    content: Optional[str] = None
    type: Optional[str] = None
    status: Optional[int] = 1
    
    # User profile information
    PhoneNumber: Optional[str] = None
    FirstName: Optional[str] = None
    LastName: Optional[str] = None
    Email: Optional[str] = None
    Username: Optional[str] = None
    Bio: Optional[str] = None
    
    # Media references
    image_key: Optional[str] = None
    ProfilePhoto: Optional[str] = None
    backgroundImage: Optional[str] = None
    
    # Additional fields
    PrivacySettingsID: Optional[str] = None
    
    def __repr__(self):
        return f"MessageResponse(id={self.id}, sender_id={self.sender_id}, content={self.content})"