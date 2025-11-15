"""
Database initialization module
Handles engine creation, session management, and table creation
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator
import logging

try:
    from .database import Base
    from ..config import settings
except ImportError:
    from models.database import Base
    from config import settings

logger = logging.getLogger(__name__)


# Create engine based on database URL
def create_db_engine(database_url: str = None):
    """
    Create database engine with appropriate configuration
    
    Args:
        database_url: Database connection URL (defaults to settings.DATABASE_URL)
        
    Returns:
        SQLAlchemy Engine
    """
    db_url = database_url or settings.DATABASE_URL
    
    # Special handling for SQLite
    if db_url.startswith("sqlite"):
        engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=settings.DEBUG
        )
    else:
        # PostgreSQL or other databases
        engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            echo=settings.DEBUG
        )
    
    return engine


# Global engine and session factory
engine = create_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """
    Initialize database by creating all tables
    Should be called on application startup
    """
    try:
        logger.info("Initializing database...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def get_db() -> Generator[Session, None, None]:
    """
    Get database session for dependency injection
    
    Usage:
        with get_db() as db:
            # use db session
            pass
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_test_engine():
    """
    Create in-memory SQLite engine for testing
    
    Returns:
        SQLAlchemy Engine for testing
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    return engine


def get_test_db(test_engine) -> Generator[Session, None, None]:
    """
    Get test database session
    
    Args:
        test_engine: Test database engine
        
    Yields:
        Test database session
    """
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Async session support (for future use with asyncpg)
try:
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker as async_sessionmaker
    
    async def create_async_db_engine(database_url: str = None):
        """Create async database engine"""
        db_url = database_url or settings.DATABASE_URL
        
        # Convert postgresql:// to postgresql+asyncpg://
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
        
        engine = create_async_engine(
            db_url,
            echo=settings.DEBUG,
            future=True
        )
        return engine
    
    async def get_async_db() -> AsyncSession:
        """Get async database session"""
        async_engine = await create_async_db_engine()
        AsyncSessionLocal = async_sessionmaker(
            async_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        async with AsyncSessionLocal() as session:
            yield session

except ImportError:
    logger.warning("asyncpg not available, async database support disabled")
    create_async_db_engine = None
    get_async_db = None
