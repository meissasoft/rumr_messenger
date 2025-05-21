from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
import uuid
from datetime import datetime, timezone

class User(SQLModel, table=True):
    __tablename__ = "user_rumr_app"  # Explicit table name as requested

    UserID: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    FirstName: Optional[str] = Field(default=None, max_length=255)
    LastName: Optional[str] = Field(default=None, max_length=255)
    Username: Optional[str] = Field(default=None, max_length=255, unique=True)
    Email: Optional[str] = Field(default=None, max_length=255)
    PhoneNumber: Optional[str] = Field(default=None, max_length=255)
    Password: Optional[str] = Field(default=None, max_length=255)
    ProfilePhoto: Optional[str] = Field(default=None, max_length=255)
    Bio: Optional[str] = Field(default=None)
    PrivacySettingsID: Optional[str] = Field(default=None)
    backgroundImage: Optional[str] = Field(default=None, max_length=255)
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen: Optional[datetime] = Field(default=None)
    fcm_token: Optional[str] = Field(default=None, max_length=255)
    is_user_online: Optional[int] = Field(default=None)
    is_verified: Optional[bool] = Field(default=False)
    isBlocked: Optional[bool] = Field(default=False)
    last_seen_visibility: Optional[bool] = Field(default=True)