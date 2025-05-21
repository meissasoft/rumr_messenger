from typing import Generator
import os
import urllib.parse

from sqlmodel import SQLModel, create_engine, Session
from dotenv import load_dotenv
# Load environment variables
load_dotenv()

# Check if we should use SQLite instead of MySQL
USE_SQLITE = os.getenv("USE_SQLITE", "false").lower() in ("true", "1", "yes")

if USE_SQLITE:
    # Use SQLite for development/testing
    # Create data directory if it doesn't exist
    os.makedirs("./data", exist_ok=True)
    
    # SQLite connection string (file-based for persistence)
    SQLALCHEMY_DATABASE_URL = "sqlite:///./data/rumr.db"
    # SQLite requires connect_args for multiple threads
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, 
        connect_args={"check_same_thread": False}
    )
    print("Using SQLite database")
else:
    # SQL Database configuration for production
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME", "rumr_db")
    DB_USER = os.getenv("DB_USER", "dbuser")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "your_secure_password")

    # URL encode the username and password to handle special characters
    encoded_user = urllib.parse.quote_plus(DB_USER)
    encoded_password = urllib.parse.quote_plus(DB_PASSWORD)

    # SQLModel setup with properly encoded connection string
    SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{encoded_user}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    print(f"Using MySQL database: {SQLALCHEMY_DATABASE_URL}")

# Database dependency for FastAPI endpoints
def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session

# Create tables
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)