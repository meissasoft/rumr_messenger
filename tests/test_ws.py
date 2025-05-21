import json
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
import asyncio
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
from app.app import app
from app.database import get_db
from app.models.message import Message
from app.models.conversation import Conversation
from app.models.conversation_participant import ConversationParticipant
from app.models.blocked_user import BlockedUser
from app.models.user import User
from app.routers.messenger import manager
from sqlmodel import select 
import websockets.exceptions
import time

# Create test database
@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture(name="client")
def client_fixture(session):
    def get_test_db():
        yield session
    
    app.dependency_overrides[get_db] = get_test_db
    with TestClient(app) as client:
        yield client

@pytest.fixture(name="test_data")
def test_data_fixture(session):
    # Create test users
    user1 = User(id="user1", username="user1", email="user1@example.com")
    user2 = User(id="user2", username="user2", email="user2@example.com")
    user3 = User(id="user3", username="user3", email="user3@example.com")
    user4 = User(id="user4", username="user4", email="user4@example.com")
    
    # Create a conversation
    conv = Conversation(
        id="conv1",
        name="Test Conversation",
        user_id="user1",
        conversation_type="text",
        created_at=datetime.now(timezone.utc)
    )
    
    # Add participants to the conversation
    participant1 = ConversationParticipant(
        conversation_id="conv1",
        user_id="user1",
        deleted=False
    )
    participant2 = ConversationParticipant(
        conversation_id="conv1",
        user_id="user2",
        deleted=False
    )
    participant3 = ConversationParticipant(
        conversation_id="conv1",
        user_id="user3",
        deleted=False
    )
    
    # User4 is not in the conversation
    
    # Create a blocked relationship (user1 blocks user3)
    blocked = BlockedUser(
        blocker_id="user1",
        blocked_id="user3"
    )
    
    session.add(user1)
    session.add(user2)
    session.add(user3)
    session.add(user4)
    session.add(conv)
    session.add(participant1)
    session.add(participant2)
    session.add(participant3)
    session.add(blocked)
    session.commit()
    
    return {
        "users": [user1, user2, user3, user4],
        "conversation": conv,
        "participants": [participant1, participant2, participant3]
    }

# Reset the connection manager before each test
@pytest.fixture(autouse=True)
def reset_manager():
    manager.active_connections = {}
    yield

# Test WebSocket connection
def test_websocket_connect(client, test_data):
    with client.websocket_connect(f"/messenger/ws/user1") as websocket:
        # Check connection was established
        assert "user1" in manager.active_connections

def receive_json_with_timeout(websocket, timeout_seconds=5):
    """Custom function to receive JSON with timeout"""
    start_time = time.time()
    while time.time() - start_time < timeout_seconds:
        try:
            # Try to receive a message with a very small timeout
            # This will either return quickly or raise an exception
            return websocket.receive_json()
        except Exception as e:
            # If we get an exception that's not a timeout, reraise it
            if "timeout" not in str(e).lower() and "would block" not in str(e).lower():
                raise
            # Otherwise, sleep a small amount and try again
        time.sleep(0.1)
    
    # If we get here, we timed out
    raise TimeoutError(f"WebSocket receive timed out after {timeout_seconds} seconds")

# Test sending a message through WebSocket
def test_websocket_send_message(client, session, test_data):
    with client.websocket_connect(f"/messenger/ws/user1") as websocket:
        # Send a message
        message_data = {
            "conversation_id": "conv1",
            "content": "Hello, WebSocket!",
            "type": "text"
        }
        websocket.send_json(message_data)
        time.sleep(1)
        # time.sleep(1)  # Give some time for the message to be processed
        
        
        # Check the message was saved to DB
        messages = session.exec(select(Message)).all()
        assert len(messages) == 1

# Test that users can't send messages to conversations they're not part of
def test_unauthorized_conversation(client, session, test_data):
    with client.websocket_connect(f"/messenger/ws/user4") as websocket:
        # Try to send a message to a conversation where user4 is not a participant
        message_data = {
            "conversation_id": "conv1",
            "content": "I shouldn't be able to send this",
            "type": "text"
        }
        websocket.send_json(message_data)
        
        # Check no messages were saved
        messages = session.query(Message).all()
        assert len(messages) == 0

# Test broadcasting behavior with multiple clients
@patch('app.routers.messenger.ConnectionManager.send_message_to_user_using_websocket')
def test_message_broadcasting(mock_send, client, session, test_data):
    # Setup mock for send_personal_message
    loop = asyncio.get_event_loop()
    mock_send.return_value = loop.create_future()
    mock_send.return_value.set_result(None)
    
    with client.websocket_connect(f"/messenger/ws/user1") as websocket1:
        # Add another user connection (normally this would happen in another client)
        manager.active_connections["user2"] = MagicMock()
        
        # Send a message from user1
        message_data = {
            "conversation_id": "conv1",
            "content": "Broadcast test",
            "type": "text"
        }
        websocket1.send_json(message_data)
        time.sleep(1)  # Give some time for the message to be processed
        # Check if the message would be broadcast to user2
        # (The actual broadcasting happens in broadcast_to_conversation)
        assert mock_send.called
        # We expect user2 to receive the message
        assert any(call.args[1] == "user2" for call in mock_send.call_args_list)



# Test handling invalid JSON
def test_invalid_json_message(client, session, test_data):
    with client.websocket_connect(f"/messenger/ws/user1") as websocket:
        # Send invalid JSON
        websocket.send_text("This is not valid JSON")
        
        # This shouldn't raise an exception, but also shouldn't save any messages
        messages = session.query(Message).all()
        assert len(messages) == 0

# Test disconnection
def test_websocket_disconnect(client, test_data):
    with client.websocket_connect(f"/messenger/ws/user1") as websocket:
        # Connection is established
        assert "user1" in manager.active_connections
    
    # After the context manager exits, connection should be closed
    # and removed from manager
    assert "user1" not in manager.active_connections
