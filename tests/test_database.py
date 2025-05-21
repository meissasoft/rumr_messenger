from app.database import get_db
from sqlmodel import text
import pytest

def test_database_connection():
    """Test if database connection can be established"""
    # Get database connection
    db = next(get_db())
    # Simple query to verify connection is working
    cursor = db.exec(text("SELECT 1"))
    result = cursor.fetchone()[0]
    assert result == 1

import os
import pytest
import uuid
from datetime import datetime
from sqlmodel import Session, select, create_engine
from app.models.message import Message

# Test database setup
@pytest.fixture(scope="module")
def test_db_engine():
    """Create a test database engine using the SQLite test database"""
    # Use the SQLite test database created by convert.py
    sqlite_path = os.path.abspath("test_rumr.db")
    
    if not os.path.exists(sqlite_path):
        pytest.skip(f"Test database not found at {sqlite_path}. Run convert.py first.")
    
    # Connect to the SQLite test database
    engine = create_engine(f"sqlite:///{sqlite_path}", connect_args={"check_same_thread": False})
    return engine

@pytest.fixture
def db_session(test_db_engine):
    """Create a database session for testing"""
    with Session(test_db_engine) as session:
        yield session

class TestMessageModelCompatibility:
    
    def test_can_read_legacy_data(self, db_session):
        """Test if the Message model can read data from the legacy table."""
        # Query for existing messages
        statement = select(Message).limit(5)
        messages = db_session.exec(statement).all()
        
        # Verify we got some messages from the database
        assert len(messages) > 0, "No messages found in legacy database"
        
    def test_field_mappings(self, db_session):
        """Test if the Message model fields correctly map to the legacy schema."""
        # Get one message for detailed field verification
        message = db_session.exec(select(Message).limit(1)).first()
        
        # Verify field mappings and types
        assert isinstance(message.id, str)
        assert isinstance(message.conversation_id, str)
        assert isinstance(message.sender_id, str)
        assert isinstance(message.content, str)
        assert isinstance(message.type, str)
        assert isinstance(message.status, bool)
        assert isinstance(message.created_at, datetime)
        # image_key could be None or str
        assert message.image_key is None or isinstance(message.image_key, str)
        
    def test_table_name_matches_legacy(self):
        """Test if the table name in the model matches the legacy table."""
        assert Message.__tablename__ == "messages_rumr_app"
        
    def test_model_instantiation(self):
        """Test that the Message model can be instantiated with proper defaults."""
        # Create a new message instance (without adding to DB)
        new_message = Message(
            conversation_id="test-conv-id",
            sender_id="test-sender",
            content="Hello world",
            type="text",
            status=True
        )
        
        # Check that default fields are populated
        assert new_message.id is not None
        assert isinstance(new_message.id, str)
        assert uuid.UUID(new_message.id, version=4)  # Valid UUID4
        assert new_message.created_at is not None
        assert isinstance(new_message.created_at, datetime)
        assert new_message.image_key is None  # Default for optional field