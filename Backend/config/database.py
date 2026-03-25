from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy import Column, Integer, Text, JSON
from pgvector.sqlalchemy import Vector
from datetime import datetime
from sqlalchemy import DateTime
from sqlalchemy import text

DATABASE_URL = "postgresql+asyncpg://myuser:mypassword@localhost:5432/TA_db"

engine = create_async_engine(DATABASE_URL, echo=True)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def init_db():
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)

class Base(DeclarativeBase):
    pass

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True)
    text = Column(Text)
    summary = Column(Text)
    images = Column(Integer)
    tables = Column(JSON)
    embedding = Column(Vector(1536))
    source_file = Column(Text)
    file_type = Column(Text)
    chunk_index = Column(Integer)
    page_number = Column(Integer)


class Instruction(Base):
    __tablename__ = "instructions"
    id = Column(Integer, primary_key=True)
    text = Column(Text)
    embedding = Column(Vector(1536))
    created_at = Column(DateTime, default=datetime.utcnow)