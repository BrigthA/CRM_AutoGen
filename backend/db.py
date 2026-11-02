import os
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import event

os.makedirs('data', exist_ok=True)
engine = create_engine(os.getenv('CRM_DB_URL', 'sqlite:///./data/crm.db'), connect_args={'check_same_thread': False}, pool_pre_ping=True)
if engine.url.get_backend_name() == 'sqlite':
    @event.listens_for(engine, 'connect')
    def pragmas(conn, record):
        cur = conn.cursor(); cur.execute('PRAGMA journal_mode=WAL'); cur.execute('PRAGMA foreign_keys=ON'); cur.execute('PRAGMA busy_timeout=5000'); cur.close()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
Base = declarative_base()
def now(): return datetime.now(timezone.utc)
class Customer(Base):
    __tablename__='customers'
    id=Column(Integer, primary_key=True); name=Column(String(150), nullable=False); email=Column(String(255), unique=True); phone=Column(String(50)); language=Column(String(20), default='English')
class Ticket(Base):
    __tablename__='tickets'
    id=Column(Integer, primary_key=True); customer_id=Column(Integer,ForeignKey('customers.id')); order_id=Column(String(100)); complaint=Column(Text,nullable=False); category=Column(String(50),default='General'); urgency=Column(String(20),default='Medium'); sentiment=Column(String(30),default='Neutral'); summary=Column(Text); response=Column(Text); sources=Column(Text,default=''); status=Column(String(30),default='Open'); escalation_reason=Column(Text,default=''); created_at=Column(DateTime(timezone=True),default=now); updated_at=Column(DateTime(timezone=True),default=now); due_at=Column(DateTime(timezone=True)); assigned_to=Column(String(100)); confidence=Column(Float,default=0)
class Message(Base):
    __tablename__='messages'
    id=Column(Integer,primary_key=True); ticket_id=Column(Integer,ForeignKey('tickets.id')); role=Column(String(20)); content=Column(Text); created_at=Column(DateTime(timezone=True),default=now)
class Document(Base):
    __tablename__='documents'
    id=Column(Integer,primary_key=True); filename=Column(String(255)); content=Column(Text); version=Column(Integer,default=1); created_at=Column(DateTime(timezone=True),default=now)
class Run(Base):
    __tablename__='agent_runs'
    id=Column(Integer,primary_key=True); ticket_id=Column(Integer,ForeignKey('tickets.id')); agent=Column(String(50)); detail=Column(Text); duration_ms=Column(Integer,default=0); created_at=Column(DateTime(timezone=True),default=now)
class Feedback(Base):
    __tablename__='feedback'
    id=Column(Integer,primary_key=True); ticket_id=Column(Integer,ForeignKey('tickets.id')); helpful=Column(Boolean); comment=Column(Text); created_at=Column(DateTime(timezone=True),default=now)
class Review(Base):
    __tablename__='reviews'
    id=Column(Integer,primary_key=True); ticket_id=Column(Integer,ForeignKey('tickets.id')); action=Column(String(30)); notes=Column(Text); reviewer=Column(String(100)); created_at=Column(DateTime(timezone=True),default=now)
class Notification(Base):
    __tablename__='notifications'
    id=Column(Integer,primary_key=True); ticket_id=Column(Integer); subject=Column(String(200)); recipient=Column(String(255)); state=Column(String(30),default='Pending'); created_at=Column(DateTime(timezone=True),default=now)
class Conversation(Base):
    __tablename__='conversations'
    id=Column(Integer,primary_key=True)
    customer_name=Column(String(150),default='Demo Customer')
    email=Column(String(255))
    order_id=Column(String(100))
    title=Column(String(180),default='New conversation')
    created_at=Column(DateTime(timezone=True),default=now)

class ChatTurn(Base):
    __tablename__='chat_turns'
    id=Column(Integer,primary_key=True)
    conversation_id=Column(Integer,ForeignKey('conversations.id'),nullable=False)
    question=Column(Text,nullable=False)
    answer=Column(Text,nullable=False)
    category=Column(String(50))
    urgency=Column(String(20))
    sources=Column(Text,default='[]')
    stages=Column(Text,default='[]')
    ticket_id=Column(Integer,ForeignKey('tickets.id'),nullable=True)
    created_at=Column(DateTime(timezone=True),default=now)

Base.metadata.create_all(engine)
