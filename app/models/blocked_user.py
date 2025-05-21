from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone
import uuid
from sqlmodel import Session, select

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

class BlockedUser(SQLModel, table=True):
    __tablename__ = "blocked_users"  # Table name as requested

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    blocker_id: Optional[str] = Field(default=None, foreign_key="user_rumr_app.UserID")
    blocked_id: Optional[str] = Field(default=None, foreign_key="user_rumr_app.UserID")
    blocked_date: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))